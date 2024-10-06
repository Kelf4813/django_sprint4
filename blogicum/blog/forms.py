from django.contrib.auth import get_user_model
from django import forms
from .models import Post, Comment

User = get_user_model()


class ProfileEdit(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class NewPost(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        exclude = ['author', 'is_published']
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }


class AddComment(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
