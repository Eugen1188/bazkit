# Bazkit öffentlich freischalten

Die Anwendung bleibt mit `PUBLIC_RELEASE_ENABLED=False` weiterhin über die bisherige Serveradresse deploybar. Für einen öffentlichen Release werden die folgenden Einstellungen bewusst hart geprüft.

## 1. Domain und HTTPS

1. Eine Domain kaufen und deren A-/AAAA-Eintrag auf den Bazkit-Server zeigen lassen.
2. In `/opt/bazkit/.env` die Werte auf die echte Domain setzen:

   ```dotenv
   BAZKIT_DOMAIN=bazkit.example
   BAZKIT_HTTPS_ENABLED=True
   FRONTEND_URL=https://bazkit.example
   DJANGO_ALLOWED_HOSTS=bazkit.example,localhost,127.0.0.1
   DJANGO_CSRF_TRUSTED_ORIGINS=https://bazkit.example
   DJANGO_CORS_ALLOWED_ORIGINS=https://bazkit.example
   ```

3. TCP 80 und 443 in der Firewall öffnen. Nach erfolgreichem HTTPS-Test Port 8080 von außen schließen.
4. In GitHub unter **Settings → Secrets and variables → Actions → Variables** die Variable `BAZKIT_PUBLIC_URL` mit `https://bazkit.example` anlegen.

Beim nächsten Deployment startet das Gateway automatisch, beschafft das TLS-Zertifikat und aktiviert die sicheren Django-Cookies, HTTPS-Weiterleitung und HSTS.

## 2. Offsite-Backups und öffentliche Freigabe

Für Datenbank-Backups nach Möglichkeit einen getrennten, nicht öffentlichen R2-Bucket verwenden. In `/opt/bazkit/.env` setzen:

```dotenv
OFFSITE_BACKUP_ENABLED=True
OFFSITE_BACKUP_REQUIRED=True
R2_BACKUP_BUCKET_NAME=bazkit-database-backups
R2_BACKUP_PREFIX=database-backups
PUBLIC_RELEASE_ENABLED=True
```

Die vorhandenen `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` und `R2_ENDPOINT_URL` müssen Schreib- und Leserechte für diesen Bucket haben. Jedes Backup wird vor dem Upload geprüft; der Upload wird anschließend per Objektgröße kontrolliert. Einmal pro Woche lädt die Automation das neueste Offsite-Backup erneut herunter und stellt es in einer isolierten Datenbank wieder her.

Mit `PUBLIC_RELEASE_ENABLED=True` bricht ein Deployment ab, wenn HTTPS, E-Mail, Monitoring, Bildspeicher oder Offsite-Backups fehlen.

## 3. Rechtliche Angaben vor dem Start bestätigen

Im aktuellen Impressum ist hinterlegt, dass keine Teilnahme an einer Verbraucherschlichtung erfolgt. Vor dem öffentlichen Start muss der Betreiber bestätigen, dass diese Aussage zutrifft und dass kein eintragungspflichtiges Register mit anzugebender Registernummer besteht. Die Texte sollten zusätzlich fachlich geprüft werden.
