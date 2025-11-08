# main.py
import pygame, sys, random
from collections import Counter
from visuals import draw_customer, draw_ingredient_buttons, draw_ui_top, draw_end_screen
from ingredients import INGREDIENTS, generate_order
from level_data import LEVELS  # список рівнів

pygame.init()
screen = pygame.display.set_mode((900, 600))
pygame.display.set_caption("Кухня 03:00")
clock = pygame.time.Clock()

FONT = pygame.font.SysFont("Arial", 18)
BIG_FONT = pygame.font.SysFont("Arial", 28)

available_items = list(INGREDIENTS.keys())
selected = []
customers = []
score = 0
served_count = 0

spawned_customers = 0 
current_level_index = 0
LEVEL = LEVELS[current_level_index]

time_remaining = LEVEL["level_time"]
spawn_interval = LEVEL["spawn_interval"]
spawn_acc = 0.0
customer_wait_ms = LEVEL["customer_wait_ms"]

def make_customer():
    colors = [(150, 200, 255), (200, 180, 255), (180, 255, 200), (255, 200, 180)]
    size_options = [(50, 70), (60, 80), (70, 90)]
    border_options = [4, 8, 12]
    return {
        "order": generate_order(),
        "wait_ms": customer_wait_ms,
        "spawn_time": pygame.time.get_ticks(),
        "color": random.choice(colors),
        "size": random.choice(size_options),
        "border_radius": random.choice(border_options)
    }

# початковий клієнт
customers.append(make_customer())

state = "game"  # game, next_level, end

while True:
    dt_ms = clock.tick(60)
    dt = dt_ms / 1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if state == "game" and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos

            # --- перевірка кліку по інгредієнтах ---
            base_x = 50; base_y = 430; gap = 14; w = 76; h = 76
            for i, name in enumerate(available_items):
                rect = pygame.Rect(base_x + i * (w + gap), base_y, w, h)
                if rect.collidepoint(pos):
                    if name in selected:
                        selected.remove(name)
                    else:
                        selected.append(name)
                    break

            # --- перевірка кліку по клієнтах ---
            for i, c in enumerate(customers):
                start_x = 120
                start_y = 160
                gap_x = 140
                x = start_x + i * gap_x
                y = start_y
                customer_rect = pygame.Rect(x, y, 60, 80)

                if customer_rect.collidepoint(pos):
                    if Counter(selected) == Counter(c["order"]):
                        score += 10
                        served_count += 1
                        customers.pop(i)
                        selected.clear()
                    break

        elif state in ["next_level", "end"] and event.type == pygame.MOUSEBUTTONDOWN:
            if state == "next_level":
                # переходимо на новий рівень
                LEVEL = LEVELS[current_level_index]
                time_remaining = LEVEL["level_time"]
                spawn_interval = LEVEL["spawn_interval"]
                customer_wait_ms = LEVEL["customer_wait_ms"]
                spawn_acc = 0.0
                customers.append(make_customer())
                state = "game"
            else:
                pygame.quit()
                sys.exit()

    # --- Логіка гри ---
    if state == "game":
        time_remaining -= dt
        spawn_acc += dt

        # спавн нових клієнтів
        if spawn_acc >= LEVEL["spawn_interval"] and spawned_customers < LEVEL["total_customers"]:
            customers.append(make_customer())
            spawned_customers += 1
            spawn_acc = 0.0

        # оновлення таймера очікування клієнтів
        new_queue = []
        for c in customers:
            c["wait_ms"] -= dt_ms
            if c["wait_ms"] > 0:
                new_queue.append(c)
        customers = new_queue
        if spawned_customers == LEVEL["total_customers"] and not customers:
            current_level_index += 1
            if current_level_index < len(LEVELS):
                # готуємо наступний рівень
                LEVEL = LEVELS[current_level_index]
                time_remaining = LEVEL["level_time"]
                spawn_acc = 0.0
                spawned_customers = 0
                selected.clear()
                customers.clear()
                state = "game"
            else:
                state = "end"

        # --- Малювання ---
        screen.fill((28, 28, 36))
        draw_ui_top(screen, time_remaining, score, BIG_FONT)

        # Малюємо клієнтів у ряд
        start_x = 120
        start_y = 160
        gap_x = 140

        for i, c in enumerate(customers):
            x = start_x + i * gap_x
            y = start_y
            progress = max(0.0, c["wait_ms"] / customer_wait_ms)
            draw_customer(screen, x, y, c["order"], FONT, progress=progress)

        draw_ingredient_buttons(screen, available_items, selected, FONT)

        pygame.display.flip()

        # перевірка завершення рівня
        if not customers:
            current_level_index += 1
            if current_level_index < len(LEVELS):
                state = "next_level"
                spawned_customers = 0 
            else:
                state = "end"

    elif state == "next_level":
        # показ повідомлення "Рівень пройдено!"
        screen.fill((28, 28, 36))
        txt = BIG_FONT.render(f"Рівень пройдено! Натисни, щоб перейти", True, (255, 255, 255))
        screen.blit(txt, (screen.get_width()//2 - txt.get_width()//2, screen.get_height()//2 - txt.get_height()//2))
        pygame.display.flip()

    elif state == "end":
        draw_end_screen(screen, score, served_count, BIG_FONT, FONT)
        pygame.display.flip()
