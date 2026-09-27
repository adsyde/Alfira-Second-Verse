#!/usr/bin/env python3
"""Голос клона для отдельных новых реплик Альфиры → voice-work/game/ (личная сборка, docs/VOICE.md).

Модели — Breeze TTS 2 и IndexTTS-2.5 без дообучения (решение автора 2026-09-27), обёртки
scripts/voice/tts/run_<модель>.py, по 3 варианта на модель (настройки — в обёртках). Выбор: из вариантов
с WER Whisper ≤ 0,15 — самый похожий на неё (ECAPA + WavLM к центру её голоса, как compare_models.py);
если таких нет — лучший по compare_models.score_of. Выбранный дубль (48 кГц моно, громкость как в
сравнении) — voice-work/game/<handle>.wav, запись в voice-work/game/voice.json; его берёт
build_pak.py --voice clone.

Видеокарта общая с другими прогонами: перед каждой моделью смотрится свободная память (nvidia-smi).
--device auto: если её меньше, чем нужно модели (NEED_MB), или идёт чужая генерация (BUSY), модель считается
на процессоре; gpu — ждать; cpu — всегда процессор. Breeze — только на видеокарте (потоковый рантайм
требует CUDA): он ждёт, пока память свободна минуту подряд и чужой генерации нет. Модели — по одной.

  python scripts/voice/voice_line.py all --handle h… --emotion excited --ref h3acb7afc….wav \\
         --instruct "warm and delighted" --vector 0.7,0,0,0,0,0,0.2,0.1
  python scripts/voice/voice_line.py gen|score|pick --handle h… (те же параметры у gen)
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from common import config, enable_utf8_stdout, resolve  # noqa: E402
import compare_models as cm  # noqa: E402

enable_utf8_stdout()

MODELS = ("indextts", "breeze")
VARIANTS = 3
# пик памяти прогона сравнения (compare/_work/<модель>/results.json) + запас
NEED_MB = {"indextts": 7000, "breeze": 9500, "metrics": 5000}
GPU_ONLY = {"breeze"}      # потоковый рантайм Breeze — только CUDA: ждём память, а не процессор
MAX_WER = 0.15


def free_mb():
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
    return int(r.stdout.split()[0]) if r.returncode == 0 and r.stdout.strip() else 0


BUSY = ("voice_act1.py", "compare_models.py", "run_breeze.py", "run_indextts.py", "run_voxcpm.py",
        "run_chatterbox.py", "metrics.py")


def others_busy():
    """Идёт ли чужая генерация (другой процесс озвучки): её модели сменяют друг друга без пауз."""
    ps = "Get-CimInstance Win32_Process -Filter \"Name like 'python%'\" | ForEach-Object { $_.CommandLine }"
    out = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True).stdout
    return [b for b in BUSY if b in out]


def steady(need, checks=3, pause=20):
    """Память свободна несколько проверок подряд и чужая генерация не идёт (не щель между её прогонами)."""
    for _ in range(checks):
        time.sleep(pause)
        if free_mb() < need or others_busy():
            return False
    return True


def device_for(what, mode):
    """cuda или cpu для очередного тяжёлого шага; на cpu — CUDA_VISIBLE_DEVICES=-1 для дочернего процесса."""
    need = NEED_MB[what]
    while True:
        free = free_mb()
        if what not in GPU_ONLY and (mode == "cpu" or (mode == "auto" and (free < need or others_busy()))):
            print(f"[{what}] видеопамяти свободно {free} МБ, нужно {need} → процессор", flush=True)
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
            return "cpu"
        if free >= need and steady(need):
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
            print(f"[{what}] видеопамяти свободно {free} МБ → видеокарта", flush=True)
            return "cuda"
        print(f"[{what}] видеопамяти свободно {free} МБ, нужно {need}; другие прогоны: {others_busy() or 'нет'} — жду…",
              flush=True)
        time.sleep(30)


def mod_text(handle):
    """Английский текст новой реплики из loca мода, без разметки (<i>…</i>)."""
    xml = resolve(config()["paths"]["mod_src"]) / "Mods/_MOD_/Localization/English/AlfiraSecondVerse_en.xml"
    m = re.search(rf'contentuid="{handle}"[^>]*>(.*?)</content>', xml.read_text(encoding="utf-8"), re.S)
    if not m:
        sys.exit(f"{handle}: нет в {xml}")
    return re.sub(r"<[^>]+>", "", html.unescape(m.group(1))).strip()


def work(handle):
    vw = resolve(config()["paths"]["voice_work"])
    return vw, vw / "trial" / handle


def cmd_gen(args):
    vw, w = work(args.handle)
    ref = cm.pick_ref(vw, args.emotion)
    if args.ref:
        import csv
        idx = vw / "refs" / args.emotion / "index.csv"
        row = next((r for r in csv.DictReader(idx.open(encoding="utf-8-sig")) if r["file"] == args.ref), None)
        if row is None:
            sys.exit(f"нет {args.ref} в {idx}")
        ref = {"ref_wav": str(idx.parent / row["file"]), "ref_text": row["text"], "ref_seconds": float(row["seconds"]),
               "ref_dialog": row["dialog"], "ref_remark": row["remark"]}
    line = {"id": "01", "handle": args.handle, "emotion": args.emotion, "text": mod_text(args.handle),
            "instruct": args.instruct, "emo_vector": [float(x) for x in args.vector.split(",")], "tags": args.tags, **ref}
    w.mkdir(parents=True, exist_ok=True)
    jobs = w / "jobs.json"
    jobs.write_text(json.dumps({"variants": VARIANTS, "lines": [line]}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{args.handle}: «{line['text']}» ← {Path(ref['ref_wav']).name} ({ref['ref_remark']})")
    for name in args.models.split(","):
        dev = device_for(name, args.device)
        code, _, wall = cm.run_model(name, jobs, w / name, vw, vw / "models")
        (w / name / "device.txt").write_text(dev, encoding="utf-8")
        if code:
            sys.exit(f"{name} упал: {w / name / 'run.log'}")


def cmd_score(args):
    vw, w = work(args.handle)
    line = json.loads((w / "jobs.json").read_text(encoding="utf-8"))["lines"][0]
    items = [{"key": f"{n}/{k}", "wav": str(w / n / f"line01_v{k}.wav"), "text": line["text"], "ref": line["ref_wav"]}
             for n in MODELS for k in range(1, VARIANTS + 1) if (w / n / f"line01_v{k}.wav").exists()]
    ij = w / "metrics_items.json"
    ij.write_text(json.dumps({"voice_set": cm.voice_set(vw), "items": items, "cache": str(vw / "cache" / "metrics")},
                             ensure_ascii=False), encoding="utf-8")
    device_for("metrics", args.device)
    p = subprocess.run([str(vw / "models" / cm.METRICS_PY), str(cm.TTS / "metrics.py"), str(ij), str(w / "metrics.json")],
                       env=cm.model_env(vw))
    if p.returncode:
        sys.exit("метрики упали")


def cmd_pick(args):
    vw, w = work(args.handle)
    line = json.loads((w / "jobs.json").read_text(encoding="utf-8"))["lines"][0]
    met = json.loads((w / "metrics.json").read_text(encoding="utf-8"))
    rows = met["items"]
    sim = lambda m: 0.5 * m["sim_ecapa"] + 0.5 * m["sim_wavlm"]  # noqa: E731
    ok = [m for m in rows if m["wer"] <= MAX_WER]
    best = max(ok, key=sim) if ok else max(rows, key=cm.score_of)
    # все варианты — к одному виду (48 кГц, громкость), чтобы автор мог сравнить на слух
    norm = w / "norm"
    norm.mkdir(exist_ok=True)
    pairs = [[str(w / m["key"].split("/")[0] / f"line01_v{m['key'].split('/')[1]}.wav"),
              str(norm / (m["key"].replace("/", "_v") + ".wav"))] for m in rows]
    nj = w / "normalize.json"
    nj.write_text(json.dumps(pairs, ensure_ascii=False), encoding="utf-8")
    subprocess.run([str(vw / "models" / cm.METRICS_PY), str(cm.TTS / "normalize.py"), str(nj)], env=cm.model_env(vw),
                   check=True)
    game = vw / "game"
    game.mkdir(exist_ok=True)
    src = norm / (best["key"].replace("/", "_v") + ".wav")
    dst = game / f"{args.handle}.wav"
    dst.write_bytes(src.read_bytes())
    with wave.open(str(dst)) as f:
        seconds = f.getnframes() / f.getframerate()
    vj = game / "voice.json"
    voice = json.loads(vj.read_text(encoding="utf-8")) if vj.exists() else {}
    model, k = best["key"].split("/")
    voice[args.handle] = {"file": dst.name, "seconds": round(seconds, 6), "model": model, "variant": int(k),
                          "device": (w / model / "device.txt").read_text(encoding="utf-8").strip(),
                          "ref": Path(line["ref_wav"]).name, "emotion": line["emotion"], "text": line["text"],
                          "sim_ecapa": round(best["sim_ecapa"], 3), "sim_wavlm": round(best["sim_wavlm"], 3),
                          "wer": round(best["wer"], 3), "asr": best["asr"]}
    vj.write_text(json.dumps(voice, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"её собственный разброс: ecapa {met['self_sim']['ecapa']:.3f}, wavlm {met['self_sim']['wavlm']:.3f}")
    for m in sorted(rows, key=lambda m: -sim(m)):
        mark = "→" if m is best else " "
        print(f" {mark} {m['key']:<12} ecapa {m['sim_ecapa']:.3f} wavlm {m['sim_wavlm']:.3f} wer {m['wer']:.2f}  «{m['asr']}»")
    print(f"выбран {best['key']}: {dst} ({seconds:.2f} с); варианты для прослушивания — {norm}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score", "pick", "all"])
    ap.add_argument("--handle", required=True)
    ap.add_argument("--emotion", default="neutral", help="папка voice-work/refs/<эмоция>/")
    ap.add_argument("--ref", default="", help="файл референса из refs/<эмоция>/ (по умолчанию — как compare_models)")
    ap.add_argument("--instruct", default="", help="подача для Breeze (Voice Direction)")
    ap.add_argument("--vector", default="0,0,0,0,0,0,0,1", help="вектор 8 эмоций IndexTTS")
    ap.add_argument("--tags", default="", help="звук в тексте для Breeze v3: laugh, sigh")
    ap.add_argument("--models", default=",".join(MODELS), help="gen: какие модели (по одной, по очереди)")
    ap.add_argument("--device", choices=["auto", "gpu", "cpu"], default="auto")
    args = ap.parse_args()
    for c in (["gen", "score", "pick"] if args.cmd == "all" else [args.cmd]):
        {"gen": cmd_gen, "score": cmd_score, "pick": cmd_pick}[c](args)


if __name__ == "__main__":
    main()
