import math
import random
import pygame
from pygame import Vector2

# --------- НАЛАШТУВАННЯ ----------
WIDTH, HEIGHT = 1000, 700
BG_COLOR = (18, 18, 20)
GLASS_COLOR = (200, 230, 255, 80)  # rgba-like: we'll use alpha when drawing surfaces
SHARD_BORDER = (30, 40, 50)
CRACK_COLOR = (40, 50, 60)
FPS = 60

# Параметри розбиття
MIN_CRACKS = 18
MAX_CRACKS = 40
RADIUS_MEAN = 220
RADIUS_VAR = 60
SHARD_FRAGMENTATION = 0.15  # 0..1 — наскільки сильно "ріжуться" секторні шматки
IMPULSE_MULT = 6.5  # сила відлітання шматків
ANGULAR_SPREAD = 6.0  # множник для кутової швидкості
GRAVITY = Vector2(0, 200)  # невелика гравітація (падають трошки)
AIR_DRAG = 0.995
GROUND_FRICTION = 0.82
# ---------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shatter — імітація розбитого скла (клік)")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 18)

# Поверхня для "скла" (щоб мати прозорість)
glass_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

def random_angle_list(n, jitter=0.4):
    # рівномірно розподілені кути + невеликий джиттер для нерівності
    base = [2 * math.pi * i / n for i in range(n)]
    return [a + (random.uniform(-jitter, jitter) * (2*math.pi/n)) for a in base]

def polygon_centroid(points):
    # centroid for polygon
    x = 0
    y = 0
    a = 0
    for i in range(len(points)):
        x0, y0 = points[i]
        x1, y1 = points[(i+1) % len(points)]
        cross = x0 * y1 - x1 * y0
        a += cross
        x += (x0 + x1) * cross
        y += (y0 + y1) * cross
    if abs(a) < 1e-6:
        return Vector2(sum(p[0] for p in points)/len(points),
                       sum(p[1] for p in points)/len(points))
    a *= 0.5
    cx = x / (6*a)
    cy = y / (6*a)
    return Vector2(cx, cy)

def offset_points(points, offset: Vector2, angle=0.0, scale=1.0):
    # повертає нові координати points після трансформації
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    out = []
    for px, py in points:
        v = Vector2(px, py) - offset
        # scale and rotate
        rx = (v.x * cos_a - v.y * sin_a) * scale
        ry = (v.x * sin_a + v.y * cos_a) * scale
        out.append((rx + offset.x, ry + offset.y))
    return out

class Shard:
    def __init__(self, points, color, centroid_override=None):
        self.local_points = [Vector2(p) for p in points]  # world coords initially
        self.color = color
        if centroid_override is None:
            self.centroid = polygon_centroid(points)
        else:
            self.centroid = Vector2(centroid_override)
        # convert to local coordinates relative to centroid
        self.points = [p - self.centroid for p in self.local_points]
        self.pos = Vector2(self.centroid)
        # physics
        self.vel = Vector2(0, 0)
        self.angle = 0.0
        self.ang_vel = 0.0
        self.mass = max(0.1, abs(self._area()))  # area as mass proxy
        self.alive = True
        self.stopped = False

    def _area(self):
        pts = [(p.x + self.centroid.x, p.y + self.centroid.y) for p in self.points]
        a = 0
        for i in range(len(pts)):
            x0, y0 = pts[i]
            x1, y1 = pts[(i+1) % len(pts)]
            a += x0*y1 - x1*y0
        return a * 0.5

    def world_points(self):
        return [(self.pos + p.rotate_rad(self.angle)) for p in self.points]

    def update(self, dt):
        if self.stopped:
            return
        # apply gravity scaled by mass (bigger shards fall slightly faster)
        self.vel += GRAVITY * (dt * (1.0 / max(1.0, self.mass/50.0)))
        self.vel *= AIR_DRAG ** (dt * 60.0)
        self.pos += self.vel * dt
        self.angle += self.ang_vel * dt
        # ground collision (simple)
        min_y = min((pt.y for pt in self.world_points()))
        max_y = max((pt.y for pt in self.world_points()))
        if max_y > HEIGHT:
            # place on ground
            dy = max_y - HEIGHT
            self.pos.y -= dy
            self.vel.y *= -0.25
            self.vel.x *= GROUND_FRICTION
            self.ang_vel *= 0.5
            # if very slow, stop the shard to save CPU
            if self.vel.length() < 10 and abs(self.ang_vel) < 0.5:
                self.stopped = True

    def draw(self, surf):
        pts = [(p.x + self.pos.x, p.y + self.pos.y) for p in self.points]
        if len(pts) >= 3:
            # fill with semi-transparent glass color
            s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            r, g, b, a = self.color
            # прозорий колір (без a!)
            def clamp(x): 
                 return max(0, min(255, int(x)))

            pygame.draw.polygon(s, (clamp(r), clamp(g), clamp(b)), pts)
            inner = offset_points(pts, self.pos, angle=0.0, scale=0.98)
            pygame.draw.polygon(s, (clamp(r+8), clamp(g+8), clamp(b+10)), inner)

            # тепер задаємо прозорість усієї поверхні
            s.set_alpha(a)
            surf.blit(s, (0, 0))

            # border
            pygame.draw.polygon(surf, SHARD_BORDER, pts, 1)

shards = []
crack_lines = []  # list of (start, end) for drawing thin cracks

def create_shatter_at(pos, power=1.0):
    """Генеруємо розбиття в точці pos (Vector2). power — множник сили/радіуса."""
    cx, cy = pos.x, pos.y
    # number of radial cracks
    n = random.randint(MIN_CRACKS, MAX_CRACKS)
    angles = random_angle_list(n, jitter=0.6)
    # sort angles around
    angles.sort()
    # radius per angle (irregular circle)
    radii = [max(40, random.gauss(RADIUS_MEAN * power, RADIUS_VAR)) for _ in range(n)]
    # make sectors points on the circle with jittered radius
    circle_points = [(cx + math.cos(a) * r, cy + math.sin(a) * r) for a, r in zip(angles, radii)]
    # create shards as triangles/polygons between center and adjacent circle points,
    # but add random inner node to make shape irregular
    shards_local = []
    for i in range(n):
        p1 = circle_points[i]
        p2 = circle_points[(i+1) % n]
        # inner point a bit out from center
        t = random.uniform(0.08, 0.32 + SHARD_FRAGMENTATION)
        inner = (cx + (p1[0] - cx)*t + (p2[0] - cx)*t * 0.05 + random.uniform(-8,8),
                 cy + (p1[1] - cy)*t + (p2[1] - cy)*t * 0.05 + random.uniform(-8,8))
        # construct polygon as [center, inner, p1, maybe mid points, p2]
        poly = [ (cx, cy), inner, p1 ]
        # sometimes add a midpoint between p1-p2 for bigger shards
        if random.random() < 0.35:
            mid = ((p1[0] + p2[0]) * 0.5 + random.uniform(-6,6), (p1[1] + p2[1]) * 0.5 + random.uniform(-6,6))
            poly.append(mid)
        poly.append(p2)
        shards_local.append(poly)

    # Optional: further split some shards to create small splinters
    final_shards = []
    for poly in shards_local:
        if random.random() < 0.12:
            # split along random chord
            a = random.choice(poly[1:-1])
            b = (a[0] + random.uniform(-30, 30), a[1] + random.uniform(-30, 30))
            p1 = [poly[0], a, b]
            p2 = [poly[0], b] + poly[2:]
            final_shards.append(p1)
            final_shards.append(p2)
        else:
            final_shards.append(poly)

    # create shards objects and assign velocities
    global shards, crack_lines
    for poly in final_shards:
        # small polygons may be ignored
        if len(poly) < 3:
            continue
        # color slightly varying
        base = GLASS_COLOR
        col = (base[0] + random.randint(-6,6), base[1] + random.randint(-6,6), base[2] + random.randint(-6,6), base[3])
        s = Shard(poly, col)
        # velocity directed downwards instead of radial
        area = max(1.0, abs(s._area()))
        impulse = (IMPULSE_MULT * power) * (200.0 / (area + 40.0)) * (random.uniform(0.8, 1.2))*200

        # основний рух вниз
        s.vel = Vector2(0, 1) * impulse

        # невеликий боковий розкид, щоб падало не ідеально рівно
        s.vel.x += random.uniform(-60, 60)
        s.vel.y += random.uniform(-20, 40)

        # невелика кутова швидкість
        s.ang_vel = random.uniform(-ANGULAR_SPREAD, ANGULAR_SPREAD) * (1.0 + 100.0/(area+50.0))

        s.ang_vel = random.uniform(-ANGULAR_SPREAD, ANGULAR_SPREAD) * (1.0 + 100.0/(area+50.0))
        final_speed = s.vel.length()
        # small upward boost sometimes
        if random.random() < 0.35:
            s.vel.y -= random.uniform(0, 120)
        shards.append(s)

    # generate crack lines radiating from center plus some branching
    crack_count = int(n * 0.9)
    crack_lines = []
    for i in range(crack_count):
        a = angles[i]
        l = radii[i] * random.uniform(0.9, 1.05)
        end = (cx + math.cos(a) * l, cy + math.sin(a) * l)
        crack_lines.append(((cx, cy), end))
        # maybe branch
        if random.random() < 0.25:
            branch_ang = a + random.uniform(-0.8, 0.8)
            bl = l * random.uniform(0.35, 0.65)
            bend = (cx + math.cos(branch_ang) * bl, cy + math.sin(branch_ang) * bl)
            crack_lines.append((end, bend))

def draw_cracks(surface):
    # thin lines with small random jitter to look natural
    for (s, e) in crack_lines:
        sx, sy = s
        ex, ey = e
        # main line
        pygame.draw.aaline(surface, CRACK_COLOR, (sx, sy), (ex, ey))
        # small micro-branches
        if random.random() < 0.6:
            mx = sx + (ex - sx) * random.uniform(0.2, 0.9)
            my = sy + (ey - sy) * random.uniform(0.2, 0.9)
            bx = mx + random.uniform(-12, 12)
            by = my + random.uniform(-12, 12)
            pygame.draw.aaline(surface, CRACK_COLOR, (mx, my), (bx, by))

def clean_stopped_shards():
    # occasionally remove shards that are far off-screen or stopped to keep performance
    global shards
    new = []
    for s in shards:
        if not s.stopped:
            # keep
            new.append(s)
        else:
            # keep a few stopped ones near top-left for aesthetic
            if 0 <= s.pos.x <= WIDTH and 0 <= s.pos.y <= HEIGHT:
                new.append(s)
    shards = new[:600]  # cap

def main():
    running = True
    last_click = None
    spawn_cool = 0.0

    while running:
        dt = clock.tick(FPS) / 1000.0
        spawn_cool = max(0.0, spawn_cool - dt)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    p = Vector2(event.pos)
                    # power may depend on double-click or SHIFT for stronger hit
                    power = 1.0
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        power = 1.6
                    create_shatter_at(p, power=power)
                    last_click = p

        # update physics
        for s in shards:
            s.update(dt)

        # drawing
        screen.fill(BG_COLOR)

        # draw background scene (simple) - subtle room gradient
        # (we keep it minimal to emphasize glass)
        # glass surface: clear
        glass_surface.fill((0,0,0,0))
        # draw shards
        for s in shards:
            s.draw(glass_surface)

        # draw cracks on top
        if crack_lines:
            draw_cracks(glass_surface)

        # composite glass: slightly bluish transparent rectangle as "pane"
        # but we want shards already drawn; to enhance, draw a faint rectangle border
        border_rect = pygame.Rect(60, 40, WIDTH - 120, HEIGHT - 80)
        # place the glass surface onto main screen
        screen.blit(glass_surface, (0,0))

        # subtle frame for glass (for context)
        pygame.draw.rect(screen, (60, 70, 80), border_rect, 2)
        # small UI hint
        hint = font.render("Клік — розбити. Shift+клік — сильніший удар. Вихід — закрити вікно.", True, (200,200,200))
        screen.blit(hint, (12, HEIGHT - 28))

        pygame.display.flip()

        # housekeeping
        if random.random() < 0.015:
            clean_stopped_shards()

    pygame.quit()

if __name__ == "__main__":
    main()
