#!/usr/bin/env python3
"""Ставит собранный мод в игру: копирует пак в Mods и включает его в порядок загрузки.

BG3 Mod Manager Redux хранит порядок сам и при экспорте перезаписывает
modsettings.lsx, поэтому мод прописывается сразу в трёх местах:
  - %LOCALAPPDATA%/Larian Studios/Baldur's Gate 3/PlayerProfiles/Public/modsettings.lsx
  - <BG3MM>/Data/CurrentOrders/<профиль>.json
  - <BG3MM>/Orders/LastExported.json
Мод ставится в конец списка. Перед записью делаются .bak-копии.
Запускать при закрытых игре и менеджере модов.

  python scripts/install.py
  python scripts/install.py --uninstall    # убрать из порядка и удалить пак
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from common import config, enable_utf8_stdout, resolve

enable_utf8_stdout()

BG3 = Path(os.environ["LOCALAPPDATA"]) / "Larian Studios" / "Baldur's Gate 3"
MODS = BG3 / "Mods"
SETTINGS = BG3 / "PlayerProfiles" / "Public" / "modsettings.lsx"


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


def mm_order_files(cfg):
    mm = Path(cfg["local"].get("bg3mm_dir", "C:/Games/BG3MM"))
    files = list((mm / "Data" / "CurrentOrders").glob("*.json")) + [mm / "Orders" / "LastExported.json"]
    return [f for f in files if f.exists()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    args = ap.parse_args()
    cfg = config()
    mod = cfg["mod"]
    for exe in ("bg3", "Redux"):
        if running(exe):
            sys.exit(f"Запущен {exe} — закройте игру и менеджер модов и повторите.")

    folder = f'{mod["name"]}_{mod["uuid"]}'
    pak = resolve(cfg["paths"]["dist"]) / f'{mod["name"]}.pak'
    target = MODS / pak.name
    from build_pak import version64
    ver = version64(mod["version"])

    s = SETTINGS.read_text(encoding="utf-8")
    backup(SETTINGS)
    s = drop_node(s, mod["uuid"])
    if not args.uninstall:
        if not pak.exists():
            sys.exit(f"Нет {pak} — сначала python scripts/build_pak.py")
        shutil.copy2(pak, target)
        mods_block = s.index('<node id="Mods">')
        end = s.index("</children>", mods_block)
        end = s.rindex("\n", 0, end) + 1
        s = s[:end] + node(folder, mod["display_name"], mod["uuid"], ver) + s[end:]
    elif target.exists():
        target.unlink()
    SETTINGS.write_text(s, encoding="utf-8")

    for f in mm_order_files(cfg):
        backup(f)
        d = json.loads(f.read_text(encoding="utf-8-sig"))
        d["Order"] = [m for m in d["Order"] if m["UUID"] != mod["uuid"]]
        if not args.uninstall:
            d["Order"].append({"UUID": mod["uuid"], "Name": mod["display_name"]})
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    print(("Удалён" if args.uninstall else f"Установлен {pak.name}") + f": modsettings + {len(mm_order_files(cfg))} файла менеджера.")


if __name__ == "__main__":
    main()
