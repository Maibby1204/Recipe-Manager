# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator

class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    measurement_unit = models.CharField(max_length=50, default='unit')
    is_predefined = models.BooleanField(default=False)  # new field for default ingredients
    recipes = models.ManyToManyField('Recipe', through='RecipeIngredient')

    def __str__(self):
        return self.name

class Recipe(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')

    def __str__(self):
        return self.title

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    # Quantity must be positive (no negatives allowed)
    quantity = models.FloatField(validators=[MinValueValidator(0.01)])

    class Meta:
        unique_together = ('recipe', 'ingredient')  # prevent duplicate entries per recipe

    def __str__(self):
        return f"{self.quantity} {self.ingredient.measurement_unit} of {self.ingredient.name} in {self.recipe.title}"

class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        ordering = ['date']
        # Removed unique_together so that multiple meal plans (even of the same recipe) on one day are allowed

    def __str__(self):
        return f"{self.recipe.title} on {self.date}"

class GroceryList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grocery_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Grocery List from {self.created_at.strftime('%Y-%m-%d')}"

class GroceryListItem(models.Model):
    grocery_list = models.ForeignKey(GroceryList, on_delete=models.CASCADE, related_name='items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    total_quantity = models.FloatField()

    def __str__(self):
        return f"{self.total_quantity} {self.ingredient.measurement_unit} of {self.ingredient.name}"

class InventoryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    # Ensure current_stock is non-negative.
    current_stock = models.FloatField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        unique_together = ('user', 'ingredient')  # only one record per user/ingredient

    def __str__(self):
        return f"{self.ingredient.name}: {self.current_stock} {self.ingredient.measurement_unit}"
