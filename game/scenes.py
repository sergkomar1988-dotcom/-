"""Меню: главное, выбор уровня, прокачка героя, итоги забега."""
import math

import pygame

import assets
from config import W, H, LEVELS, SKILLS, SKILL_MAX, xp_needed
from ui import text, panel, dim, Menu


class Scene:
    def handle(self, e):
        pass

    def update(self, dt):
        pass


class MainMenu(Scene):
    def __init__(self, app):
        self.app = app
        self.t = 0.0
        self.bg = assets.background(0)
        self.hero = assets.hero_run()
        self.menu = Menu([
            ("Играть", self.play),
            ("Выбор уровня", self.levels),
            ("Прокачка героя", self.upgrades),
            ("Выход", app.quit),
        ], top=330)

    def play(self):
        self.app.sfx.play("select")
        self.app.start_level(self.app.save.data["unlocked"] - 1, 0)

    def levels(self):
        self.app.set_scene(LevelSelect(self.app))

    def upgrades(self):
        self.app.set_scene(Upgrades(self.app))

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            return
        self.menu.handle(e)

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        dim(s, 110)
        text(s, "РЖАВЫЙ РЫВОК", 110, (W // 2, 120), (255, 170, 80), anchor="center")
        text(s, "Бесконечный бег · 4 уровня · боссы · прокачка героя", 30, (W // 2, 200),
             (235, 225, 210), anchor="center")
        d = self.app.save.data
        text(s, f"Герой: ур. {d['hero_level']}   Очки навыков: {d['points']}   "
                f"Рекорд: {d['best_m']} м   Уровней открыто: {d['unlocked']}/4",
             24, (W // 2, 250), (230, 220, 200), anchor="center")
        self.menu.draw(s)
        bob = abs(math.sin(self.t * 2)) * 6
        s.blit(self.hero, self.hero.get_rect(midbottom=(W - 220, H - 40 - bob)))
        text(s, "Управление: Пробел - прыжок, S - скольжение, X/Z - огонь, Esc - пауза",
             22, (W // 2, H - 24), (200, 190, 180), anchor="center")


class LevelSelect(Scene):
    def __init__(self, app):
        self.app = app
        items = []
        for i, cfg in enumerate(LEVELS):
            items.append((f"{i + 1}. {cfg['name']}  ·  босс: {cfg['boss_name']}", self.make(i)))
        items.append(("Назад", self.back))
        self.menu = Menu(items, top=250, spacing=72, width=700)
        self.bg = assets.background(0)

    def make(self, i):
        def go():
            if i < self.app.save.data["unlocked"]:
                self.app.start_level(i, 0)
        return go

    def back(self):
        self.app.go_menu()

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.back()
            return
        self.menu.handle(e)

    def draw(self, s):
        s.blit(self.bg, (0, 0))
        dim(s, 140)
        text(s, "ВЫБОР УРОВНЯ", 84, (W // 2, 110), (255, 170, 80), anchor="center")
        unlocked = self.app.save.data["unlocked"]
        for i in range(len(LEVELS)):
            if i >= unlocked:
                r = self.menu.rect(i)
                panel(s, r, alpha=200, border=(90, 90, 90))
                text(s, "закрыт: победите босса предыдущего уровня", 22, r.center, (150, 150, 150),
                     anchor="center", shadow=False)
        self.menu.draw(s)
        text(s, "Enter - выбрать, Esc - назад", 22, (W // 2, H - 30), (200, 190, 180), anchor="center")


class Upgrades(Scene):
    def __init__(self, app):
        self.app = app
        self.sel = 0
        self.bg = assets.background(0)
        self.back_rect = pygame.Rect(W // 2 - 150, H - 84, 300, 54)

    def row(self, i):
        return pygame.Rect(W // 2 - 430, 250 + i * 76, 860, 62)

    def back(self):
        self.app.go_menu()

    def buy(self, i):
        if i >= len(SKILLS):
            self.back()
            return
        ok = self.app.save.buy(SKILLS[i]["id"])
        self.app.sfx.play("pickup" if ok else "select")

    def handle(self, e):
        n = len(SKILLS)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.back()
            elif e.key == pygame.K_UP:
                self.sel = (self.sel - 1) % (n + 1)
            elif e.key == pygame.K_DOWN:
                self.sel = (self.sel + 1) % (n + 1)
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.buy(self.sel)
        elif e.type == pygame.MOUSEMOTION:
            for i in range(n):
                if self.row(i).collidepoint(e.pos):
                    self.sel = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i in range(n):
                if self.row(i).collidepoint(e.pos):
                    self.sel = i
                    self.buy(i)
                    return
            if self.back_rect.collidepoint(e.pos):
                self.back()

    def draw(self, s):
        d = self.app.save.data
        s.blit(self.bg, (0, 0))
        dim(s, 150)
        text(s, "ПРОКАЧКА ГЕРОЯ", 80, (W // 2, 70), (255, 170, 80), anchor="center")
        need = xp_needed(d["hero_level"])
        text(s, f"Уровень героя: {d['hero_level']}     Опыт: {d['xp']} / {need}     "
                f"Очки навыков: {d['points']}", 28, (W // 2, 160), (240, 230, 210), anchor="center")
        bar = pygame.Rect(W // 2 - 300, 196, 600, 12)
        pygame.draw.rect(s, (40, 35, 40), bar, border_radius=6)
        pygame.draw.rect(s, (255, 150, 60), (bar.x, bar.y, int(bar.w * d["xp"] / need), bar.h), border_radius=6)

        for i, sk in enumerate(SKILLS):
            r = self.row(i)
            rank = d["skills"][sk["id"]]
            sel = i == self.sel
            panel(s, r, alpha=200 if sel else 150, border=(255, 220, 160) if sel else (110, 90, 70))
            text(s, sk["name"], 30, (r.x + 22, r.y + 9), (255, 230, 180) if sel else (235, 225, 210))
            text(s, sk["desc"], 20, (r.x + 22, r.y + 40), (200, 190, 180), shadow=False)
            for k in range(SKILL_MAX):
                pip = pygame.Rect(r.right - 160 + k * 30, r.centery - 9, 22, 18)
                pygame.draw.rect(s, (255, 150, 60) if k < rank else (60, 55, 60), pip, border_radius=4)
                pygame.draw.rect(s, (30, 25, 30), pip, 1, border_radius=4)
            status = "MAX" if rank >= SKILL_MAX else ("Enter: +1" if d["points"] > 0 else "нет очков")
            text(s, status, 20, (r.right - 176, r.centery), (200, 190, 180), anchor="midright", shadow=False)

        sel = self.sel == len(SKILLS)
        panel(s, self.back_rect, alpha=220, border=(255, 220, 160) if sel else (110, 90, 70))
        text(s, "Назад", 34, self.back_rect.center, (255, 230, 180), anchor="center")


class Result(Scene):
    """Итоги забега. summary - dict из App.finish_run."""

    def __init__(self, app, summary, snapshot):
        self.app = app
        self.s = summary
        self.snap = snapshot
        self.t = 0.0
        if summary["cleared"]:
            if summary["idx"] < len(LEVELS) - 1:
                nxt = ("Дальше: " + LEVELS[summary["idx"] + 1]["name"], self.next_level)
            else:
                nxt = ("Следующий круг (бесконечный бег)", self.next_level)
            items = [nxt, ("В меню", app.go_menu)]
        else:
            items = [("Заново", self.retry), ("В меню", app.go_menu)]
        self.menu = Menu(items, top=500, width=520)

    def next_level(self):
        idx, cycle = self.s["idx"], self.s["cycle"]
        if idx < len(LEVELS) - 1:
            self.app.start_level(idx + 1, cycle)
        else:
            self.app.start_level(0, cycle + 1)

    def retry(self):
        self.app.start_level(self.s["idx"], self.s["cycle"])

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
            self.retry()
            return
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.app.go_menu()
            return
        self.menu.handle(e)

    def update(self, dt):
        self.t += dt

    def draw(self, s):
        s.blit(self.snap, (0, 0))
        dim(s, 170)
        s_ = self.s
        title = "УРОВЕНЬ ПРОЙДЕН!" if s_["cleared"] else "ТЫ ПАЛ В БОЮ"
        col = (140, 255, 170) if s_["cleared"] else (255, 110, 90)
        text(s, title, 84, (W // 2, 110), col, anchor="center")
        lines = [
            f"Пройдено: {s_['meters']} м   ·   уровень {s_['idx'] + 1}" + (f"   ·   круг {s_['cycle'] + 1}" if s_['cycle'] else ""),
            f"Уничтожено: {s_['kills']}   ·   лом: {s_['scrap']}   ·   опыт: +{s_['xp']}",
            f"Уровень героя: {s_['hero_level']}" + (f"   (повышен на {s_['levels']})" if s_['levels'] else ""),
            f"Очки навыков: {s_['points']}   ·   рекорд: {s_['best_m']} м",
        ]
        for i, ln in enumerate(lines):
            text(s, ln, 30, (W // 2, 220 + i * 52), (240, 230, 210), anchor="center")
        self.menu.draw(s)
