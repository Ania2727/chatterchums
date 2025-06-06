from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from forums.models import Tag

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    bio = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    interests = models.ManyToManyField(Tag, related_name='interested_users', blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, email=instance.email)
    else:
        instance.userprofile.save()