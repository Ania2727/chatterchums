from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from forums.models import Tag

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    bio = models.TextField(max_length=500, blank=True, verbose_name="Biography")
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    interests = models.ManyToManyField(Tag, related_name='interested_users', blank=True)
    show_interests = models.BooleanField(default=True, verbose_name="Show interests to other users")
    
    is_banned = models.BooleanField(default=False)
    ban_duration = models.IntegerField(null=True, blank=True)  # Duration in months
    ban_end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def is_currently_banned(self):
        if self.is_banned and self.ban_end_date:
            if timezone.now().date() >= self.ban_end_date:

                self.is_banned = False
                self.ban_duration = None
                self.ban_end_date = None
                self.save(update_fields=["is_banned", "ban_duration", "ban_end_date"])
                return False
            return True
        return False

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, email=instance.email)
    else:
        instance.userprofile.save()


def is_forum_admin(self):
    print(self.groups)
    return self.groups.filter(name='administrator').exists() or self.is_superuser

def is_forum_moderator(self):
    return self.groups.filter(name__in=['administrator', 'moderator']).exists() or self.is_superuser

User.add_to_class("is_forum_admin", is_forum_admin)
User.add_to_class("is_forum_moderator", is_forum_moderator)