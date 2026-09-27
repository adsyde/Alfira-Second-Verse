#!/usr/bin/env python3
"""Проверяет сценарии Osiris мода компилятором LSLib вместе с ванильными — до запуска игры.

Ошибка в goal мода может сломать сборку сюжета при загрузке, поэтому перед build_pak:

  python scripts/check_story.py

Что делает:
  1. один раз строит game-data/_story/story_header.div из story.div.osi игры
     (нужен .NET SDK 8+: генератор scripts/osiheader собирается через dotnet run);
  2. раскладывает ванильные goals из game-data/ (хотфикс поверх Shared) и goals мода
     в build/story_check/ (литералы перечислений вида DEATHTYPE.DoT заменяются на
     (DEATHTYPE)0 — парсер LSLib их не знает);
  3. запускает StoryCompiler --check-only с модом и без него и печатает сообщения, которых нет без мода.
Ванильные goals дают около сотни «своих» ошибок (неполный заголовок): они не показываются.
"""
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from common import ROOT, config, divine, enable_utf8_stdout, game_data_dir, game_pak, resolve

enable_utf8_stdout()

VANILLA = ["Shared", "SharedDev", "Gustav", "GustavDev", "GustavX"]
# Порядок важен: хотфикс перекрывает одноимённые goals.
PAKS = ["Shared", "Gustav", "GustavX", "Patch8_HotFix9"]
ENUMS = ("DEATHTYPE|GRAVITYTYPE|LQUANT|TAGCATEGORY|ARMOURSET|CROWDBEHAVIOUR|SPLATTERTYPE|QUANTITY|"
         "TRADABLETYPE|EQUIPMENTSLOT|UNSHEATHSTATE|CRITICALITYTYPE|TRADEMODE|JOINBLOCKTYPE")
ENUM_RE = re.compile(r"\b(" + ENUMS + r")\.[A-Za-z_0-9]+\b")
META = '''<?xml version="1.0" encoding="UTF-8"?>
<save><version major="4" minor="0" revision="9" build="0"/><region id="Config"><node id="root"><children>
<node id="Dependencies"/><node id="ModuleInfo">
<attribute id="Folder" type="LSString" value="{0}"/><attribute id="Name" type="LSString" value="{0}"/>
<attribute id="UUID" type="FixedString" value="{0}"/><attribute id="Version64" type="int64" value="1"/>
</node></children></node></region></save>
'''


def header(cfg, lslib):
    out = game_data_dir(cfg) / "_story" / "story_header.div"
    if out.exists():
        return out
    osi_dir = out.parent / "osi"
    divine("-a", "extract-package", "-s", game_pak("Patch8_HotFix9.pak"), "-d", osi_dir,
           "-x", "Mods/GustavX/Story/story.div.osi")
    osi = osi_dir / "Mods" / "GustavX" / "Story" / "story.div.osi"
    r = subprocess.run(["dotnet", "run", "--project", ROOT / "scripts" / "osiheader", f"-p:LSLibDir={lslib}",
                        "--", osi, out], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"Не удалось построить заголовок:\n{r.stdout}\n{r.stderr}")
    return out


def copy_goal(src, dst):
    text = Path(src).read_text(encoding="utf-8", errors="replace")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(ENUM_RE.sub(lambda m: f"({m.group(1)})0", text), encoding="utf-8")


def main():
    cfg = config()
    mod = cfg["mod"]
    folder = f'{mod["name"]}_{mod["uuid"]}'
    lslib = Path(cfg["local"]["divine_path"]).parent
    hdr = header(cfg, lslib)

    data = resolve(cfg["paths"]["build"]) / "story_check" / "Data"
    if data.exists():
        shutil.rmtree(data)
    gd = game_data_dir(cfg)
    for pak in PAKS:
        for f in glob.glob(str(gd / pak / "Mods" / "*" / "Story" / "RawFiles" / "Goals" / "*.txt")):
            m = Path(f).parts[-5]
            if m in VANILLA:
                copy_goal(f, data / "Mods" / m / "Story" / "RawFiles" / "Goals" / Path(f).name)
    goals = sorted(resolve(cfg["paths"]["mod_src"]).glob("Mods/_MOD_/Story/RawFiles/Goals/*.txt"))
    if not goals:
        sys.exit("В mod/ нет goals — проверять нечего.")
    for f in goals:
        copy_goal(f, data / "Mods" / folder / "Story" / "RawFiles" / "Goals" / f.name)
    shutil.copyfile(hdr, data / "Mods" / "Shared" / "Story" / "RawFiles" / "story_header.div")
    for m in (data / "Mods").iterdir():
        (m / "meta.lsx").write_text(META.format(m.name), encoding="utf-8")

    def run(mods):
        cmd = [str(lslib / "StoryCompiler.exe"), "--game", "bg3", "--no-packages", "--check-only",
               "--game-data-path", str(data)]
        for m in mods:
            cmd += ["--mod", m]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        return [l.strip() for l in (r.stdout + r.stderr).splitlines() if "ERR" in l or "WARN" in l]

    # Часть сообщений не содержит имени файла (например, «Database "X(2)" is read, but is never written to»
    # для опечатки в имени запроса), поэтому «наши» — это всё, чего нет в прогоне одних ванильных goals.
    vanilla = set(run(VANILLA))
    ours = [l for l in dict.fromkeys(run(VANILLA + [folder])) if l not in vanilla]
    for l in ours:
        print(l)
    errors = [l for l in ours if "ERR" in l]
    print(f"{len(goals)} goal(s) мода: ошибок {len(errors)}, предупреждений {len(ours) - len(errors)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
