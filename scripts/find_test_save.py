#!/usr/bin/env python3
"""Ищет сохранения, пригодные для проверки мода: читает сюжетные флаги прямо из сохранения.

Сохранение (.lsv) — архив. В нём StorySave.bin — состояние Osiris. LSLib StoryDecompiler
читает его, если дать расширение .osi, а в debug.log выписывает содержимое баз, в том
числе DB_GlobalFlag.

Для вербовки нужен акт 1: песня закончена (DEN_TieflingBard_State_FinishedSong),
тифлинги ещё в Роще (нет DEN_TieflingRefugees_State_LeftDen).

  python scripts/find_test_save.py                 # все сохранения акта 1 без Альфиры в отряде
  python scripts/find_test_save.py --prefix Леший  # только одно прохождение
  python scripts/find_test_save.py --save "Леший-402612611841__AutoSave_51"
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from common import enable_utf8_stdout

enable_utf8_stdout()

SAVES = Path(os.environ["LOCALAPPDATA"]) / "Larian Studios" / "Baldur's Gate 3" / "PlayerProfiles" / "Public" / "Savegames" / "Story"
DIVINE = r"C:\Tools\LSLib\Tools\Divine.exe"
DECOMPILER = r"C:\Tools\LSLib\Tools\StoryDecompiler.exe"
FLAGS = {
    "песня": "DEN_TieflingBard_State_FinishedSong",
    "бросила": "DEN_TieflingBard_State_ConvincedToQuit",
    "налёт отбит": "DEN_AttackOnDen_State_DenVictory",
    "тифлинги ушли": "DEN_TieflingRefugees_State_LeftDen",
}


def extract(lsv, name, dest):
    subprocess.run([DIVINE, "-g", "bg3", "-a", "extract-package", "-s", str(lsv), "-d", str(dest), "-x", name],
                   capture_output=True)
    return dest / name


def info(save_dir):
    lsv = next(save_dir.glob("*.lsv"), None)
    if not lsv:
        return None, None
    with tempfile.TemporaryDirectory() as t:
        f = extract(lsv, "SaveInfo.json", Path(t))
        return lsv, json.loads(f.read_text(encoding="utf-8-sig")) if f.exists() else None


def flags(lsv):
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        story = extract(lsv, "StorySave.bin", t)
        osi = story.rename(t / "story.osi")
        out = t / "out"
        out.mkdir()
        subprocess.run([DECOMPILER, "--input", str(osi), "--output", str(out), "--debug-log"], capture_output=True)
        log = (out / "debug.log").read_text(encoding="utf-8", errors="replace")
    i = log.find("DB_GlobalFlag(1)FLAG")
    block = log[i:log.find("\n#", i + 10)] if i >= 0 else ""
    return {k: f + "_" in block for k, f in FLAGS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", default="")
    ap.add_argument("--save")
    args = ap.parse_args()
    dirs = [SAVES / args.save] if args.save else sorted(
        (d for d in SAVES.iterdir() if d.is_dir() and d.name.startswith(args.prefix)),
        key=lambda d: max((p.stat().st_mtime for p in d.glob("*.lsv")), default=0))
    for d in dirs:
        lsv, si = info(d)
        if not si:
            continue
        party = [c.get("Origin") for c in si["Active Party"]["Characters"]]
        if not args.save and (si["Current Level"] != "WLD_Main_A" or "Alfira" in party):
            continue
        st = flags(lsv)
        good = st["песня"] and not st["тифлинги ушли"] and not st["бросила"]
        when = datetime.datetime.fromtimestamp(lsv.stat().st_mtime).strftime("%m-%d %H:%M")
        marks = " ".join(("+" if v else "-") + k for k, v in st.items())
        print(f"{'✅' if good else '  '} {when}  {d.name}  {marks}")


if __name__ == "__main__":
    main()
