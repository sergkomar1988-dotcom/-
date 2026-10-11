"""Загрузка арта. Если файла нет, рисуется временная процедурная графика,
поэтому игра запускается и без картинок (см. tools/prepare_assets.py)."""
import base64
import io
import os

import pygame

from config import ASSETS_DIR, W, H, HERO_H, GROUND_Y, LEVELS, BOSS_MAX_W

try:  # арт, вшитый в одиночный файл (см. tools/build_single_file.py)
    from _embedded_assets import ASSETS as _EMBEDDED
except ImportError:
    _EMBEDDED = {}

_cache = {}


def _load(name, alpha=True):
    if name in _EMBEDDED:
        try:
            raw = io.BytesIO(base64.b64decode(_EMBEDDED[name]))
            img = pygame.image.load(raw, name)
            return img.convert_alpha() if alpha else img.convert()
        except pygame.error:
            return None
    path = os.path.join(ASSETS_DIR, name)
    if not os.path.exists(path):
        return None
    try:
        img = pygame.image.load(path)
        return img.convert_alpha() if alpha else img.convert()
    except pygame.error:
        return None


def _cached(key, make):
    if key not in _cache:
        _cache[key] = make()
    return _cache[key]


def _fit(img, max_w, max_h):
    """Масштабирует картинку с сохранением пропорций, не больше max_w x max_h."""
    w, h = img.get_size()
    k = min(max_w / w, max_h / h)
    return pygame.transform.smoothscale(img, (max(1, round(w * k)), max(1, round(h * k))))


# ---------- фоны ----------

def _fallback_bg(idx):
    top, bottom = LEVELS[idx]["sky"]
    surf = pygame.Surface((W, H))
    for y in range(H):
        t = y / H
        col = [int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)]
        pygame.draw.line(surf, col, (0, y), (W, y))
    sun = LEVELS[idx]["sky"][1]
    pygame.draw.circle(surf, (255, 240, 200), (int(W * 0.72), 260), 90)
    pygame.draw.rect(surf, (25, 20, 22), (0, GROUND_Y - 10, W, H - GROUND_Y + 10))
    for x in range(0, W, 160):
        pygame.draw.rect(surf, sun, (x, GROUND_Y + 40, 80, 6))
    return surf


def background(idx):
    def make():
        img = _load(LEVELS[idx]["bg"], alpha=False)
        if img is None:
            img = _fallback_bg(idx)
        if img.get_size() != (W, H):
            img = pygame.transform.smoothscale(img, (W, H))
        return img
    return _cached(("bg", idx), make)


# ---------- герой ----------

def _fallback_hero(jump):
    surf = pygame.Surface((120, HERO_H), pygame.SRCALPHA)
    pygame.draw.rect(surf, (25, 25, 30), (30, 110, 26, 58))      # ноги
    pygame.draw.rect(surf, (25, 25, 30), (62, 110 if not jump else 96, 26, 58))
    pygame.draw.rect(surf, (80, 60, 40), (26, 150, 34, 16))       # ботинки
    pygame.draw.rect(surf, (80, 60, 40), (62, 150 if not jump else 136, 34, 16))
    pygame.draw.rect(surf, (80, 95, 60), (30, 60, 60, 60), border_radius=10)  # куртка
    pygame.draw.polygon(surf, (190, 40, 40), [(30, 62), (90, 62), (84, 74), (40, 74)])  # шарф
    pygame.draw.circle(surf, (150, 100, 80), (60, 40), 18)        # голова
    pygame.draw.ellipse(surf, (235, 235, 240), (42, 14, 36, 22))  # волосы
    pygame.draw.rect(surf, (120, 170, 190), (84, 70, 14, 40), border_radius=4)  # рука
    pygame.draw.circle(surf, (80, 220, 255), (66, 38), 4)         # киберглаз
    return surf


def hero_run():
    def make():
        img = _load("hero_run.png")
        if img is None:
            img = _fallback_hero(False)
        return _fit(img, 10000, HERO_H)
    return _cached("hero_run", make)


def hero_jump():
    def make():
        img = _load("hero_jump.png")
        if img is None:
            img = _fallback_hero(True)
        return _fit(img, 10000, HERO_H)
    return _cached("hero_jump", make)


def hero_slide():
    def make():
        base = hero_run()
        w, h = base.get_size()
        return pygame.transform.smoothscale(base, (int(w * 1.25), int(h * 0.5)))
    return _cached("hero_slide", make)


# ---------- боссы ----------

def _fallback_boss(idx):
    cfg = LEVELS[idx]
    h = cfg["boss_h"]
    w = int(h * 0.8)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    col = cfg["boss_color"]
    pygame.draw.rect(surf, col, (w * 0.15, h * 0.3, w * 0.7, h * 0.6), border_radius=24)
    pygame.draw.circle(surf, tuple(c // 2 for c in col), (w // 2, int(h * 0.18)), int(w * 0.24))
    pygame.draw.circle(surf, cfg["accent"], (int(w * 0.42), int(h * 0.18)), 7)
    pygame.draw.circle(surf, cfg["accent"], (int(w * 0.58), int(h * 0.18)), 7)
    pygame.draw.rect(surf, tuple(c // 2 for c in col), (w * 0.05, h * 0.55, w * 0.18, h * 0.4), border_radius=10)
    pygame.draw.rect(surf, tuple(c // 2 for c in col), (w * 0.77, h * 0.55, w * 0.18, h * 0.4), border_radius=10)
    return surf


def boss(idx):
    def make():
        img = _load(LEVELS[idx]["boss_img"])
        if img is None:
            img = _fallback_boss(idx)
        return _fit(img, BOSS_MAX_W, LEVELS[idx]["boss_h"])
    return _cached(("boss", idx), make)
