from uuid import uuid4

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

from recipes.storage import (
    RecipeImageError,
    prepare_recipe_image,
    r2_client,
    r2_is_configured,
)


class AvatarImageError(Exception):
    pass


def upload_avatar(uploaded_file, user_id):
    try:
        body = prepare_recipe_image(uploaded_file)
        image_key = f"avatars/{user_id}/{uuid4().hex}.webp"
        r2_client().put_object(
            Bucket=settings.R2_BUCKET_NAME,
            Key=image_key,
            Body=body,
            ContentType="image/webp",
            CacheControl="private, max-age=3600",
        )
        return image_key
    except RecipeImageError as error:
        raise AvatarImageError(str(error)) from error
    except (BotoCoreError, ClientError) as error:
        raise AvatarImageError(
            "Das Profilbild konnte momentan nicht gespeichert werden."
        ) from error


def get_avatar_url(image_key):
    if not image_key or not r2_is_configured():
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


def delete_avatar(image_key):
    if not image_key or not r2_is_configured():
        return
    try:
        r2_client().delete_object(Bucket=settings.R2_BUCKET_NAME, Key=image_key)
    except (RecipeImageError, BotoCoreError, ClientError):
        return
