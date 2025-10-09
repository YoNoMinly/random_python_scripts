import pygame
import numpy as np
from numba import cuda
import math

# --- Налаштування ---
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 400
SAND_RADIUS = 3
MAX_SAND = 1000
DT = 1/FPS
neck = 8  
bottom_base = 100

# --- Масиви піщинок ---
sand_x = np.zeros(MAX_SAND, dtype=np.float32)
sand_y = np.zeros(MAX_SAND, dtype=np.float32)
sand_vx = np.zeros(MAX_SAND, dtype=np.float32)
sand_vy = np.zeros(MAX_SAND, dtype=np.float32)
sand_active = np.zeros(MAX_SAND, dtype=np.int32)  # активні піщинки
sand_ready = np.zeros(MAX_SAND, dtype=np.int32)   # готові пройти шию
collision_array = np.zeros(MAX_SAND, dtype=np.int32)

# --- Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Пісочний годинник з чергою і фізикою")
clock = pygame.time.Clock()

# --- Обмеження піщинок по формі годинника ---
@cuda.jit(device=True)
def constrain_hourglass(x, y, vx, vy, radius, width, height):
    cx = width / 2
    cy = height / 2
    neck = 8
    top_width = 100
    bottom_top_y = cy
    bottom_bottom_y = HEIGHT - 50
    slope_bottom = bottom_base / (bottom_bottom_y - bottom_top_y)

    collision = 0

    # --- Верхній трикутник ---
    if y < cy:
        max_x = top_width * (1 - y/cy) + neck
    else:
        # --- Нижній перевернутий трикутник ---
        max_x = neck + slope_bottom * (y - bottom_top_y)
        y_max = bottom_bottom_y
        if y > y_max:
            y = y_max
            vy = 0

    # Обмеження по X
    if x < cx - max_x + radius:
        x = cx - max_x + radius
        vx *= -0.2
        vy *= 0.9
        collision = 1
    if x > cx + max_x - radius:
        x = cx + max_x - radius
        vx *= -0.2
        vy *= 0.9
        collision = 2

    # Верхня межа
    if y < radius:
        y = radius
        vy = 0

    return x, y, vx, vy, collision

# --- Оновлення руху та колізій ---
@cuda.jit
def update_sand_cuda(x, y, vx, vy, active, radius, gravity, dt, width, height, collision_array):
    i = cuda.grid(1)
    if i < x.size and active[i]:
        vy[i] += gravity * dt
        x[i] += vx[i] * dt
        y[i] += vy[i] * dt

        # Реалістичні колізії між піщинками
        for j in range(x.size):
            if j != i and active[j]:
                dx = x[i] - x[j]
                dy = y[i] - y[j]
                dist = math.sqrt(dx*dx + dy*dy)
                min_dist = radius*2
                if dist < min_dist and dist > 0:
                    nx = dx / dist
                    ny = dy / dist
                    force = (min_dist - dist) * 50.0
                    vx[i] += nx * force * dt
                    vy[i] += ny * force * dt
                    vx[j] -= nx * force * dt
                    vy[j] -= ny * force * dt

        # Обмеження форми годинника
        x[i], y[i], vx[i], vy[i], col = constrain_hourglass(x[i], y[i], vx[i], vy[i], radius, width, height)
        collision_array[i] = col

# --- Активація піщинок у верхньому відсіку ---
def activate_sand(num):
    for i in range(MAX_SAND):
        if not sand_active[i]:
            sand_active[i] = 1
            sand_ready[i] = 0  # ще не готова пройти шию
            sand_x[i] = WIDTH//2 + np.random.uniform(-3,3)
            sand_y[i] = 50
            sand_vx[i] = np.random.uniform(-10,10)
            sand_vy[i] = 0
            num -= 1
            if num <= 0:
                break

# --- Головний цикл ---
running = True
sand_timer = 0.0

while running:
    dt = clock.tick(FPS)/1000.0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Додаємо всі піщинки в верхній відсік ---
    activate_sand(2)

    # --- Пропуск через шию по одній піщинці на секунду ---
    sand_timer += dt
    if sand_timer >= 1.0:
        for i in range(MAX_SAND):
            if sand_active[i] and sand_y[i] < HEIGHT//2 and sand_ready[i] == 0:
                sand_ready[i] = 1
                break
        sand_timer -= 1.0

    # --- Обмеження шии, щоб решта піщинок тіснилися, але не проходили ---
    for i in range(MAX_SAND):
        if sand_active[i] and sand_y[i] < HEIGHT//2 and sand_ready[i] == 0:
            # обмежуємо y, але залишаємо vx і vy для колізій
            if sand_y[i] + sand_vy[i]*DT > HEIGHT//2 - SAND_RADIUS:
                sand_y[i] = HEIGHT//2 - SAND_RADIUS
                sand_vy[i] = 0

    # GPU оновлення
    threadsperblock = 32
    blockspergrid = (MAX_SAND + (threadsperblock - 1)) // threadsperblock
    update_sand_cuda[blockspergrid, threadsperblock](
        sand_x, sand_y, sand_vx, sand_vy, sand_active, SAND_RADIUS, GRAVITY, DT, WIDTH, HEIGHT, collision_array
    )

    # --- Візуалізація ---
    screen.fill((30,30,40))

    # Верхній трикутник
    pygame.draw.polygon(screen, (200,200,200),
                        [(WIDTH//2-100,50),(WIDTH//2+100,50),(WIDTH//2+neck,HEIGHT//2),(WIDTH//2-neck,HEIGHT//2)], 2)
    # Нижній перевернутий трикутник
    left_color = (200,50,50) if 1 in collision_array else (200,200,200)
    right_color = (200,50,50) if 2 in collision_array else (200,200,200)
    pygame.draw.line(screen, left_color, (WIDTH//2-neck, HEIGHT//2), (WIDTH//2-bottom_base, HEIGHT-50), 2)
    pygame.draw.line(screen, right_color, (WIDTH//2+neck, HEIGHT//2), (WIDTH//2+bottom_base, HEIGHT-50), 2)
    pygame.draw.line(screen, (200,200,200), (WIDTH//2-bottom_base, HEIGHT-50), (WIDTH//2+bottom_base, HEIGHT-50), 2)

    # Піщинки
    for i in range(MAX_SAND):
        if sand_active[i]:
            pygame.draw.circle(screen, (255,200,50), (int(sand_x[i]), int(sand_y[i])), SAND_RADIUS)

    pygame.display.flip()

pygame.quit()
