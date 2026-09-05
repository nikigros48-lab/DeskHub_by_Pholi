from django.core.exceptions import ValidationError
from django.db import models

from apps.coworkings.models import Slot
from apps.users.models import User


class Reservation(models.Model):
    STATUS_CHOICES = (
        ('awaiting', 'Ожидает'),
        ('approved', 'Подтверждена'),
        ('declined', 'Отклонена'),
        ('cancelled', 'Отменена'),
        ('completed', 'Завершена'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(choices=STATUS_CHOICES, default='awaiting', max_length=50)
    slot = models.ForeignKey(Slot, on_delete=models.SET_NULL, null=True, blank=True)
    amount_people = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"

    def clean(self):
        # Проверка занятости слота
        if self.status in ['awaiting', 'approved']:
            if self.slot is None:
                raise ValidationError("Этого слота не существует")
            if self.slot.user and self.slot.user != self.user:
                raise ValidationError("Этот слот уже занят другим пользователем.")
        # Проверка фактического количества людей с вместимостью места
        if self.status not in ['completed', 'cancelled', 'declined']:
            capacity_place = self.slot.place.capacity
            if self.amount_people > capacity_place:
                raise ValidationError(f"Максимальная вместимость данного места - {capacity_place}")

    def save(self, *args, **kwargs):
        def occupy_slot():
            if self.slot and self.slot.user is None:
                self.slot.user = self.user
                self.slot.save(update_fields=['user'])

        def release_slot():
            if self.slot and self.slot.user == self.user:
                self.slot.user = None
                self.slot.save(update_fields=['user'])

        if self.pk:
            old = Reservation.objects.get(pk=self.pk)
            old_status = old.status
            new_status = self.status

            if old_status not in ['awaiting', 'approved'] and new_status in ['awaiting', 'approved']:
                occupy_slot()
            elif old_status in ['awaiting', 'approved'] and new_status not in ['awaiting', 'approved']:
                release_slot()
        else:
            if self.status in ['awaiting', 'approved']:
                occupy_slot()

        self.full_clean()
        super().save(*args, **kwargs)


