import random

INGREDIENTS = {
    "bread": {"color": (200, 180, 100)},
    "patty": {"color": (150, 75, 0)},
    "cheese": {"color": (255, 220, 50)},
    "fries": {"color": (255, 200, 0)},
    "cola": {"color": (50, 100, 255)},
    "coffee": {"color": (90, 60, 30)},
    "salad": {"color": (100, 200, 100)},  # новий інгредієнт
}

ADDITIONALS = ["fries", "cola", "coffee", "salad"]  # додаємо salad

def generate_order():
    """
    Генерує замовлення згідно правил:
    - bread + patty завжди разом (обов'язково)
    - до них може бути доданий cheese (50%)
    - додаткові боки (0..2) випадкові з ADDITIONALS
    Повертає список назв інгредієнтів.
    """
    order = ["bread", "patty"]

    if random.random() < 0.5:
        order.append("cheese")

    n_add = random.randint(0, 2)
    if n_add > 0:
        sides = random.sample(ADDITIONALS, k=n_add)
        order.extend(sides)

    return order
