from __future__ import annotations

import io
import warnings
from functools import lru_cache
from uuid import uuid4

import boto3
from botocore.client import Config
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from PIL import Image, ImageOps, UnidentifiedImageError


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_DIMENSION = 1920
MAX_IMAGE_PIXELS = 25_000_000


class RecipeImageError(Exception):
    """Eine sichere, für die API geeignete Fehlermeldung beim Bild-Upload."""


def r2_is_configured() -> bool:
    return all((
        settings.R2_ACCESS_KEY_ID,
        settings.R2_SECRET_ACCESS_KEY,
        settings.R2_BUCKET_NAME,
        settings.R2_ENDPOINT_URL,
    ))


@lru_cache(maxsize=1)
def r2_client():
    if not r2_is_configured():
        raise RecipeImageError(
            "Der Bildspeicher ist noch nicht vollständig konfiguriert."
        )
    return boto3.client(
        service_name="s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


def prepare_recipe_image(uploaded_file) -> bytes:
    content_type = str(getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise RecipeImageError("Bitte lade ein JPG-, PNG- oder WebP-Bild hoch.")
    if getattr(uploaded_file, "size", 0) > settings.RECIPE_IMAGE_MAX_BYTES:
        max_mb = max(1, settings.RECIPE_IMAGE_MAX_BYTES // (1024 * 1024))
        raise RecipeImageError(f"Das Bild darf höchstens {max_mb} MB groß sein.")

    try:
        uploaded_file.seek(0)
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(uploaded_file) as source:
                width, height = source.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise RecipeImageError("Das Bild hat eine zu hohe Auflösung.")
                source.load()
                image = ImageOps.exif_transpose(source)
                has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
                image = image.convert("RGBA" if has_alpha else "RGB")
                image.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
                output = io.BytesIO()
                image.save(output, format="WEBP", quality=86, method=6)
                return output.getvalue()
    except RecipeImageError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise RecipeImageError("Die Bilddatei ist beschädigt oder wird nicht unterstützt.") from error


def upload_recipe_image(uploaded_file, user_id: int) -> str:
    body = prepare_recipe_image(uploaded_file)
    image_key = f"recipes/{user_id}/{uuid4().hex}.webp"
    try:
        r2_client().put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=image_key,
            Body=body,
            ContentType="image/webp",
            CacheControl="private, max-age=3600",
        )
    except (BotoCoreError, ClientError) as error:
        raise RecipeImageError(
            "Das Bild konnte momentan nicht gespeichert werden. Bitte versuche es erneut."
        ) from error
    return image_key


def get_recipe_image_url(image_key: str) -> str | None:
    if not image_key:
        return None
    try:
        return r2_client().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.R2_BUCKET_NAME,
                "Key": image_key,
                "ResponseContentType": "image/webp",
            },
            ExpiresIn=settings.R2_PRESIGNED_URL_TTL,
        )
    except (RecipeImageError, BotoCoreError, ClientError):
        return None


def delete_recipe_image(image_key: str) -> None:
    if not image_key or not r2_is_configured():
        return
    try:
        r2_client().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=image_key)
    except (BotoCoreError, ClientError):
        # Fehlgeschlagene Bereinigung darf das Speichern/Löschen eines Rezepts
        # nicht verhindern. Der Schlüssel kann später erneut bereinigt werden.
        return


def delete_recipe_image_if_unused(image_key: str) -> None:
    if not image_key:
        return
    from .models import Recipe

    if not Recipe.objects.filter(image_key=image_key).exists():
        delete_recipe_image(image_key)
