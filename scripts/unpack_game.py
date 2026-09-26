#!/usr/bin/env python3
"""Достаёт нужные файлы из паков игры в game-data/<пак>/ (в git не попадает).

Наборы описаны в config/tools.json → unpack.sets. Файлы .loca сразу
переводятся в .xml, а у наборов с "convert": "lsx" бинарные .lsf — в .lsx, чтобы их можно было читать и искать grep'ом.

  python scripts/unpack_game.py goals dialogs-alfira
  python scripts/unpack_game.py --all
  python scripts/unpack_game.py --list      # какие наборы есть
"""
import argparse

from common import config, divine, enable_utf8_stdout, game_data_dir, game_pak

enable_utf8_stdout()


def main():
    cfg = config()
    sets = cfg["unpack"]["sets"]
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list or not (args.sets or args.all):
        for name, s in sets.items():
            print(f"{name:20} {', '.join(s['paks'])}  ←  {', '.join(s['expressions'])}")
        return

    out_root = game_data_dir(cfg)
    for name in (sets if args.all else args.sets):
        s = sets[name]
        for pak in s["paks"]:
            src = game_pak(pak)
            dest = out_root / pak.replace("/", "_").removesuffix(".pak")
            for expr in s["expressions"]:
                divine("-a", "extract-package", "-s", src, "-d", dest, "-x", expr)
            print(f"{name}: {pak} → {dest.relative_to(out_root.parent)}")
            if s.get("convert") == "lsx" and dest.exists():
                # Бинарные .lsf → читаемые .lsx рядом (Divine пакетом, по всей папке)
                divine("-a", "convert-resources", "-s", dest, "-d", dest, "-i", "lsf", "-o", "lsx")
        if name == "loca":
            for loca in out_root.rglob("*.loca"):
                xml = loca.with_suffix(".xml")
                if not xml.exists():
                    divine("-a", "convert-loca", "-s", loca, "-d", xml)
                    print(f"  loca → {xml.name}")


if __name__ == "__main__":
    main()
