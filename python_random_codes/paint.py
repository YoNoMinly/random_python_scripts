import pygame
import sys
import math
from datetime import datetime

# --- Налаштування ---
WIDTH, HEIGHT = 1000, 700
TOP_PANEL_HEIGHT = 50
BUTTON_PANEL_HEIGHT = 50
BG_COLOR = (255, 255, 255)
FPS = 60

# Кольори
PALETTE = [
    (0,0,0), (255,0,0), (0,0,255), (0,200,0),
    (255,165,0), (255,192,203), (128,0,128), (0,255,255),
    "rainbow"
]

RAINBOW_COLORS = [
    (255,0,0),(255,127,0),(255,255,0),(0,255,0),
    (0,0,255),(75,0,130),(148,0,211)
]

current_color = PALETTE[0]
brush_size = 5
eraser_size = 10
current_tool = "brush"
rainbow_index = 0

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pixel Paint with Save/Clear")
clock = pygame.time.Clock()
screen.fill(BG_COLOR)

drawing = False
start_pos = None

SAVE_RECT = None
CLEAR_RECT = None

# Робоча область починається нижче обох панелей
CANVAS_TOP = TOP_PANEL_HEIGHT + BUTTON_PANEL_HEIGHT

# --- Функції малювання ---
def draw_pixel_brush(surface, x, y, color, size):
    half = size // 2
    for i in range(-half, half + 1):
        for j in range(-half, half + 1):
            px, py = x + i, y + j
            if CANVAS_TOP <= py < HEIGHT and 0 <= px < WIDTH:
                surface.set_at((px, py), color)

def flood_fill(surface, x, y, target_color, replacement_color):
    if target_color == replacement_color:
        return
    stack = [(x, y)]
    while stack:
        cx, cy = stack.pop()
        if 0 <= cx < WIDTH and CANVAS_TOP <= cy < HEIGHT and surface.get_at((cx, cy))[:3] == target_color:
            surface.set_at((cx, cy), replacement_color)
            stack.extend([(cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)])

def draw_line(surface, start, end, color):
    x1, y1 = start
    x2, y2 = end
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x, y = x1, y1
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    if dx > dy:
        err = dx / 2.0
        while x != x2:
            if y >= CANVAS_TOP:
                surface.set_at((x, y), color)
            err -= dy
            if err < 0:
                y += sy
                err += dx
            x += sx
    else:
        err = dy / 2.0
        while y != y2:
            if y >= CANVAS_TOP:
                surface.set_at((x, y), color)
            err -= dx
            if err < 0:
                x += sx
                err += dy
            y += sy
    if y >= CANVAS_TOP:
        surface.set_at((x, y), color)

def draw_rect(surface, start, end, color):
    x1, y1 = start
    x2, y2 = end
    for x in range(min(x1,x2), max(x1,x2)+1):
        for y in range(min(y1,y2), max(y1,y2)+1):
            if y >= CANVAS_TOP:
                surface.set_at((x,y), color)

def draw_circle(surface, start, end, color):
    x1, y1 = start
    x2, y2 = end
    radius = int(math.hypot(x2-x1, y2-y1))
    for x in range(x1-radius, x1+radius+1):
        for y in range(y1-radius, y1+radius+1):
            if CANVAS_TOP <= y < HEIGHT and 0 <= x < WIDTH:
                if (x - x1)**2 + (y - y1)**2 <= radius**2:
                    surface.set_at((x, y), color)

# --- Панелі ---
def draw_top_panel():
    pygame.draw.rect(screen, (200,200,200), (0,0,WIDTH,TOP_PANEL_HEIGHT))

    font = pygame.font.SysFont(None, 24)

    # палітра
    for i, color in enumerate(PALETTE):
        if color == "rainbow":
            for j, c in enumerate(RAINBOW_COLORS):
                pygame.draw.rect(screen, c, (10 + i*50 + j*5, 10, 5, 30))
        else:
            pygame.draw.rect(screen, color, (10 + i*50, 10, 40, 30))

    # індикатор кольору
    if current_color == "rainbow":
        pygame.draw.rect(screen, (0,0,0), (WIDTH-100, 10, 40, 30))
    else:
        pygame.draw.rect(screen, current_color, (WIDTH-100, 10, 40, 30))

    # написи праворуч
    screen.blit(font.render(f"Brush: {brush_size}", True, (0,0,0)), (WIDTH-300, 5))
    screen.blit(font.render(f"Eraser: {eraser_size}", True, (0,0,0)), (WIDTH-300, 25))
    screen.blit(font.render(f"Tool: {current_tool}", True, (0,0,0)), (WIDTH-200, 15))


def draw_button_panel():
    global SAVE_RECT, CLEAR_RECT
    pygame.draw.rect(screen, (180,180,180), (0, TOP_PANEL_HEIGHT, WIDTH, BUTTON_PANEL_HEIGHT))

    font = pygame.font.SysFont(None, 24)
    SAVE_RECT = pygame.Rect(WIDTH//2 - 100, TOP_PANEL_HEIGHT + 10, 80, 30)
    CLEAR_RECT = pygame.Rect(WIDTH//2 + 20, TOP_PANEL_HEIGHT + 10, 80, 30)

    pygame.draw.rect(screen, (220,220,220), SAVE_RECT)
    pygame.draw.rect(screen, (220,220,220), CLEAR_RECT)

    screen.blit(font.render("Save", True, (0,0,0)), (SAVE_RECT.x + 15, SAVE_RECT.y + 5))
    screen.blit(font.render("Clear", True, (0,0,0)), (CLEAR_RECT.x + 15, CLEAR_RECT.y + 5))

# --- Основний цикл ---
running = True
while running:
    clock.tick(FPS)
    draw_top_panel()
    draw_button_panel()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            # палітра
            if my <= TOP_PANEL_HEIGHT:
                for i, color in enumerate(PALETTE):
                    if 10 + i*50 <= mx <= 50 + i*50 and 10 <= my <= 40:
                        current_color = color
                        current_tool = "brush"
                continue

            # кнопки
            if SAVE_RECT and SAVE_RECT.collidepoint(event.pos):
                filename = f"pixel_art_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                pygame.image.save(screen.subsurface((0, CANVAS_TOP, WIDTH, HEIGHT-CANVAS_TOP)), filename)
                print(f"Saved as {filename}")
                continue
            elif CLEAR_RECT and CLEAR_RECT.collidepoint(event.pos):
                screen.fill(BG_COLOR, (0, CANVAS_TOP, WIDTH, HEIGHT-CANVAS_TOP))
                continue

            # інструменти
            if my >= CANVAS_TOP:
                drawing = True
                start_pos = event.pos
                if current_tool == "fill":
                    target = screen.get_at(start_pos)[:3]
                    flood_fill(screen, start_pos[0], start_pos[1], target,
                               current_color if current_color != "rainbow" else RAINBOW_COLORS[0])
                elif current_tool == "eyedropper":
                    current_color = screen.get_at(start_pos)[:3]
                    current_tool = "brush"

        elif event.type == pygame.MOUSEBUTTONUP:
            if drawing:
                end_pos = event.pos
                if current_tool == "line":
                    draw_line(screen, start_pos, end_pos,
                              current_color if current_color != "rainbow" else RAINBOW_COLORS[0])
                elif current_tool == "rect":
                    draw_rect(screen, start_pos, end_pos,
                              current_color if current_color != "rainbow" else RAINBOW_COLORS[0])
                elif current_tool == "circle":
                    draw_circle(screen, start_pos, end_pos,
                                current_color if current_color != "rainbow" else RAINBOW_COLORS[0])
            drawing = False
            start_pos = None

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                current_tool = "brush"
            elif event.key == pygame.K_e:
                current_tool = "eraser"
            elif event.key == pygame.K_f:
                current_tool = "fill"
            elif event.key == pygame.K_l:
                current_tool = "line"
            elif event.key == pygame.K_r:
                current_tool = "rect"
            elif event.key == pygame.K_c:
                current_tool = "circle"
            elif event.key == pygame.K_p:
                current_tool = "eyedropper"
            elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                if current_tool == "eraser":
                    eraser_size += 1
                else:
                    brush_size += 1
            elif event.key == pygame.K_MINUS:
                if current_tool == "eraser" and eraser_size > 1:
                    eraser_size -= 1
                elif brush_size > 1:
                    brush_size -= 1

    if drawing:
        mx, my = pygame.mouse.get_pos()
        if current_tool == "brush":
            draw_pixel_brush(screen, mx, my,
                             current_color if current_color != "rainbow"
                             else RAINBOW_COLORS[rainbow_index % len(RAINBOW_COLORS)],
                             brush_size)
            if current_color == "rainbow":
                rainbow_index += 1
        elif current_tool == "eraser":
            draw_pixel_brush(screen, mx, my, BG_COLOR, eraser_size)

    pygame.display.flip()

pygame.quit()
sys.exit()
