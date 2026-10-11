"""Автотесты без окна: python -m unittest discover -s game/tests -v

Проверяют, что меню и все 4 уровня с боссами работают без ошибок, что сохранение
и прокачка корректны. Скриншоты кладутся в SCREENSHOT_DIR (по умолчанию в tempdir).
"""
import os
import random
import sys
import tempfile
import unittest

GAME_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMP = tempfile.mkdtemp(prefix="rust_runner_test_")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ["RUST_RUNNER_SAVE"] = os.path.join(TMP, "save.json")
sys.path.insert(0, GAME_DIR)

import pygame  # noqa: E402

import main  # noqa: E402
from config import LEVELS, SKILLS, W, H  # noqa: E402
from entities import Boss  # noqa: E402
from play import Play  # noqa: E402
from scenes import MainMenu, LevelSelect, Upgrades, Result  # noqa: E402
import assets  # noqa: E402

SHOTS = os.environ.get("SCREENSHOT_DIR", os.path.join(TMP, "shots"))
os.makedirs(SHOTS, exist_ok=True)
DT = 1 / 60


def shot(surface, name):
    pygame.image.save(surface, os.path.join(SHOTS, name))


class GameTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        random.seed(1234)
        cls.app = main.App()

    def drive(self, scene, frames, invulnerable=True, jump_every=0.9, shoot=True, stop=None):
        """Крутит игровой цикл: случайные прыжки/скольжение, стрельба."""
        t = 0.0
        seen = set()
        for i in range(frames):
            if stop and stop():
                break
            if invulnerable:
                scene.hero.hp = scene.hero.max_hp = max(scene.hero.max_hp, 50)
            if shoot:
                scene.shoot_held = True
            scene.down_held = random.random() < 0.15
            t += DT
            if t >= jump_every:
                t = 0.0
                scene.hero.press_jump()
            scene.update(DT)
            seen.add(scene.phase)
            if i % 240 == 0:
                scene.draw(self.app.screen)
        return seen

    def test_menus_render(self):
        for scene, name in [(MainMenu(self.app), "menu.png"),
                            (LevelSelect(self.app), "levels.png"),
                            (Upgrades(self.app), "upgrades.png")]:
            scene.draw(self.app.screen)
            shot(self.app.screen, name)

    def test_full_level_with_boss_each(self):
        """Каждый из 4 уровней: бег -> предупреждение -> бой (пули попадают) -> победа."""
        from entities import Bullet
        for idx in range(len(LEVELS)):
            with self.subTest(level=idx):
                ended = []
                real_end = self.app.end_run
                self.app.end_run = lambda p, c: ended.append((c, p.boss_down, p.run_xp))
                try:
                    play = Play(self.app, idx, 0)
                    play.meters = play.length - 6  # почти до босса
                    phases = set()
                    for frame in range(60 * 150):
                        phases |= self.drive(play, 1)
                        if play.phase == "boss" and play.boss and play.boss.arrived and frame % 8 == 0:
                            r = play.boss.rect()
                            play.bullets.append(Bullet(r.centerx - 10, r.centery + 20, 6, play.accent))
                        if play.phase == "boss" and frame % 900 == 0:
                            shot(self.app.screen, f"level{idx + 1}_boss.png")
                        if ended:
                            break
                finally:
                    self.app.end_run = real_end
                self.assertIn("warn", phases)
                self.assertIn("boss", phases)
                self.assertIn("boss_dying", phases)
                self.assertEqual(len(ended), 1, "уровень должен завершиться ровно один раз")
                cleared, boss_down, run_xp = ended[0]
                self.assertTrue(cleared)
                self.assertTrue(boss_down)
                self.assertGreater(run_xp, 0)

    def test_all_boss_patterns_run(self):
        """Все атаки всех боссов выполняются и выпускают снаряды."""
        for idx, cfg in enumerate(LEVELS):
            with self.subTest(level=idx):
                out = []
                img = assets.boss(idx)
                boss = Boss(cfg, img, 10, 0, out)
                boss.arrived = True
                boss.wait = 0
                for name in cfg["patterns"]:
                    gen = getattr(boss, "p_" + name)()
                    for _ in gen:
                        pass
                self.assertGreater(len(out), 0)
                for s in out:
                    self.assertTrue(s.rect().width > 0)

    def test_death_ends_run(self):
        play = Play(self.app, 0, 0)
        ended = []
        play.app.end_run = lambda p, c: ended.append(c)
        play.hero.hp = 1
        play.hero.max_hp = 1
        from entities import Shot
        for _ in range(120):
            play.shots.append(Shot("bolt", 240, 640 - 120, -600, w=80, h=24))
            play.update(DT)
            if ended:
                break
        for _ in range(120):
            if ended:
                break
            play.update(DT)
        self.assertEqual(ended, [False])

    def test_save_and_progression(self):
        d = self.app.save.data
        before_points = d["points"]
        class FakePlay:
            run_xp = 500
            meters = 333.3
            scrap = 7
            kills = 2
            idx = 0
            cycle = 0
            boss_down = True
        summary = self.app.finish_run(FakePlay(), True)
        self.assertTrue(summary["cleared"])
        self.assertGreaterEqual(d["hero_level"], 2)
        self.assertGreater(d["points"], before_points)
        self.assertGreaterEqual(d["unlocked"], 2)
        self.assertTrue(os.path.exists(os.environ["RUST_RUNNER_SAVE"]))
        # прокачка: покупаем навык
        ok = self.app.save.buy(SKILLS[0]["id"])
        self.assertTrue(ok)
        self.assertEqual(d["skills"][SKILLS[0]["id"]], 1)

    def test_result_screen_draws(self):
        summary = dict(meters=100, kills=1, scrap=2, xp=30, levels=1, cleared=False, idx=1, cycle=0,
                       hero_level=2, points=1, best_m=100)
        r = Result(self.app, summary, self.app.screen.copy())
        r.draw(self.app.screen)
        shot(self.app.screen, "result_dead.png")

    def test_gameplay_screenshots(self):
        play = Play(self.app, 1, 0)
        play.hint_t = 0
        for _ in range(60 * 6):
            self.drive(play, 1, invulnerable=True)
        play.paused = False
        play.draw(self.app.screen)
        shot(self.app.screen, "gameplay_run.png")
        play.meters = play.length
        play.hero.hp = play.hero.max_hp = 3
        for _ in range(60 * 4):
            self.drive(play, 1)  # неуязвимость включена по умолчанию
        play.draw(self.app.screen)
        shot(self.app.screen, "gameplay_boss.png")


if __name__ == "__main__":
    unittest.main()
