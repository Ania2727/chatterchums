from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Forum(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_forums', default=None)
    #name = models.CharField(max_length=50, default="Anonymous")
    link = models.CharField(max_length=100, null=True, blank=True)
    date_posted = models.DateTimeField(auto_now_add=True, null=True)
    title = models.CharField(max_length=250)
    description = models.CharField(max_length=750, blank=True)
    members = models.ManyToManyField(User, related_name='joined_forums', blank=True)
    tags = models.ManyToManyField(Tag, related_name='forums', blank=True)

    def __str__(self):
        return str(self.title)

    def get_absolute_url(self):
        return reverse('forums:forum_detail', args=[str(self.id)])

class Topic(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name='topics')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    title = models.CharField(max_length=250)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('forums:topic_detail', args=[str(self.forum.id), str(self.id)])


class Comment(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author.username} on {self.topic.title}'

class Complaint(models.Model):

    COMPLAINT_REASONS = [
        ('hate_speech', 'hate speech'),
        ('spam', 'spam'),
        ('offensive', 'offensive'),
        ('harassment', 'harassment'),
        ('other', 'other'),
    ]

    complaint_text = models.TextField(max_length=256)
    complaint_time = models.DateTimeField(auto_now_add=True)
    complaint_type = models.CharField(max_length=32, choices=COMPLAINT_REASONS)

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')

    # Ціль скарги: тільки одне поле має бути заповнене
    user_target = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_received', null=True, blank=True)
    forum_target = models.ForeignKey(Forum, on_delete=models.CASCADE, null=True, blank=True)
    topic_target = models.ForeignKey(Topic, on_delete=models.CASCADE, null=True, blank=True)
    comment_target = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)

    status = models.CharField(
        max_length=16,
        choices=[('pending', 'pending'), ('reviewed', 'reviewed'), ('dismissed', 'dismissed')],
        default='pending'
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        targets = [self.user_target, self.forum_target, self.topic_target, self.comment_target]
        filled = list(filter(None, targets))
        if len(filled) != 1:
            raise ValidationError("The complaint must refer to exactly one object: a forum, a topic, a user, or a comment.")

    def get_target(self):
        return self.user_target or self.forum_target or self.topic_target or self.comment_target

    def __str__(self):
        return f"Complaint about {self.get_target()} — reason: {self.get_complaint_type_display()}"