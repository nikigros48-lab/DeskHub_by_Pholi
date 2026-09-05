from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone = models.CharField(max_length=13, verbose_name="Номер телефона")
    avatar = models.ImageField(upload_to="avatar", default="avatar/default.jpg", blank=True, null=True, verbose_name="Фото профиля")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"