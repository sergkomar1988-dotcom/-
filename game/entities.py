"""Игровые объекты: герой, препятствия, снаряды, боссы, лом, частицы."""
import math
import random

import pygame

from config import (
    GROUND_Y, HERO_X, HERO_HIT_W, HERO_STAND_H, HERO_SLIDE_H, BASE_HP, INVULN_TIME,
    GRAVITY, JUMP_VEL, DOUBLE_JUMP_VEL, JUMP_BUFFER, SLIDE_MIN, HIGH_Y, LOW_Y, W, H,
)

# ---------------- герой ----------------


class Hero:
    def __init__(self, skills):
        self.max_hp = BASE_HP + skills["hp"]
        self.hp = self.max_hp
        self.dmg = 1 + skills["dmg"]
        self.fire_base = 0.30 * (0.92 ** skills["rate"])
        self.magnet = 90 + 40 * skills["magnet"]
        self.xp_mult = 1.0 + 0.2 * skills["xp"]
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.on_ground = True
        self.jumps = 0
        self.jump_buf = 0.0
        self.slide_t = 0.0
        self.sliding = False
        self.fire_cd = 0.0
        self.invuln = 0.0
        self.t = 0.0
        self.events = []  # звуковые события для Play

    def press_jump(self):
        self.jump_buf = JUMP_BUFFER

    def update(self, dt, down):
        self.t += dt
        self.fire_cd -= dt
        self.invuln -= dt
        if self.jump_buf > 0:
            self.jump_buf -= dt
        if self.jump_buf > 0 and (self.on_ground or self.jumps < 2):
            if self.on_ground:
                self.vy = -JUMP_VEL
                self.jumps = 1
                self.events.append("jump")
            else:
                self.vy = -DOUBLE_JUMP_VEL
                self.jumps = 2
                self.events.append("double")
            self.on_ground = False
            self.jump_buf = 0.0
            self.slide_t = 0.0
        if down:
            if self.on_ground:
                self.slide_t = SLIDE_MIN
            elif self.vy < 1100:
                self.vy = 1100.0  # быстрое падение вниз
        if self.slide_t > 0:
            self.slide_t = max(0.0, self.slide_t - dt)
        self.sliding = self.on_ground and (down or self.slide_t > 0)
        if not self.on_ground:
            self.vy += GRAVITY * dt
            self.y += self.vy * dt
            if self.y >= GROUND_Y:
                self.y = float(GROUND_Y)
                self.vy = 0.0
                self.on_ground = True
                self.jumps = 0
                self.events.append("land")

    def hitbox(self):
        h = HERO_SLIDE_H if self.sliding else HERO_STAND_H
        return pygame.Rect(HERO_X - HERO_HIT_W // 2, int(self.y) - h, HERO_HIT_W, h)

    def hurt(self):
        if self.invuln > 0 or self.hp <= 0:
            return False
        self.hp -= 1
        self.invuln = INVULN_TIME
        return True

    def can_fire(self):
        return self.fire_cd <= 0 and self.hp > 0

    def fire(self):
        self.fire_cd = self.fire_base

    def draw(self, s, img_run, img_jump, img_slide):
        if self.invuln > 0 and int(self.t * 18) % 2 == 0:
            return
        if self.sliding:
            img = img_slide
            bob = 0
        elif not self.on_ground:
            img = img_jump
            bob = 0
        else:
            img = img_run
            bob = abs(math.sin(self.t * 15)) * 6
        shadow_w = max(40, 90 - (GROUND_Y - self.y) * 0.25)
        pygame.draw.ellipse(s, (20, 14, 14), (HERO_X - shadow_w / 2, GROUND_Y - 6, shadow_w, 12))
        rect = img.get_rect(midbottom=(HERO_X, int(self.y - bob)))
        s.blit(img, rect)


# ---------------- препятствия ----------------

OBS_DEFS = {
    "crate": dict(w=64, h=64, bottom=GROUND_Y, breakable=True),
    "spikes": dict(w=84, h=36, bottom=GROUND_Y, breakable=False),
    "barrel": dict(w=54, h=76, bottom=GROUND_Y, breakable=False),
    "beam": dict(w=110, h=70, bottom=GROUND_Y - 100, breakable=False),  # под неё скользят
    "drone": dict(w=60, h=42, bottom=GROUND_Y - 79, breakable=True),    # летающий, скольжение
}


class Obstacle:
    def __init__(self, kind, x, accent):
        d = OBS_DEFS[kind]
        self.kind = kind
        self.w, self.h, self.bottom = d["w"], d["h"], d["bottom"]
        self.breakable = d["breakable"]
        self.x = float(x)
        self.accent = accent
        self.alive = True
        self.spent = False
        self.t = 0.0

    def rect(self):
        return pygame.Rect(int(self.x), int(self.bottom - self.h), self.w, self.h)

    def update(self, dt, speed):
        self.x -= speed * dt
        self.t += dt
        if self.x < -self.w - 20:
            self.alive = False

    def draw(self, s):
        r = self.rect()
        k = self.kind
        if k == "crate":
            pygame.draw.rect(s, (120, 84, 48), r)
            pygame.draw.rect(s, (70, 46, 26), r, 4)
            pygame.draw.line(s, (70, 46, 26), r.topleft, r.bottomright, 4)
            pygame.draw.line(s, (70, 46, 26), r.topright, r.bottomleft, 4)
            pygame.draw.rect(s, self.accent, r.inflate(-14, -14), 2)
        elif k == "spikes":
            n = 3
            for i in range(n):
                x0 = r.x + i * r.w / n
                pts = [(x0, r.bottom), (x0 + r.w / n / 2, r.top), (x0 + r.w / n, r.bottom)]
                pygame.draw.polygon(s, (150, 150, 160), pts)
                pygame.draw.polygon(s, (60, 60, 70), pts, 2)
        elif k == "barrel":
            pygame.draw.rect(s, (60, 95, 150), r, border_radius=10)
            pygame.draw.rect(s, (30, 40, 70), r, 3, border_radius=10)
            for yy in (r.top + 12, r.centery, r.bottom - 12):
                pygame.draw.line(s, (30, 40, 70), (r.x, yy), (r.right, yy), 4)
            pygame.draw.circle(s, self.accent, r.center, 9)
        elif k == "beam":
            pygame.draw.rect(s, (90, 90, 100), r)
            s.set_clip(r)
            for x in range(r.x - r.h, r.right, 28):
                pygame.draw.line(s, (240, 200, 40), (x, r.bottom), (x + r.h, r.top), 12)
            s.set_clip(None)
            pygame.draw.rect(s, (40, 40, 48), r, 3)
        elif k == "drone":
            c = r.center
            pygame.draw.circle(s, (50, 50, 60), c, 18)
            pygame.draw.circle(s, (230, 60, 50), c, 5)
            a = self.t * 30
            for sign in (1, -1):
                dx, dy = math.cos(a) * 28 * sign, math.sin(a) * 6
                pygame.draw.line(s, (200, 200, 210), (c[0] - dx, c[1] - dy), (c[0] + dx, c[1] + dy), 4)


# ---------------- снаряды врагов ----------------


class Shot:
    """Снаряд босса. kind определяет вид и то, можно ли его сбить выстрелом."""

    def __init__(self, kind, x, y, vx, vy=0.0, g=0.0, w=40, h=40, color=(255, 120, 60)):
        self.kind = kind
        self.x, self.y = float(x), float(y)
        self.vx, self.vy, self.g = vx, vy, g
        self.w, self.h = w, h
        self.color = color
        self.alive = True
        self.t = 0.0
        self.destroyable = kind not in ("saw", "wave", "fist")

    def rect(self):
        return pygame.Rect(int(self.x - self.w / 2), int(self.y - self.h / 2), self.w, self.h)

    def update(self, dt):
        self.t += dt
        self.vy += self.g * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.g > 0 and self.y >= GROUND_Y - self.h / 2:
            self.alive = False  # кислота упала на землю
        if self.x < -150 or self.x > W + 400 or self.y > H + 100 or self.y < -300:
            self.alive = False

    def draw(self, s):
        r = self.rect()
        c = self.color
        k = self.kind
        if k == "saw":
            cx, cy, R = int(self.x), int(self.y), self.w // 2
            pygame.draw.circle(s, (190, 190, 200), (cx, cy), R)
            for i in range(10):
                a = self.t * 12 + i * math.pi / 5
                pygame.draw.line(s, (235, 235, 245), (cx + math.cos(a) * (R - 8), cy + math.sin(a) * (R - 8)),
                                 (cx + math.cos(a) * (R + 4), cy + math.sin(a) * (R + 4)), 5)
            pygame.draw.circle(s, (60, 60, 70), (cx, cy), R // 3)
        elif k == "wave":
            pygame.draw.rect(s, c, r)
            pygame.draw.rect(s, (255, 230, 150), r.inflate(-16, -16))
            pygame.draw.rect(s, (120, 40, 10), r, 3)
        elif k == "fist":
            pygame.draw.rect(s, (120, 120, 130), r, border_radius=14)
            pygame.draw.rect(s, (40, 40, 48), r, 4, border_radius=14)
            for i in range(1, 4):
                pygame.draw.line(s, (50, 50, 58), (r.x + i * r.w / 4, r.y + 10), (r.x + i * r.w / 4, r.bottom - 10), 3)
        elif k == "rocket":
            flame = [(r.left, r.centery - 7), (r.left - 22, r.centery), (r.left, r.centery + 7)]
            pygame.draw.polygon(s, (255, 170, 60), flame)
            pygame.draw.rect(s, (70, 70, 80), r, border_radius=6)
        elif k == "blade":
            cx, cy, R = int(self.x), int(self.y), self.w // 2
            for i in range(2):
                a = self.t * 18 + i * math.pi / 2
                pygame.draw.line(s, (200, 240, 255), (cx - math.cos(a) * R, cy - math.sin(a) * R),
                                 (cx + math.cos(a) * R, cy + math.sin(a) * R), 8)
            pygame.draw.circle(s, c, (cx, cy), 8)
        elif k == "bolt" or k == "bullet":
            pygame.draw.rect(s, c, r, border_radius=10)
            pygame.draw.rect(s, (255, 255, 255), r.inflate(-r.w // 2, -r.h // 2), border_radius=6)
        else:  # spit, acid, spore
            cx, cy, R = int(self.x), int(self.y), self.w // 2
            pygame.draw.circle(s, c, (cx, cy), R)
            pygame.draw.circle(s, (240, 255, 200), (cx - R // 3, cy - R // 3), max(2, R // 4))


# ---------------- снаряды героя, лом, частицы ----------------


class Bullet:
    def __init__(self, x, y, dmg, color):
        self.x, self.y = float(x), float(y)
        self.dmg = dmg
        self.color = color
        self.alive = True

    def rect(self):
        return pygame.Rect(int(self.x), int(self.y - 17), 26, 34)

    def update(self, dt):
        self.x += 1200 * dt
        if self.x > W + 40:
            self.alive = False

    def draw(self, s):
        pygame.draw.rect(s, self.color, (int(self.x), int(self.y - 4), 26, 8), border_radius=4)
        pygame.draw.rect(s, (255, 255, 255), (int(self.x) + 6, int(self.y - 2), 14, 4), border_radius=2)


class Pickup:
    def __init__(self, kind, x, y):
        self.kind = kind  # "scrap" или "heart"
        self.x, self.y = float(x), float(y)
        self.alive = True
        self.t = random.random() * 6

    def rect(self):
        return pygame.Rect(int(self.x - 14), int(self.y - 14), 28, 28)

    def update(self, dt, speed, target, magnet):
        self.t += dt
        self.x -= speed * dt
        dx, dy = target[0] - self.x, target[1] - self.y
        dist = math.hypot(dx, dy)
        if 0 < dist < magnet:
            k = min(1.0, 700 * dt / dist)
            self.x += dx * k
            self.y += dy * k
        if self.x < -40:
            self.alive = False

    def draw(self, s):
        bob = math.sin(self.t * 5) * 3
        cx, cy = int(self.x), int(self.y + bob)
        if self.kind == "scrap":
            pygame.draw.circle(s, (255, 205, 80), (cx, cy), 11)
            pygame.draw.circle(s, (120, 80, 20), (cx, cy), 11, 2)
            pygame.draw.circle(s, (120, 80, 20), (cx, cy), 4)
            for i in range(6):
                a = self.t * 3 + i * math.pi / 3
                pygame.draw.circle(s, (255, 205, 80), (int(cx + math.cos(a) * 14), int(cy + math.sin(a) * 14)), 3)
        else:
            pygame.draw.circle(s, (230, 60, 70), (cx - 6, cy - 3), 8)
            pygame.draw.circle(s, (230, 60, 70), (cx + 6, cy - 3), 8)
            pygame.draw.polygon(s, (230, 60, 70), [(cx - 14, cy), (cx + 14, cy), (cx, cy + 14)])


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size, grav=500.0):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.grav = grav

    def update(self, dt):
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.life -= dt

    def draw(self, s):
        k = max(0.0, self.life / self.max_life)
        pygame.draw.circle(s, self.color, (int(self.x), int(self.y)), max(1, int(self.size * k)))


# ---------------- боссы ----------------


class Boss:
    """Босс стоит справа и атакует по сценариям-генераторам. Каждый сценарий
    выдаёт паузы через yield; между сценариями есть перезарядка."""

    def __init__(self, cfg, img, hp, cycle, out_list):
        self.cfg = cfg
        self.img = img
        self.flash_img = img.copy()
        self.flash_img.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
        self.w, self.h = img.get_size()
        self.x = W + self.w / 2 + 60
        self.target_x = W - self.w / 2 - 40
        self.bottom = GROUND_Y + 6
        self.max_hp = hp
        self.hp = hp
        self.color = cfg["accent"]
        self.out = out_list
        self.patterns = cfg["patterns"]
        self.cooldown = max(0.9, 1.6 - 0.2 * cycle)
        self.arrived = False
        self.wait = 1.2
        self.flash = 0.0
        self.dying = False
        self.t = 0.0
        self.last = None
        self.routine = self._routine()

    @property
    def ox(self):
        """Точка, из которой вылетают снаряды (примерно у головы/пушки)."""
        return self.x - self.w * 0.35

    def rect(self):
        return pygame.Rect(int(self.x - self.w * 0.4), int(self.bottom - self.h * 0.9),
                           int(self.w * 0.8), int(self.h * 0.9))

    def hit(self, dmg):
        self.hp -= dmg
        self.flash = 0.08
        return self.hp <= 0

    def update(self, dt):
        self.t += dt
        self.flash -= dt
        if self.dying:
            return
        if not self.arrived:
            self.x -= 380 * dt
            if self.x <= self.target_x:
                self.x = self.target_x
                self.arrived = True
            return
        self.wait -= dt
        if self.wait <= 0:
            try:
                self.wait = next(self.routine)
            except StopIteration:
                self.wait = 999

    def _routine(self):
        while True:
            options = [p for p in self.patterns if p != self.last] or self.patterns
            name = random.choice(options)
            self.last = name
            yield from getattr(self, "p_" + name)()
            ratio = self.hp / self.max_hp
            yield self.cooldown * (0.7 if ratio < 0.5 else 1.0)

    def shoot(self, kind, x, y, vx, vy=0.0, g=0.0, w=40, h=40, color=None):
        self.out.append(Shot(kind, x, y, vx, vy, g, w, h, color or self.color))

    # --- сценарии атак: уровень 1 (грейдер)
    def p_saw(self):
        for _ in range(2):
            self.shoot("saw", self.ox, GROUND_Y - 28, -520, w=56, h=56, color=(200, 200, 210))
            yield 0.8

    def p_bolt(self):
        for _ in range(3):
            self.shoot("bolt", self.ox, HIGH_Y, -640, w=80, h=24)
            yield 0.45

    def p_mix(self):
        self.shoot("saw", self.ox, GROUND_Y - 28, -520, w=56, h=56, color=(200, 200, 210))
        yield 0.6
        self.shoot("bolt", self.ox, HIGH_Y, -660, w=80, h=24)
        yield 1.0

    # --- уровень 2 (хищник)
    def p_acid(self):
        for _ in range(2):
            sy, g, vy = GROUND_Y - 240, 1400.0, -380.0
            y0 = sy - GROUND_Y
            t_land = (-vy + math.sqrt(vy * vy - 2 * g * y0)) / g
            target = HERO_X + random.uniform(40, 200)
            vx = (target - self.ox) / t_land
            self.shoot("acid", self.ox, sy, vx, vy=vy, g=g, w=34, h=34, color=(170, 255, 60))
            yield 1.1

    def p_spit(self):
        for _ in range(3):
            self.shoot("spit", self.ox, LOW_Y - 4, -720, w=44, h=26, color=(120, 230, 40))
            yield 0.45

    def p_spore(self):
        for _ in range(3):
            self.shoot("spore", self.ox, HIGH_Y, -440, w=30, h=30, color=(230, 230, 200))
            yield 0.5

    # --- уровень 3 (жнец)
    def p_stream(self):
        for i in range(6):
            y = LOW_Y if i % 2 == 0 else HIGH_Y
            self.shoot("bullet", self.ox, y, -900, w=44, h=12)
            yield 0.5

    def p_blade(self):
        for _ in range(2):
            self.shoot("blade", self.ox, HIGH_Y, -520, w=60, h=60, color=(200, 240, 255))
            yield 0.9

    # --- уровень 4 (колосс)
    def p_stomp(self):
        for _ in range(2):
            self.shoot("wave", self.ox, GROUND_Y - 28, -480, w=60, h=56, color=(255, 140, 40))
            yield 1.0

    def p_fist(self):
        self.shoot("fist", self.ox, GROUND_Y - 120, -380, w=110, h=90)
        yield 0.9

    def p_barrage(self):
        for i in range(3):
            y = LOW_Y if i % 2 else HIGH_Y
            self.shoot("rocket", self.ox, y, -640, w=70, h=26, color=(255, 120, 40))
            yield 0.5

    def draw(self, s):
        bob = math.sin(self.t * 2.2) * 4 if self.arrived else 0
        img = self.flash_img if self.flash > 0 else self.img
        s.blit(img, img.get_rect(midbottom=(int(self.x), int(self.bottom - bob))))
