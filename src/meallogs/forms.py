from django import forms

from .constants import TIME_MINUTES_CHOICES
from .enums import TasteLevel
from .models import MealLog


class MealLogForm(forms.ModelForm):
    time_minutes = forms.ChoiceField(
        required=False,
        choices=[("", "-")] + [(value, str(value)) for value in TIME_MINUTES_CHOICES],
    )

    class Meta:
        model = MealLog
        fields = ["time_minutes", "taste_level"]

    def clean_time_minutes(self):
        value = self.cleaned_data.get("time_minutes")
        if value in (None, ""):
            return None
        value_int = int(value)
        if value_int not in TIME_MINUTES_CHOICES:
            raise forms.ValidationError("指定できない時間です。")
        return value_int

    def clean_taste_level(self):
        value = self.cleaned_data.get("taste_level")
        if value in (None, ""):
            return None
        value_int = int(value)
        if not TasteLevel.is_valid_value(value_int):
            raise forms.ValidationError("指定できない値です。")
        return value_int
