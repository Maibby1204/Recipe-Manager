import requests
import json
from faker import Faker

fake = Faker()
Faker.seed(42)

# Fetch recipes from DummyJSON
response = requests.get('https://dummyjson.com/recipes')
recipes = response.json().get('recipes', [])

# Extract unique ingredients
unique_ingredients = set()
for recipe in recipes:
    ingredients = recipe.get('ingredients', [])
    unique_ingredients.update(ingredients)

# Define common measurement units
measurement_units = ["grams", "ml", "pieces", "cups", "tbsp", "tsp"]

# Function to assign measurement units based on ingredient name
def assign_measurement_unit(ingredient_name):
    lower_name = ingredient_name.lower()
    if any(term in lower_name for term in ['milk', 'water', 'oil']):
        return 'ml'
    elif any(term in lower_name for term in ['egg']):
        return 'pieces'
    elif any(term in lower_name for term in ['flour', 'sugar', 'salt']):
        return 'grams'
    else:
        return fake.random_element(measurement_units)

# Create the formatted list
formatted_ingredients = []
for pk, ingredient in enumerate(unique_ingredients, start=1):
    formatted_ingredients.append({
        "model": "core.ingredient",
        "pk": pk,
        "fields": {
            "name": ingredient,
            "measurement_unit": assign_measurement_unit(ingredient),
            "is_predefined": True
        }
    })

# Save to JSON file
with open("ingredients.json", "w") as f:
    json.dump(formatted_ingredients, f, indent=4)

print("Ingredients have been successfully saved to ingredients.json")
