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


class MealLogSearchForm(forms.Form):
    q = forms.CharField(required=False, label="キーワード")
    date_from = forms.DateField(required=False, label="開始日")
    date_to = forms.DateField(required=False, label="終了日")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["q"].widget.attrs.update({"placeholder": "タグや気分、食材を入力"})
        self.fields["date_from"].widget.attrs.update({"type": "date"})
        self.fields["date_to"].widget.attrs.update({"type": "date"})

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            self.add_error("date_to", "開始日以降の日付を指定してください。")
        return cleaned_data


class BackupImportForm(forms.Form):
    backup_file = forms.FileField(label="バックアップ ZIP")
