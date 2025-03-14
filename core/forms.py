from django import forms
from django.forms.models import BaseInlineFormSet
from .models import Recipe, InventoryItem, MealPlan, RecipeIngredient, Ingredient

# Extended measurement unit choices.
# For mass, canonical unit is grams (g); for volume, canonical is milliliters (ml).
UNIT_CHOICES = [
    ("kg", "Kilograms (kg) [1000 g]"),
    ("g", "Grams (g) [1 g]"),
    ("oz", "Ounces (oz) [28.35 g]"),
    ("lb", "Pounds (lb) [453.59 g]"),
    ("L", "Liters (L) [1000 ml]"),
    ("ml", "Milliliters (ml) [1 ml]"),
    ("cup", "Cups (cup) [240 ml]"),
    ("tbsp", "Tablespoons (tbsp) [15 ml]"),
    ("tsp", "Teaspoons (tsp) [5 ml]"),
    ("pint", "Pints (pint) [473 ml]"),
    ("gallon", "Gallons (gallon) [3785 ml]"),
    ("pieces", "Pieces"),
    ("fillets", "Fillets"),
]

# Conversion map: maps a unit to a tuple (canonical_unit, conversion_factor).
CONVERSION_MAP = {
    "kg": ("g", 1000),
    "g": ("g", 1),
    "oz": ("g", 28.3495),
    "lb": ("g", 453.592),
    "L": ("ml", 1000),
    "ml": ("ml", 1),
    "cup": ("ml", 240),
    "tbsp": ("ml", 15),
    "tsp": ("ml", 5),
    "pint": ("ml", 473.176),
    "gallon": ("ml", 3785.41),
    "pieces": ("pieces", 1),
    "fillets": ("fillets", 1),
}

class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'description', 'instructions']

class RecipeIngredientForm(forms.ModelForm):
    # New ingredient text input appears only if no existing ingredient is selected.
    new_ingredient = forms.CharField(
        required=False,
        label="New Ingredient",
        help_text="Enter a new ingredient name if not listed."
    )
    # Measurement unit dropdown – always shown.
    measurement_unit = forms.ChoiceField(
        required=False,
        label="Measurement Unit",
        choices=UNIT_CHOICES,
        help_text="Select the measurement unit for this ingredient's quantity."
    )

    class Meta:
        model = RecipeIngredient
        fields = ['ingredient', 'quantity', 'new_ingredient', 'measurement_unit']

    def __init__(self, *args, **kwargs):
        super(RecipeIngredientForm, self).__init__(*args, **kwargs)
        self.fields['ingredient'].required = False
        self.fields['ingredient'].queryset = Ingredient.objects.all()
        # Override label to show the ingredient's canonical unit.
        self.fields['ingredient'].label_from_instance = lambda obj: f"{obj.name} ({obj.measurement_unit})"
        # (Optional) You could set an initial value for measurement_unit here if desired.
        self.fields['measurement_unit'].initial = ''

    def clean(self):
        cleaned_data = super().clean()
        ingredient = cleaned_data.get('ingredient')
        new_ing = cleaned_data.get('new_ingredient')
        if not ingredient and not new_ing:
            raise forms.ValidationError("Please select an ingredient or enter a new one.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        qty = self.cleaned_data.get('quantity')
        chosen_unit = self.cleaned_data.get('measurement_unit')
        new_ing = self.cleaned_data.get('new_ingredient')
        if new_ing:
            # For new ingredients, default to "g" if no unit is chosen.
            if not chosen_unit:
                chosen_unit = "g"
            canonical_unit, factor = CONVERSION_MAP.get(chosen_unit, ("unit", 1))
            converted_qty = qty * factor
            from .models import Ingredient
            ingredient, created = Ingredient.objects.get_or_create(
                name=new_ing.strip(),
                defaults={'measurement_unit': canonical_unit}
            )
            instance.ingredient = ingredient
            instance.quantity = converted_qty
        else:
            # For existing ingredients, use the chosen measurement unit if provided.
            ingredient = self.cleaned_data.get('ingredient')
            if chosen_unit:
                canonical_unit, factor = CONVERSION_MAP.get(chosen_unit, (ingredient.measurement_unit, 1))
                converted_qty = qty * factor
                instance.quantity = converted_qty
            else:
                instance.quantity = qty
        if commit:
            instance.save()
        return instance

class BaseRecipeIngredientInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        ingredients = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            ingredient = form.cleaned_data.get('ingredient')
            new_ingredient = form.cleaned_data.get('new_ingredient')
            ing_identifier = None
            if ingredient:
                ing_identifier = ingredient.id
            elif new_ingredient:
                ing_identifier = new_ingredient.strip().lower()
            if ing_identifier:
                if ing_identifier in ingredients:
                    raise forms.ValidationError("Duplicate ingredients are not allowed in a recipe.")
                ingredients.append(ing_identifier)

# core/forms.py
from django import forms
from .models import InventoryItem, Ingredient
from .forms import UNIT_CHOICES, CONVERSION_MAP  # assuming these are defined above

class InventoryItemForm(forms.ModelForm):
    new_ingredient = forms.CharField(
        required=False,
        label="New Ingredient",
        help_text="Enter a new ingredient name if not listed."
    )
    measurement_unit = forms.ChoiceField(
        required=False,
        label="Measurement Unit",
        choices=UNIT_CHOICES,
        help_text="Select the measurement unit for the current stock."
    )

    class Meta:
        model = InventoryItem
        fields = ['ingredient', 'current_stock', 'new_ingredient', 'measurement_unit']

    def __init__(self, *args, **kwargs):
        super(InventoryItemForm, self).__init__(*args, **kwargs)
        self.fields['ingredient'].required = False
        self.fields['ingredient'].queryset = Ingredient.objects.all()
        self.fields['ingredient'].label_from_instance = lambda obj: f"{obj.name} ({obj.measurement_unit})"
        
        # If updating an existing inventory item, set the default measurement unit
        if self.instance and self.instance.pk and self.instance.ingredient:
            self.fields['measurement_unit'].initial = self.instance.ingredient.measurement_unit
            # For predefined ingredients, remove new ingredient fields.
            if self.instance.ingredient.is_predefined:
                self.fields.pop('new_ingredient', None)
                self.fields.pop('measurement_unit', None)
        # For creation (no instance yet), leave fields visible.
    
    def clean(self):
        cleaned_data = super().clean()
        ingredient = cleaned_data.get('ingredient')
        new_ing = cleaned_data.get('new_ingredient')
        if not ingredient and not new_ing:
            raise forms.ValidationError("Please select an ingredient or enter a new one.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        stock = self.cleaned_data.get('current_stock')
        # Only process new_ingredient if the field exists in cleaned_data.
        new_ing = self.cleaned_data.get('new_ingredient') if 'new_ingredient' in self.cleaned_data else None
        chosen_unit = self.cleaned_data.get('measurement_unit') if 'measurement_unit' in self.cleaned_data else None
        if new_ing:
            if not chosen_unit:
                chosen_unit = "g"
            canonical_unit, factor = CONVERSION_MAP.get(chosen_unit, ("unit", 1))
            converted_stock = stock * factor
            from .models import Ingredient
            ingredient, created = Ingredient.objects.get_or_create(
                name=new_ing.strip(),
                defaults={'measurement_unit': canonical_unit}
            )
            instance.ingredient = ingredient
            instance.current_stock = converted_stock
        else:
            # For an existing ingredient, if the user selected a measurement unit (e.g., "kg"), convert the stock.
            ingredient = self.cleaned_data.get('ingredient')
            if chosen_unit:
                canonical_unit, factor = CONVERSION_MAP.get(chosen_unit, (ingredient.measurement_unit, 1))
                converted_stock = stock * factor
                instance.current_stock = converted_stock
            else:
                instance.current_stock = stock
        if commit:
            instance.save()
        return instance
    
# ---------------------------------------------------------------------
# Form for adding a new ingredient to inventory.
# This form does NOT allow selecting an existing ingredient.
class AddNewIngredientForm(forms.ModelForm):
    # Ask for the ingredient name (free text)
    name = forms.CharField(label="Ingredient Name", required=True)
    # Measurement unit dropdown; default is grams.
    measurement_unit = forms.ChoiceField(
        label="Measurement Unit",
        choices=UNIT_CHOICES,
        required=True,
        initial="g"
    )
    # Current stock field.
    current_stock = forms.FloatField(label="Current Stock", required=True, min_value=0)

    class Meta:
        model = InventoryItem
        # We don’t include the ingredient field here.
        fields = ['name', 'measurement_unit', 'current_stock']

    def save(self, commit=True):
        # Create the Ingredient first.
        name = self.cleaned_data['name'].strip()
        chosen_unit = self.cleaned_data['measurement_unit']
        stock = self.cleaned_data['current_stock']
        # Convert the entered stock to canonical units.
        canonical_unit, factor = CONVERSION_MAP.get(chosen_unit, ("g", 1))
        converted_stock = stock * factor
        from .models import Ingredient, InventoryItem
        ingredient, created = Ingredient.objects.get_or_create(
            name=name,
            defaults={'measurement_unit': canonical_unit}
        )
        # Create a new InventoryItem instance.
        instance = InventoryItem(ingredient=ingredient, current_stock=converted_stock)
        if commit:
            instance.save()
        return instance

class MealPlanForm(forms.ModelForm):
    class Meta:
        model = MealPlan
        fields = ['recipe', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class UpdateStockForm(forms.ModelForm):
    current_stock = forms.FloatField(label="Current Stock", required=True, min_value=0)

    class Meta:
        model = InventoryItem
        fields = ['current_stock']
