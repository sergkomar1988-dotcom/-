"""Звуки генерируются кодом (без аудиофайлов). Без звуковой карты игра работает тихо."""
import array
import math
import random

import pygame

RATE = 44100


def _gen(f0, f1, dur, wave="square", vol=0.2, noise=0.0, decay=2.0):
    n = int(RATE * dur)
    out = array.array("h")
    phase = 0.0
    tau = 2 * math.pi
    for i in range(n):
        p = i / n
        f = f0 + (f1 - f0) * p
        phase += tau * f / RATE
        if wave == "square":
            v = 1.0 if math.sin(phase) >= 0 else -1.0
        elif wave == "saw":
            v = 2.0 * ((phase / tau) % 1.0) - 1.0
        else:
            v = math.sin(phase)
        if noise:
            v = v * (1 - noise) + noise * random.uniform(-1, 1)
        s = int(max(-1.0, min(1.0, v * (1 - p) ** decay)) * vol * 32767)
        out.append(s)
        out.append(s)
    return pygame.mixer.Sound(buffer=out.tobytes())


SPECS = {
    "jump": (300, 900, 0.16, "square", 0.18, 0.0),
    "double": (500, 1200, 0.14, "square", 0.18, 0.0),
    "shoot": (1400, 300, 0.07, "saw", 0.10, 0.0),
    "hit": (200, 60, 0.35, "saw", 0.35, 0.4),
    "pickup": (900, 1400, 0.08, "square", 0.12, 0.0),
    "boss_hit": (300, 150, 0.12, "square", 0.18, 0.3),
    "break": (500, 80, 0.22, "square", 0.18, 0.5),
    "boss_die": (400, 40, 1.2, "saw", 0.28, 0.2),
    "warn": (800, 400, 0.6, "square", 0.16, 0.0),
    "levelup": (400, 1500, 0.5, "square", 0.18, 0.0),
    "select": (700, 900, 0.05, "square", 0.10, 0.0),
}


class Sounds:
    def __init__(self):
        self.snd = {}
        if pygame.mixer.get_init() is None:
            return
        for name, args in SPECS.items():
            try:
                self.snd[name] = _gen(*args)
            except (pygame.error, ValueError):
                pass

    def play(self, name):
        s = self.snd.get(name)
        if s is not None:
            s.play()
