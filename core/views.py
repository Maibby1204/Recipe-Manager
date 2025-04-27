# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from datetime import datetime
import requests

from django.conf import settings
from django.forms import inlineformset_factory

from .models import (Recipe, InventoryItem, MealPlan, RecipeIngredient, Ingredient, 
                     GroceryList, GroceryListItem)
from .forms import (RecipeForm, InventoryItemForm, MealPlanForm, RecipeIngredientForm, 
                    BaseRecipeIngredientInlineFormSet)

def home(request):
    return render(request, 'core/home.html')

def recipe_list(request):
    recipes = Recipe.objects.all()
    sufficient_recipe_ids = []
    if request.user.is_authenticated:
        user_inventory = {item.ingredient.id: item.current_stock for item in InventoryItem.objects.filter(user=request.user)}
        for recipe in recipes:
            enough = True
            for ri in recipe.recipeingredient_set.all():
                if user_inventory.get(ri.ingredient.id, 0) < ri.quantity:
                    enough = False
                    break
            if enough:
                sufficient_recipe_ids.append(recipe.id)
    return render(request, 'core/recipe_list.html', {'recipes': recipes, 'sufficient_recipe_ids': sufficient_recipe_ids})

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    return render(request, 'core/recipe_detail.html', {'recipe': recipe})

@login_required
def add_recipe(request):
    RecipeIngredientFormSet = inlineformset_factory(
        Recipe, RecipeIngredient, form=RecipeIngredientForm,
        formset=BaseRecipeIngredientInlineFormSet, extra=1, can_delete=False
    )
    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.author = request.user
            recipe.save()
            formset = RecipeIngredientFormSet(request.POST, instance=recipe)
            if formset.is_valid():
                formset.save()
                return redirect('recipe_detail', pk=recipe.pk)
        else:
            formset = RecipeIngredientFormSet(request.POST)
    else:
        form = RecipeForm()
        formset = RecipeIngredientFormSet()
    return render(request, 'core/add_recipe.html', {'form': form, 'formset': formset})

@login_required
def edit_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if recipe.author != request.user:
        messages.error(request, "You can only edit recipes you have created.")
        return redirect('recipe_list')
    RecipeIngredientFormSet = inlineformset_factory(
        Recipe, RecipeIngredient, form=RecipeIngredientForm,
        formset=BaseRecipeIngredientInlineFormSet, extra=0, can_delete=True
    )
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        formset = RecipeIngredientFormSet(request.POST, instance=recipe)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Recipe updated successfully.")
            return redirect('recipe_detail', pk=recipe.pk)
    else:
        form = RecipeForm(instance=recipe)
        formset = RecipeIngredientFormSet(instance=recipe)
    return render(request, 'core/edit_recipe.html', {'form': form, 'formset': formset, 'recipe': recipe})


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
    query = request.GET.get('query', '')

    in_stock_items = InventoryItem.objects.filter(user=request.user, current_stock__gt=0)
    if query:
        in_stock_items = in_stock_items.filter(ingredient__name__icontains=query)

    in_stock_ids = in_stock_items.values_list('ingredient_id', flat=True)
    missing_ingredients = Ingredient.objects.all()
    if query:
        missing_ingredients = missing_ingredients.filter(name__icontains=query)
    missing_ingredients = missing_ingredients.exclude(id__in=in_stock_ids)
    
    context = {
        'in_stock_items': in_stock_items,
        'missing_ingredients': missing_ingredients,
        'query': query,
    }
    return render(request, 'core/inventory_list.html', context)

@login_required
def add_inventory_item(request):
    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            temp_item = form.save(commit=False)
            # Check if an inventory item for this user and ingredient already exists
            existing = InventoryItem.objects.filter(user=request.user, ingredient=temp_item.ingredient).first()
            if existing:
                # Add the entered stock to the existing current_stock
                existing.current_stock += temp_item.current_stock
                existing.save()
                return redirect('inventory_list')
            else:
                temp_item.user = request.user
                temp_item.save()
                return redirect('inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'core/add_inventory_item.html', {'form': form})

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
def add_stock(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if request.method == 'POST':
        stock_value = request.POST.get('stock')
        try:
            stock = float(stock_value)
            if stock < 0:
                raise ValueError("Stock cannot be negative.")
        except (ValueError, TypeError):
            error = "Please enter a valid positive number."
            return render(request, 'core/add_stock.html', {'ingredient': ingredient, 'error': error})
        inv, created = InventoryItem.objects.get_or_create(user=request.user, ingredient=ingredient, defaults={'current_stock': 0})
        inv.current_stock += stock
        inv.save()
        # Redirect to inventory management page instead of ingredients list.
        return redirect('inventory_list')
    return render(request, 'core/add_stock.html', {'ingredient': ingredient})


@login_required
def delete_ingredient(request, ingredient_id):
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    from django.contrib import messages
    # Do not allow deletion of pre-defined ingredients.
    if ingredient.is_predefined:
        messages.error(request, "Cannot delete a pre-defined ingredient.")
        return redirect('ingredient_list')
    # Check if the ingredient is used in any recipe.
    if ingredient.recipeingredient_set.exists():
        messages.error(request, "Cannot delete ingredient because it is used in a recipe.")
        return redirect('ingredient_list')
    ingredient.delete()
    messages.success(request, "Ingredient deleted successfully.")
    return redirect('ingredient_list')

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
            recipe = meal_plan.recipe
            missing = {}
            # Check each recipe ingredient against inventory.
            for ri in recipe.recipeingredient_set.all():
                req_qty = ri.quantity
                inv = InventoryItem.objects.filter(user=request.user, ingredient=ri.ingredient).first()
                available = inv.current_stock if inv else 0
                if available < req_qty:
                    missing[ri.ingredient] = req_qty - available
            if missing:
                # Render an error page with the missing ingredients.
                return render(request, 'core/meal_plan_error.html', {'missing': missing, 'form': form})
            else:
                # Deduct required quantities from inventory.
                for ri in recipe.recipeingredient_set.all():
                    inv = InventoryItem.objects.filter(user=request.user, ingredient=ri.ingredient).first()
                    if inv:
                        inv.current_stock -= ri.quantity
                        inv.save()
                meal_plan.save()
                return redirect('meal_plan_list')
    else:
        form = MealPlanForm()
    return render(request, 'core/add_meal_plan.html', {'form': form})

@login_required
def grocery_list(request):
    glist = GroceryList.objects.filter(user=request.user, is_complete=False).order_by('-created_at').first()
    if glist:
         items = glist.items.all()
    else:
         items = []
    return render(request, 'core/grocery_list.html', {'items': items})

def search_external_recipes(request):
    query = request.GET.get('query', '')
    results = []
    error = None
    if query:
        api_key = settings.SPOONACULAR_API_KEY
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

def ingredient_list(request):
    query = request.GET.get('query', '')
    if query:
        ingredients = Ingredient.objects.filter(name__icontains=query)
    else:
        ingredients = Ingredient.objects.all()
    return render(request, 'core/ingredient_list.html', {'ingredients': ingredients, 'query': query})

@login_required
def auto_generate_grocery_list(request):
    meal_plans = MealPlan.objects.filter(user=request.user)
    required = {}
    for mp in meal_plans:
        for ri in mp.recipe.recipeingredient_set.all():
            required[ri.ingredient] = required.get(ri.ingredient, 0) + ri.quantity

    inventory = {item.ingredient: item.current_stock for item in InventoryItem.objects.filter(user=request.user)}
    missing = {}
    for ingredient, req_qty in required.items():
        available = inventory.get(ingredient, 0)
        deficit = req_qty - available
        if deficit > 0:
            missing[ingredient] = deficit

    if missing:
        grocery_list = GroceryList.objects.create(user=request.user)
        for ingredient, qty in missing.items():
            GroceryListItem.objects.create(grocery_list=grocery_list, ingredient=ingredient, total_quantity=qty)
    # Redirect to the grocery list page.
    return redirect('grocery_list')

@login_required
def add_missing_to_grocery_list(request):
    if request.method == 'POST':
        missing = {}
        for key, value in request.POST.items():
            if key.startswith("missing_"):
                ing_id = key.replace("missing_", "")
                try:
                    missing[ing_id] = float(value)
                except ValueError:
                    continue
        if missing:
            grocery_list = GroceryList.objects.create(user=request.user)
            for ing_id, qty in missing.items():
                ingredient = get_object_or_404(Ingredient, id=ing_id)
                GroceryListItem.objects.create(
                    grocery_list=grocery_list,
                    ingredient=ingredient,
                    total_quantity=qty
                )
        return redirect('grocery_list')
    return redirect('add_meal_plan')

@login_required
def confirm_purchase(request, grocery_item_id):
    item = get_object_or_404(GroceryListItem, id=grocery_item_id, grocery_list__user=request.user)
    if request.method == 'POST':
        try:
            purchased = float(request.POST.get('purchased'))
            if purchased < 0:
                raise ValueError("Negative value not allowed.")
        except ValueError:
            error = "Please enter a valid positive number."
            return render(request, 'core/confirm_purchase.html', {'item': item, 'error': error})
        
        # Check if the purchase amount meets the missing quantity.
        if purchased < item.total_quantity:
            error = (f"You must confirm purchase of at least {item.total_quantity} "
                     f"{item.ingredient.measurement_unit}.")
            return render(request, 'core/confirm_purchase.html', {'item': item, 'error': error})
        
        # If purchase is sufficient, update inventory.
        inv, created = InventoryItem.objects.get_or_create(
            user=request.user, 
            ingredient=item.ingredient,
            defaults={'current_stock': 0}
        )
        inv.current_stock += purchased
        inv.save()
        # Once confirmed, remove the grocery list item.
        item.delete()
        return redirect('grocery_list')
    return render(request, 'core/confirm_purchase.html', {'item': item})

from .forms import AddNewIngredientForm, UpdateStockForm
@login_required
def add_new_ingredient(request):
    if request.method == 'POST':
        form = AddNewIngredientForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user  # assign the logged-in user
            instance.save()
            return redirect('inventory_list')
    else:
        form = AddNewIngredientForm()
    return render(request, 'core/add_new_ingredient.html', {'form': form})

@login_required
def update_stock(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk, user=request.user)
    if request.method == 'POST':
        form = UpdateStockForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('inventory_list')
    else:
        form = UpdateStockForm(instance=item)
    return render(request, 'core/update_stock.html', {'form': form, 'item': item})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Ingredient, InventoryItem
from .forms import InventoryItemForm  # we'll modify this form for editing as needed

from .forms import UNIT_CHOICES


@login_required
def edit_nonpredefined_ingredient(request, ingredient_id):
    # Get the ingredient; ensure it's non-predefined.
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if ingredient.is_predefined:
        messages.error(request, "Predefined ingredients cannot be edited here.")
        return redirect('inventory_list')
    
    # We'll build a simple form that allows editing the name and measurement_unit.
    if request.method == 'POST':
        # Use a simple form that we build inline.
        name = request.POST.get('name', '').strip()
        measurement_unit = request.POST.get('measurement_unit', '').strip()
        if not name or not measurement_unit:
            messages.error(request, "Both name and measurement unit are required.")
        else:
            # Update the ingredient.
            ingredient.name = name
            ingredient.measurement_unit = measurement_unit
            ingredient.save()
            messages.success(request, "Ingredient updated successfully.")
            return redirect('inventory_list')
    return render(request, 'core/edit_nonpredefined_ingredient.html', {'ingredient': ingredient, 'unit_choices': UNIT_CHOICES})

@login_required
def delete_nonpredefined_ingredient(request, ingredient_id):
    from .models import GroceryListItem, MealPlan, Recipe
    ingredient = get_object_or_404(Ingredient, id=ingredient_id)
    if ingredient.is_predefined:
        messages.error(request, "Predefined ingredients cannot be deleted.")
        return redirect('inventory_list')
    
    if request.method == 'POST':
        # Cascade deletion: 
        # 1. Find recipes that use this ingredient and delete them.
        recipes_to_delete = Recipe.objects.filter(recipeingredient__ingredient=ingredient).distinct()
        for recipe in recipes_to_delete:
            recipe.delete()
        # 2. Delete inventory items for this ingredient.
        InventoryItem.objects.filter(ingredient=ingredient).delete()
        # 3. Delete grocery list items for this ingredient.
        GroceryListItem.objects.filter(ingredient=ingredient).delete()
        # Optionally, if meal plans depend on recipes, they may be cascade-deleted if the foreign key is set with on_delete=CASCADE.
        ingredient.delete()
        messages.success(request, "Ingredient and all dependent data have been deleted.")
        return redirect('inventory_list')
    return render(request, 'core/confirm_delete_ingredient.html', {'ingredient': ingredient})

@login_required
def delete_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    # Debug: Check the author information
    if recipe.author != request.user:
        messages.error(request, f"You do not have permission to delete this recipe. (Recipe author: {recipe.author}, You: {request.user})")
        return redirect('recipe_list')
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, "Recipe deleted successfully.")
        return redirect('recipe_list')
    return render(request, 'core/confirm_delete_recipe.html', {'recipe': recipe})

@login_required
def cook_recipe_view(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    ingredients = recipe.recipeingredient_set.all()
    return render(request, 'core/cook_recipe.html', {'recipe': recipe, 'ingredients': ingredients})

@login_required
def confirm_cook_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    ingredients = recipe.recipeingredient_set.all()

    user_inventory = {item.ingredient.id: item for item in InventoryItem.objects.filter(user=request.user)}

    missing = {}
    for ri in ingredients:
        inventory_item = user_inventory.get(ri.ingredient.id)
        available = inventory_item.current_stock if inventory_item else 0
        if available < ri.quantity:
            missing[ri.ingredient] = ri.quantity - available

    if missing:
        return render(request, 'core/cook_recipe_error.html', {'missing': missing, 'recipe': recipe})

    # If enough ingredients, deduct them
    for ri in ingredients:
        inventory_item = user_inventory.get(ri.ingredient.id)
        inventory_item.current_stock -= ri.quantity
        inventory_item.save()

    messages.success(request, f"Successfully cooked {recipe.title} and updated your inventory!")
    return redirect('recipe_list')

@login_required
def add_to_grocery_list(request):
    if request.method == 'POST':
        ingredient_id = request.POST.get('ingredient')
        quantity = request.POST.get('quantity')

        if ingredient_id and quantity:
            ingredient = get_object_or_404(Ingredient, id=ingredient_id)

            # Fetch the latest open grocery list (create a new one if none exist)
            grocery_list = GroceryList.objects.filter(user=request.user, is_complete=False).order_by('-created_at').first()
            if not grocery_list:
                grocery_list = GroceryList.objects.create(user=request.user)

            # Now add the item
            GroceryListItem.objects.create(
                grocery_list=grocery_list,
                ingredient=ingredient,
                total_quantity=quantity
            )
            return redirect('grocery_list')

    ingredients = Ingredient.objects.all()
    return render(request, 'core/add_to_grocery_list.html', {'ingredients': ingredients})

