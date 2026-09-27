#!/usr/bin/env python3
"""Конвейер «новая реплика с голосом → файлы для пака»: write_takes() вызывает build_pak.py --voice clone
(личная сборка), CLI ниже — прототип для одного handle в voice-work/pipeline/proto/.

Для handle новой реплики и готового .wav (48 кГц, моно, 16 бит — так выдают voice_act1.py pick и
tts/normalize.py) пишет то, что по данным игры нужно движку для озвученной реплики (docs/VOICE.md,
«Конвейер в игру»); <id> — uuid говорящего без дефисов, свой банк на каждого говорящего:

  Mods/_MOD_/Localization/English/Soundbanks/v<id>_<handle>.wem          — звук: Wwise RIFF, кодек PCM
  Mods/_MOD_/Localization/English/Soundbanks/<id>.lsf                    — VoiceMeta: handle → файл, длина, приоритет
  Mods/_MOD_/Localization/English/Animation/FX_v<id>_<handle>.ffxanim    — липсинк FaceFX (заимствован)
  Mods/_MOD_/Localization/English/Animation/MC_v<id>_<handle>.gr2        — жесты мокапа (заимствованы)
  Mods/_MOD_/Localization/English/Animation/FaceFXActors/<uuid>.ffxactor/.ffxbones — актёр FaceFX говорящего

Проверено в игре на пробной реплике (Альфира): .wem Wwise PCM 48 кГц моно звучит, рот двигается.
  * .wem — Wwise PCM (fmt 0xFFFE). Ванильные — Wwise Vorbis, кодировщика Vorbis без Wwise нет.
  * Липсинк FaceFX без инструментов FaceFX не сделать: .ffxanim — скомпилированные данные. Берётся
    ванильный .ffxanim того же говорящего близкой длины (pick_donor) — рот двигается, но не по словам.
    У говорящего без FaceFX в English_Animations.pak — без липсинка.
  * Папка _MOD_ — как в mod/, build_pak подставит <name>_<uuid>. Клон в mod/ (git) не кладётся.

  python scripts/voice/game_voice.py --handle hafab7af6g9ceag5788g87a8g3227f8639bd5 --wav <file.wav> [--speaker <uuid>]
"""
import argparse
import csv
import re
import shutil
import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import config, divine, enable_utf8_stdout, game_data_dir, game_pak, resolve  # noqa: E402
from gamedb import ALFIRA  # noqa: E402

enable_utf8_stdout()

SR = 48000
KEY = ALFIRA.replace("-", "")
PRIORITY = "P1_StoryDialog"     # сюжетный диалог (у неё в VoiceMeta 437 из 548); AD над головой — P4_RepeatingDialog_AD
# говорящие с голосом клона в «Разговорах» акта 1 (docs/VOICE.md, «Голоса NPC»); прочие — по uuid
SPEAKER_NAMES = {ALFIRA: "Альфира", "02025646-347a-4235-aef7-e46b7c94b435": "Ашарак",
                 "23129d6c-8d39-4a4c-a4f6-cfc6637b597c": "Лакрисса", "e2ad06ec-8034-479a-9f69-b86faea6dc79": "Даммон"}


def write_wem_pcm(wav_path, wem_path):
    """RIFF WAVE с заголовком Wwise PCM: fmt 0xFFFE, 0x18 байт, маска каналов FC (как у её .wem)."""
    with wave.open(str(wav_path)) as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (SR, 1, 2):
            sys.exit(f"{wav_path}: нужен 48 кГц, моно, 16 бит (tts/normalize.py), а тут "
                     f"{w.getframerate()} Гц, {w.getnchannels()} кан., {8 * w.getsampwidth()} бит")
        frames = w.getnframes()
        pcm = w.readframes(frames)
    fmt = struct.pack("<HHIIHHHHI", 0xFFFE, 1, SR, SR * 2, 2, 16, 6, 16, 0x4)
    body = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt + b"data" + struct.pack("<I", len(pcm)) + pcm
    wem_path.parent.mkdir(parents=True, exist_ok=True)
    wem_path.write_bytes(b"RIFF" + struct.pack("<I", len(body)) + body)
    return frames / SR


def voicemeta_lsx(speaker, entries):
    """entries: [(handle, source, length, priority)] → текст .lsx банка голоса speaker (uuid с дефисами).

    Структура — как у VoiceMeta игры: один VoiceSpeakerMetaData на банк, MapKey — uuid говорящего с дефисами,
    имя файла банка — тот же uuid без дефисов (VoiceMeta.pak: 4a405fba…, 02025646…, 23129d6c…, e2ad06ec…)."""
    items = []
    for handle, source, length, priority in sorted(entries):
        items.append(f"""								<node id="VoiceTextMetaData">
									<attribute id="MapKey" type="FixedString" value="{handle}" />
									<children>
										<node id="MapValue">
											<attribute id="Codec" type="FixedString" value="PCM" />
											<attribute id="Length" type="float" value="{length:.7g}" />
											<attribute id="Priority" type="FixedString" value="{priority}" />
											<attribute id="Source" type="FixedString" value="{source}" />
										</node>
									</children>
								</node>""")
    body = "\n".join(items)
    return f"""<?xml version="1.0" encoding="utf-8"?>
<save>
	<version major="3" minor="2" revision="0" build="0" lslib_meta="v1,bswap_guids" />
	<region id="VoiceMetaData">
		<node id="VoiceMetaData">
			<children>
				<node id="VoiceSpeakerMetaData">
					<attribute id="MapKey" type="FixedString" value="{speaker}" />
					<children>
						<node id="MapValue">
							<children>
{body}
							</children>
						</node>
					</children>
				</node>
			</children>
		</node>
	</region>
</save>
"""


ENTRY_RE = re.compile(r'id="MapKey" type="FixedString" value="(h[0-9a-g]+)".*?id="Length" type="float" value="([^"]+)"'
                      r'.*?id="Source" type="FixedString" value="([^"]+)"', re.S)


def vanilla_bank(speaker):
    """Банк VoiceMeta говорящего в игре: [(handle, длина, файл .wem)]; нет банка — []."""
    key = speaker.replace("-", "")
    meta_dir = game_data_dir() / "Localization_VoiceMeta"
    lsf = next(meta_dir.rglob(f"{key}.lsf"), None) if meta_dir.exists() else None
    if lsf is None:
        divine("-a", "extract-package", "-s", game_pak("Localization/VoiceMeta.pak"), "-d", meta_dir, "-x", f"*{key}*")
        lsf = next(meta_dir.rglob(f"{key}.lsf"), None)
        if lsf is None:
            return []
    lsx = lsf.with_suffix(".lsx")
    if not lsx.exists():
        divine("-a", "convert-resource", "-s", lsf, "-d", lsx)
    return [(h, float(n), src) for h, n, src in ENTRY_RE.findall(lsx.read_text(encoding="utf-8-sig"))]


def speaker_anims(vw, speaker):
    """FaceFX говорящего из English_Animations.pak (кэш voice-work/pipeline/vanilla_anim, один раз на говорящего):
    {имя файла: путь} для FX_v<id>_*.ffxanim, MC_v<id>_*.gr2 и FaceFXActors/<uuid>.ffxactor/.ffxbones."""
    key = speaker.replace("-", "")
    dest = vw / "pipeline" / "vanilla_anim"
    mark = dest / f".{key}.extracted"
    if not mark.exists():
        pak = game_pak("Localization/English_Animations.pak")
        divine("-a", "extract-package", "-s", pak, "-d", dest, "-x", f"*_v{key}_*")
        divine("-a", "extract-package", "-s", pak, "-d", dest, "-x", f"*FaceFXActors/{speaker}.*")
        mark.parent.mkdir(parents=True, exist_ok=True)
        mark.write_text("", encoding="utf-8")
    return {p.name: p for p in dest.rglob("*")
            if p.is_file() and (f"_v{key}_" in p.name or p.name.startswith(speaker + "."))}


def donors(vw, speaker, anims):
    """Реплики говорящего в игре, годные в доноры липсинка: [(handle, длина, основа имени .wem)] с FX_ в игре.

    FX_/MC_ названы по файлу .wem (Source), а не по handle: у Даммона 87 handle делят чужие .wem. Пение,
    «Разговор с мёртвыми» и рыдание (labels.csv датасета говорящего, если он есть) в доноры не идут."""
    key = speaker.replace("-", "")
    labels = vw / ("dataset" if key == KEY else f"dataset_{key[:8]}") / "labels.csv"
    bad = set()
    if labels.exists():
        bad = {r["handle"] for r in csv.DictReader(labels.open(encoding="utf-8-sig"))
               if any(x in r["exclude"] for x in ("пение", "мёртвые", "рыдание"))}
    out, seen = [], set()
    for h, length, src in vanilla_bank(speaker):
        base = src[:-4]
        if h in bad or base in seen or f"FX_{base}.ffxanim" not in anims:
            continue
        seen.add(base)
        out.append((h, length, base))
    return out


def pick_donor(pool, seconds):
    """Как в пробе: не короче новой реплики и ближайшая по длине; если таких нет — самая длинная."""
    longer = [d for d in pool if d[1] >= seconds]
    return min(longer, key=lambda d: d[1]) if longer else max(pool, key=lambda d: d[1])


def write_takes(loc, takes, vw, keep_lsx=False):
    """Файлы озвучки для пака в loc (= Mods/<папка>/Localization/English).

    takes — [(handle, wav, uuid говорящего, приоритет)]. Раскладка — как в паках игры: Voice.pak и VoiceMeta.pak →
    Mods/Gustav/Localization/English/Soundbanks/ (v<id>_<handle>.wem и банк <id>.lsf рядом, Source — имя файла;
    <id> — uuid говорящего без дефисов), English_Animations.pak → …/English/Animation/ (FX_/MC_ по имени .wem,
    FaceFXActors/<uuid>). Свой банк на каждого говорящего. Липсинк — заимствованный FX_/MC_ его же реплики
    ближайшей длины (pick_donor); нет FaceFX у говорящего — без липсинка.

    Возвращает (строки отчёта по handle, TSV; сводку {uuid говорящего: {"lines", "lipsync", "seconds"}})."""
    bank, anim = loc / "Soundbanks", loc / "Animation"
    by_speaker = {}
    for handle, wav, speaker, priority in takes:
        by_speaker.setdefault(speaker, []).append((handle, wav, priority))
    report, summary = [], {}
    for speaker, items in sorted(by_speaker.items()):
        key = speaker.replace("-", "")
        anims = speaker_anims(vw, speaker)
        pool = donors(vw, speaker, anims)
        entries, lips = [], 0
        for handle, wav, priority in sorted(items):
            base = f"v{key}_{handle}"
            length = write_wem_pcm(wav, bank / f"{base}.wem")
            entries.append((handle, f"{base}.wem", length, priority))
            if not pool:
                report.append(f"{handle}\t{speaker}\t{length:.3f}\t{priority}\t-\t-\tбез липсинка (нет FaceFX)")
                continue
            dh, dlen, dbase = pick_donor(pool, length)
            got = []
            for prefix, ext in (("FX_", ".ffxanim"), ("MC_", ".gr2")):
                src = anims.get(f"{prefix}{dbase}{ext}")
                if src:
                    anim.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, anim / f"{prefix}{base}{ext}")
                    got.append(prefix.rstrip("_"))
            lips += 1
            report.append(f"{handle}\t{speaker}\t{length:.3f}\t{priority}\t{dh}\t{dlen:.3f}\t{'+'.join(got)}")
        bank.mkdir(parents=True, exist_ok=True)
        lsx = bank / f"{key}.lsx"
        lsx.write_text(voicemeta_lsx(speaker, entries), encoding="utf-8")
        divine("-a", "convert-resource", "-s", lsx, "-d", lsx.with_suffix(".lsf"))
        if not keep_lsx:
            lsx.unlink()
        if lips:
            (anim / "FaceFXActors").mkdir(parents=True, exist_ok=True)
            for n, a in anims.items():
                if n.startswith(speaker + "."):
                    shutil.copy2(a, anim / "FaceFXActors" / n)
        summary[speaker] = {"lines": len(entries), "lipsync": lips, "seconds": round(sum(e[2] for e in entries), 1)}
    return report, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True, help="handle новой реплики из loca мода")
    ap.add_argument("--wav", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--speaker", default=ALFIRA, help="uuid говорящего (по умолчанию Альфира)")
    ap.add_argument("--priority", default=PRIORITY)
    args = ap.parse_args()
    vw = resolve(config()["paths"]["voice_work"])
    out = args.out or vw / "pipeline" / "proto"
    if out.exists():
        shutil.rmtree(out)
    report, _ = write_takes(out / "Mods" / "_MOD_" / "Localization" / "English",
                            [(args.handle, args.wav, args.speaker, args.priority)], vw, keep_lsx=True)
    report = ["handle\tговорящий\tдлина\tприоритет\tдонор липсинка\tего длина\tфайлы"] + report
    report.append("Прототип; в пак это кладёт build_pak.py --voice clone (docs/VOICE.md).")
    (out / "README.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"→ {out}")


if __name__ == "__main__":
    main()
