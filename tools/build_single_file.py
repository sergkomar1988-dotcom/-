"""Собирает игру в один самодостаточный файл rust_rush.py.

Внутрь файла вкладываются все модули game/*.py и картинки из game/assets/
(base64). Файлу нужен только Python 3.9+ и pygame; файлы рядом не нужны.

Использование:
  python tools/build_single_file.py [--assets ПАПКА] [--out ФАЙЛ]

По умолчанию: ассеты из game/assets, результат rust_rush.py в корне репозитория.
"""
import argparse
import base64
import os
import py_compile
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")
MODULES = ["config", "assets", "audio", "save", "entities", "ui", "play", "scenes", "main"]
ASSET_EXT = (".png", ".jpg", ".jpeg", ".webp")

TEMPLATE = '''#!/usr/bin/env python3
"""Ржавый Рывок - 2D раннер (одиночный файл).

Запуск:  python rust_rush.py      (нужен pygame: pip install pygame)
Сгенерировано tools/build_single_file.py из game/ - не редактируйте вручную.
"""
import base64
import importlib.abc
import importlib.util
import os
import sys

_FILE = os.path.abspath(__file__)
_SOURCES = __SOURCES__


class _Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname in _SOURCES:
            return importlib.util.spec_from_loader(fullname, _Loader(), origin=_FILE)
        return None


class _Loader(importlib.abc.Loader):
    def create_module(self, spec):
        return None  # стандартный модуль

    def exec_module(self, module):
        module.__file__ = _FILE
        code = compile(_SOURCES[module.__name__], _FILE, "exec")
        exec(code, module.__dict__)


sys.meta_path.insert(0, _Finder())

if __name__ == "__main__":
    import main as _game
    _game.main()
'''


def build(assets_dir, out_path):
    sources = {}
    for name in MODULES:
        with open(os.path.join(GAME, name + ".py"), encoding="utf-8") as f:
            sources[name] = f.read()
    assets = {}
    if os.path.isdir(assets_dir):
        for fname in sorted(os.listdir(assets_dir)):
            if fname.lower().endswith(ASSET_EXT):
                with open(os.path.join(assets_dir, fname), "rb") as f:
                    assets[fname] = base64.b64encode(f.read()).decode("ascii")
    # модуль с вшитым артом (пустой, если картинок нет)
    sources["_embedded_assets"] = "ASSETS = " + repr(assets) + "\n"

    body = TEMPLATE.replace("__SOURCES__", "{\n" + "".join(
        f"    {name!r}: {src!r},\n" for name, src in sources.items()) + "}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    py_compile.compile(out_path, doraise=True)
    return len(assets), os.path.getsize(out_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", default=os.path.join(GAME, "assets"))
    ap.add_argument("--out", default=os.path.join(ROOT, "rust_rush.py"))
    args = ap.parse_args()
    n, size = build(args.assets, args.out)
    print(f"Собрано: {args.out} ({size / 1024:.0f} КБ), картинок вшито: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
