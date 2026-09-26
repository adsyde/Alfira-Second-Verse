#!/usr/bin/env python3
"""Собирает мод из mod/ в dist/<name>_<version>.pak.

mod/ повторяет раскладку пака:
  mod/Mods/<Folder>/...        сценарий (Story), диалоги, локализация
  mod/Public/<Folder>/...      статы, шаблоны, флаги, теги
Вместо <Folder> в путях пишется литерально «_MOD_» — сборщик подставит
настоящее имя папки (name_uuid), чтобы оно было записано ровно в одном месте.

Шаги:
  1. копия mod/ → build/ с подстановкой _MOD_;
  2. *.lsf.lsx и *.lsx, у которых игра ждёт бинарный формат, → .lsf (Divine);
  3. meta.lsx из config/tools.json;
  4. проверки (нет XML-комментариев в локализации: игра падает при запуске);
  5. Divine create-package → dist/.

  python scripts/build_pak.py            # версия из config
  python scripts/build_pak.py --version 0.1.0
"""
import argparse
import re
import shutil
import sys

from common import config, divine, enable_utf8_stdout, resolve

enable_utf8_stdout()

# Каталоги, файлы в которых игра читает только в бинарном виде (.lsf).
# Остальные .lsx (meta.lsx, Story/*.txt, Localization/*.xml) кладутся как есть.
BINARY_DIRS = ("RootTemplates", "Flags", "Tags", "DialogsBinary", "Timeline", "Globals", "Levels", "Content")


def version64(text):
    major, minor, revision, build = ([int(p) for p in text.split(".")] + [0, 0, 0, 0])[:4]
    return (major << 55) | (minor << 47) | (revision << 31) | build


def meta_lsx(mod, folder, version):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<save>
    <version major="4" minor="8" revision="0" build="500"/>
    <region id="Config">
        <node id="root">
            <children>
                <node id="Conflicts"/>
                <node id="Dependencies"/>
                <node id="ModuleInfo">
                    <attribute id="Author" type="LSString" value="{mod["author"]}"/>
                    <attribute id="CharacterCreationLevelName" type="FixedString" value=""/>
                    <attribute id="Description" type="LSString" value="Alfira, the tiefling bard, as a full companion."/>
                    <attribute id="FileSize" type="uint64" value="0"/>
                    <attribute id="Folder" type="LSString" value="{folder}"/>
                    <attribute id="LobbyLevelName" type="FixedString" value=""/>
                    <attribute id="MD5" type="LSString" value=""/>
                    <attribute id="MenuLevelName" type="FixedString" value=""/>
                    <attribute id="Name" type="LSString" value="{mod["display_name"]}"/>
                    <attribute id="NumPlayers" type="uint8" value="4"/>
                    <attribute id="PhotoBooth" type="FixedString" value=""/>
                    <attribute id="PublishHandle" type="uint64" value="0"/>
                    <attribute id="StartupLevelName" type="FixedString" value=""/>
                    <attribute id="Tags" type="LSString" value=""/>
                    <attribute id="Type" type="FixedString" value="Add-on"/>
                    <attribute id="UUID" type="FixedString" value="{mod["uuid"]}"/>
                    <attribute id="Version64" type="int64" value="{version64(version)}"/>
                    <children>
                        <node id="PublishVersion">
                            <attribute id="Version64" type="int64" value="{version64(version)}"/>
                        </node>
                        <node id="Scripts"/>
                    </children>
                </node>
            </children>
        </node>
    </region>
</save>
'''


def main():
    cfg = config()
    mod = cfg["mod"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=mod["version"])
    args = ap.parse_args()

    folder = f'{mod["name"]}_{mod["uuid"]}'
    src = resolve(cfg["paths"]["mod_src"])
    build = resolve(cfg["paths"]["build"]) / "pak"
    dist = resolve(cfg["paths"]["dist"])
    if build.exists():
        shutil.rmtree(build)

    files = [p for p in src.rglob("*") if p.is_file() and p.name not in (".gitkeep", "README.md")]
    if not files:
        sys.exit("mod/ пуст — собирать нечего.")
    errors = []
    for p in files:
        rel = p.relative_to(src).as_posix().replace("_MOD_", folder)
        out = build / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        data = p.read_bytes()
        if p.suffix == ".xml" and "/Localization/" in rel and b"<!--" in data:
            errors.append(f"{rel}: XML-комментарий в локализации роняет игру при запуске")
        shutil.copyfile(p, out)
        if p.suffix == ".lsx" and any(f"/{d}/" in f"/{rel}" for d in BINARY_DIRS):
            lsf = out.with_suffix(".lsf") if not out.name.endswith(".lsf.lsx") else out.with_suffix("")
            divine("-a", "convert-resource", "-s", out, "-d", lsf)
            out.unlink()
    if errors:
        sys.exit("Сборка остановлена:\n  " + "\n  ".join(errors))

    meta = build / "Mods" / folder / "meta.lsx"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(meta_lsx(mod, folder, args.version), encoding="utf-8")

    stray = {p.relative_to(build).parts[1] for p in build.glob("*/*") if p.is_dir()} - {folder}
    if stray:
        sys.exit(f"В паке лишние папки модулей {sorted(stray)}: всё должно лежать в _MOD_ (иначе мод пропадёт из списка).")

    dist.mkdir(parents=True, exist_ok=True)
    pak = dist / f'{mod["name"]}.pak'
    divine("-a", "create-package", "-s", build, "-d", pak)
    print(f"{pak}  ({pak.stat().st_size // 1024} КБ, версия {args.version})")


if __name__ == "__main__":
    main()
