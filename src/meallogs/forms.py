from django import forms

from .constants import TIME_MINUTES_CHOICES
from .enums import IngredientCategory, TasteLevel
from .models import MealLog


class MealLogForm(forms.ModelForm):
    time_minutes = forms.ChoiceField(
        required=False,
        choices=[("", "-")] + [(value, str(value)) for value in TIME_MINUTES_CHOICES],
    )
    ingredient_categories = forms.MultipleChoiceField(
        required=False,
        choices=IngredientCategory.choices,
        widget=forms.CheckboxSelectMultiple,
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

    def clean_ingredient_categories(self):
        values = self.cleaned_data.get("ingredient_categories") or []
        if not values:
            return []
        try:
            parsed = [int(value) for value in values]
        except (TypeError, ValueError) as exc:
            raise forms.ValidationError("指定できない値です。") from exc
        valid_values = {choice.value for choice in IngredientCategory}
        if any(value not in valid_values for value in parsed):
            raise forms.ValidationError("指定できない値です。")
        return parsed
