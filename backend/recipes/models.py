from django.db import models

class Recipe(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    instructions = models.TextField()
    
class Incredients(models.Model):
    items = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="incredients"
    )
    name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    