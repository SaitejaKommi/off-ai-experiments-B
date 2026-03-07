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
CATEGORY_PAIRINGS = {
    "nut-butters": ["banana", "whole grain bread", "oatmeal", "apple slices", "celery"],
    "peanut-butter": ["banana", "whole grain bread", "oatmeal", "apple slices", "celery"],
    "jams": ["whole grain bread", "yogurt", "oatmeal", "rice cakes"],
    "bread": ["peanut butter", "avocado", "eggs", "cheese", "tomatoes"],
    "cereals": ["low-fat milk", "yogurt", "berries", "banana"],
    "yogurts": ["granola", "berries", "honey", "nuts"],
    "cheese": ["whole grain crackers", "grapes", "apple", "walnuts"],
    "chips": ["salsa", "guacamole", "hummus"],
    "chocolate": ["strawberries", "almonds", "red wine", "raspberries"],
    "biscuits": ["tea", "coffee", "milk"],
    "soups": ["whole grain bread", "crackers", "salad"],
    "pasta": ["tomato sauce", "vegetables", "lean meat", "olive oil"],
    "beverages": ["lemon", "ice", "mint"],
    "juices": ["sparkling water", "yogurt"],
    "milk": ["cereals", "coffee", "tea", "berries"],
    "default": ["water", "fresh vegetables", "whole grain bread"],
}
