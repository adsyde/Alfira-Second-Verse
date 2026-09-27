#!/usr/bin/env python3
"""Озвучка новых реплик Альфиры акта 1 выбранными моделями и страница для выбора дублей.

Решение автора (2026-09-27, слепое сравнение): Breeze TTS 2 + IndexTTS-2.5, без дообучения.

  python scripts/voice/list_lines.py                         # voice-work/act1/lines.json
  python scripts/voice/voice_act1.py gen ch01_first_night ch02_lute   # генерация групп
  python scripts/voice/voice_act1.py score ch01_first_night ch02_lute # метрики и предотбор
  python scripts/voice/voice_act1.py page                    # страница по всему, что оценено
  python scripts/voice/voice_act1.py all                     # все группы по очереди: gen → score → page
  python scripts/voice/voice_act1.py pick voice-work/act1/picks/ch01-02.txt   # выбор автора → voice-work/game/

На реплику: Breeze — 2 варианта (v1 клон по образцу эмоции, v2 то же + инструкция подачи, cfg 4;
у похмелья инструкция «hungover, groggy» поверх образца «усталость»); IndexTTS — 2 (v1 эмоция из
образца, v3 без отдельной эмоции, другой seed), для смеха, флирта и воодушевления — 3 (+ v2 вектор эмоций).
Образец (он же тембр) — лучший фрагмент voice-work/refs/<эмоция>/ (как в compare_models.py).

Предотбор: брак отбрасывается — WER Whisper > 0,15 (у реплик до 6 слов — больше одного слова ошибки),
длина не по тексту, клиппинг, обрыв в конце, пауза длиннее 2 с (3 с, если в тексте «...»); имена мира
(NAMES) подсказываются Whisper и не считаются ошибкой. Из остальных по умолчанию выбран
самый похожий на неё (ECAPA + WavLM к центру её голоса) вариант Breeze; IndexTTS — только если у Breeze брак
(автор по главам 1–2 выбрал Breeze в 40 репликах из 41). Яркие эмоции (VIVID: смех, навеселе, флирт…) — IndexTTS,
если его похожесть ниже лучшей Breeze не больше чем на VIVID_SIM_GAP (на празднике автор трижды выбрал IndexTTS).
Если брак у всех — выбран лучший из брака, с пометкой.
«Переделка» (redo_act1.json): свои образцы, тексты и подача на вариант; группа «Переделка» наверху страницы,
варианты breeze_rK / indextts_rK:
  python scripts/voice/voice_act1.py gen _redo && python scripts/voice/voice_act1.py score _redo

Выход:
  voice-work/act1/gen/<группа>/<модель>/line<handle>_v<k>.wav, gpu.csv, run.log; score.json группы;
  C:/Users/<пользователь>/Downloads/Альфира — голос акт 1/index.html и папки групп с .wav (48 кГц,
  одна громкость), _образцы/ — её фрагменты. Пути на странице относительные, без base64.
Во время генерации пишется nvidia-smi, после каждого прогона проверяется журнал nvlddmkm:
при сбросе драйвера скрипт останавливается (compare_models.run_model).
"""
import argparse
import html
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from common import enable_utf8_stdout  # noqa: E402
import compare_models as cm  # noqa: E402

enable_utf8_stdout()

MODELS = ("breeze", "indextts")
PREFERRED = "breeze"          # решение автора по главам 1–2 (voice-work/act1/picks/ch01-02.txt)
GAME_DIR_NAME = "game"        # voice-work/game/<handle>.wav — отсюда голос берёт build_pak --voice clone
TITLE = {"breeze": "Breeze TTS 2", "indextts": "IndexTTS-2.5"}
EMO_RU = {**cm.EMO_RU, "hungover": "похмелье", "grateful": "тепло"}
PAGE_DIR = Path.home() / "Downloads" / "Альфира — голос акт 1"
WER_MAX = 0.15
PAUSE_MAX = 2.0          # с; у реплик с «...» — PAUSE_MAX_ELLIPSIS: там паузу пишет сценарий
PAUSE_MAX_ELLIPSIS = 3.0
# имена мира: подсказка Whisper и терпимость WER к их написанию (tts/metrics.py)
NAMES = ["Alfira", "Lihala", "Elturel", "Lakrissa", "tiefling", "tieflings", "Baldur's Gate", "Mattis", "Zevlor",
         "Beregost", "Nashkel", "Candlekeep", "Mol", "Arabella", "Karlach", "Astarion", "Shadowheart", "Lae'zel", "Wyll",
         "Gale", "Halsin", "Volo", "Kagha", "Tav", "Faerûn", "Milil", "Mystra", "Ikaron", "Asharak", "Quil", "Rolan",
         "Ravengard", "Duke"]


def act1_paths():
    vw, models, _comp, _work = cm.paths()
    return vw, models, vw / "act1", vw / "act1" / "gen"


ALFIRA_UUID = "4a405fba-3000-4c63-97e5-a8001ebb883c"
# говорящий → (ключ, имя, папка образцов, датасет) — NPC клонируются только в личную сборку (docs/VOICE.md)
SPEAKERS = {
    ALFIRA_UUID: ("alfira", "Альфира", "refs", "dataset"),
    "02025646-347a-4235-aef7-e46b7c94b435": ("asharak", "Ашарак", "refs_asharak", "dataset_02025646"),
    "23129d6c-8d39-4a4c-a4f6-cfc6637b597c": ("lakrissa", "Лакрисса", "refs_lakrissa", "dataset_23129d6c"),
    "e2ad06ec-8034-479a-9f69-b86faea6dc79": ("dammon", "Даммон", "refs_dammon", "dataset_e2ad06ec"),
}
TALKS = "talks"                  # группа «Разговоры»: voice-work/act1/lines_talks.json (разговоры по событиям и локальные)
_lines_cache = None


def talks_lines(act):
    """lines_talks.json → формат lines.json: эмоция и подача — по ремарке и лицу сценария, как в list_lines.py."""
    p = act / "lines_talks.json"
    if not p.exists():
        return []
    import types
    import list_lines
    out = []
    for x in json.loads(p.read_text(encoding="utf-8")):
        ln = types.SimpleNamespace(note=x.get("note", ""), emo=x.get("emo") or "neutral", en=x["en"])
        cat, why = list_lines.category(ln, TALKS, x.get("block", ""))
        instr, vec = list_lines.STYLE[cat]
        spk = SPEAKERS.get(x.get("speaker_uuid", ALFIRA_UUID), SPEAKERS[ALFIRA_UUID])
        out.append({**x, "group": TALKS, "group_title": "Разговоры", "scene_title": x.get("group_title", ""),
                    "emo": x.get("emo") if isinstance(x.get("emo"), str) else json.dumps(x.get("emo")),
                    "emotion": cat, "why": why, "ref_emotion": list_lines.REF_OF.get(cat, cat), "instruct": instr,
                    "emo_vector": vec, "tags": "laugh" if cat == "laugh" else "",
                    "index_variants": 3 if cat in list_lines.VECTOR_EXTRA else 2,
                    "speaker_key": spk[0], "speaker_name": spk[1], "ref_dir": spk[2]})
    return out


def load_lines():
    """Реплики акта 1 (lines.json) и «Разговоров» (lines_talks.json)."""
    global _lines_cache
    if _lines_cache is None:
        vw, _m, act, _g = act1_paths()
        _lines_cache = json.loads((act / "lines.json").read_text(encoding="utf-8")) + talks_lines(act)
    return [dict(x) for x in _lines_cache]


def pick_ref(vw, ln_or_emotion):
    """Образец эмоции из папки образцов говорящего; если такой эмоции у NPC нет — нейтраль, потом тепло."""
    if isinstance(ln_or_emotion, str):
        return cm.pick_ref(vw, ln_or_emotion)
    ln = ln_or_emotion
    d = ln.get("ref_dir", "refs")
    for emo in (ln["ref_emotion"], "neutral", "grateful"):
        idx = vw / d / emo / "index.csv"
        if idx.exists():
            import csv
            rows = list(csv.DictReader(idx.open(encoding="utf-8-sig")))
            ref = next((r for r in rows if float(r["seconds"]) >= 4.0), rows[0])
            return {"ref_wav": str(idx.parent / ref["file"]), "ref_text": ref["text"], "ref_seconds": float(ref["seconds"]),
                    "ref_dialog": ref["dialog"], "ref_remark": ref["remark"], "ref_emo_used": emo}
    raise FileNotFoundError(f"нет образцов в {vw / d}")


def speaker_voice_set(vw, ln, n=60):
    """Эталон голоса для похожести: у Альфиры — датасет дообучения, у NPC — его чистые реплики без исключений."""
    if ln.get("speaker_key", "alfira") == "alfira":
        return cm.voice_set(vw, n)
    import csv
    import random
    ds = vw / SPEAKERS[ln["speaker_uuid"]][3]
    rows = [r for r in csv.DictReader((ds / "labels.csv").open(encoding="utf-8-sig")) if not r["exclude"] and not r["noise"]]
    files = sorted(str(ds / "wav" / f"{r['handle']}.wav") for r in rows)
    random.Random(7).shuffle(files)
    return files[:n]


REDO = "_redo"   # группа «Переделка»: реплики из redo_act1.json, варианты breeze_rK / indextts_rK
# эмоции, где автор на празднике выбирал IndexTTS («на живых и пьяных репликах он сильнее»)
VIVID = {"laugh", "drunk", "excited", "flirty", "teasing", "embarrassed", "tearful"}
VIVID_SIM_GAP = 0.03   # ★ на IndexTTS, если его похожесть ниже лучшей Breeze не больше чем на столько


EVEN = "_even"   # «ровный набор»: все реплики похмелья с одним образцом, одной инструкцией и одними seed
EVEN_EMOTION = "hungover"
EVEN_SEEDS = (4301, 4302)
HANGOVER_BLOCK = "Похмелье"   # блок наверху страницы: все реплики похмелья подряд, выбор синхронизирован с главой
SPECIAL = {REDO: "r", EVEN: "e"}


# Правило автора (выбор all_v7: все реплики похмелья — ровный набор): если одна эмоция идёт в сцене подряд,
# сразу делается ровный набор — общий образец, одна инструкция, общие seed, и ★ ставится на него.
# Сцены-главы с этого правила (главы 1–5 автор уже выбрал); места, фразы в пути и беседы — отдельные AD, не сцены.
EVEN_GROUPS = ("ch06_elturel", "ch07_fear", "ch08_first_kiss", "inparty", TALKS)
EVEN_RUN_MIN = 2


def even_runs():
    """[(ключ серии, [реплики])]: все реплики похмелья — одна серия; в EVEN_GROUPS — подряд идущие одной эмоции."""
    import itertools
    lines = load_lines()
    runs = [(f"ch05_morning_after/{EVEN_EMOTION}", [x for x in lines if x["emotion"] == EVEN_EMOTION])]
    for g in EVEN_GROUPS:
        grp = [x for x in lines if x["group"] == g]
        i = 0
        # в «Разговорах» серия — внутри одной сцены и одного говорящего
        key = lambda x: (x.get("scene_title", ""), x.get("speaker_key", "alfira"), x["emotion"])  # noqa: E731
        for (scene, spk, emo), it in itertools.groupby(grp, key=key):
            run = list(it)
            if len(run) >= EVEN_RUN_MIN and spk == "alfira":
                runs.append((f"{g}/{scene}/{emo}/{i}" if scene else f"{g}/{emo}/{i}", run))
            i += len(run)
    return [r for r in runs if r[1]]


def even_spec():
    """Ровный набор: на реплику серии — 2 варианта Breeze с образцом эмоции серии, её инструкцией и общими seed."""
    import list_lines
    vw = act1_paths()[0]
    out = {}
    for key, run in even_runs():
        ref = Path(cm.pick_ref(vw, run[0]["ref_emotion"])["ref_wav"]).relative_to(vw).as_posix()
        instr = list_lines.STYLE[run[0]["emotion"]][0]
        for x in run:
            out[x["id"]] = {"why": f"ровный набор серии {key}: один образец, одна инструкция, одни seed",
                            "emotion": run[0]["emotion"], "ref": ref, "indextts": {}, "run": key, "src_group": x["group"],
                            "breeze": {str(i + 1): {"instruct": instr, "cfg": 4.0, "seed": sd} for i, sd in enumerate(EVEN_SEEDS)}}
    return out


def redo_spec():
    p = HERE / "redo_act1.json"
    return json.loads(p.read_text(encoding="utf-8"))["lines"] if p.exists() else {}


def all_lines():
    """Реплики акта 1 и их копии в группе «Переделка» (со своими вариантами из redo_act1.json)."""
    lines = load_lines()
    by = {x["id"]: x for x in lines}
    out = []
    for group, title, spec_all in ((REDO, "Переделка", redo_spec()), (EVEN, "Похмелье: ровный набор", even_spec())):
        for h, spec in spec_all.items():
            if h in by:
                emo = spec.get("emotion", by[h]["emotion"])
                out.append({**by[h], "group": group, "group_title": title, "emotion": emo,
                            "ref_emotion": by[h]["ref_emotion"] if group == EVEN else emo, "why": spec["why"],
                            "redo": spec, "tag": SPECIAL[group]})
    return out + lines


def groups_order(lines):
    return list(dict.fromkeys(x["group"] for x in lines))


def model_variants(model, ln):
    if ln.get("redo"):
        return sorted(int(k) for k in ln["redo"].get(model, {}))
    if model == "breeze":
        return [1, 2]
    return [1, 2, 3] if ln["index_variants"] == 3 else [1, 3]


def vtag(ln):
    return ln.get("tag") or ("r" if ln.get("redo") else "v")


def redo_custom(vw, model, spec):
    """Параметры вариантов переделки для обёртки модели: пути образцов — абсолютные, текст с экранированием."""
    out = {}
    for k, c in spec.get(model, {}).items():
        c = dict(c)
        if "ref" in c:
            ref = vw / c.pop("ref")
            c["ref_wav"], c["ref_text"] = str(ref), ref.with_suffix(".txt").read_text(encoding="utf-8").strip()
        if "emo_ref" in c:
            c["emo_ref"] = str(vw / c["emo_ref"])
        out[k] = c
    return out


def wav_ok(path):
    """Файл есть и читается (прерванный прогон оставляет wav без заголовка — такой переделываем)."""
    try:
        with wave.open(str(path)) as w:
            return w.getnframes() > 0
    except (OSError, EOFError, wave.Error):
        return False


def cmd_gen(args):
    vw, models, act, gen = act1_paths()
    lines = all_lines()
    refs = {}
    for group in args.groups:
        todo = [x for x in lines if x["group"] == group]
        if group == EVEN and getattr(args, "src_groups", None):
            todo = [x for x in todo if x["redo"]["src_group"] in args.src_groups]
        for model in args.models:
            out = gen / group / model
            jobs = []
            for ln in todo:
                emo = (ln.get("ref_dir", "refs"), ln["ref_emotion"])
                refs.setdefault(emo, pick_ref(vw, ln))
                ks = [k for k in model_variants(model, ln) if not wav_ok(out / f"line{ln['id']}_v{k}.wav")]
                if ks:
                    ref = {k: v for k, v in refs[emo].items() if k != "ref_emo_used"}
                    job = {"id": ln["id"], "text": ln["text"], "instruct": ln["instruct"], "emo_vector": ln["emo_vector"],
                           "tags": ln["tags"], "variants": ks, **ref}
                    if ln.get("redo"):
                        base = vw / ln["redo"]["ref"]
                        job.update(ref_wav=str(base), ref_text=base.with_suffix(".txt").read_text(encoding="utf-8").strip(),
                                   custom=redo_custom(vw, model, ln["redo"]))
                    jobs.append(job)
            if not jobs:
                print(f"{group}/{model}: уже готово")
                continue
            out.mkdir(parents=True, exist_ok=True)
            jp = out / "jobs.json"
            jp.write_text(json.dumps({"variants": 2, "lines": jobs}, ensure_ascii=False, indent=1), encoding="utf-8")
            n = sum(len(j["variants"]) for j in jobs)
            print(f"{group}/{model}: {len(jobs)} реплик, {n} вариантов", flush=True)
            tag = f"_{len(list(out.glob('run*.log')))}"
            code, _s, _w = cm.run_model(model, jp, out, vw, models, tag=tag)
            if code != 0:
                sys.exit(f"{group}/{model}: модель упала, см. {out}")


# --- проверки и предотбор -----------------------------------------------------------------------

def audio_checks(path, text):
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    dur = len(x) / sr
    hop = int(sr * 0.02)
    fr = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)
    thr = max(-50.0, float(db.max()) - 40)
    voiced = np.where(db > thr)[0]
    probs = []
    words = len(text.split())
    expected = 0.34 * words + 0.6
    if not len(voiced):
        return dur, ["тишина"]
    speech = (voiced[-1] - voiced[0] + 1) * 0.02
    if speech < 0.45 * expected:
        probs.append(f"коротко ({speech:.1f} с на {words} слов)")
    if speech > 2.2 * expected + 1.0:
        probs.append(f"длинно ({speech:.1f} с на {words} слов)")
    gaps, run = [], 0
    for v in db[voiced[0]:voiced[-1] + 1] > thr:
        run = 0 if v else run + 1
        gaps.append(run)
    if max(gaps) * 0.02 > (PAUSE_MAX_ELLIPSIS if "..." in text or "…" in text else PAUSE_MAX):
        probs.append(f"пауза {max(gaps) * 0.02:.1f} с")
    if int((np.abs(x) >= 0.999).sum()) > 50:
        probs.append("клиппинг")
    if db[-3:].mean() > float(db.max()) - 10:      # конец на громкости середины слова, а не затухание
        probs.append("обрыв в конце")
    return dur, probs


def default_pick(cands, emotion="", tag="v"):
    """Предотбор ★. Выбор автора по главам 1–2: Breeze 40 из 41 (v1 19, v2 21), IndexTTS 1. Поэтому ★ — у самого
    похожего варианта Breeze без брака; IndexTTS — только если у Breeze брак; брак у всех — лучший из всех."""
    ok = [c for c in cands if not c["reject"]]
    pool = [c for c in ok if c["model"] == PREFERRED] or ok or cands
    if not pool:
        return ""
    c = max(pool, key=lambda c: c["sim"])
    # яркие эмоции (праздник, смех, флирт): IndexTTS, если похожесть не сильно ниже лучшей Breeze
    alt = [x for x in ok if x["model"] != PREFERRED]
    if emotion in VIVID and alt and c["model"] == PREFERRED:
        a = max(alt, key=lambda x: x["sim"])
        if a["sim"] >= c["sim"] - VIVID_SIM_GAP:
            c = a
    return f"{c['model']}_{tag}{c['k']}"


def cmd_score(args):
    vw, models, act, gen = act1_paths()
    lines = all_lines()
    for group in args.groups:
        todo = [x for x in lines if x["group"] == group]
        items, by_spk = [], {}
        for ln in todo:
            ref = pick_ref(vw, ln)["ref_wav"]
            for model in MODELS:
                for k in model_variants(model, ln):
                    w = gen / group / model / f"line{ln['id']}_v{k}.wav"
                    if wav_ok(w):
                        it = {"key": f"{ln['id']}|{model}|{k}", "wav": str(w), "text": ln["text"], "ref": ref}
                        items.append(it)
                        by_spk.setdefault(ln.get("speaker_key", "alfira"), (ln, []))[1].append(it)
        if not items:
            print(f"{group}: нечего оценивать")
            continue
        met = {}
        for key, (ln0, its) in by_spk.items():
            suffix = "" if key == "alfira" else f"_{key}"
            ij = gen / group / f"metrics_items{suffix}.json"
            mj = gen / group / f"metrics{suffix}.json"
            ij.write_text(json.dumps({"voice_set": speaker_voice_set(vw, ln0), "items": its,
                                      "cache": str(vw / "cache" / "metrics"), "names": NAMES},
                                     ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([str(models / cm.METRICS_PY), str(cm.TTS / "metrics.py"), str(ij), str(mj)], env=cm.model_env(vw),
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0:
                sys.exit(f"{group}: метрики упали\n{r.stdout[-2000:]}\n{r.stderr[-3000:]}")
            met.update({m["key"]: m for m in json.loads(mj.read_text(encoding="utf-8"))["items"]})
        score = {}
        for ln in todo:
            cands = []
            for it in (i for i in items if i["key"].startswith(ln["id"] + "|")):
                m = met[it["key"]]
                _id, model, k = it["key"].split("|")
                dur, probs = audio_checks(it["wav"], ln["text"])
                words = len(ln["text"].split())
                if m["wer"] > WER_MAX and (words > 6 or m["wer"] * words > 1.01):
                    probs.insert(0, f"WER {m['wer']:.2f}: «{m['asr']}»")
                cands.append({"model": model, "k": int(k), "wav": it["wav"], "dur": round(dur, 2), "wer": round(m["wer"], 3),
                              "sim": round(0.5 * m["sim_ecapa"] + 0.5 * m["sim_wavlm"], 4), "sim_ecapa": round(m["sim_ecapa"], 4),
                              "asr": m["asr"], "reject": probs})
            ok = [c for c in cands if not c["reject"]]
            score[ln["id"]] = {"cands": cands, "default": default_pick(cands, ln["emotion"], vtag(ln)),
                               "all_rejected": bool(cands) and not ok}
        (gen / group / "score.json").write_text(json.dumps(score, ensure_ascii=False, indent=1), encoding="utf-8")
        rej = sum(1 for s in score.values() for c in s["cands"] if c["reject"])
        tot = sum(len(s["cands"]) for s in score.values())
        print(f"{group}: {len(score)} реплик, вариантов {tot}, брак {rej}, у всех брак — "
              f"{sum(s['all_rejected'] for s in score.values())}")


# --- страница -----------------------------------------------------------------------------------

CSS = """
:root{--bg:#f7f5f2;--card:#fff;--ink:#1d1b19;--mute:#6b6560;--line:#e3ded8;--accent:#7a3b8f;--bad:#b3261e;--pick:#f1e8f5}
@media (prefers-color-scheme:dark){:root{--bg:#161416;--card:#211e22;--ink:#eee9ee;--mute:#a79fa8;--line:#3a343b;--accent:#c89ad8;--bad:#ff8a80;--pick:#2e2433}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,Segoe UI,sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:12px;flex-wrap:wrap;align-items:center}
header h1{font-size:17px;margin:0 12px 0 0}button{font:inherit;padding:6px 12px;border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:6px;cursor:pointer}
button.ghost{background:transparent;color:var(--accent)}nav{display:flex;gap:6px;flex-wrap:wrap}nav a{color:var(--accent);font-size:13px;text-decoration:none;border:1px solid var(--line);padding:2px 8px;border-radius:12px}
main{max-width:980px;margin:0 auto;padding:8px 16px 80px}h2{margin:28px 0 8px;font-size:18px}
.line{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:10px 0}
.en{font-weight:600;font-size:16px}.ru{color:var(--mute);font-style:italic}.meta{font-size:13px;color:var(--mute);margin:4px 0 8px}
.emo{display:inline-block;background:var(--accent);color:#fff;border-radius:6px;padding:1px 10px;margin-right:8px;font-size:15px;font-weight:700}
.remark{font-style:italic;margin:2px 0 6px;color:var(--ink)}
.spk{display:inline-block;background:var(--ink);color:var(--bg);border-radius:6px;padding:1px 10px;margin-right:6px;font-size:15px;font-weight:700}
h3{margin:18px 0 4px;font-size:16px}.hid{font-size:11px;color:var(--mute);margin-top:6px}
.opt{display:grid;grid-template-columns:22px 170px 1fr;gap:8px;align-items:start;padding:6px;border-radius:6px;border-top:1px solid var(--line)}
.opt:has(input:checked){background:var(--pick)}.opt label{font-size:14px;font-weight:600}.opt audio{width:100%;height:32px}
.how{font-size:14px;margin-top:2px}
.warn{color:var(--bad);font-size:13px}.ref{font-size:13px;color:var(--mute)}.ref audio{height:28px;vertical-align:middle;width:260px;max-width:60%}
textarea{width:100%;height:160px}#out{display:none;margin-top:8px}
.mline{background:var(--card);border:2px solid var(--accent);border-radius:10px;padding:12px 14px;margin:10px 0}
.cur{font-size:16px;margin:8px 0;padding:8px;background:var(--pick);border-radius:8px}.cur audio{width:100%;height:40px;margin-top:4px}
.mline.playing{box-shadow:0 0 0 3px var(--accent)}
@media (max-width:600px){.opt{grid-template-columns:22px 1fr}.opt audio{grid-column:1/-1}}
"""

JS = """
const KEY='alfira-voice-act1';
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function save(){try{const s={};document.querySelectorAll('.line input[type=radio]:checked').forEach(r=>{if(!r.defaultChecked)s[r.name]=r.value});localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
function restore(){const s=load();for(const [n,v] of Object.entries(s)){const r=document.querySelector(`.line input[name="${CSS.escape(n)}"][value="${CSS.escape(v)}"]`);if(r)r.checked=true}syncAll()}
function pick(name,val){const r=document.querySelector(`input[name="${CSS.escape(name)}"][value="${CSS.escape(val)}"]`);if(r)r.checked=true}
function curOf(m){const r=m.querySelector('input[type=radio]:checked');const cur=m.querySelector('.cur audio'),nm=m.querySelector('.curname');
 const a=r?r.closest('.opt').querySelector('audio'):null;if(a){if(cur.getAttribute('src')!==a.getAttribute('src'))cur.setAttribute('src',a.getAttribute('src'))}else{cur.removeAttribute('src')}
 nm.textContent=r?r.nextElementSibling.firstChild.textContent:'—'}
function syncAll(){document.querySelectorAll('.mline').forEach(m=>{const h=m.dataset.handle;const r=document.querySelector(`.line input[name="${CSS.escape(h)}"]:checked`);if(r)pick('m:'+h,r.value);curOf(m)})}
document.addEventListener('change',e=>{const r=e.target;if(r.type!=='radio')return;if(r.name.startsWith('m:')){pick(r.name.slice(2),r.value)}else{pick('m:'+r.name,r.value)}
 document.querySelectorAll('.mline').forEach(curOf)});
let queue=[];function stopAll(){queue=[];document.querySelectorAll('audio').forEach(a=>a.pause());document.querySelectorAll('.mline').forEach(m=>m.classList.remove('playing'))}
function playNext(){document.querySelectorAll('.mline').forEach(m=>m.classList.remove('playing'));const m=queue.shift();if(!m)return;const a=m.querySelector('.cur audio');
 if(!a.getAttribute('src')){playNext();return}m.classList.add('playing');m.scrollIntoView({block:'center',behavior:'smooth'});a.currentTime=0;a.onended=()=>{a.onended=null;setTimeout(playNext,400)};a.play()}
function playAll(){stopAll();queue=[...document.querySelectorAll('.mline')];playNext()}
function result(){const out=[];document.querySelectorAll('.line').forEach(d=>{const r=d.querySelector('input[type=radio]:checked');out.push(d.dataset.handle+'='+(r?r.value:'?'))});return out.join('\\n')}
async function copyChoice(){const t=result();const ta=document.getElementById('out');ta.value=t;ta.style.display='block';
 try{await navigator.clipboard.writeText(t);flash('Скопировано: '+t.split('\\n').length+' строк')}catch(e){ta.select();document.execCommand('copy');flash('Скопировано (выделено ниже)')}}
function flash(m){const f=document.getElementById('msg');f.textContent=m;setTimeout(()=>f.textContent='',4000)}
function resetAll(){try{localStorage.removeItem(KEY)}catch(e){}document.querySelectorAll('input[type=radio]').forEach(r=>r.checked=r.defaultChecked);syncAll()}
document.addEventListener('change',save);document.addEventListener('play',e=>{document.querySelectorAll('audio').forEach(a=>{if(a!==e.target)a.pause()})},true);
restore();
"""


def rel(p):
    """Путь для src: как есть, относительный; экранируются только " & < (с %-кодированием у автора не играло)."""
    return Path(p).as_posix().replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


VEC_NAMES = ["happy", "angry", "sad", "afraid", "disgusted", "melancholic", "surprised", "calm"]


def variant_how(model, k, ln, ref_name):
    """Как сделан вариант: эмоция образца, файл образца, инструкция или режим эмоции (run_breeze/run_indextts)."""
    emo = EMO_RU.get(ln["ref_emotion"], ln["ref_emotion"])
    src = f"образец «{emo}» ({ref_name})"
    if model == "breeze":
        if k == 1:
            return f"{src}; без инструкции — эмоция из образца (cfg 1)"
        return f"{src} + инструкция: “{ln['instruct']}” (cfg 4)"
    if k == 1:
        return f"{src}; эмоция из образца, emo_alpha 0.8"
    if k == 2:
        vec = ", ".join(f"{n} {v:g}" for n, v in zip(VEC_NAMES, ln["emo_vector"]) if v)
        return f"{src} — тембр; эмоция вектором: {vec}"
    return f"{src}; тембр и эмоция из образца, без отдельной эмоции"


def accepted_redo(vw, act):
    """handle → принятый вариант переделки (rK) по voice-work/game/voice.json, если он не снова в redo.txt."""
    meta_p = vw / GAME_DIR_NAME / "voice.json"
    if not meta_p.exists():
        return {}
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    redo_p = act / "redo.txt"
    again = set(redo_p.read_text(encoding="utf-8").split()) if redo_p.exists() else set()
    out = {}
    for h in redo_spec():
        m = meta.get(h)
        if m and str(m.get("variant", "")).startswith("r") and h not in again:
            out[h] = f"{m['model']}_{m['variant']}"
    return out


def even_run_best(gen, even):
    """Ключ серии → seed (1 или 2) с лучшей средней похожестью по репликам серии без брака."""
    p = gen / EVEN / "score.json"
    if not p.exists():
        return {}
    sc = json.loads(p.read_text(encoding="utf-8"))
    acc = {}
    for h, spec in even.items():
        for c in sc.get(h, {}).get("cands", []):
            if not c["reject"]:
                acc.setdefault(spec["run"], {}).setdefault(c["k"], []).append(c["sim"])
    return {run: max(ks, key=lambda k: (len(ks[k]), sum(ks[k]) / len(ks[k]))) for run, ks in acc.items()}


def special_cands(gen, group, h):
    """Варианты реплики h из особой группы (переделка, ровный набор) — с пометками для страницы."""
    p = gen / group / "score.json"
    if not p.exists():
        return []
    return [{**c, "_tag": SPECIAL[group], "_special": group}
            for c in json.loads(p.read_text(encoding="utf-8")).get(h, {}).get("cands", [])]


def ln_group(lines, h):
    return orig_line(lines, h)["group"]


def orig_line(lines, h):
    return next(x for x in lines if x["id"] == h and not x.get("redo"))


def current_choice(vw, h):
    meta_p = vw / GAME_DIR_NAME / "voice.json"
    m = json.loads(meta_p.read_text(encoding="utf-8")).get(h) if meta_p.exists() else None
    return f"{m['model']}_{m['variant'] if isinstance(m['variant'], str) else 'v' + str(m['variant'])}" if m else ""


def redo_how(model, k, ln):
    c = ln["redo"][model][str(k)]
    ref = Path(c.get("ref", ln["redo"]["ref"]))
    parts = [f"образец {ref.parent.name} ({ref.name[:9]}….wav)"]
    if c.get("text"):
        parts.append(f"текст: “{c['text']}”")
    if model == "breeze":
        parts.append(f"инструкция: “{c['instruct']}” (cfg {c.get('cfg', 4.0):g})")
    else:
        if c.get("emo_ref"):
            parts.append(f"эмоция из {Path(c['emo_ref']).parent.name} ({Path(c['emo_ref']).name[:9]}…), emo_alpha {c.get('emo_alpha', 0.8):g}")
        if c.get("emo_vector"):
            vec = ", ".join(f"{n} {v:g}" for n, v in zip(VEC_NAMES, c["emo_vector"]) if v)
            parts.append(f"вектор эмоций: {vec}, emo_alpha {c.get('emo_alpha', 1.0):g}")
    return "; ".join(parts)


def render_opts(h, opts, mirror=False):
    """Радиокнопки вариантов. Зеркало (блок «Похмелье») — свои name/id с префиксом m:, выбор синхронизирует JS."""
    name = f"m:{h}" if mirror else h
    idp = f"m_{h}" if mirror else h
    out = []
    for val, chk, label, sub, src, how, warn in opts:
        audio = f'<audio controls preload="none" src="{src}"></audio>' if src else ""
        howd = f'<div class="how">{html.escape(how)}</div>' if how else ""
        out.append(f'<div class="opt"><input type="radio" name="{name}" id="{idp}_{val}" value="{val}"{chk}>'
                   f'<label for="{idp}_{val}">{html.escape(label)}{"<br><small>" + sub + "</small>" if sub else ""}</label>'
                   f'<div>{audio}{howd}{warn}</div></div>')
    return "".join(out)


def cmd_page(_args):
    vw, models, act, gen = act1_paths()
    lines = all_lines()
    order = groups_order(lines)     # «Переделка» первой
    titles = {x["group"]: x["group_title"] for x in lines}
    ready = [g for g in order if (gen / g / "score.json").exists()]
    if not ready:
        sys.exit("нет оценённых групп (voice_act1.py score …)")
    PAGE_DIR.mkdir(parents=True, exist_ok=True)
    norm, body, nav = [], [], []
    refdir = PAGE_DIR / "_образцы"
    refdir.mkdir(exist_ok=True)
    ref_rel = {}
    total = 0
    chapters = [x for x in order if x not in SPECIAL]
    ready = [x for x in ready if x != EVEN]      # ровный набор — не группа, а варианты в карточках похмелья
    mirror = []                                  # (ln, s, folder) для блока «Похмелье»
    even = even_spec()
    run_best = even_run_best(gen, even)
    # переделка, которую автор уже принял (в voice.json выбран вариант rK): её карточка — снова в своей главе,
    # принятый вариант — в ней и выбран; «Переделка» на странице — только непринятые
    accepted = accepted_redo(vw, act)
    redo_ids = (set(redo_spec()) - set(accepted)) if REDO in ready else set()
    if REDO in ready and not redo_ids:
        ready = [x for x in ready if x != REDO]
    last_scene = ""
    for gi, g in enumerate(ready, 1):
        score = json.loads((gen / g / "score.json").read_text(encoding="utf-8"))
        num = 0 if g == REDO else chapters.index(g) + 1
        folder = f"{num:02d} " + re.sub(r'[<>:"/\|?*]', "", titles[g].split(".")[0]).strip()
        (PAGE_DIR / folder).mkdir(exist_ok=True)
        anchor = f"g{num:02d}"
        nav.append(f'<a href="#{anchor}">{html.escape(titles[g])}</a>')
        body.append(f'<h2 id="{anchor}">{html.escape(titles[g])}</h2>')
        for ln in (x for x in lines if x["group"] == g):
            s = score.get(ln["id"])
            if not s or not s["cands"]:
                continue
            if g != REDO and ln["id"] in redo_ids:
                continue                      # её карточка — в «Переделке»
            if g == REDO and ln["id"] in accepted:
                continue
            for c in s["cands"]:
                c["_tag"] = vtag(ln)
            s["default"] = default_pick(s["cands"], ln["emotion"], vtag(ln))
            if g != REDO and ln["id"] in accepted:
                rs = json.loads((gen / REDO / "score.json").read_text(encoding="utf-8")).get(ln["id"], {}).get("cands", [])
                val = accepted[ln["id"]]
                for c in rs:
                    if f"{c['model']}_r{c['k']}" == val:
                        s = {**s, "cands": s["cands"] + [{**c, "_tag": "r", "reject": [], "_accepted": True}]}
                s["default"] = val
            if g != REDO and ln["id"] in even:
                extra_c = special_cands(gen, EVEN, ln["id"])
                s = {**s, "cands": s["cands"] + extra_c}
                best_k = run_best.get(even[ln["id"]]["run"])
                if best_k and any(c["k"] == best_k and not c["reject"] for c in extra_c):
                    s["default"] = f"breeze_e{best_k}"       # ★ на ровный набор: один seed на всю серию

            if g == REDO:
                orig = (gen / ln_group(lines, ln["id"]) / "score.json")
                if orig.exists():
                    old = json.loads(orig.read_text(encoding="utf-8")).get(ln["id"], {}).get("cands", [])
                    for c in old:
                        c["_tag"] = "v"
                        c["_old"] = True
                    s = {**s, "cands": s["cands"] + old}
            # отмечен выбор автора (voice.json, если этот вариант есть в карточке), иначе предотбор ★
            picked = current_choice(vw, ln["id"]) if g != REDO else ""
            s = {**s, "checked": picked if picked and any(f"{c['model']}_{c['_tag']}{c['k']}" == picked
                                                          for c in s["cands"]) else s["default"]}
            total += 1
            spk = ln.get("speaker_key", "alfira")
            emo = ln["ref_emotion"] if spk == "alfira" else f"{spk}_{ln['ref_emotion']}"
            if emo not in ref_rel:
                ref = pick_ref(vw, ln)
                dst = refdir / f"{emo}.wav"
                norm.append([ref["ref_wav"], str(dst)])
                ref_rel[emo] = (f"_образцы/{emo}.wav", ref["ref_text"], Path(ref["ref_wav"]).name[:9] + "….wav")
            if g == TALKS and ln.get("scene_title") and ln["scene_title"] != last_scene:
                last_scene = ln["scene_title"]
                body.append(f'<h3>{html.escape(last_scene)}</h3>')
            short = ln["id"][:9]
            # у переделки показываем всё: на обрывках вроде «I - we -» Whisper ошибается чаще модели
            shown = ([c for c in s["cands"] if not c["reject"]] if not (s["all_rejected"] or ln.get("redo"))
                     else [c for c in s["cands"] if not (c.get("_old") and c["reject"])])
            dropped = [c for c in s["cands"] if c["reject"] and c not in shown]
            opts = []
            for c in sorted(shown, key=lambda c: (bool(c.get("_old")), c.get("_special") == EVEN, c["model"], c["k"])):
                val = f"{c['model']}_{c['_tag']}{c['k']}"
                name = f"{short}_{val}.wav"
                norm.append([c["wav"], str(PAGE_DIR / folder / name)])
                chk = " checked" if val == s["checked"] else ""
                warn = f'<div class="warn">{html.escape("; ".join(c["reject"]))}</div>' if c["reject"] else ""
                star = " ★" if val == s["default"] else ""
                how = variant_how(c["model"], c["k"], ln, ref_rel[emo][2])
                if c.get("_special") == EVEN:
                    how = "ровный набор: " + redo_how(c["model"], c["k"], {**ln, "redo": even[ln["id"]]})
                elif c.get("_accepted"):
                    how = "из переделки: " + redo_how(c["model"], c["k"], {**ln, "redo": redo_spec()[ln["id"]]})
                elif ln.get("redo") and not c.get("_old"):
                    how = redo_how(c["model"], c["k"], ln)
                elif c.get("_old"):
                    how = "прежний вариант: " + variant_how(c["model"], c["k"], {**ln, **orig_line(lines, ln["id"])},
                                                              ref_rel[emo][2])
                label = f"{TITLE[c['model']]} {c['_tag'] if c['_tag'] != 'v' else 'v'}{c['k']}"
                if c.get("_special") == EVEN:
                    label = f"{TITLE[c['model']]} ровный {c['k']}"
                opts.append((val, chk, label + star, f"похожесть {c['sim']:.3f}, {c['dur']:.1f} с",
                             rel(folder + "/" + name), how, warn))
            opts.append(("переделать", "", "переделать", "", "", "", ""))
            extra = f' · ещё {len(ln["handles"]) - 1} handle с тем же текстом' if len(ln["handles"]) > 1 else ""
            drop = (f'<div class="warn">отброшено {len(dropped)}: ' + html.escape("; ".join(
                f'{TITLE[c["model"]]} v{c["k"]} — {c["reject"][0]}' for c in dropped)) + "</div>") if dropped else ""
            allrej = '<div class="warn">у всех вариантов брак — выбран лучший из них</div>' if s["all_rejected"] else ""
            rp, rt, rn = ref_rel[emo]
            # ремарка сценария: note из сцены (как в design/dialogs) и откуда взята эмоция
            basis = ("по ремарке" if ln["why"].startswith("ремарка") else "по лицу в сценарии"
                     if ln["why"].startswith("лицо") else f"по сцене: {ln['why']}")
            remark = " · ".join(x for x in [f"ремарка: {ln['note']}" if ln["note"] else "ремарки нет",
                                            f"лицо: {ln['emo']}", f"эмоция {basis}"] if x)
            refemo = EMO_RU.get(ln["ref_emotion"], ln["ref_emotion"])
            who = f'<span class="spk">{html.escape(ln["speaker_name"])}</span>' if ln.get("speaker_name") else ""
            head = (f'<div class="en">{who}<span class="emo">{html.escape(EMO_RU.get(ln["emotion"], ln["emotion"]))}</span>'
                    f'{html.escape(ln["text"])}</div>'
                    f'<div class="remark">{html.escape(remark)}</div>'
                    f'<div class="ru">{html.escape(re.sub(r"<[^>]+>", "", ln["ru"]))}</div>'
                    f'<div class="ref">её образец «{html.escape(refemo)}» ({rn}): <audio controls preload="none" src="{rel(rp)}"></audio> '
                    f'«{html.escape(rt[:90])}»</div>')
            body.append(f'<div class="line" data-handle="{ln["id"]}">{head}{allrej}{render_opts(ln["id"], opts)}{drop}'
                        f'<div class="hid">{ln["id"]}{extra}</div></div>')
            if g != REDO and ln["emotion"] == EVEN_EMOTION:
                mirror.append((ln, head, opts))
    if mirror:
        cards = []
        for ln, head, opts in mirror:
            cards.append(f'<div class="mline" data-handle="{ln["id"]}">{head}'
                         f'<div class="cur"><b>сейчас выбран:</b> <span class="curname"></span><audio controls preload="none"></audio></div>'
                         f'{render_opts(ln["id"], opts, mirror=True)}</div>')
        body.insert(0, f'<h2 id="hang">{HANGOVER_BLOCK}: все реплики подряд, в порядке сцены</h2>'
                       f'<p class="meta">Выбор здесь и в карточке главы 5 — один и тот же (синхронизирован). «Ровный» — '
                       f'новые варианты Breeze: у всех реплик один образец, одна инструкция и одинаковые seed.</p>'
                       f'<button onclick="playAll()">Играть все по порядку</button> <button class="ghost" onclick="stopAll()">Стоп</button>'
                       + "".join(cards))
        nav.insert(0, f'<a href="#hang">{HANGOVER_BLOCK}</a>')
    nj = act / "page_normalize.json"
    todo = [p for p in norm if not Path(p[1]).exists() or Path(p[1]).stat().st_mtime < Path(p[0]).stat().st_mtime]
    nj.write_text(json.dumps(todo, ensure_ascii=False), encoding="utf-8")
    if todo:
        subprocess.run([str(models / cm.METRICS_PY), str(cm.TTS / "normalize.py"), str(nj)], env=cm.model_env(vw), check=True)
    pending = [titles[g] for g in order if g not in ready and g not in SPECIAL]
    note = (f"<p class='meta'>Ещё генерируются: {html.escape(', '.join(pending))}. Страница обновится.</p>" if pending else "")
    page = f"""<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Голос Альфиры, акт 1</title><style>{CSS}</style></head><body>
<header><h1>Голос Альфиры · акт 1</h1><button onclick="copyChoice()">Скопировать выбор</button>
<button class="ghost" onclick="resetAll()">Сбросить к предотбору</button><span id="msg" class="meta"></span><nav>{''.join(nav)}</nav></header>
<main><p class="meta">{total} реплик. Модели: Breeze TTS 2 и IndexTTS-2.5, без дообучения. По умолчанию выбран предотбор ★:
самый похожий на её голос вариант без брака (брак — ошибки распознавания Whisper, обрывы, длина не по тексту). «Её образец» —
её реплика из игры, по которой модель взяла эмоцию и тембр. Выбор запоминается в браузере; «Скопировать выбор» даёт строки
<code>handle=вариант</code> — их нужно вставить в чат.</p>{note}
<textarea id="out" readonly></textarea>
{''.join(body)}</main><script>{JS}</script></body></html>"""
    (PAGE_DIR / "index.html").write_text(page, encoding="utf-8")
    print(f"страница: {total} реплик, групп {len(ready)} из {len(order)} → {PAGE_DIR / 'index.html'}")


def cmd_pick(args):
    """Выбор автора (строки handle=вариант, как даёт «Скопировать выбор») → voice-work/game/<handle>.wav.

    Файл — выбранный вариант, приведённый к 48 кГц моно 16 бит (tts/normalize.py): такой берёт game_voice.py.
    Одинаковый текст в разных сценах — один звук на все его handle. «переделать» — в voice-work/act1/redo.txt.
    voice-work/game/voice.json: handle → файл, длина, модель, вариант, группа, говорящий (для build_pak --voice clone;
    говорящего и приоритет VoiceMeta сборка берёт из сцен, speaker_uuid здесь — для справки)."""
    vw, models, act, gen = act1_paths()
    lines = {x["id"]: x for x in load_lines()}
    game = vw / GAME_DIR_NAME
    game.mkdir(parents=True, exist_ok=True)
    meta_p = game / "voice.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    redo_p = act / "redo.txt"
    redo = set(redo_p.read_text(encoding="utf-8").split()) if redo_p.exists() else set()
    jobs, chosen, bad = [], [], []
    for f in args.files:
        for row in Path(f).read_text(encoding="utf-8-sig").splitlines():
            if "=" not in row.strip():
                continue
            h, v = (x.strip() for x in row.split("=", 1))
            ln = lines.get(h)
            if ln is None:
                bad.append(f"{h}: нет в lines.json")
                continue
            if v == "переделать":
                redo.add(h)
                continue
            m = re.fullmatch(r"(breeze|indextts)_([vre])(\d)", v)
            # r — вариант из «Переделки», e — из «ровного набора»
            folder = {"r": REDO, "e": EVEN}.get(m.group(2), ln["group"]) if m else ln["group"]
            src = gen / folder / m.group(1) / f"line{h}_v{m.group(3)}.wav" if m else None
            if not src or not wav_ok(src):
                bad.append(f"{h}={v}: нет файла")
                continue
            redo.discard(h)
            for hh in ln["handles"]:
                jobs.append([str(src), str(game / f"{hh}.wav")])
                chosen.append((hh, m.group(1), f"{m.group(2)}{m.group(3)}", ln["group"], h,
                               ln.get("speaker_uuid") or ALFIRA_UUID))
    if jobs:
        nj = act / "pick_normalize.json"
        nj.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
        subprocess.run([str(models / cm.METRICS_PY), str(cm.TTS / "normalize.py"), str(nj)], env=cm.model_env(vw), check=True)
    for hh, model, k, group, h, spk in chosen:
        with wave.open(str(game / f"{hh}.wav")) as w:
            length = w.getnframes() / w.getframerate()
        meta[hh] = {"file": f"{hh}.wav", "seconds": round(length, 3), "model": model, "variant": k, "group": group,
                    "text_handle": h, "speaker_uuid": spk}
    meta_p.write_text(json.dumps(dict(sorted(meta.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    redo_p.write_text("\n".join(sorted(redo)) + ("\n" if redo else ""), encoding="utf-8")
    print(f"выбрано {len({c[4] for c in chosen})} реплик → {len(chosen)} handle в {game}; переделать: {len(redo)}; "
          f"всего в voice.json: {len(meta)}")
    for b in bad:
        print("  !", b)


def cmd_all(args):
    lines = load_lines()
    for g in [x for x in groups_order(lines) if x not in SPECIAL]:
        if args.skip_done and (act1_paths()[3] / g / "score.json").exists():
            continue
        cmd_gen(argparse.Namespace(groups=[g], models=list(MODELS)))
        if g in EVEN_GROUPS:
            cmd_gen(argparse.Namespace(groups=[EVEN], models=["breeze"], src_groups=[g]))
        cmd_score(argparse.Namespace(groups=[g]))
        if g in EVEN_GROUPS:
            cmd_score(argparse.Namespace(groups=[EVEN]))
        cmd_page(None)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("groups", nargs="+")
    g.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    s = sub.add_parser("score")
    s.add_argument("groups", nargs="+")
    sub.add_parser("page")
    a = sub.add_parser("all")
    a.add_argument("--skip-done", action="store_true", default=True)
    k = sub.add_parser("pick")
    k.add_argument("files", nargs="+", help="файлы с выбором автора: строки handle=вариант")
    args = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score, "page": cmd_page, "all": cmd_all, "pick": cmd_pick}[args.cmd](args)


if __name__ == "__main__":
    main()
