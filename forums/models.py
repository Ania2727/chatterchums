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
    name = models.CharField(max_length=50, default="Anonymous")
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