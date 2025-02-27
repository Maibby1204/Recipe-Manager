from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from datetime import datetime
import requests

from django.conf import settings
from .models import Recipe, InventoryItem, MealPlan
from .forms import RecipeForm, InventoryItemForm, MealPlanForm

def home(request):
    context = {
        'current_year': datetime.now().year,
    }
    return render(request, 'core/home.html', context)

def recipe_list(request):
    recipes = Recipe.objects.all()
    return render(request, 'core/recipe_list.html', {'recipes': recipes})

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'core/recipe_detail.html', {'recipe': recipe})

@login_required
def add_recipe(request):
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm()
    return render(request, 'core/add_recipe.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def inventory_list(request):
    items = InventoryItem.objects.filter(user=request.user)
    return render(request, 'core/inventory_list.html', {'items': items})

@login_required
def update_inventory(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'core/update_inventory.html', {'form': form})

@login_required
def meal_plan_list(request):
    meal_plans = MealPlan.objects.filter(user=request.user).order_by('date')
    return render(request, 'core/meal_plan_list.html', {'meal_plans': meal_plans})

@login_required
def add_meal_plan(request):
    if request.method == 'POST':
        form = MealPlanForm(request.POST)
        if form.is_valid():
            meal_plan = form.save(commit=False)
            meal_plan.user = request.user
            meal_plan.save()
            return redirect('meal_plan_list')
    else:
        form = MealPlanForm()
    return render(request, 'core/add_meal_plan.html', {'form': form})

@login_required
def grocery_list(request):
    """
    Aggregates ingredients from the user's meal plans.
    Note: Ensure that each Recipe has associated RecipeIngredient entries.
    """
    meal_plans = MealPlan.objects.filter(user=request.user)
    grocery_dict = {}
    for mp in meal_plans:
        recipe = mp.recipe
        # Check if the recipe has any associated RecipeIngredient entries
        if hasattr(recipe, 'recipeingredient_set'):
            for ri in recipe.recipeingredient_set.all():
                ingredient = ri.ingredient
                grocery_dict[ingredient] = grocery_dict.get(ingredient, 0) + ri.quantity
    context = {
        'grocery_dict': grocery_dict
    }
    return render(request, 'core/grocery_list.html', context)

def search_external_recipes(request):
    """
    Searches for recipes using the Spoonacular API.
    """
    query = request.GET.get('query', '')
    results = []
    error = None
    if query:
        api_key = settings.SPOONACULAR_API_KEY
        # Example endpoint - adjust parameters as needed
        url = f"https://api.spoonacular.com/recipes/complexSearch?query={query}&apiKey={api_key}&number=10"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
            else:
                error = f"API returned status code {response.status_code}"
        except Exception as e:
            error = str(e)
    context = {
        'query': query,
        'results': results,
        'error': error,
    }
    return render(request, 'core/external_recipe_search.html', context)
