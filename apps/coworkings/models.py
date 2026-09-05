from zoneinfo import available_timezones

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.users.models import User


class City(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название города", unique=True)
    timezone = models.CharField(
        max_length=50,
        choices=[(tz, tz) for tz in sorted(available_timezones())],
        default='Asia/Novosibirsk',
        verbose_name="Часовой пояс"
    )

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self):
        return self.name


class Coworking(models.Model):
    picture = models.ImageField(upload_to="coworking", default="coworking/default.jpg", blank=True, null=True, verbose_name="Изображение коворкинга")
    name = models.CharField(max_length=100, verbose_name="Название")
    address = models.CharField(max_length=250, verbose_name="Адрес")
    city = models.ForeignKey(City, on_delete=models.CASCADE, verbose_name="Город")
    work_time_start = models.TimeField(verbose_name="Начало рабочего дня")
    work_time_end = models.TimeField(verbose_name="Конец рабочего дня")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["address", "city"],
                name="unique_city_address",
            )
        ]
        verbose_name = 'Коворкинг'
        verbose_name_plural = 'Коворкинги'

    def __str__(self):
        return f"{self.name} - {self.city}. {self.address} | {self.work_time_start} - {self.work_time_end}"


class Place(models.Model):
    PLACE_TYPE = (
        ("Workplace", "Рабочее место"),
        ("Meeting_room", "Переговорная"),
    )

    coworking = models.ForeignKey(Coworking, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=PLACE_TYPE, verbose_name="Тип места")
    name = models.CharField(max_length=50, verbose_name="Название")
    picture = models.ImageField(upload_to="coworking/place", default="coworking/place/default.jpg", blank=True, null=True)
    capacity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Место"
        verbose_name_plural = "Места"
        constraints = [
            models.UniqueConstraint(
                fields=["coworking", "name", "type"],
                name="unique_place_per_coworking",
            )
        ]

    def __str__(self):
        return f"{self.get_type_display()} {self.name}"


class Slot(models.Model):
    time_start = models.DateTimeField(verbose_name="Начало слота")
    time_end = models.DateTimeField(verbose_name="Конец слота")
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name="slots", verbose_name="Место")
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Забронировавший пользователь")

    class Meta:
        verbose_name = "Слот"
        verbose_name_plural = "Слоты"

    def is_free(self):
        return self.user is None

    def clean(self):
        if not self.time_start or not self.time_end:
            raise ValidationError("Необходимо указать время начала и конца слота")

        if self.time_start.date() != self.time_end.date():
            raise ValidationError("Слот не может длиться более одного дня.")

        if self.time_start >= self.time_end:
            raise ValidationError("Время начала должно быть меньше времени конца слота.")

        coworking = self.place.coworking
        slot_start = self.time_start.time()
        slot_end = self.time_end.time()

        if slot_start < coworking.work_time_start or slot_end > coworking.work_time_end:
            raise ValidationError(
                f"Слот должен быть в пределах рабочего времени коворкинга ({coworking.work_time_start} – {coworking.work_time_end})"
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.place} - {self.time_start}:{self.time_end}"