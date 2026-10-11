"""Сохранение прогресса героя (save.json рядом с игрой)."""
import copy
import json
import os

from config import SAVE_PATH, SKILLS, SKILL_MAX, xp_needed

DEFAULT = {
    "hero_level": 1,
    "xp": 0,
    "points": 0,
    "skills": {s["id"]: 0 for s in SKILLS},
    "unlocked": 1,       # сколько уровней открыто (1..4)
    "best_m": 0,
    "runs": 0,
    "bosses": 0,
    "total_scrap": 0,
}


class SaveData:
    def __init__(self, data):
        self.data = data

    @classmethod
    def load(cls):
        data = copy.deepcopy(DEFAULT)
        try:
            with open(SAVE_PATH, encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, ValueError):
            loaded = {}
        for key, default in DEFAULT.items():
            if key == "skills":
                continue
            value = loaded.get(key, default)
            data[key] = int(value) if isinstance(default, int) and isinstance(value, (int, float)) else default
        skills = loaded.get("skills", {})
        for s in SKILLS:
            value = skills.get(s["id"], 0)
            data["skills"][s["id"]] = min(SKILL_MAX, max(0, int(value))) if isinstance(value, (int, float)) else 0
        data["unlocked"] = min(4, max(1, data["unlocked"]))
        data["hero_level"] = max(1, data["hero_level"])
        return cls(data)

    def write(self):
        tmp = SAVE_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, SAVE_PATH)
        except OSError:
            pass  # нет прав на запись: игра продолжает работать без сохранения

    def add_xp(self, amount):
        """Начисляет опыт, возвращает количество полученных уровней героя."""
        d = self.data
        d["xp"] += amount
        gained = 0
        while d["xp"] >= xp_needed(d["hero_level"]):
            d["xp"] -= xp_needed(d["hero_level"])
            d["hero_level"] += 1
            d["points"] += 1
            gained += 1
        return gained

    def buy(self, skill_id):
        d = self.data
        if d["points"] <= 0 or d["skills"][skill_id] >= SKILL_MAX:
            return False
        d["points"] -= 1
        d["skills"][skill_id] += 1
        self.write()
        return True
