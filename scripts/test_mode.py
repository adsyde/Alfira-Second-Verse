#!/usr/bin/env python3
"""Режим проверки мода в основном профиле игры — с возвратом всего как было.

Отдельного профиля в BG3 не создать (меню профилей Larian убрали), поэтому проверка
идёт в Public, но обратимо:

  on   — запоминает список модов (modsettings.lsx + файлы BG3 Mod Manager), копирует
         все сохранения (игра может удалить старые автосохранения во время проверки), выключает Alfira Joins The Party с переводом и патчем Redux,
         ставит наш мод (scripts/install.py --remove-conflicts);
  off  — возвращает список модов из копии; сохранения, появившиеся за время проверки,
         переносит в папку копии (не удаляет), а удалённые игрой — возвращает из копии.

Копии: %LOCALAPPDATA%/Larian Studios/Baldur's Gate 3/ALFSV_test/<время>/.
Игра и менеджер модов должны быть закрыты.

  python scripts/test_mode.py on
  python scripts/test_mode.py off
  python scripts/test_mode.py status
"""
import argparse
import json
import shutil
import sys
import time
from pathlib import Path

import install
from common import config, enable_utf8_stdout
from install import BG3, MAIN_PROFILE, PROFILES, mm_order_files, running

enable_utf8_stdout()

STORE = BG3 / "ALFSV_test"
STATE = STORE / "active.json"
SAVES = PROFILES / MAIN_PROFILE / "Savegames" / "Story"
SETTINGS = PROFILES / MAIN_PROFILE / "modsettings.lsx"


def closed():
    for exe in ("bg3", "Redux"):
        if running(exe):
            sys.exit(f"Запущен {exe} — закройте игру и менеджер модов и повторите.")


def saves():
    return sorted(p.name for p in SAVES.iterdir() if p.is_dir()) if SAVES.exists() else []


def on(cfg):
    if STATE.exists():
        sys.exit(f"Режим проверки уже включён ({json.loads(STATE.read_text(encoding='utf-8'))['dir']}).")
    snap = STORE / time.strftime("%Y%m%d-%H%M%S")
    snap.mkdir(parents=True)
    files = {"modsettings.lsx": str(SETTINGS)}
    shutil.copy2(SETTINGS, snap / "modsettings.lsx")
    for i, f in enumerate(mm_order_files(cfg)):
        name = f"bg3mm_{i}_{f.name}"
        shutil.copy2(f, snap / name)
        files[name] = str(f)
    state = {"dir": str(snap), "files": files, "saves": saves()}
    # Игра держит ограниченное число автосохранений и может удалить старые, пока идёт проверка
    print("Копирую сохранения…")
    shutil.copytree(SAVES, snap / "saves-backup")
    argv, sys.argv = sys.argv, ["install.py", "--remove-conflicts"]
    try:
        install.main()
    except SystemExit as e:
        if e.code:
            shutil.rmtree(snap)
            sys.exit(f"{e.code}\nУстановка не удалась — ничего не изменено.")
    finally:
        sys.argv = argv
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Режим проверки включён. Копии: {snap}")
    print("Загружайте сохранения, сделанные ДО установки Alfira Joins The Party "
          "(например, Леший AutoSave_51 от 26.09 14:40). Более поздние без него не загрузятся.")


def off():
    if not STATE.exists():
        sys.exit("Режим проверки не включён.")
    state = json.loads(STATE.read_text(encoding="utf-8"))
    snap = Path(state["dir"])
    for name, target in state["files"].items():
        shutil.copy2(snap / name, target)
    new = [s for s in saves() if s not in set(state["saves"])]
    if new:
        dest = snap / "test-saves"
        dest.mkdir(exist_ok=True)
        for s in new:
            shutil.move(str(SAVES / s), str(dest / s))
    lost = [s for s in state["saves"] if not (SAVES / s).exists()]
    for s in lost:
        shutil.copytree(snap / "saves-backup" / s, SAVES / s)
    if lost:
        print(f"Возвращены из копии сохранения, которые игра удалила за время проверки: {len(lost)}.")
    STATE.unlink()
    print(f"Список модов возвращён. Сохранений за время проверки: {len(new)}"
          + (f" — перенесены в {snap / 'test-saves'}" if new else "") + ".")
    print("Пак мода остаётся в Mods, но в списке загрузки его нет.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["on", "off", "status"])
    args = ap.parse_args()
    if args.action == "status":
        print("включён: " + json.loads(STATE.read_text(encoding="utf-8"))["dir"] if STATE.exists() else "выключен")
        return
    closed()
    on(config()) if args.action == "on" else off()


if __name__ == "__main__":
    main()
