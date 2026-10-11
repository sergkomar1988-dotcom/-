"""Игровая сцена: бесконечный бег, предупреждение о боссе, бой, гибель."""
import math
import random

import pygame

import assets
from config import (
    W, H, GROUND_Y, HERO_X, PX_PER_M, LOW_Y, HIGH_Y, LEVELS,
)
from entities import Hero, Obstacle, Shot, Bullet, Pickup, Particle, Boss  # noqa: F401
from ui import text, panel, Menu


def lerp(a, b, t):
    return a + (b - a) * t


def heart(s, cx, cy, size, color):
    r = size / 4
    pygame.draw.circle(s, color, (int(cx - r), int(cy - r / 2)), int(r))
    pygame.draw.circle(s, color, (int(cx + r), int(cy - r / 2)), int(r))
    pygame.draw.polygon(s, color, [(cx - size / 2, cy - r / 2), (cx + size / 2, cy - r / 2), (cx, cy + size / 2)])


class Play:
    def __init__(self, app, idx, cycle=0):
        self.app = app
        self.idx = idx
        self.cycle = cycle
        self.cfg = LEVELS[idx]
        self.accent = self.cfg["accent"]
        self.hero = Hero(app.save.data["skills"])
        self.bg = assets.background(idx)
        self.img_run = assets.hero_run()
        self.img_jump = assets.hero_jump()
        self.img_slide = assets.hero_slide()
        self.shade = pygame.Surface((W, H), pygame.SRCALPHA)
        self.shade.fill((0, 0, 0, 70))
        self.canvas = pygame.Surface((W, H))
        self.streak_color = tuple(int(c * 0.7) for c in self.accent)
        self.streaks = [[random.uniform(0, W), random.uniform(180, H), random.uniform(30, 90)] for _ in range(26)]

        self.speed = float(self.cfg["speed"][0])
        self.meters = 0.0
        self.length = self.cfg["length"]
        self.obstacles = []
        self.shots = []
        self.bullets = []
        self.pickups = []
        self.particles = []
        self.obs_gap = 300.0
        self.pick_timer = 0.8
        self.phase = "run"          # run -> warn -> boss -> boss_dying | dying
        self.phase_t = 0.0
        self.boss = None
        self.boss_down = False
        self.kills = 0
        self.scrap = 0
        self.run_xp = 0
        self.score = 0
        self.banner = ""
        self.banner_t = 0.0
        self.banner_color = (255, 230, 160)
        self.hint_t = 9.0
        self.shake = 0.0
        self.down_held = False
        self.shoot_held = False
        self.paused = False
        self.done = False
        self.t = 0.0
        self.pause_menu = Menu([("Продолжить", self.resume),
                                ("В меню (прогресс сохранится)", self.abandon)], top=360, width=440)
        title = self.cfg["name"] + (f"  ·  круг {cycle + 1}" if cycle else "")
        self.show_banner(f"УРОВЕНЬ {idx + 1}: {title}", 2.6)

    # ---------- управление ----------

    def show_banner(self, msg, dur, color=(255, 230, 160)):
        self.banner, self.banner_t, self.banner_color = msg, dur, color

    def resume(self):
        self.paused = False

    def abandon(self):
        self.app.abandon_run(self)

    def handle(self, e):
        if e.type == pygame.KEYUP:
            if e.key in (pygame.K_DOWN, pygame.K_s):
                self.down_held = False
            elif e.key in (pygame.K_x, pygame.K_z):
                self.shoot_held = False
            return
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.shoot_held = False
            return
        if self.paused:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.resume()
            else:
                self.pause_menu.handle(e)
            return
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                self.hero.press_jump()
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.down_held = True
            elif e.key in (pygame.K_x, pygame.K_z):
                self.shoot_held = True
            elif e.key == pygame.K_ESCAPE:
                self.paused = True
                self.pause_menu.sel = 0
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                self.shoot_held = True
            elif e.button == 3:
                self.hero.press_jump()

    # ---------- логика ----------

    def update(self, dt):
        if self.paused or self.done:
            return
        self.t += dt
        self.phase_t += dt
        if self.banner_t > 0:
            self.banner_t -= dt
        if self.hint_t > 0:
            self.hint_t -= dt
        self.shake = max(0.0, self.shake - dt * 40)

        ph = self.phase
        if ph == "run":
            target = lerp(self.cfg["speed"][0], self.cfg["speed"][1],
                          min(1.0, self.meters / self.length)) * (1 + 0.04 * self.cycle)
            self.speed += (target - self.speed) * min(1.0, dt * 1.5)
            self.meters += self.speed * dt / PX_PER_M
            self.obs_gap -= self.speed * dt
            if self.obs_gap <= 0:
                self.spawn_obstacle()
            self.pick_timer -= dt
            if self.pick_timer <= 0:
                self.spawn_pickups()
                self.pick_timer = random.uniform(1.2, 2.4)
            if self.meters >= self.length:
                self.begin_warning()
        elif ph == "warn":
            self.speed += (120 - self.speed) * min(1.0, dt * 1.5)
            if self.phase_t >= 2.4:
                self.begin_boss()
        elif ph == "boss":
            self.speed = 0.0
            self.boss.update(dt)
            if self.boss.hp <= 0:
                self.boss_defeated()
        elif ph == "boss_dying":
            self.speed = 0.0
            self.boss.update(dt)
            for _ in range(3):
                r = self.boss.rect()
                self.particles.append(Particle(random.uniform(r.left, r.right), random.uniform(r.top, r.bottom),
                                               random.uniform(-120, 120), random.uniform(-260, -40),
                                               random.uniform(0.5, 1.0), random.choice([(255, 200, 80), (255, 90, 40), (250, 250, 250)]),
                                               random.randint(4, 9)))
            if self.phase_t > 2.2:
                self.end(True)
                return
        elif ph == "dying":
            self.speed += (0.0 - self.speed) * min(1.0, dt * 3)
            if self.phase_t > 1.4:
                self.end(False)
                return

        self.hero.update(dt, self.down_held)
        for ev in self.hero.events:
            self.app.sfx.play(ev)
        self.hero.events.clear()

        if self.shoot_held and ph in ("run", "warn", "boss") and self.hero.can_fire():
            self.hero.fire()
            self.bullets.append(Bullet(HERO_X + 40, GROUND_Y - 70, self.hero.dmg, self.accent))
            self.app.sfx.play("shoot")

        hero_pt = (HERO_X, self.hero.y - 70)
        for ob in self.obstacles:
            ob.update(dt, self.speed)
        for p in self.pickups:
            p.update(dt, self.speed, hero_pt, self.hero.magnet)
        for s in self.shots:
            s.update(dt)
        for b in self.bullets:
            b.update(dt)
        for p in self.particles:
            p.update(dt)
        for st in self.streaks:
            st[0] -= self.speed * dt * 1.4
            if st[0] < -120:
                st[0] = W + random.uniform(0, 200)
                st[1] = random.uniform(180, H)

        self.obstacles = [o for o in self.obstacles if o.alive]
        self.shots = [s for s in self.shots if s.alive]
        self.bullets = [b for b in self.bullets if b.alive]
        self.pickups = [p for p in self.pickups if p.alive]
        self.particles = [p for p in self.particles if p.life > 0]

        self.check_collisions()

    def spawn_obstacle(self):
        m = self.meters
        pool = ["crate", "spikes", "barrel"]
        if m > 60:
            pool.append("drone")
        if m > 120:
            pool.append("beam")
        kind = random.choice(pool)
        x0 = W + 40
        self.add_obstacle(kind, x0)
        if kind in ("crate", "spikes", "barrel") and m > 150 and random.random() < 0.3:
            # Два наземных препятствия подряд: прыжок и двойной прыжок
            self.add_obstacle(random.choice(["crate", "spikes", "barrel"]), x0 + 230)
        self.obs_gap = self.speed * random.uniform(0.9, 1.3) * (1 - 0.06 * min(self.cycle, 4))

    def add_obstacle(self, kind, x):
        self.obstacles.append(Obstacle(kind, x, self.accent))

    def spawn_pickups(self):
        row = random.choice([GROUND_Y - 30, GROUND_Y - 110, GROUND_Y - 160])
        x0 = W + 40
        n = random.randint(3, 5)
        for i in range(n):
            self.pickups.append(Pickup("scrap", x0 + i * 44, row))
        if self.hero.hp < self.hero.max_hp and random.random() < 0.3:
            self.pickups.append(Pickup("heart", x0 + n * 44, GROUND_Y - 30))

    def begin_warning(self):
        self.phase = "warn"
        self.phase_t = 0.0
        self.show_banner("ВНИМАНИЕ: БОСС!", 2.4, (255, 90, 70))
        self.app.sfx.play("warn")

    def begin_boss(self):
        self.phase = "boss"
        self.phase_t = 0.0
        self.obstacles = []
        self.pickups = []
        hp = round(self.cfg["boss_hp"] * (1 + 0.5 * self.cycle))
        self.boss = Boss(self.cfg, assets.boss(self.idx), hp, self.cycle, self.shots)
        self.show_banner(self.cfg["boss_name"], 2.6, (255, 120, 90))

    def boss_defeated(self):
        self.phase = "boss_dying"
        self.phase_t = 0.0
        self.boss_down = True
        self.boss.dying = True
        self.shots.clear()
        self.kills += 1
        self.run_xp += int(250 * (1 + 0.5 * self.cycle) * self.hero.xp_mult)
        self.score += 1000
        self.show_banner("БОСС ПОВЕРЖЕН!", 2.2, (140, 255, 170))
        self.app.sfx.play("boss_die")

    def hero_dies(self):
        self.phase = "dying"
        self.phase_t = 0.0
        self.explode(HERO_X, self.hero.y - 80, (255, 120, 60), n=30, speed=380)
        self.app.sfx.play("hit")

    def damage_hero(self):
        if self.hero.hurt():
            self.shake = 10.0
            self.app.sfx.play("hit")
            if self.hero.hp <= 0 and self.phase in ("run", "warn", "boss"):
                self.hero_dies()
            return True
        return False

    def explode(self, x, y, color, n=14, speed=260):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * speed
            self.particles.append(Particle(x, y, math.cos(a) * v, math.sin(a) * v - 80,
                                           random.uniform(0.4, 0.9), color, random.randint(3, 7)))

    def check_collisions(self):
        hb = self.hero.hitbox()
        live = self.phase in ("run", "warn", "boss")
        if live:
            for ob in self.obstacles:
                if not ob.spent and ob.rect().colliderect(hb):
                    if self.damage_hero():
                        ob.spent = True
                        if ob.breakable:
                            ob.alive = False
                            self.explode(ob.rect().centerx, ob.rect().centery, (150, 110, 70), n=10)
            for s in self.shots:
                if s.alive and s.rect().colliderect(hb):
                    s.alive = False
                    self.damage_hero()
            for p in self.pickups:
                if p.alive and p.rect().colliderect(hb.inflate(30, 30)):
                    p.alive = False
                    if p.kind == "scrap":
                        self.scrap += 1
                        self.score += 10
                        self.run_xp += int(6 * self.hero.xp_mult)
                        self.app.sfx.play("pickup")
                    else:
                        self.hero.hp = min(self.hero.max_hp, self.hero.hp + 1)
                        self.app.sfx.play("levelup")

        for b in self.bullets:
            if not b.alive:
                continue
            br = b.rect()
            hit_obstacle = False
            for ob in self.obstacles:
                if ob.alive and ob.rect().colliderect(br):
                    hit_obstacle = True
                    if ob.breakable:
                        ob.alive = False
                        self.kills += 1
                        self.score += 50
                        self.run_xp += int(8 * self.hero.xp_mult)
                        self.explode(ob.rect().centerx, ob.rect().centery, (150, 110, 70), n=10)
                        self.app.sfx.play("break")
                    break
            if hit_obstacle:
                b.alive = False
                continue
            for s in self.shots:
                if s.alive and s.destroyable and s.rect().colliderect(br):
                    s.alive = False
                    b.alive = False
                    self.explode(s.x, s.y, s.color, n=6, speed=160)
                    break
            if b.alive and self.boss and self.phase == "boss" and self.boss.rect().colliderect(br):
                b.alive = False
                self.explode(br.centerx, br.centery, (255, 220, 120), n=8)
                self.boss.hit(b.dmg)
                self.app.sfx.play("boss_hit")

    # ---------- отрисовка ----------

    def draw(self, s):
        c = self.canvas
        c.blit(self.bg, (0, 0))
        c.blit(self.shade, (0, 0))
        if self.speed > 30:
            for x, y, ln in self.streaks:
                pygame.draw.line(c, self.streak_color, (x, y), (x + ln * self.speed / 600, y), 2)
        for p in self.pickups:
            p.draw(c)
        for ob in self.obstacles:
            ob.draw(c)
        if self.boss:
            self.boss.draw(c)
        for sh in self.shots:
            sh.draw(c)
        self.hero.draw(c, self.img_run, self.img_jump, self.img_slide)
        for b in self.bullets:
            b.draw(c)
        for p in self.particles:
            p.draw(c)
        self.draw_hud(c)
        if self.phase == "dying":
            red = pygame.Surface((W, H), pygame.SRCALPHA)
            red.fill((160, 20, 20, min(120, int(self.phase_t * 200))))
            c.blit(red, (0, 0))
        if self.paused:
            layer = pygame.Surface((W, H), pygame.SRCALPHA)
            layer.fill((0, 0, 0, 160))
            c.blit(layer, (0, 0))
            text(c, "ПАУЗА", 80, (W // 2, 230), (255, 220, 160), anchor="center")
            self.pause_menu.draw(c)
        ox = oy = 0
        if self.shake > 0:
            ox = random.randint(-int(self.shake), int(self.shake))
            oy = random.randint(-int(self.shake), int(self.shake))
        s.blit(c, (ox, oy))

    def draw_hud(self, c):
        d = self.app.save.data
        # левая панель: здоровье и счёт
        panel(c, pygame.Rect(16, 14, 310, 104), alpha=150)
        if self.hero.max_hp <= 8:
            for i in range(self.hero.max_hp):
                heart(c, 38 + i * 32, 40, 24, (230, 60, 70) if i < self.hero.hp else (70, 60, 65))
        else:
            text(c, f"HP {max(0, self.hero.hp)} / {self.hero.max_hp}", 28, (30, 40), (240, 90, 90))
        text(c, f"Счёт: {self.score}", 26, (30, 62))
        text(c, f"Лом: {self.scrap}    Опыт: +{self.run_xp}", 24, (30, 92), (230, 220, 200))

        # полоса прогресса уровня
        bar = pygame.Rect(W // 2 - 300, 22, 600, 14)
        pygame.draw.rect(c, (30, 25, 30), bar, border_radius=6)
        ratio = min(1.0, self.meters / self.length)
        pygame.draw.rect(c, self.accent, (bar.x, bar.y, int(bar.w * ratio), bar.h), border_radius=6)
        pygame.draw.rect(c, (235, 225, 210), bar, 2, border_radius=6)
        pygame.draw.polygon(c, (255, 70, 60), [(bar.right + 4, bar.y - 4), (bar.right + 16, bar.centery),
                                               (bar.right + 4, bar.bottom + 4)])
        text(c, f"{self.cfg['name']}  ·  {int(self.meters)} / {self.length} м",
             24, (W // 2, 46), anchor="midtop")

        # правая панель: герой
        panel(c, pygame.Rect(W - 250, 14, 236, 70), alpha=150)
        text(c, f"Герой: ур. {d['hero_level']}", 28, (W - 232, 30))
        text(c, f"Очки навыков: {d['points']}", 22, (W - 232, 62), (255, 220, 160))

        # полоса здоровья босса
        if self.boss and self.phase in ("boss", "boss_dying"):
            bw = 560
            bx = W // 2 - bw // 2
            text(c, f"{self.cfg['boss_name']}", 28, (W // 2, 84), (255, 200, 170), anchor="midtop")
            pygame.draw.rect(c, (30, 15, 15), (bx, 116, bw, 14), border_radius=6)
            hp_ratio = max(0.0, self.boss.hp / self.boss.max_hp)
            pygame.draw.rect(c, (230, 60, 50), (bx, 116, int(bw * hp_ratio), 14), border_radius=6)
            pygame.draw.rect(c, (235, 225, 210), (bx, 116, bw, 14), 2, border_radius=6)

        if self.banner_t > 0:
            alpha = int(255 * min(1.0, self.banner_t / 0.4))
            text(c, self.banner, 66, (W // 2, 250), self.banner_color, anchor="center", alpha=alpha)
        if self.hint_t > 0:
            alpha = int(255 * min(1.0, self.hint_t / 2.0))
            text(c, "Пробел/W - прыжок (дважды - двойной)   S - скольжение под балкой и дроном   "
                    "X/Z - огонь   Esc - пауза", 22, (W // 2, H - 26), (240, 230, 220),
                 anchor="midbottom", alpha=alpha)

    # ---------- завершение ----------

    def end(self, cleared):
        self.done = True
        self.app.end_run(self, cleared)
