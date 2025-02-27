from django.db import models
from django.contrib.auth.models import User

# Model to represent a recipe
class Recipe(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # Optionally, associate the recipe with a user (creator)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipes')

    def __str__(self):
        return self.title

# Model to represent an ingredient
class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    # You can add additional fields like unit (grams, cups, etc.)
    unit = models.CharField(max_length=50, default='unit')
    # Many-to-many relationship with Recipe through RecipeIngredient
    recipes = models.ManyToManyField(Recipe, through='RecipeIngredient')

    def __str__(self):
        return self.name

# Through model to capture quantities for a recipe's ingredients
class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()

    def __str__(self):
        return f"{self.quantity} of {self.ingredient.name} in {self.recipe.title}"

# Model to represent a meal plan (assign recipes to a specific date)
class MealPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    date = models.DateField()

    class Meta:
        unique_together = ('user', 'recipe', 'date')
        ordering = ['date']

    def __str__(self):
        return f"{self.recipe.title} on {self.date}"

# Model for a grocery list (generated from meal plans)
class GroceryList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grocery_lists')
    created_at = models.DateTimeField(auto_now_add=True)
    # You can also add a boolean flag if the list is complete or not
    is_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Grocery List from {self.created_at.strftime('%Y-%m-%d')}"

# Model to represent individual grocery list items (aggregated ingredients)
class GroceryListItem(models.Model):
    grocery_list = models.ForeignKey(GroceryList, on_delete=models.CASCADE, related_name='items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    total_quantity = models.FloatField()

    def __str__(self):
        return f"{self.total_quantity} {self.ingredient.unit} of {self.ingredient.name}"

# Model for inventory management (tracking pantry stock)
class InventoryItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inventory_items')
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    current_stock = models.FloatField(default=0)
    threshold = models.FloatField(default=0)  # Alert when stock falls below this value

    def __str__(self):
        return f"{self.ingredient.name}: {self.current_stock} {self.ingredient.unit}"

    def is_low_stock(self):
        return self.current_stock < self.threshold