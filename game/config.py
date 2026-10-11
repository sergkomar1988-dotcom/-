"""Настройки игры: экран, физика, уровни, навыки героя."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(ROOT, "assets")
# Путь к сохранению можно переопределить (используется тестами).
SAVE_PATH = os.environ.get("RUST_RUNNER_SAVE", os.path.join(ROOT, "save.json"))

TITLE = "Ржавый Рывок"
W, H = 1280, 720
FPS = 60

# Геометрия и физика
GROUND_Y = 640            # линия бега (низ спрайта героя)
HERO_X = 240              # экранная позиция героя (бежит на месте, мир движется)
HERO_H = 170              # высота спрайта героя, px
HERO_HIT_W = 56
HERO_STAND_H = 140
HERO_SLIDE_H = 64
BASE_HP = 3
INVULN_TIME = 1.2
GRAVITY = 2600.0
JUMP_VEL = 980.0          # высота прыжка ~170 px
DOUBLE_JUMP_VEL = 860.0
JUMP_BUFFER = 0.12
SLIDE_MIN = 0.55
PX_PER_M = 100.0          # 100 px = 1 метр дистанции

# Высоты атак (центры снарядов)
HIGH_Y = GROUND_Y - 125   # "в голову": пройдёт над скольжением, попадёт по стоящему
LOW_Y = GROUND_Y - 22     # "по ногам": перепрыгивается

# Прокачка героя: 5 навыков, каждый до 5 рангов, очки дают уровни героя
SKILL_MAX = 5
SKILLS = [
    {"id": "hp", "name": "Броня", "desc": "+1 максимальное здоровье за ранг"},
    {"id": "dmg", "name": "Плазмоган", "desc": "+1 урон выстрела за ранг"},
    {"id": "rate", "name": "Перезарядка", "desc": "-8% задержки между выстрелами за ранг"},
    {"id": "magnet", "name": "Магнит", "desc": "+40 px радиус сбора лома за ранг"},
    {"id": "xp", "name": "Сборщик", "desc": "+20% опыта за ранг"},
]


def xp_needed(hero_level):
    """Сколько опыта нужно для перехода с hero_level на следующий уровень."""
    return 100 + 60 * (hero_level - 1)


# 4 уровня, у каждого свой фон, босс и темп. После 4-го уровня игра уходит в
# бесконечный режим: уровни повторяются, сложность растёт с каждым кругом.
LEVELS = [
    dict(name="Ржавая пустошь", bg="bg_lvl1.jpg", boss_img="boss_lvl1.png",
         boss_name="Ржавый Грейдер", length=900, boss_hp=36, boss_h=400,
         patterns=["saw", "bolt", "mix"], speed=(430, 680),
         accent=(255, 150, 60), boss_color=(150, 110, 80), sky=((60, 25, 15), (255, 150, 70))),
    dict(name="Токсичное болото", bg="bg_lvl2.jpg", boss_img="boss_lvl2.png",
         boss_name="Гнилой Хищник", length=1100, boss_hp=52, boss_h=380,
         patterns=["acid", "spit", "spore"], speed=(450, 720),
         accent=(150, 255, 60), boss_color=(60, 90, 40), sky=((10, 40, 10), (120, 200, 30))),
    dict(name="Мёртвый город", bg="bg_lvl3.jpg", boss_img="boss_lvl3.png",
         boss_name="Кибер-Жнец", length=1300, boss_hp=66, boss_h=420,
         patterns=["stream", "blade"], speed=(470, 760),
         accent=(220, 120, 255), boss_color=(60, 60, 80), sky=((30, 20, 60), (180, 90, 200))),
    dict(name="Раскалённый завод", bg="bg_lvl4.jpg", boss_img="boss_lvl4.png",
         boss_name="Железный Колосс", length=1500, boss_hp=85, boss_h=460,
         patterns=["stomp", "fist", "barrage"], speed=(490, 800),
         accent=(255, 90, 40), boss_color=(80, 70, 70), sky=((30, 10, 5), (230, 80, 20))),
]
BOSS_MAX_W = 520
