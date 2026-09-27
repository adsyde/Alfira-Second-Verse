#!/usr/bin/env python3
"""Конвейер «новая реплика с голосом → файлы для пака»: write_takes() вызывает build_pak.py --voice clone
(личная сборка), CLI ниже — прототип для одного handle в voice-work/pipeline/proto/.

Для одного handle из loca мода и готового .wav (48 кГц, моно, 16 бит — так выдаёт
compare_models.py publish / tts/normalize.py) собирает в voice-work/pipeline/proto/ то, что
по данным игры нужно движку для озвученной реплики её голосом (docs/VOICE.md, «Конвейер в игру»):

  Mods/_MOD_/Localization/English/Soundbanks/v<спикер>_<handle>.wem   — звук: Wwise RIFF, кодек PCM
  Mods/_MOD_/Localization/English/Soundbanks/<спикер>.lsx/.lsf        — VoiceMeta: handle → файл, длина, приоритет
  Mods/_MOD_/Localization/English/Animation/FX_v<спикер>_<handle>.ffxanim — липсинк FaceFX (заимствован)
  Mods/_MOD_/Localization/English/Animation/MC_v<спикер>_<handle>.gr2     — жесты мокапа (заимствованы)
  Mods/_MOD_/Localization/English/Animation/FaceFXActors/<guid>.ffxactor/.ffxbones — её актёр FaceFX

Ограничения (проверены только инструментами, не игрой):
  * .wem — Wwise PCM (fmt 0xFFFE). Ванильные — Wwise Vorbis, кодировщика Vorbis без Wwise нет.
    vgmstream читает наш файл как «Audiokinetic Wwise RIFF, 16-bit PCM»; кодек PCM есть в списке
    кодеков bg3_dx11.exe. Примет ли его игра — проверить в игре.
  * Липсинк FaceFX без инструментов FaceFX не сделать: .ffxanim — скомпилированные данные. Берётся
    её ванильный .ffxanim реплики близкой длины (не короче новой) — рот двигается, но не по словам.
  * Папка _MOD_ — как в mod/, build_pak подставит <name>_<uuid>. Клон в mod/ (git) не кладётся.

  python scripts/voice/game_voice.py --handle hafab7af6g9ceag5788g87a8g3227f8639bd5 --wav <file.wav>
"""
import argparse
import csv
import shutil
import struct
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import config, divine, enable_utf8_stdout, game_pak, resolve  # noqa: E402
from gamedb import ALFIRA  # noqa: E402

enable_utf8_stdout()

SR = 48000
KEY = ALFIRA.replace("-", "")
PRIORITY = "P1_StoryDialog"     # как у её реплик в сюжетных диалогах (VoiceMeta: 437 из 548)


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


def voicemeta_lsx(entries):
    """entries: [(handle, source, length)] → текст .lsx банка её голоса (структура как у VoiceMeta игры)."""
    items = []
    for handle, source, length in sorted(entries):
        items.append(f"""								<node id="VoiceTextMetaData">
									<attribute id="MapKey" type="FixedString" value="{handle}" />
									<children>
										<node id="MapValue">
											<attribute id="Codec" type="FixedString" value="PCM" />
											<attribute id="Length" type="float" value="{length:.7g}" />
											<attribute id="Priority" type="FixedString" value="{PRIORITY}" />
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
					<attribute id="MapKey" type="FixedString" value="{ALFIRA}" />
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


def donor_line(vw, seconds):
    """Её ванильная реплика для липсинка: не короче новой и ближайшая по длине, без пения и выкриков."""
    labels = {r["handle"]: r for r in csv.DictReader((vw / "dataset" / "labels.csv").open(encoding="utf-8-sig"))}
    ok = [r for r in labels.values() if not any(x in r["exclude"] for x in ("пение", "мёртвые", "рыдание"))
          and float(r["seconds"]) >= seconds]
    if not ok:
        sys.exit(f"нет её реплики длиннее {seconds:.1f} с для липсинка")
    return min(ok, key=lambda r: float(r["seconds"]))


def extract_anim(vw, pattern):
    """Файлы анимации её голоса из English_Animations.pak (кэш — voice-work/pipeline/vanilla_anim)."""
    dest = vw / "pipeline" / "vanilla_anim"
    hits = list(dest.rglob(pattern)) if dest.exists() else []
    if not hits:
        divine("-a", "extract-package", "-s", game_pak("Localization/English_Animations.pak"), "-d", dest, "-x", f"*{pattern}*")
        hits = list(dest.rglob(pattern))
    return hits


def write_takes(loc, takes, vw, keep_lsx=False):
    """Файлы озвучки для пака в loc (= Mods/<папка>/Localization/English): takes — [(handle, wav)].

    Раскладка — как у её голоса в паках игры: Voice.pak и VoiceMeta.pak → Mods/Gustav/Localization/English/
    Soundbanks/ (.wem и банк VoiceMeta рядом, Source — имя файла), English_Animations.pak →
    Mods/Gustav/Localization/English/Animation/ (FX_/MC_, FaceFXActors). Возвращает строки отчёта."""
    bank, anim = loc / "Soundbanks", loc / "Animation"
    entries, report = [], []
    anim.mkdir(parents=True, exist_ok=True)
    for handle, wav in takes:
        base = f"v{KEY}_{handle}"
        length = write_wem_pcm(wav, bank / f"{base}.wem")
        entries.append((handle, f"{base}.wem", length))
        donor = donor_line(vw, length)
        got = []
        for prefix, ext in (("FX_", ".ffxanim"), ("MC_", ".gr2")):
            src = extract_anim(vw, f"{prefix}v{KEY}_{donor['handle']}{ext}")
            if src:
                shutil.copy2(src[0], anim / f"{prefix}{base}{ext}")
                got.append(f"{prefix}{ext}")
        report += [f"{handle}: {Path(wav).name} → {base}.wem (Wwise PCM, {length:.3f} с); "
                   f"{', '.join(got) or 'без липсинка'} от её реплики {donor['handle']} ({donor['seconds']} с): "
                   f"«{donor['text'][:60]}…» — рот по чужому тексту"]
    lsx = bank / f"{KEY}.lsx"
    lsx.write_text(voicemeta_lsx(entries), encoding="utf-8")
    divine("-a", "convert-resource", "-s", lsx, "-d", lsx.with_suffix(".lsf"))
    if not keep_lsx:
        lsx.unlink()
    actors = extract_anim(vw, f"{ALFIRA}.ffx*")
    (anim / "FaceFXActors").mkdir(exist_ok=True)
    for a in actors:
        shutil.copy2(a, anim / "FaceFXActors" / a.name)
    report += [f"VoiceMeta: Soundbanks/{KEY}.lsf, реплик {len(entries)}, Codec=PCM, Priority={PRIORITY}",
               f"FaceFXActors: {', '.join(a.name for a in actors)}"]
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--handle", required=True, help="handle новой реплики из loca мода")
    ap.add_argument("--wav", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    vw = resolve(config()["paths"]["voice_work"])
    out = args.out or vw / "pipeline" / "proto"
    if out.exists():
        shutil.rmtree(out)
    report = write_takes(out / "Mods" / "_MOD_" / "Localization" / "English", [(args.handle, args.wav)], vw,
                         keep_lsx=True)
    report.append("Прототип; в пак это кладёт build_pak.py --voice clone (docs/VOICE.md).")
    (out / "README.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"→ {out}")


if __name__ == "__main__":
    main()
