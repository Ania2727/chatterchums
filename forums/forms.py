from django.forms import ModelForm
from forums.models import *
from django import forms


class CreateInForum(ModelForm):
    link = forms.URLField(required=False)
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select relevant tags for your forum"
    )

    class Meta:
        model = Forum
        fields = ['title', 'description', 'link', 'tags']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(CreateInForum, self).__init__(*args, **kwargs)
        self.fields['link'].required = False

    def save(self, commit=True):
        instance = super(CreateInForum, self).save(commit=False)
        if self.user:
            instance.creator = self.user
            instance.name = self.user.username  # Username is display name.
        if commit:
            instance.save()
            # Add the creator as a member automatically
            instance.members.add(self.user)
            # Save the tags
            self.save_m2m()
        return instance


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Topic title'}),
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Describe your topic here...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.forum = kwargs.pop('forum', None)
        super(TopicForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TopicForm, self).save(commit=False)
        if self.user:
            instance.author = self.user
        if self.forum:
            instance.forum = self.forum
        if commit:
            instance.save()
        return instance


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your comment...'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.topic = kwargs.pop('topic', None)
        super(CommentForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(CommentForm, self).save(commit=False)
        if self.user:
            instance.author = self.user
        if self.topic:
            instance.topic = self.topic
        if commit:
            instance.save()
        return instance