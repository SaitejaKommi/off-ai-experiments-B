"""Nutrition thresholds and category-based pairing rules."""

# Per-100g thresholds
FAT_HIGH = 20.0        # g / 100 g
SUGAR_HIGH = 15.0      # g / 100 g
SALT_HIGH = 1.5        # g / 100 g
SATURATED_FAT_HIGH = 5.0  # g / 100 g
PROTEIN_HIGH = 10.0    # g / 100 g
FIBER_HIGH = 6.0       # g / 100 g
CALORIES_HIGH = 400.0  # kcal / 100 g
NOVA_ULTRA_PROCESSED = 4

# NutriScore descriptions
NUTRISCORE_DESCRIPTIONS = {
    "a": "excellent nutritional quality",
    "b": "good nutritional quality",
    "c": "moderate nutritional quality",
    "d": "poor nutritional quality",
    "e": "very poor nutritional quality",
}

# NOVA group descriptions
NOVA_DESCRIPTIONS = {
    1: "unprocessed or minimally processed food",
    2: "processed culinary ingredient",
    3: "processed food",
    4: "ultra-processed food",
}

# Category → list of complementary foods
# Note: Keys can match as substrings in product category slugs
CATEGORY_PAIRINGS = {
    "nut-butters": ["banana", "whole grain bread", "oatmeal", "apple slices", "celery"],
    "peanut-butter": ["banana", "whole grain bread", "oatmeal", "apple slices", "celery"],
    "jams": ["whole grain bread", "yogurt", "oatmeal", "rice cakes"],
    "bread": ["peanut butter", "avocado", "eggs", "cheese", "tomatoes"],
    "cereals": ["low-fat milk", "yogurt", "berries", "banana"],
    # Yogurt and fermented dairy products
    "yogurts": ["granola", "berries", "honey", "nuts"],
    "yogurt": ["granola", "berries", "honey", "nuts"],
    "greek-yogurt": ["granola", "berries", "honey", "nuts"],
    "fermented-milk": ["granola", "berries", "honey", "nuts"],
    "fermented-dairy": ["granola", "berries", "honey", "nuts"],
    "kefir": ["granola", "berries", "honey", "nuts"],
    "sour-cream": ["berries", "potatoes", "salmon", "dill"],
    # General dairy
    "dairy": ["berries", "granola", "honey", "nuts"],
    "milk-products": ["cereals", "coffee", "tea", "berries"],
    "milk": ["cereals", "coffee", "tea", "berries"],
    "cheese": ["whole grain crackers", "grapes", "apple", "walnuts"],
    # Oils and fats (cooking ingredients)
    "olive-oils": ["pasta", "vegetables", "bread", "tomatoes", "garlic"],
    "olive-oil": ["pasta", "vegetables", "bread", "tomatoes", "garlic"],
    "extra-virgin-olive-oils": ["pasta", "vegetables", "bread", "tomatoes", "garlic"],
    "virgin-olive-oils": ["pasta", "vegetables", "bread", "tomatoes", "garlic"],
    "vegetable-oils": ["pasta", "vegetables", "bread", "potatoes", "rice"],
    "cooking-oils": ["pasta", "vegetables", "bread", "potatoes", "rice"],
    "oils": ["pasta", "vegetables", "bread", "potatoes", "rice"],
    "fats": ["vegetables", "bread", "potatoes", "pasta"],
    # Legumes and pulses
    "legumes": ["rice", "onions", "garlic", "tomatoes", "spinach"],
    "legume-seeds": ["rice", "onions", "garlic", "tomatoes", "spinach"],
    "pulses": ["rice", "onions", "garlic", "tomatoes", "spinach"],
    "lentils": ["rice", "onions", "garlic", "tomatoes", "spinach"],
    "red-lentils": ["rice", "onions", "garlic", "tomatoes", "spinach"],
    "beans": ["rice", "corn", "tomatoes", "onions", "peppers"],
    "chickpeas": ["turmeric", "cumin", "olive oil", "tomatoes", "onions"],
    "legumes-and-their-products": ["rice", "onions", "garlic", "tomatoes", "spinach"],
    # Other categories
    "chips": ["salsa", "guacamole", "hummus"],
    "chocolate": ["strawberries", "almonds", "red wine", "raspberries"],
    "biscuits": ["tea", "coffee", "milk"],
    "soups": ["whole grain bread", "crackers", "salad"],
    "pasta": ["tomato sauce", "vegetables", "lean meat", "olive oil"],
    "beverages": ["lemon", "ice", "mint"],
    "juices": ["sparkling water", "yogurt"],
    "default": ["water", "fresh vegetables", "whole grain bread"],
}
