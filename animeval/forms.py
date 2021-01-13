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

class CreateProfile(forms.Form):

    GENDER_CHOICES = (
    (1,'男性'),
    (2,'女性'),
    (3,'その他'),
    )

    nickname = forms.CharField(max_length = 10)
    gender = forms.ChoiceField(
        widget = forms.RadioSelect(attrs = {'class' : 'form'}),
        choices = GENDER_CHOICES,
        required = True,
        initial = '男性'
    )
    favarite_anime = forms.CharField(max_length = 100)
    avator = forms.ImageField(required = True)

        
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

class CSVUpload(forms.Form):
    file = forms.FileField(label = 'CSVファイル', help_text = '拡張子CSVのファイルをアップロードしてください')





