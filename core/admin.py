from django.contrib import admin
from .models import Recipe, Ingredient, RecipeIngredient, MealPlan, GroceryList, GroceryListItem, InventoryItem

class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1

class RecipeAdmin(admin.ModelAdmin):
    inlines = [RecipeIngredientInline]
    list_display = ('title', 'author', 'created_at')

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient)
admin.site.register(MealPlan)
admin.site.register(GroceryList)
admin.site.register(GroceryListItem)
admin.site.register(InventoryItem)