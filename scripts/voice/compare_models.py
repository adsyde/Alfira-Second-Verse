#!/usr/bin/env python3
"""Слепое сравнение моделей клонирования голоса на 10 новых репликах Альфиры.

Каждая модель стоит в своём venv под voice-work/models/<имя>/ (docs/VOICE.md, «Кандидаты»),
её обёртка — scripts/voice/tts/run_<имя>.py. Этот скрипт (системный python) только раздаёт задания,
следит за видеокартой и собирает результат.

  python scripts/voice/compare_models.py prepare            # задания: реплики + референсы эмоций
  python scripts/voice/compare_models.py stress indextts --minutes 7   # проверка стабильности GPU
  python scripts/voice/compare_models.py run indextts voxcpm chatterbox breeze
  python scripts/voice/compare_models.py score              # метрики (venv _metrics)
  python scripts/voice/compare_models.py publish            # lineNN_X.wav, LISTEN.md; ключ отдельно

Два набора:
  * 10 новых реплик (scripts/voice/compare_lines.json) — lineNN/;
  * «тот же текст» — 5 её реплик из игры, отложенных от референсов и датасета (holdout.json):
    модели озвучивают их текст, рядом лежит оригинал — same_text/.
Референс — лучший фрагмент voice-work/refs/<эмоция>/ (label_emotions.py), один и тот же для всех моделей.
На реплику и модель — 3 варианта (у каждой модели свои настройки, см. обёртки); в сравнение идёт
лучший по метрикам (похожесть − разборчивость), остальные остаются в compare/_work/<модель>/.

Выход (voice-work/compare/, в git не попадает):
  lineNN/lineNN_A..D.wav и lineNN_ORIG_ref.wav (фрагмент её голоса, который получили модели);
  same_text/sNN_ORIG.wav (оригинал из игры) и sNN_A..D.wav;
  всё — 48 кГц, одинаковая громкость; буквы перемешаны отдельно для каждой реплики;
  LISTEN.md — лист для прослушивания (модели не названы);
  _key/key.json, _key/METRICS.md — раскрывают модели, автору до выбора не показывать.
Во время run/stress раз в секунду пишется nvidia-smi (_work/<модель>/gpu.csv); после — журнал
System проверяется на новые сбросы драйвера (nvlddmkm). При сбросе скрипт останавливается.
"""
import argparse
import csv
import json
import os
import random
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import config, enable_utf8_stdout, resolve  # noqa: E402
from gamedb import text as loca  # noqa: E402

enable_utf8_stdout()

VARIANTS = 3
TTS = Path(__file__).resolve().parent / "tts"
# имя → (python venv, рабочая папка) относительно voice-work/models; обёртка — tts/run_<имя>.py
MODELS = {
    "indextts": ("indextts/repo/.venv/Scripts/python.exe", "indextts/repo"),
    "voxcpm": ("voxcpm/.venv/Scripts/python.exe", "voxcpm"),
    "chatterbox": ("chatterbox/.venv/Scripts/python.exe", "chatterbox"),
    "breeze": ("breeze/.venv/Scripts/python.exe", "breeze/repo"),
}
METRICS_PY = "_metrics/Scripts/python.exe"
# подача для отложенных реплик (у новых реплик она в compare_lines.json)
HOLDOUT_INSTRUCT = {"laugh": "laughing, amused, playing along with a joke", "sad": "dejected and devastated, quiet",
                    "angry": "disgusted, bitter and hurt", "excited": "excited and a little star-struck",
                    "fear": "horrified, grieving, voice shaking"}
HOLDOUT_VECTOR = {"laugh": [0.8, 0, 0, 0, 0, 0, 0.1, 0.1], "sad": [0, 0, 0.6, 0, 0, 0.4, 0, 0],
                  "angry": [0, 0.5, 0.2, 0, 0.3, 0, 0, 0], "excited": [0.8, 0, 0, 0, 0, 0, 0.2, 0],
                  "fear": [0, 0, 0.3, 0.7, 0, 0, 0, 0]}
EMO_RU = {"laugh": "смех", "embarrassed": "смущение", "sad": "грусть", "angry": "злость, обида", "flirty": "флирт",
          "whisper": "тихо, почти шёпотом", "drunk": "навеселе", "tired": "похмелье, усталость", "fear": "страх",
          "excited": "воодушевление", "neutral": "нейтраль", "teasing": "подначка", "grateful": "тепло",
          "tearful": "сквозь слёзы", "surprise": "удивление"}


def paths():
    vw = resolve(config()["paths"]["voice_work"])
    return vw, vw / "models", vw / "compare", vw / "compare" / "_work"


def model_env(vw):
    env = dict(os.environ)
    env.update({
        "HF_HOME": str(vw / "cache" / "hf"), "TORCH_HOME": str(vw / "cache" / "torch"),
        "XDG_CACHE_HOME": str(vw / "cache" / "xdg"), "HF_HUB_DISABLE_TELEMETRY": "1",
        "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "VOICE_WORK": str(vw),
    })
    return env


# --- видеокарта ---------------------------------------------------------------------------------

class GpuLog(threading.Thread):
    """nvidia-smi раз в секунду: мощность, температура, память, загрузка."""
    Q = "timestamp,power.draw,power.limit,temperature.gpu,memory.used,utilization.gpu,clocks.sm"

    def __init__(self, path):
        super().__init__(daemon=True)
        self.path, self.stop_ev, self.rows = path, threading.Event(), []

    def run(self):
        with self.path.open("w", encoding="utf-8") as f:
            f.write(self.Q + "\n")
            while not self.stop_ev.is_set():
                r = subprocess.run(["nvidia-smi", f"--query-gpu={self.Q}", "--format=csv,noheader,nounits"],
                                   capture_output=True, text=True)
                line = r.stdout.strip()
                if r.returncode != 0 or not line:
                    line = f"{datetime.now():%Y/%m/%d %H:%M:%S},ERR,,,,,"
                f.write(line + "\n")
                f.flush()
                self.rows.append(line.split(", "))
                self.stop_ev.wait(1.0)

    def summary(self):
        ok = [r for r in self.rows if len(r) >= 7 and r[1] != "ERR"]
        if not ok:
            return {"samples": 0, "errors": len(self.rows)}
        num = lambda i: [float(r[i]) for r in ok if r[i].replace(".", "", 1).isdigit()]  # noqa: E731
        return {"samples": len(ok), "errors": len(self.rows) - len(ok),
                "power_max_w": max(num(1)), "power_avg_w": round(sum(num(1)) / len(num(1)), 1),
                "power_limit_w": num(2)[0], "temp_max_c": max(num(3)), "mem_max_mb": max(num(4)),
                "util_avg": round(sum(num(5)) / len(num(5)), 1)}


def driver_resets(since):
    """События nvlddmkm в журнале System после since (datetime)."""
    ps = ("Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='nvlddmkm'; StartTime=[datetime]'"
          f"{since:%Y-%m-%dT%H:%M:%S}'" "} -ErrorAction SilentlyContinue | "
          "ForEach-Object { $_.TimeCreated.ToString('s') + ' ' + $_.Id }")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    return [x for x in r.stdout.split("\n") if x.strip()]


def run_model(name, jobs_path, out, vw, models, tag=""):
    py, cwd = MODELS[name]
    py, cwd = models / py, models / cwd
    if not py.exists():
        sys.exit(f"{name}: нет venv {py} — поставьте модель (docs/VOICE.md)")
    out.mkdir(parents=True, exist_ok=True)
    gpu = GpuLog(out / f"gpu{tag}.csv")
    start = datetime.now()
    gpu.start()
    t = time.perf_counter()
    with (out / f"run{tag}.log").open("w", encoding="utf-8") as log:
        p = subprocess.run([str(py), str(TTS / f"run_{name}.py"), str(jobs_path), str(out)], cwd=cwd,
                           env=model_env(vw), stdout=log, stderr=subprocess.STDOUT)
    wall = time.perf_counter() - t
    gpu.stop_ev.set()
    gpu.join()
    resets = driver_resets(start)
    s = gpu.summary()
    print(f"[{name}] код {p.returncode}, {wall:.0f} с; GPU: {s}")
    if resets:
        print(f"!!! СБРОС ДРАЙВЕРА во время прогона {name}: {resets}. Останавливаюсь.")
        sys.exit(2)
    if p.returncode != 0:
        print(f"[{name}] упал, см. {out / f'run{tag}.log'}")
    return p.returncode, s, wall


# --- команды ------------------------------------------------------------------------------------

def pick_ref(vw, emotion):
    idx = vw / "refs" / emotion / "index.csv"
    rows = list(csv.DictReader(idx.open(encoding="utf-8-sig")))
    # лучший фрагмент категории; не короче 4 с, если есть — моделям нужен материал
    ref = next((r for r in rows if float(r["seconds"]) >= 4.0), rows[0])
    return {"ref_wav": str(idx.parent / ref["file"]), "ref_text": ref["text"], "ref_seconds": float(ref["seconds"]),
            "ref_dialog": ref["dialog"], "ref_remark": ref["remark"]}


def cmd_prepare(_args):
    vw, models, comp, work = paths()
    here = Path(__file__).parent
    spec = json.loads((here / "compare_lines.json").read_text(encoding="utf-8"))
    lines = [{**ln, "text": ln["en"], **pick_ref(vw, ln["emotion"])} for ln in spec["lines"]]
    meta = {r["file"][:-4]: r for r in csv.DictReader((vw / "dataset" / "metadata.csv").open(encoding="utf-8"),
                                                        delimiter="|")}
    labels = {r["handle"]: r for r in csv.DictReader((vw / "dataset" / "labels.csv").open(encoding="utf-8-sig"))}
    for h in json.loads((here / "holdout.json").read_text(encoding="utf-8"))["lines"]:
        en = meta[h["handle"]]["text"]
        lab = labels[h["handle"]]
        lines.append({"id": h["id"], "source": lab["dialog"], "remark": f"({lab['remark']})", "emotion": h["emotion"],
                      "en": en, "ru": loca(h["handle"], "ru"), "text": en, "orig_wav": str(vw / "dataset" / "wav" / f"{h['handle']}.wav"),
                      "instruct": HOLDOUT_INSTRUCT[h["emotion"]], "emo_vector": HOLDOUT_VECTOR[h["emotion"]],
                      "tags": "laugh" if h["emotion"] == "laugh" else "", **pick_ref(vw, h["emotion"])})
    work.mkdir(parents=True, exist_ok=True)
    (work / "jobs.json").write_text(json.dumps({"variants": VARIANTS, "lines": lines}, ensure_ascii=False, indent=1),
                                    encoding="utf-8")
    for ln in lines:
        print(f"line{ln['id']} {ln['emotion']:<12} ← {Path(ln['ref_wav']).name} ({ln['ref_seconds']:.1f} с)")
    print(f"→ {work / 'jobs.json'}")


def cmd_run(args):
    vw, models, comp, work = paths()
    for name in args.models:
        run_model(name, work / "jobs.json", work / name, vw, models)


def cmd_stress(args):
    """Проверка стабильности: гоняем модель по репликам, пока не выйдет время."""
    vw, models, comp, work = paths()
    jobs = json.loads((work / "jobs.json").read_text(encoding="utf-8"))
    jobs["variants"] = 1
    sj = work / "stress_jobs.json"
    sj.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
    end = time.time() + args.minutes * 60
    n, summ = 0, []
    while time.time() < end:
        n += 1
        code, s, _wall = run_model(args.model, sj, work / "_stress" / args.model, vw, models, tag=f"_{n}")
        summ.append(s)
        if code != 0:
            break
    print(f"стресс {args.model}: {n} прогонов за {args.minutes} мин, сбросов нет")
    print("макс. мощность", max(s.get("power_max_w", 0) for s in summ), "Вт; макс. температура",
          max(s.get("temp_max_c", 0) for s in summ), "°C; макс. память", max(s.get("mem_max_mb", 0) for s in summ), "МБ")


def voice_set(vw, n=60):
    files = sorted((vw / "dataset" / "finetune" / "wav").glob("*.wav"))
    random.Random(7).shuffle(files)
    return [str(p) for p in files[:n]]


def cmd_score(_args):
    vw, models, comp, work = paths()
    jobs = json.loads((work / "jobs.json").read_text(encoding="utf-8"))
    items = []
    for ln in jobs["lines"]:
        items.append({"key": f"orig/{ln['id']}", "wav": ln.get("orig_wav") or ln["ref_wav"],
                      "text": ln["text"] if ln.get("orig_wav") else ln["ref_text"], "ref": ln["ref_wav"] if ln.get("orig_wav") else ""})
        for name in MODELS:
            for k in range(1, VARIANTS + 1):
                w = work / name / f"line{ln['id']}_v{k}.wav"
                if w.exists():
                    items.append({"key": f"{name}/{ln['id']}/{k}", "wav": str(w), "text": ln["text"], "ref": ln["ref_wav"],
                                  "target": ln.get("orig_wav", "")})
    ij = work / "metrics_items.json"
    ij.write_text(json.dumps({"voice_set": voice_set(vw), "items": items, "cache": str(vw / "cache" / "metrics")},
                             ensure_ascii=False), encoding="utf-8")
    t = time.perf_counter()
    p = subprocess.run([str(models / METRICS_PY), str(TTS / "metrics.py"), str(ij), str(work / "metrics.json")],
                       env=model_env(vw))
    print(f"метрики: код {p.returncode}, {time.perf_counter() - t:.0f} с → {work / 'metrics.json'}")


def score_of(m):
    return 0.5 * m["sim_ecapa"] + 0.5 * m["sim_wavlm"] - 0.5 * min(m["wer"], 1.0)


def cmd_publish(args):
    vw, models, comp, work = paths()
    jobs = json.loads((work / "jobs.json").read_text(encoding="utf-8"))
    met = json.loads((work / "metrics.json").read_text(encoding="utf-8"))
    by = {m["key"]: m for m in met["items"]}
    results = {n: json.loads((work / n / "results.json").read_text(encoding="utf-8"))
               for n in MODELS if (work / n / "results.json").exists()}
    names = list(results)
    key_dir = comp / "_key"
    for old in list(comp.glob("line*/*.wav")) + list(comp.glob("same_text/*.wav")):
        old.unlink()
    key_dir.mkdir(parents=True, exist_ok=True)

    key, best, norm_jobs = {}, {}, []
    rng = random.Random(args.seed)
    for ln in jobs["lines"]:
        order = names[:]
        rng.shuffle(order)
        key[ln["id"]] = {}
        held = ln["id"].startswith("s")
        d = comp / "same_text" if held else comp / f"line{ln['id']}"
        d.mkdir(parents=True, exist_ok=True)
        stem = ln["id"] if held else f"line{ln['id']}"
        orig = ln["orig_wav"] if held else ln["ref_wav"]
        norm_jobs.append([orig, str(d / (f"{stem}_ORIG.wav" if held else f"{stem}_ORIG_ref.wav"))])
        for letter, name in zip("ABCD", order):
            cands = [(score_of(by[f"{name}/{ln['id']}/{k}"]), k) for k in range(1, VARIANTS + 1)
                     if f"{name}/{ln['id']}/{k}" in by]
            if not cands:
                continue
            sc, k = max(cands)
            best[(name, ln["id"])] = k
            key[ln["id"]][letter] = {"model": name, "variant": k}
            norm_jobs.append([str(work / name / f"line{ln['id']}_v{k}.wav"), str(d / f"{stem}_{letter}.wav")])
    # одинаковые 48 кГц и громкость: частота и уровень не должны выдавать модель
    nj = work / "normalize.json"
    nj.write_text(json.dumps(norm_jobs), encoding="utf-8")
    subprocess.run([str(models / METRICS_PY), str(TTS / "normalize.py"), str(nj)], env=model_env(vw), check=True)
    (key_dir / "key.json").write_text(json.dumps(key, ensure_ascii=False, indent=1), encoding="utf-8")
    write_listen(comp, jobs, key, vw)
    write_metrics(key_dir / "METRICS.md", jobs, results, by, best, met, work)
    print(f"→ {comp / 'LISTEN.md'}; ключ и метрики → {key_dir}")


def write_listen(comp, jobs, key, vw):
    out = ["# Голос Альфиры: слепое прослушивание", "",
           "Две части. **Часть 1** — десять новых реплик (✍️ из design/dialogs), варианты A–D от разных моделей,",
           "рядом `lineNN_ORIG_ref.wav` — фрагмент её голоса из игры, который получили все модели как образец эмоции.",
           "**Часть 2** — «тот же текст»: пять её настоящих реплик из игры (их не было ни в образцах, ни в датасете).",
           "Модели озвучили тот же текст; `sNN_ORIG.wav` — как это сказала она сама.", "",
           "Буквы перемешаны отдельно для каждой реплики: A в строке 01 и A в строке 02 — не обязательно одна модель.",
           "Громкость и частота всех файлов выровнены (48 кГц).", "",
           "Оценка по каждому варианту от 1 до 5: **похож ли голос**, **естественно ли**, **та ли эмоция**.",
           "Можно просто назвать лучший вариант в каждой строке.", ""]

    def table(letters):
        return ["| | " + " | ".join(letters) + " |", "|---|" + "---|" * len(letters),
                "| голос 1–5 |" + " |" * len(letters), "| естественно 1–5 |" + " |" * len(letters),
                "| эмоция 1–5 |" + " |" * len(letters), ""]

    new = [ln for ln in jobs["lines"] if not ln["id"].startswith("s")]
    held = [ln for ln in jobs["lines"] if ln["id"].startswith("s")]
    out += ["# Часть 1. Новые реплики (папки `lineNN/`)", ""]
    for ln in new:
        letters = "".join(sorted(key[ln["id"]]))
        ref = Path(ln["ref_wav"]).relative_to(vw)
        out += [f"## {ln['id']}. {EMO_RU.get(ln['emotion'], ln['emotion'])} {ln['remark']}", "",
                f"> **EN:** {ln['en']}", f"> **RU:** {ln['ru']}", "",
                f"- Сценарий: `{ln['source']}`",
                f"- Образец эмоции: `line{ln['id']}/line{ln['id']}_ORIG_ref.wav` — «{ln['ref_text']}» "
                f"({ln['ref_dialog']}; исходник `voice-work/{ref.as_posix()}`)",
                f"- Варианты: " + ", ".join(f"`line{ln['id']}/line{ln['id']}_{c}.wav`" for c in letters), ""] + table(letters)
    out += ["# Часть 2. Тот же текст (папка `same_text/`)", ""]
    for ln in held:
        letters = "".join(sorted(key[ln["id"]]))
        ref = Path(ln["ref_wav"]).relative_to(vw)
        out += [f"## {ln['id']}. {EMO_RU.get(ln['emotion'], ln['emotion'])}", "",
                f"> **EN:** {ln['en']}", f"> **RU:** {ln['ru']}", "",
                f"- Оригинал: `same_text/{ln['id']}_ORIG.wav` ({ln['source']}; ремарка актрисе {ln['remark']})",
                f"- Образец эмоции для моделей (другая её реплика): `voice-work/{ref.as_posix()}` — «{ln['ref_text']}»",
                f"- Варианты: " + ", ".join(f"`same_text/{ln['id']}_{c}.wav`" for c in letters), ""] + table(letters)
    out += ["## Итог", "", "Лучшая модель на слух (буквы по строкам или общее впечатление):", "", ""]
    (comp / "LISTEN.md").write_text("\n".join(out), encoding="utf-8")


def write_metrics(path, jobs, results, by, best, met, work):
    ids = [ln["id"] for ln in jobs["lines"]]
    avg = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
    out = ["# Метрики сравнения (раскрывает модели — автору до выбора не показывать)", "",
           f"Похожесть — косинус эмбеддинга спикера с центром её голоса (60 чистых реплик игры). "
           f"«Потолок» — её собственные реплики: ECAPA {met['self_sim']['ecapa']:.3f}, WavLM {met['self_sim']['wavlm']:.3f}. "
           "WER — Whisper large-v3-turbo против текста реплики. RTF — время генерации / длина звука. "
           "VRAM — пик torch (reserved) и пик nvidia-smi за прогон (вся карта, вместе с рабочим столом ~1 ГБ).", "",
           "## Сводка (лучший вариант на реплику)", "",
           "| Модель | Версия | ECAPA | WavLM | к референсу (ECAPA) | WER | RTF | с на реплику | загрузка, с | VRAM torch, МБ | VRAM карта, МБ | Вт макс | °C макс |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    orig = [by[f"orig/{i}"] for i in ids if f"orig/{i}" in by]
    for name, res in results.items():
        ms = [by[f"{name}/{i}/{best[(name, i)]}"] for i in ids if (name, i) in best]
        its = [x for x in res["items"] if not x["error"]]
        gen, aud = sum(x["gen_s"] for x in its), sum(x["audio_s"] for x in its)
        g = gpu_summary(work / name / "gpu.csv")
        out.append(f"| {name} | {res.get('version', '')} | {avg([m['sim_ecapa'] for m in ms]):.3f} | "
                   f"{avg([m['sim_wavlm'] for m in ms]):.3f} | {avg([m.get('sim_ecapa_ref', 0) for m in ms]):.3f} | "
                   f"{avg([m['wer'] for m in ms]):.3f} | {gen / aud if aud else 0:.2f} | {avg([x['gen_s'] for x in its]):.1f} | "
                   f"{res.get('load_s')} | {res.get('peak_vram_mb')} | {g.get('mem', '')} | {g.get('power', '')} | {g.get('temp', '')} |")
    out.append(f"| оригинал (референсы) | — | {avg([m['sim_ecapa'] for m in orig]):.3f} | {avg([m['sim_wavlm'] for m in orig]):.3f} "
               f"| — | {avg([m['wer'] for m in orig]):.3f} | — | — | — | — | — | — | — |")
    out += ["", "## По репликам: ECAPA / WER лучшего варианта (в скобках — какой из 3)", "",
            "| Реплика | " + " | ".join(results) + " |", "|---|" + "---|" * len(results)]
    for i in ids:
        cells = []
        for name in results:
            if (name, i) in best:
                m = by[f"{name}/{i}/{best[(name, i)]}"]
                cells.append(f"{m['sim_ecapa']:.3f} / {m['wer']:.2f} (v{best[(name, i)]})")
            else:
                cells.append("—")
        out.append(f"| {i} | " + " | ".join(cells) + " |")
    held = [i for i in ids if i.startswith("s")]
    if held:
        out += ["", "## «Тот же текст»: похожесть на её настоящую реплику (ECAPA / WavLM, лучший вариант)", "",
                "| Модель | " + " | ".join(held) + " | среднее |", "|---|" + "---|" * (len(held) + 1)]
        for name in results:
            ms = [by[f"{name}/{i}/{best[(name, i)]}"] for i in held if (name, i) in best]
            cells = [f"{m.get('sim_ecapa_target', 0):.3f} / {m.get('sim_wavlm_target', 0):.3f}" for m in ms]
            out.append(f"| {name} | " + " | ".join(cells) + f" | {avg([m.get('sim_ecapa_target', 0) for m in ms]):.3f} / "
                       f"{avg([m.get('sim_wavlm_target', 0) for m in ms]):.3f} |")
    out += ["", "## Ошибки генерации", ""]
    errs = [f"- {n} line{x['id']} v{x['k']}: {x['error']}" for n, r in results.items() for x in r["items"] if x["error"]]
    out += errs or ["нет"]
    out += ["", "## Распознанный текст лучших вариантов (для проверки WER)", ""]
    for i in ids:
        for name in results:
            if (name, i) in best:
                out.append(f"- {i} {name}: {by[f'{name}/{i}/{best[(name, i)]}']['asr']}")
    path.write_text("\n".join(out) + "\n", encoding="utf-8")


def gpu_summary(path):
    if not path.exists():
        return {}
    rows = [r.split(", ") for r in path.read_text(encoding="utf-8").splitlines()[1:]]
    ok = [r for r in rows if len(r) >= 7 and r[1] != "ERR"]
    if not ok:
        return {}
    return {"mem": max(int(float(r[4])) for r in ok), "power": max(float(r[1]) for r in ok),
            "temp": max(int(float(r[3])) for r in ok)}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prepare")
    r = sub.add_parser("run")
    r.add_argument("models", nargs="+", choices=list(MODELS))
    s = sub.add_parser("stress")
    s.add_argument("model", choices=list(MODELS))
    s.add_argument("--minutes", type=float, default=7)
    sub.add_parser("score")
    p = sub.add_parser("publish")
    p.add_argument("--seed", type=int, default=20260927)
    args = ap.parse_args()
    {"prepare": cmd_prepare, "run": cmd_run, "stress": cmd_stress, "score": cmd_score, "publish": cmd_publish}[args.cmd](args)


if __name__ == "__main__":
    main()
