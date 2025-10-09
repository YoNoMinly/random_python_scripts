import pygame
import random

# --- Налаштування ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Кольори
SKY_COLOR = (10, 10, 30)
GROUND_COLOR = (70, 70, 70)
PATH_COLOR = (40, 40, 40)
PUDDLE_COLOR = (20, 20, 50)
FRISK_COLOR = (255, 200, 200)
FRISK_REFLECTION_COLOR = (200, 160, 160)
RAIN_COLOR = (170, 200, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Frisk on the Dark Path")
clock = pygame.time.Clock()

# --- Зірки ---
NUM_STARS = 100
stars = []
for _ in range(NUM_STARS):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT // 2)
    brightness = random.randint(150, 255)
    stars.append([x, y, brightness, random.choice([-1, 1])])

# --- Дощ ---
NUM_RAINDROPS = 150
raindrops = []
for _ in range(NUM_RAINDROPS):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    length = random.randint(10, 20)
    speed = random.uniform(4, 8)
    raindrops.append([x, y, length, speed])

# --- Стежка ---
PATH_HEIGHT = 100
path_rect = pygame.Rect(0, HEIGHT - PATH_HEIGHT, WIDTH, PATH_HEIGHT)
ground_rect = pygame.Rect(0, HEIGHT - 50, WIDTH, 50)

# --- Калюжі ---
puddles = []
for _ in range(12):  # більше калюж
    w = random.randint(80, 150)
    h = random.randint(30, 60)
    x = random.randint(0, WIDTH - w)
    y = random.randint(HEIGHT - PATH_HEIGHT + 20, HEIGHT - 30)
    puddles.append(pygame.Rect(x, y, w, h))

# --- Фриск ---
FRISK_SIZE = 30
frisk_pos = [WIDTH // 2, HEIGHT - PATH_HEIGHT + 30]
FRISK_SPEED = 5

running = True
while running:
    clock.tick(FPS)
    screen.fill(SKY_COLOR)

    # --- Зірки ---
    for star in stars:
        x, y, brightness, direction = star
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 2)
        brightness += direction * 2
        if brightness > 255:
            brightness = 255
            star[3] = -1
        elif brightness < 150:
            brightness = 150
            star[3] = 1
        star[2] = brightness

    # --- Обрив під стежкою ---
    pygame.draw.rect(screen, GROUND_COLOR, ground_rect)

    # --- Стежка ---
    pygame.draw.rect(screen, PATH_COLOR, path_rect)

    # --- Калюжі з відображенням зірок і Фріска ---
    for puddle in puddles:
        pygame.draw.ellipse(screen, PUDDLE_COLOR, puddle)
        # Відображення зірок
        for star in stars:
            sx, sy, b, _ = star
            if puddle.top < HEIGHT - sy < puddle.bottom and puddle.left < sx < puddle.right:
                puddle_y = puddle.top + (puddle.bottom - puddle.top) - (HEIGHT - sy - puddle.top)
                pygame.draw.circle(screen, (b//2, b//2, b//2), (sx, puddle_y), 1)
        # Відображення Фріска
        fx, fy = frisk_pos
        if puddle.left < fx + FRISK_SIZE//2 < puddle.right:
            if puddle.top < fy + FRISK_SIZE < puddle.bottom:
                puddle_y = puddle.top + (puddle.bottom - puddle.top) - (fy + FRISK_SIZE - puddle.top)
                pygame.draw.rect(screen, FRISK_REFLECTION_COLOR, (fx, puddle_y - FRISK_SIZE, FRISK_SIZE, FRISK_SIZE))

    # --- Дощ ---
    for drop in raindrops:
        x, y, length, speed = drop
        pygame.draw.line(screen, RAIN_COLOR, (x, y), (x, y + length))
        drop[1] += speed
        if drop[1] > HEIGHT:
            drop[0] = random.randint(0, WIDTH)
            drop[1] = random.randint(-50, -10)
            drop[2] = random.randint(10, 20)
            drop[3] = random.uniform(4, 8)

    # --- Фриск ---
    pygame.draw.rect(screen, FRISK_COLOR, (frisk_pos[0], frisk_pos[1], FRISK_SIZE, FRISK_SIZE))

    # --- Рух героя ---
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and frisk_pos[0] > 0:
        frisk_pos[0] -= FRISK_SPEED
    if keys[pygame.K_RIGHT] and frisk_pos[0] < WIDTH - FRISK_SIZE:
        frisk_pos[0] += FRISK_SPEED
    if keys[pygame.K_UP] and frisk_pos[1] > HEIGHT - PATH_HEIGHT - FRISK_SIZE//2:
        frisk_pos[1] -= FRISK_SPEED
    if keys[pygame.K_DOWN] and frisk_pos[1] < HEIGHT - FRISK_SIZE:
        frisk_pos[1] += FRISK_SPEED

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
