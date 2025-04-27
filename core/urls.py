# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/add/', views.add_recipe, name='add_recipe'),
    path('recipes/edit/<int:pk>/', views.edit_recipe, name='edit_recipe'),
    path('signup/', views.signup, name='signup'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/add/', views.add_inventory_item, name='add_inventory_item'),
    path('inventory/add-new/', views.add_new_ingredient, name='add_new_ingredient'),
    path('inventory/update/<int:pk>/', views.update_inventory, name='update_inventory'),
    path('ingredients/add_stock/<int:ingredient_id>/', views.add_stock, name='add_stock'),
    path('ingredients/delete/<int:ingredient_id>/', views.delete_ingredient, name='delete_ingredient'),
    path('meal-plans/', views.meal_plan_list, name='meal_plan_list'),
    path('meal-plans/add/', views.add_meal_plan, name='add_meal_plan'),
    path('grocery-list/', views.grocery_list, name='grocery_list'),
    path('external-recipes/', views.search_external_recipes, name='external_recipe_search'),
    path('ingredients/', views.ingredient_list, name='ingredient_list'),
    path('auto-grocery/', views.auto_generate_grocery_list, name='auto_generate_grocery_list'),
    path('add-missing/', views.add_missing_to_grocery_list, name='add_missing_to_grocery_list'),
    path('confirm-purchase/<int:grocery_item_id>/', views.confirm_purchase, name='confirm_purchase'),
    path('inventory/update-stock/<int:pk>/', views.update_stock, name='update_stock'),
    path('ingredient/edit/<int:ingredient_id>/', views.edit_nonpredefined_ingredient, name='edit_nonpredefined_ingredient'),
    path('ingredient/delete/<int:ingredient_id>/', views.delete_nonpredefined_ingredient, name='delete_nonpredefined_ingredient'),
    path('recipes/delete/<int:pk>/', views.delete_recipe, name='delete_recipe'),
    path('recipes/<int:pk>/cook/', views.cook_recipe_view, name='cook_recipe'),
    path('recipes/<int:pk>/confirm-cook/', views.confirm_cook_recipe, name='confirm_cook_recipe'),
    path('grocery-list/add/', views.add_to_grocery_list, name='add_to_grocery_list'),
]
