import pygame
import numpy as np
import sys

# --- Налаштування ---
GRID_W, GRID_H = 240, 160   # розмір сітки хвиль (чем більше — тем точніше, но повільніше)
WINDOW_W, WINDOW_H = 960, 640  # розмір вікна (сітка буде масштабована)
FPS = 60

DAMPING = 0.995    # демпінг хвиль (0..1) — як швидко гасяться
IMPULSE = 1.0      # сила імпульсу при кліку
BRUSH_RADIUS = 3   # радіус області, що отримує імпульс при кліку

# Ініціалізація масивів: prev (t-1), cur (t)
prev = np.zeros((GRID_H, GRID_W), dtype=np.float32)
cur  = np.zeros_like(prev)

def step_wave(prev, cur, damping):
    """
    Один крок дискретного хвильового рівняння (популярна реалізація).
    Використовує сусідів по 4 напрямках.
    Повертає next масив.
    """
    # сума чотирьох сусідів
    neighbors = (
        np.roll(cur, 1, axis=0) + np.roll(cur, -1, axis=0) +
        np.roll(cur, 1, axis=1) + np.roll(cur, -1, axis=1)
    )
    # стандартна формула: next = (neighbors / 2) - prev
    next_ = (neighbors * 0.5) - prev
    # застосувати демпінг
    next_ *= damping
    return next_

def add_impulse(cur, pos, radius, strength):
    """Додає круглий імпульс у масив cur (pos у координатах сітки)."""
    cx, cy = pos
    y, x = np.ogrid[-cy:GRID_H-cy, -cx:GRID_W-cx]
    mask = x*x + y*y <= radius*radius
    # градація сили по відстані (м'якший край)
    dist = np.sqrt(x*x + y*y)
    factor = np.clip(1 - (dist / (radius + 1)), 0, 1)
    cur[mask] += strength * factor[mask]

def height_to_surface(arr):
    """
    Перетворює масив висот у surface pygame.
    Нормалізує значення в 0..255 і робить RGB.
    """
    # невелике обмеження амплітуди для кращого відображення
    img = np.clip(arr, -1.5, 1.5)
    # нормалізація: від -max до +max -> 0..255
    img = ((img + 1.5) / 3.0) * 255.0
    img = img.astype(np.uint8)
    # зробити RGB (H, W, 3)
    rgb = np.dstack((img, img, img))
    # pygame очікує (W,H,3) від surfarray; використаємо make_surface з транспозицією
    # Але simpler: створимо surface через pygame.surfarray.make_surface, треба транспонувати
    surf = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))
    return surf

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Імітація хвиль — клік мишки створює імпульс")
    clock = pygame.time.Clock()

    global prev, cur

    running = True
    mouse_down = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ліва кнопка
                    mouse_down = True
                    mx, my = event.pos
                    gx = int(mx * GRID_W / WINDOW_W)
                    gy = int(my * GRID_H / WINDOW_H)
                    add_impulse(cur, (gx, gy), BRUSH_RADIUS, IMPULSE)
                elif event.button == 3:  # права кнопка — сильніший імпульс
                    mx, my = event.pos
                    gx = int(mx * GRID_W / WINDOW_W)
                    gy = int(my * GRID_H / WINDOW_H)
                    add_impulse(cur, (gx, gy), BRUSH_RADIUS * 2, IMPULSE * 1.8)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    mouse_down = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # клавіші для регулювання параметрів у реальному часі
                elif event.key == pygame.K_UP:
                    # зменшуємо демпінг (хвилі довше)
                    nonlocal_damping = globals().get('DAMPING', DAMPING)
                    new_damp = min(0.999, nonlocal_damping + 0.002)
                    globals()['DAMPING'] = new_damp
                elif event.key == pygame.K_DOWN:
                    nonlocal_damping = globals().get('DAMPING', DAMPING)
                    new_damp = max(0.90, nonlocal_damping - 0.002)
                    globals()['DAMPING'] = new_damp

        # якщо тримаємо мишку, додавати маленькі імпульси (для "малювання" хвиль)
        if mouse_down:
            mx, my = pygame.mouse.get_pos()
            gx = int(mx * GRID_W / WINDOW_W)
            gy = int(my * GRID_H / WINDOW_H)
            add_impulse(cur, (gx, gy), BRUSH_RADIUS // 2, IMPULSE * 0.35)

        # крок симуляції
        next_ = step_wave(prev, cur, globals().get('DAMPING', DAMPING))

        # обмін буферів: prev <- cur, cur <- next_
        prev, cur = cur, next_

        # візуалізація
        surf = height_to_surface(cur)
        # масштабувати до розміру вікна
        surf = pygame.transform.smoothscale(surf, (WINDOW_W, WINDOW_H))
        screen.blit(surf, (0,0))

        # накласти трохи кольору для "морського" ефекту:
        # беремо поверхню в режимі per-pixel alpha і заповнюємо синім з alpha
        overlay = pygame.Surface((WINDOW_W, WINDOW_H), flags=pygame.SRCALPHA)
        overlay.fill((10, 30, 80, 30))  # слабкий синій відтінок
        screen.blit(overlay, (0,0))

        # показати просту інструкцію
        font = pygame.font.SysFont(None, 20)
        text = font.render("Ліва кнопка: крапля | Права: сильніша | Esc: вийти", True, (230,230,230))
        screen.blit(text, (8, 8))

        # оновити екран
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
