#!/usr/bin/env python3
"""Собирает мод из mod/ в dist/<name>_<version>.pak.

mod/ повторяет раскладку пака:
  mod/Mods/<Folder>/...        сценарий (Story), диалоги, локализация
  mod/Public/<Folder>/...      статы, шаблоны, флаги, теги
Вместо <Folder> в путях пишется литерально «_MOD_» — сборщик подставит
настоящее имя папки (name_uuid), чтобы оно было записано ровно в одном месте.

Шаги:
  0. генератор диалогов scripts/dialogs/build.py пишет в mod/ диалоги, таймлайны, сцены, банки,
     тексты, реакции и флаги (--no-generate — собрать из того, что уже лежит в mod/);
  1. копия mod/ → build/ с подстановкой _MOD_ в путях и в тексте ресурсов
     (SourceFile в банке диалогов ссылается на папку модуля);
  2. *.lsf.lsx и *.lsx, у которых игра ждёт бинарный формат, → .lsf (Divine); если рядом лежит
     X.lsf.lsx, то X.lsx — настоящий lsx пака (так игра хранит _Scene.lsx) и идёт как есть;
     диалог в формате редактора (Story/Dialogs/**/*.lsj) → Story/DialogsBinary/**/*.lsf;
  3. meta.lsx из config/tools.json;
  4. проверки: нет XML-комментариев в локализации (игра падает при запуске),
     у каждой реплики диалога есть текст во всех xml локализации (кроме озвученных реплик
     игры из build/dialogs/manifest.json — их тексты в локализации игры);
  5. Divine create-package → dist/.

  python scripts/build_pak.py            # публичная сборка: версия из config, реплики ✍️ — текстом
  python scripts/build_pak.py --version 0.1.0
  python scripts/build_pak.py --voice clone   # личная: + голос клона из voice-work/game/ (docs/VOICE.md)

Личная сборка (--voice clone) не публикуется: пак — build/personal/<name>_personal.pak, в dist/ не попадает.
Аудио в git не лежит: voice-work/game/voice.json (handle → файл, длина) и <handle>.wav 48 кГц моно.
Генератор ставит фазам этих реплик длину звука (Stager.voice_durations), после конвертации в пак кладутся
.wem Wwise PCM, банк VoiceMeta и заимствованный липсинк (scripts/voice/game_voice.py → write_takes).
"""
import argparse
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from common import config, divine, enable_utf8_stdout, resolve

enable_utf8_stdout()

# Каталоги, файлы в которых игра читает только в бинарном виде (.lsf).
# Остальные .lsx (meta.lsx, Story/*.txt, Localization/*.xml) кладутся как есть.
BINARY_DIRS = ("RootTemplates", "Flags", "Tags", "DialogsBinary", "Timeline", "Globals", "Levels", "Content")
# Текстовые ресурсы, в которых _MOD_ заменяется на имя папки модуля.
TEXT_SUFFIXES = (".lsx", ".lsj", ".xml")
HANDLE = re.compile(rb'handle="(h[0-9a-g]{36})"')
CONTENTUID = re.compile(rb'contentuid="(h[0-9a-g]{36})"')


def check_loca(build, folder, vanilla=frozenset()):
    """Каждый handle из DialogsBinary должен быть во всех языках локализации мода (кроме озвученных
    реплик игры: их текст и голос берутся из игры)."""
    loca = {}
    for x in (build / "Mods" / folder / "Localization").glob("*/*.xml"):
        loca.setdefault(x.parent.name, set()).update(CONTENTUID.findall(x.read_bytes()))
    errors = []
    for dlg in (build / "Mods" / folder / "Story" / "DialogsBinary").rglob("*.lsx"):
        for h in sorted(set(HANDLE.findall(dlg.read_bytes())) - {v.encode() for v in vanilla}):
            missing = [lang for lang, handles in loca.items() if h not in handles]
            if missing or not loca:
                errors.append(f"{dlg.name}: нет текста {h.decode()} в {missing or 'локализации'}")
    return errors


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


def pak_path(cfg, voice="none"):
    """Пак сборки: публичная — dist/<name>.pak, личная (голос клона) — build/personal/<name>_personal.pak."""
    name = cfg["mod"]["name"]
    if voice == "clone":
        return resolve(cfg["paths"]["build"]) / "personal" / f"{name}_personal.pak"
    return resolve(cfg["paths"]["dist"]) / f"{name}.pak"


def main():
    cfg = config()
    mod = cfg["mod"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=mod["version"])
    ap.add_argument("--no-generate", action="store_true", help="не запускать генератор диалогов")
    ap.add_argument("--voice", choices=["none", "clone"], default="none",
                    help="clone — личная сборка с голосом клона из voice-work/game/ (не публикуется)")
    args = ap.parse_args()

    takes = {}
    if args.voice == "clone":
        vdir = resolve(cfg["paths"]["voice_work"]) / "game"
        vj = vdir / "voice.json"
        if not vj.exists():
            sys.exit(f"Нет {vj}: сначала python scripts/voice/voice_line.py (docs/VOICE.md)")
        takes = {h: (vdir / t["file"], t["seconds"]) for h, t in json.loads(vj.read_text(encoding="utf-8")).items()}
        missing = [str(w) for w, _ in takes.values() if not w.exists()]
        if missing:
            sys.exit("Нет файлов голоса: " + ", ".join(missing))
    if not args.no_generate:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "dialogs"))
        import build as dialogs_build  # scripts/dialogs/build.py
        print("Генератор диалогов (scripts/dialogs/build.py):")
        dialogs_build.generate(voice={h: s for h, (_, s) in takes.items()})
    manifest = resolve(cfg["paths"]["build"]) / "dialogs" / "manifest.json"
    if not manifest.exists():
        sys.exit("Нет build/dialogs/manifest.json: запустите сборку без --no-generate.")
    man = json.loads(manifest.read_text(encoding="utf-8"))
    vanilla = set(man["vanilla_handles"])
    if set(man.get("voice_clone", [])) != set(takes):
        sys.exit("Таймлайны в mod/ собраны для другого набора голоса клона: запустите сборку без --no-generate.")

    folder = f'{mod["name"]}_{mod["uuid"]}'
    src = resolve(cfg["paths"]["mod_src"])
    build = resolve(cfg["paths"]["build"]) / "pak"
    if build.exists():
        shutil.rmtree(build)
    twins = set()   # X.lsx рядом с X.lsf.lsx: настоящий lsx (например, _Scene.lsx таймлайна)

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
        if p.suffix in TEXT_SUFFIXES:
            data = data.replace(b"_MOD_", folder.encode())
        out.write_bytes(data)
    # Конвертация — после копирования: проверка локализации читает текстовые .lsx диалогов.
    errors += check_loca(build, folder, vanilla)
    for out in build.rglob("*.lsf.lsx"):
        twins.add(out.with_name(out.name[:-len(".lsf.lsx")] + ".lsx"))
    for out in sorted(build.rglob("*.ls[xj]")):
        rel = out.relative_to(build).as_posix()
        if out in twins:
            continue
        if out.suffix == ".lsj" and "/Story/Dialogs/" in rel:
            lsf = build / rel.replace("/Story/Dialogs/", "/Story/DialogsBinary/", 1)
            lsf = lsf.with_suffix(".lsf")
        elif out.suffix == ".lsx" and any(f"/{d}/" in f"/{rel}" for d in BINARY_DIRS):
            lsf = out.with_suffix(".lsf") if not out.name.endswith(".lsf.lsx") else out.with_suffix("")
        else:
            continue
        lsf.parent.mkdir(parents=True, exist_ok=True)
        divine("-a", "convert-resource", "-s", out, "-d", lsf)
        out.unlink()
    if errors:
        sys.exit("Сборка остановлена:\n  " + "\n  ".join(errors))

    if takes:
        sys.path.insert(0, str(Path(__file__).resolve().parent / "voice"))
        from game_voice import write_takes  # scripts/voice/game_voice.py
        print("Голос клона (личная сборка):")
        for line in write_takes(build / "Mods" / folder / "Localization" / "English",
                                [(h, w) for h, (w, _) in sorted(takes.items())], resolve(cfg["paths"]["voice_work"])):
            print("  " + line)

    meta = build / "Mods" / folder / "meta.lsx"
    meta.parent.mkdir(parents=True, exist_ok=True)
    meta.write_text(meta_lsx(mod, folder, args.version), encoding="utf-8")

    stray = {p.relative_to(build).parts[1] for p in build.glob("*/*") if p.is_dir()} - {folder}
    if stray:
        sys.exit(f"В паке лишние папки модулей {sorted(stray)}: всё должно лежать в _MOD_ (иначе мод пропадёт из списка).")

    pak = pak_path(cfg, args.voice)
    pak.parent.mkdir(parents=True, exist_ok=True)
    # Divine молча пропускает файлы, если в пути есть папка на «.» (например, .claude/worktrees):
    # тогда пакуем из временной копии.
    staged = build
    if any(part.startswith(".") for part in build.parts):
        staged = Path(tempfile.mkdtemp(prefix="alfsv_pak_")) / "pak"
        shutil.copytree(build, staged)
    divine("-a", "create-package", "-s", staged, "-d", pak)
    if staged is not build:
        shutil.rmtree(staged.parent)
    listed = [l for l in divine("-a", "list-package", "-s", pak).splitlines() if "\t" in l]
    packed = sum(1 for p in build.rglob("*") if p.is_file())
    if len(listed) != packed:
        sys.exit(f"В паке {len(listed)} файлов из {packed}: Divine что-то пропустил.")
    for line in listed:
        print("  " + line.split("\t")[0])
    print(f"{pak}  ({pak.stat().st_size // 1024} КБ, {len(listed)} файлов, версия {args.version})")


if __name__ == "__main__":
    main()
