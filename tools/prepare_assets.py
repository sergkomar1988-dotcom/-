"""Подготовка арта для игры.

Берёт исходные картинки и кладёт оптимизированные версии в game/assets/:
  bg_lvl1..4.png   -> фоны 1280x720 (JPG, обрезка по центру без искажений)
  boss_lvl1..4.png -> боссы (белый фон удаляется, PNG с прозрачностью)
  hero_run.png, hero_jump.png -> герой (белый фон удаляется, PNG)

Использование:
  python tools/prepare_assets.py [папка_с_исходниками]
По умолчанию папка исходников: ~/uploads
"""
import os
import sys

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "game", "assets")
DEFAULT_SRC = os.path.join(os.path.expanduser("~"), "uploads")
BG_SIZE = (1280, 720)
WHITE_THRESH = 40
MARK = (255, 0, 255)


def find_source(src, base):
    """Ищет файл с нужным базовым именем (.png/.jpg/.jpeg/.webp)."""
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = os.path.join(src, base + ext)
        if os.path.exists(p):
            return p
    return None


def cover(img, size):
    """Масштаб с заполнением области и обрезкой по центру."""
    w, h = img.size
    tw, th = size
    k = max(tw / w, th / h)
    img = img.resize((round(w * k), round(h * k)), Image.LANCZOS)
    x = (img.width - tw) // 2
    y = (img.height - th) // 2
    return img.crop((x, y, x + tw, y + th))


def is_near_white(px):
    r, g, b = px[:3]
    return min(r, g, b) >= 255 - WHITE_THRESH


def remove_white_background(img):
    """Заливает белый фон, связанный с краями картинки, и делает его прозрачным.
    Белые детали внутри персонажа (не связанные с краем) сохраняются."""
    rgb = img.convert("RGB")
    w, h = rgb.size
    border = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
             [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    for seed in border[::3]:
        if is_near_white(rgb.getpixel(seed)):
            ImageDraw.floodfill(rgb, seed, MARK, thresh=WHITE_THRESH)
    rgba = img.convert("RGBA")
    src, dst = rgb.load(), rgba.load()
    for y in range(h):
        for x in range(w):
            if src[x, y] == MARK:
                dst[x, y] = (0, 0, 0, 0)
    bbox = rgba.getchannel("A").getbbox()
    if bbox:
        pad = 4
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                min(w, bbox[2] + pad), min(h, bbox[3] + pad))
        rgba = rgba.crop(bbox)
    return rgba


def process_sprite(src_path, out_path):
    img = Image.open(src_path)
    rgba = remove_white_background(img)
    rgba.save(out_path, optimize=True)
    return rgba.size


def process_bg(src_path, out_path):
    img = Image.open(src_path).convert("RGB")
    cover(img, BG_SIZE).save(out_path, quality=88, optimize=True)
    return BG_SIZE


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SRC
    if not os.path.isdir(src):
        print(f"Папка не найдена: {src}")
        print("Положите картинки в эту папку или передайте путь аргументом.")
        return 1
    os.makedirs(OUT, exist_ok=True)
    done = 0
    jobs = []
    for i in range(1, 5):
        jobs.append((f"bg_lvl{i}", f"bg_lvl{i}.jpg", process_bg))
        jobs.append((f"boss_lvl{i}", f"boss_lvl{i}.png", process_sprite))
    jobs.append(("hero_run", "hero_run.png", process_sprite))
    jobs.append(("hero_jump", "hero_jump.png", process_sprite))
    for base, out_name, fn in jobs:
        found = find_source(src, base)
        if not found:
            print(f"  пропущено (нет файла): {base}")
            continue
        size = fn(found, os.path.join(OUT, out_name))
        print(f"  {os.path.basename(found)} -> game/assets/{out_name} {size}")
        done += 1
    print(f"Готово: {done} из {len(jobs)} файлов.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
