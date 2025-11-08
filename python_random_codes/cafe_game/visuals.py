# visuals.py
import pygame
from ingredients import INGREDIENTS
import random

ICON_SIZE = 28

def draw_customer(screen, x, y, order, font, progress=None, c=None):
    """
    Малює клієнта:
    - різний колір, розмір та border_radius
    - очі та рот
    - замовлення над головою
    - таймбар з градієнтом (зелений → жовтий → червоний)
    """
    # параметри клієнта
    if c is None:
        c = {}
    color = c.get("color", (150, 200, 255))
    w, h = c.get("size", (60, 80))
    radius = c.get("border_radius", 8)

    # тіло
    customer_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, color, customer_rect, border_radius=radius)

    # очі
    eye_y = y + int(h*0.2)
    pygame.draw.circle(screen, (0,0,0), (x + int(w*0.25), eye_y), 4)
    pygame.draw.circle(screen, (0,0,0), (x + int(w*0.75), eye_y), 4)

    # рот
    mouth_y = y + int(h*0.75)
    if random.random() < 0.5:
        pygame.draw.rect(screen, (255, 0, 0), (x + int(w*0.25), mouth_y, int(w*0.5), 4))  # усмішка
    else:
        pygame.draw.rect(screen, (0, 0, 0), (x + int(w*0.25), mouth_y, int(w*0.5), 4))  # нейтральний рот

    # Малюємо замовлення над головою
    start_x = x - (len(order)-1) * (ICON_SIZE + 6) // 2 + w//2 - ICON_SIZE//2
    base_y = y - 40
    for i, item in enumerate(order):
        cx = start_x + i * (ICON_SIZE + 6)
        cy = base_y
        color_i = INGREDIENTS[item]["color"]
        pygame.draw.rect(screen, color_i, (cx, cy, ICON_SIZE, ICON_SIZE), border_radius=4)
        label = font.render(item[0].upper(), True, (0,0,0))
        screen.blit(label, (cx + 6, cy + 4))

    # Таймбар з градієнтним кольором
    if progress is not None:
        bar_w = w
        bar_h = 6
        bx = x
        by = y - 50
        pygame.draw.rect(screen, (60, 60, 60), (bx, by, bar_w, bar_h))  # фон

        # визначаємо колір: зелений → жовтий → червоний
        if progress > 0.5:
            # зелений → жовтий
            ratio = (progress - 0.5) / 0.5
            r = int(255 * (1 - ratio))
            g = 255
        else:
            # жовтий → червоний
            ratio = progress / 0.5
            r = 255
            g = int(255 * ratio)
        b = 0

        pygame.draw.rect(screen, (r, g, b), (bx, by, int(bar_w * progress), bar_h))


def draw_ingredient_buttons(screen, items, selected, font, base_x=50, base_y=430):
    """Малює кнопки інгредієнтів."""
    rects = []
    gap = 14
    w = 76
    h = 76
    for i, name in enumerate(items):
        x = base_x + i * (w + gap)
        y = base_y
        rect = pygame.Rect(x, y, w, h)
        rects.append(rect)
        color = INGREDIENTS[name]["color"]
        pygame.draw.rect(screen, color, rect, border_radius=8)
        if name in selected:
            pygame.draw.rect(screen, (255, 0, 0), rect, 4)
        lbl = font.render(name, True, (0,0,0))
        screen.blit(lbl, (x + 6, y + h//2 - 10))
    return rects


def draw_ui_top(screen, time_left_sec, score, font):
    txt = f"Час: {int(time_left_sec)}    Очки: {score}"
    label = font.render(txt, True, (255,255,255))
    screen.blit(label, (20, 16))


def draw_end_screen(screen, score, served, font_big, font_small):
    """Показує напівпрозорий екран результатів."""
    overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    center_x, center_y = screen.get_width()//2, screen.get_height()//2
    text1 = font_big.render("Кінець зміни", True, (255, 255, 255))
    text2 = font_small.render(f"Очки: {score}", True, (255, 255, 255))
    text3 = font_small.render(f"Обслужено клієнтів: {served}", True, (255, 255, 255))
    text4 = font_small.render("Натисни будь-де, щоб вийти", True, (200, 200, 200))

    screen.blit(text1, (center_x - text1.get_width()//2, center_y - 80))
    screen.blit(text2, (center_x - text2.get_width()//2, center_y - 20))
    screen.blit(text3, (center_x - text3.get_width()//2, center_y + 20))
    screen.blit(text4, (center_x - text4.get_width()//2, center_y + 70))
