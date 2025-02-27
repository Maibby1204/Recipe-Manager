from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('recipes/', views.recipe_list, name='recipe_list'),
    path('recipes/<int:pk>/', views.recipe_detail, name='recipe_detail'),
    path('recipes/add/', views.add_recipe, name='add_recipe'),
    path('signup/', views.signup, name='signup'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('inventory/update/<int:pk>/', views.update_inventory, name='update_inventory'),
    path('meal-plans/', views.meal_plan_list, name='meal_plan_list'),
    path('meal-plans/add/', views.add_meal_plan, name='add_meal_plan'),
    path('grocery-list/', views.grocery_list, name='grocery_list'),
    path('external-recipes/', views.search_external_recipes, name='external_recipe_search'),
]