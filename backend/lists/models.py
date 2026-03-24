from django.db import models
from django.conf import settings


class lists(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lists')
    titel = models.CharField(max_length=30)
    
    
    