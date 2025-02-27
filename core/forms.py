from django import forms
from .models import Recipe, InventoryItem, MealPlan

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'instructions']

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['ingredient', 'current_stock', 'threshold']

class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['recipe', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }