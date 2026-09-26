#!/usr/bin/env python3
"""Собирает датасет голоса Альфиры из файлов игры: wav + текст каждой реплики.

Источник:
  - VoiceMeta.pak → Mods/Gustav/Localization/English/Soundbanks/<guid без дефисов>.lsf:
    handle реплики → имя .wem, длительность, приоритет;
  - Voice.pak → сами .wem (Vorbis);
  - loca → английский текст реплики.
Результат в voice-work/dataset/ (в git не попадает — это записи актрисы):
  wav/<handle>.wav, metadata.csv (file|text|seconds|priority), stats.txt.

Для конвертации .wem → .wav нужен vgmstream-cli (путь в tools.local.json).
Без него скрипт только достанет .wem и составит список.

  python scripts/voice/extract_voice.py
  python scripts/voice/extract_voice.py --speaker <guid>   # чужой голос, для сравнения
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import config, divine, enable_utf8_stdout, game_data_dir, game_pak, resolve  # noqa: E402
from gamedb import ALFIRA, text  # noqa: E402

enable_utf8_stdout()

ENTRY_RE = re.compile(
    r'id="MapKey" type="FixedString" value="(h[0-9a-g]+)".*?'
    r'id="Length" type="float" value="([^"]+)".*?'
    r'id="Priority" type="FixedString" value="([^"]*)".*?'
    r'id="Source" type="FixedString" value="([^"]+)"', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", default=ALFIRA)
    args = ap.parse_args()
    cfg = config()
    key = args.speaker.replace("-", "")

    meta_dir = game_data_dir(cfg) / "Localization_VoiceMeta"
    lsf = next(meta_dir.rglob(f"{key}.lsf"), None)
    if lsf is None:
        divine("-a", "extract-package", "-s", game_pak("Localization/VoiceMeta.pak"), "-d", meta_dir, "-x", f"*{key}*")
        lsf = next(meta_dir.rglob(f"{key}.lsf"))
    lsx = lsf.with_suffix(".lsx")
    if not lsx.exists():
        divine("-a", "convert-resource", "-s", lsf, "-d", lsx)
    entries = ENTRY_RE.findall(lsx.read_text(encoding="utf-8"))
    print(f"реплик в VoiceMeta: {len(entries)}, {sum(float(e[1]) for e in entries) / 60:.1f} мин")

    work = resolve(cfg["paths"]["voice_work"]) / ("dataset" if args.speaker == ALFIRA else f"dataset_{key[:8]}")
    wem_dir = work / "wem"
    if not any(wem_dir.rglob("*.wem")):
        divine("-a", "extract-package", "-s", game_pak("Localization/Voice.pak"), "-d", wem_dir, "-x", f"*v{key}_*")
    wems = {p.name: p for p in wem_dir.rglob("*.wem")}

    vgm = cfg["local"].get("vgmstream_path", "")
    have_vgm = vgm and Path(vgm).exists()
    wav_dir = work / "wav"
    wav_dir.mkdir(parents=True, exist_ok=True)

    rows, missing, no_text = [], 0, 0
    for handle, length, prio, source in entries:
        if source not in wems:
            missing += 1
            continue
        line = TAG_RE.sub("", text(handle, "en")).strip()
        if not line:
            no_text += 1
        wav = wav_dir / f"{handle}.wav"
        if have_vgm and not wav.exists():
            subprocess.run([vgm, "-o", str(wav), str(wems[source])], capture_output=True, check=True)
        rows.append(f"{wav.name}|{line}|{float(length):.2f}|{prio}")

    (work / "metadata.csv").write_text("file|text|seconds|priority\n" + "\n".join(rows) + "\n", encoding="utf-8")
    stats = [
        f"реплик с аудио: {len(rows)}",
        f"нет .wem в Voice.pak: {missing}",
        f"нет текста в loca (крики, вздохи, пение без слов): {no_text}",
        f"wav: {'готовы' if have_vgm else 'не сделаны — нет vgmstream (tools.local.json → vgmstream_path)'}",
    ]
    (work / "stats.txt").write_text("\n".join(stats) + "\n", encoding="utf-8")
    print("\n".join(stats))
    print(f"→ {work}")


if __name__ == "__main__":
    main()
