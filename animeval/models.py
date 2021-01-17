from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.base_user import BaseUserManager
from django_mysql.models import ListCharField, ListTextField

# Create your models here.

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.
    Username and password are required. Other fields are optional.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        #abstract = True # ここを削除しないといけないことを忘れない！！！！！！！！！！

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

class ProfileModel(models.Model):

    GENDER_CHOICES = (
        (1,'男性'),
        (2,'女性'),
        (3,'その他'),
    )

    user = models.ForeignKey(User, on_delete = models.CASCADE,related_name = 'user')
    nickname = models.CharField(max_length = 10,verbose_name = 'ニックネーム')
    gender = models.IntegerField(choices = GENDER_CHOICES, blank = True)
    favarite_anime = models.CharField(max_length = 100)
    avator = models.ImageField(upload_to = 'images/', blank = True)
    

    def __str__(self):
        return self.nickname

class AnimeModel(models.Model):
    title = models.CharField(max_length = 100)
    started = models.CharField(max_length = 10,default = 'None')
    genre = models.CharField(max_length = 15, default= 'None')
    corporation = models.CharField (max_length = 100,default = 'None')
    character_voice = ListCharField(
        base_field = models.CharField(max_length = 20),
        size = 6,
        max_length = (6 * 21),
        default = ['None']
    )

    def __str__(self):
        return self.title

class ReviewModel(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    profile = models.ForeignKey(ProfileModel, on_delete = models.CASCADE)
    anime = models.ForeignKey(AnimeModel, on_delete = models.CASCADE)
    review_title = models.CharField(max_length =50)
    review_content = models.TextField()
    evaluation = ListTextField(
        base_field = models.IntegerField(),
        size = 5,
        default = [0,0,0,0,0]
    )
    evaluation_ave = models.DecimalField(max_digits=2, decimal_places=1)
    post_date = models.DateTimeField(auto_now_add = True)

class Counter(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    counter = ListTextField(
        base_field = models.IntegerField(),
        size = 8,
        default = [0,0,0,0,0,0,0,0]
    )

class AccessReview(models.Model):
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    review = models.ForeignKey(ReviewModel, on_delete = models.CASCADE)

    def __str__(self):
        return 'アクセス名:{} / レビュータイトル:{}'.format(self.user.username, self.review.review_title)

class Comment(models.Model):
    comment = models.CharField(max_length = 255)
    review = models.ForeignKey(ReviewModel, on_delete = models.CASCADE)
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)

class ReplyComment(models.Model):
    reply = models.CharField(max_length = 255)
    comment = models.ForeignKey(Comment, on_delete = models.CASCADE)
    user = models.ForeignKey(User,on_delete = models.CASCADE)
    created_at = models.DateTimeField(auto_now_add = True)

class Like(models.Model):
    review = models.ForeignKey(ReviewModel, on_delete = models.CASCADE)
    user = models.ForeignKey(User, on_delete = models.CASCADE)
    like = models.IntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add = True)