from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserExtra(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='extra'
    )

    character = models.CharField(
        max_length=1,
        null=True,
        blank=True
    )

    tiny_number = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} extra"
    
    
    

@receiver(post_save, sender=User)
def create_user_extra(sender, instance, created, **kwargs):
    if created:
        UserExtra.objects.create(user=instance)