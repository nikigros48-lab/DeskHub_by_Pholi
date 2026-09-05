from django import forms
from .models import City, Place

class CoworkingFilterForm(forms.Form):
    city = forms.ModelChoiceField(
        queryset=City.objects.all(),
        required=False,
        empty_label="Все города",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    place_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + list(Place.PLACE_TYPE),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label="Дата (доступные слоты)"
    )