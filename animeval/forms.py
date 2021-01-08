from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django import forms
from . import models

#################User info.#######################
class LoginForm(AuthenticationForm):
    """ログインフォーム"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class UserCreateForm(UserCreationForm):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
    class Meta:
        model = models.User
        fields = ('username',)

class CreateProfile(forms.ModelForm):
    class Meta:
        model = models.ProfileModel
        fields = ('nickname','gender','favarite_anime')
        
class CreateReview(forms.ModelForm):
    class Meta:
        model = models.ReviewModel
        fields = ('anime_genre',)

class CreateComment(forms.ModelForm):
    class Meta:
        model = models.Comment
        fields = ('comment',)

class CreateReply(forms.ModelForm):
    class Meta:
        model = models.ReplyComment
        fields = ('reply',)









