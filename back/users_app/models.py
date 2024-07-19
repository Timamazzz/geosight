from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from users_app.utils import generate_activation_code


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Поле "Email" должно быть заполнено')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class Company(models.Model):
    name = models.CharField(max_length=256, unique=True, verbose_name="Название компании")

    class Meta:
        verbose_name = "Компания"
        verbose_name_plural = "Компании"

    def __str__(self):
        return self.name


class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', 'Пользователь'),
        ('staff', 'Сотрудник'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    ]
    username = models.CharField(max_length=150, unique=False, blank=True, null=True, verbose_name="Имя пользователя")
    email = models.EmailField(unique=True, blank=False, null=False, verbose_name="Email")
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True, verbose_name="Номер телефона")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name="Роль")
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, blank=True, null=True, related_name='users', verbose_name="Компания")
    avatar = models.ImageField(null=True, blank=True, verbose_name="Аватар")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class ActivationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Пользователь")
    code = models.CharField(max_length=4, default=generate_activation_code, verbose_name="Код активации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    @property
    def is_expired(self):
        expiration_time = self.created_at + timezone.timedelta(hours=3)
        return timezone.now() > expiration_time

    @property
    def regenerate_code(self):
        self.code = generate_activation_code()
        self.created_at = timezone.now()
        self.save()
        return self.code
