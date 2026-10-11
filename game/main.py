"""Ржавый Рывок - 2D раннер на pygame.

Запуск:  python main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame  # noqa: E402

from audio import Sounds  # noqa: E402
from config import FPS, TITLE, W, H  # noqa: E402
from save import SaveData  # noqa: E402
from scenes import MainMenu, Result  # noqa: E402


class App:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        self.fullscreen = False
        self.screen = self._mode()
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.save = SaveData.load()
        self.sfx = Sounds()
        self.running = True
        self.scene = MainMenu(self)

    def _mode(self):
        flags = pygame.SCALED | (pygame.FULLSCREEN if self.fullscreen else 0)
        return pygame.display.set_mode((W, H), flags)

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.screen = self._mode()

    # ----- переходы между сценами
    def set_scene(self, scene):
        self.scene = scene

    def go_menu(self):
        self.scene = MainMenu(self)

    def start_level(self, idx, cycle=0):
        from play import Play
        self.scene = Play(self, idx, cycle)

    def quit(self):
        self.running = False

    def finish_run(self, play, cleared):
        """Сохраняет итоги забега и прогресс героя, возвращает сводку для экрана."""
        d = self.save.data
        xp = int(play.run_xp)
        levels = self.save.add_xp(xp)
        meters = int(play.meters)
        d["best_m"] = max(d["best_m"], meters)
        d["runs"] += 1
        d["total_scrap"] += play.scrap
        if play.boss_down:
            d["bosses"] += 1
        if cleared:
            d["unlocked"] = max(d["unlocked"], min(4, play.idx + 2))
        self.save.write()
        if levels:
            self.sfx.play("levelup")
        return dict(meters=meters, kills=play.kills, scrap=play.scrap, xp=xp, levels=levels,
                    cleared=cleared, idx=play.idx, cycle=play.cycle, hero_level=d["hero_level"],
                    points=d["points"], best_m=d["best_m"])

    def end_run(self, play, cleared):
        summary = self.finish_run(play, cleared)
        self.scene = Result(self, summary, self.screen.copy())

    def abandon_run(self, play):
        self.finish_run(play, False)
        self.go_menu()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self.toggle_fullscreen()
                else:
                    self.scene.handle(e)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()


def main():
    App().run()
    pygame.quit()


if __name__ == "__main__":
    main()
