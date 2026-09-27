#!/usr/bin/env python3
"""Ставит собранный мод в игру: копирует пак в Mods и включает его в порядок загрузки профиля.

Папка Mods у игры общая, а порядок загрузки и сохранения — свои у каждого профиля
(PlayerProfiles/<профиль>/). Основной профиль игры — Public. Меню профилей в BG3 нет,
поэтому для проверки в основном профиле есть scripts/test_mode.py (с возвратом всего как было).

BG3 Mod Manager Redux хранит порядок основного профиля сам и при экспорте
перезаписывает modsettings.lsx, поэтому для Public мод прописывается сразу в трёх местах:
  - PlayerProfiles/Public/modsettings.lsx
  - <BG3MM>/Data/CurrentOrders/<профиль>.json
  - <BG3MM>/Orders/LastExported.json
Для других профилей — только их modsettings.lsx (не нажимать «экспорт» в менеджере,
пока выбран такой профиль).

Мод ставится в конец списка — после Alfira Redone (оба правят её персонажа, см.
docs/ARCHITECTURE.md). Вместе с Alfira Joins The Party он не ставится: оба мода делают
Альфиру спутницей. Перед записью делаются .bak-копии. Игра и менеджер модов закрыты.

  python scripts/install.py                                  # основной профиль
  python scripts/install.py --profile Тест --clone-mods-from Public --remove-conflicts \\
                            --copy-save "Леший-402612611841__AutoSave_51"
  python scripts/install.py --uninstall [--profile Тест]     # убрать из порядка
  python scripts/install.py --voice clone                    # личная сборка с голосом клона вместо публичной

В Mods лежит только одна из двух сборок (AlfiraSecondVerse.pak или AlfiraSecondVerse_personal.pak):
установка одной убирает из Mods копию другой.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from common import config, enable_utf8_stdout, resolve

enable_utf8_stdout()

BG3 = Path(os.environ["LOCALAPPDATA"]) / "Larian Studios" / "Baldur's Gate 3"
MODS = BG3 / "Mods"
PROFILES = BG3 / "PlayerProfiles"
MAIN_PROFILE = "Public"

# Моды, которые делают то же самое: вместе с нашим их включать нельзя
CONFLICTS = {
    "3539eba9-6d77-c53d-1009-b3c77c9cd04c": "Alfira Joins The Party",
    "ee2dd6cc-7bb2-4972-bf69-dcb054367dbf": "Alfira Joins The Party RU",
    "4f0f54de-069f-426f-98d1-3c27aa1d7077": "Alfira Redux — патч для Alfira Joins The Party",
}


def running(name):
    return name.lower() in subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()


def backup(p):
    shutil.copy2(p, p.with_name(p.name + time.strftime(".%Y%m%d-%H%M%S.bak")))


def node(folder, name, uuid, ver):
    return f'''            <node id="ModuleShortDesc">
              <attribute id="Folder" type="LSString" value="{folder}" />
              <attribute id="MD5" type="LSString" value="" />
              <attribute id="Name" type="LSString" value="{name}" />
              <attribute id="PublishHandle" type="uint64" value="0" />
              <attribute id="UUID" type="guid" value="{uuid}" />
              <attribute id="Version64" type="int64" value="{ver}" />
            </node>
'''


def drop_node(text, uuid):
    i = text.find(f'value="{uuid}"')
    if i < 0:
        return text
    a = text.rindex('<node id="ModuleShortDesc">', 0, i)
    a = text.rindex("\n", 0, a) + 1
    b = text.index("</node>", i) + len("</node>\n")
    return text[:a] + text[b:]


def active_uuids(text):
    return set(re.findall(r'id="UUID" type="(?:guid|FixedString)" value="([^"]+)"', text))


def mm_order_files(cfg):
    mm = Path(cfg["local"].get("bg3mm_dir", "C:/Games/BG3MM"))
    files = list((mm / "Data" / "CurrentOrders").glob("*.json")) + [mm / "Orders" / "LastExported.json"]
    return [f for f in files if f.exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--profile", default=MAIN_PROFILE, help="папка профиля в PlayerProfiles (по умолчанию Public)")
    ap.add_argument("--clone-mods-from", metavar="ПРОФИЛЬ",
                    help="взять порядок модов из другого профиля (для нового тестового профиля)")
    ap.add_argument("--remove-conflicts", action="store_true",
                    help="выключить в профиле Alfira Joins The Party, его перевод и патч Redux")
    ap.add_argument("--copy-save", metavar="ПАПКА",
                    help="скопировать сохранение из Public/Savegames/Story в профиль")
    ap.add_argument("--voice", choices=["none", "clone"], default="none",
                    help="clone — личная сборка с голосом клона (build_pak.py --voice clone)")
    args = ap.parse_args()
    cfg = config()
    mod = cfg["mod"]
    for exe in ("bg3", "Redux"):
        if running(exe):
            sys.exit(f"Запущен {exe} — закройте игру и менеджер модов и повторите.")

    profile_dir = PROFILES / args.profile
    if not profile_dir.is_dir():
        sys.exit(f"Нет профиля {profile_dir} — создайте его в игре (главное меню → Профиль).")
    settings = profile_dir / "modsettings.lsx"
    main_profile = args.profile == MAIN_PROFILE

    if args.clone_mods_from:
        src = PROFILES / args.clone_mods_from / "modsettings.lsx"
        if settings.exists():
            backup(settings)
        shutil.copy2(src, settings)
        print(f"Порядок модов взят из профиля {args.clone_mods_from}.")

    folder = f'{mod["name"]}_{mod["uuid"]}'
    from build_pak import pak_path, version64
    pak = pak_path(cfg, args.voice)
    # в Mods — только одна из двух сборок: два пака одного модуля не ставим
    other = pak_path(cfg, "none" if args.voice == "clone" else "clone")
    ver = version64(mod["version"])

    s = settings.read_text(encoding="utf-8")
    found = {u: n for u, n in CONFLICTS.items() if u in active_uuids(s)}
    if found and not args.uninstall:
        if not args.remove_conflicts:
            sys.exit("В профиле включены моды, которые делают то же самое:\n  " + "\n  ".join(found.values())
                     + "\nВместе с нашим их включать нельзя. Запустите с --remove-conflicts, чтобы выключить их"
                       " в этом профиле (сохранения, где Альфира вступила через них, без них не работают).")
        for u in found:
            s = drop_node(s, u)
        print("Выключены в профиле: " + ", ".join(found.values()))

    if not args.clone_mods_from:
        backup(settings)
    s = drop_node(s, mod["uuid"])
    if not args.uninstall:
        if not pak.exists():
            sys.exit(f"Нет {pak} — сначала python scripts/build_pak.py" + (" --voice clone" if args.voice == "clone" else ""))
        shutil.copy2(pak, MODS / pak.name)
        if (MODS / other.name).exists():
            (MODS / other.name).unlink()    # копия другой сборки; сам пак остаётся в dist/ или build/personal/
            print(f"Убран из Mods {other.name} (другая сборка того же мода).")
        mods_block = s.index('<node id="Mods">')
        end = s.index("</children>", mods_block)
        end = s.rindex("\n", 0, end) + 1
        s = s[:end] + node(folder, mod["display_name"], mod["uuid"], ver) + s[end:]
    settings.write_text(s, encoding="utf-8")

    touched = 0
    if main_profile:
        for f in mm_order_files(cfg):
            backup(f)
            d = json.loads(f.read_text(encoding="utf-8-sig"))
            d["Order"] = [m for m in d["Order"] if m["UUID"] != mod["uuid"] and m["UUID"] not in found]
            if not args.uninstall:
                d["Order"].append({"UUID": mod["uuid"], "Name": mod["display_name"]})
            f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            touched += 1

    if args.copy_save:
        src = PROFILES / MAIN_PROFILE / "Savegames" / "Story" / args.copy_save
        dst = profile_dir / "Savegames" / "Story" / args.copy_save
        if not src.is_dir():
            sys.exit(f"Нет сохранения {src}")
        shutil.copytree(src, dst, dirs_exist_ok=True)
        print(f"Сохранение скопировано: {args.copy_save}")

    what = "Убран из порядка" if args.uninstall else f"Установлен {pak.name}"
    print(f"{what} — профиль {args.profile}: modsettings" + (f" + {touched} файла менеджера" if touched else ""))


if __name__ == "__main__":
    main()
