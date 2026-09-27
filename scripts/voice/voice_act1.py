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
         "Gale", "Halsin", "Volo", "Kagha", "Tav", "Faerûn", "Milil", "Mystra", "Ikaron", "Asharak", "Quil", "Rolan"]


def act1_paths():
    vw, models, _comp, _work = cm.paths()
    return vw, models, vw / "act1", vw / "act1" / "gen"


def load_lines():
    vw, _m, act, _g = act1_paths()
    return json.loads((act / "lines.json").read_text(encoding="utf-8"))


REDO = "_redo"   # группа «Переделка»: реплики из redo_act1.json, варианты breeze_rK / indextts_rK
# эмоции, где автор на празднике выбирал IndexTTS («на живых и пьяных репликах он сильнее»)
VIVID = {"laugh", "drunk", "excited", "flirty", "teasing", "embarrassed", "tearful"}
VIVID_SIM_GAP = 0.03   # ★ на IndexTTS, если его похожесть ниже лучшей Breeze не больше чем на столько


def redo_spec():
    p = HERE / "redo_act1.json"
    return json.loads(p.read_text(encoding="utf-8"))["lines"] if p.exists() else {}


def all_lines():
    """Реплики акта 1 и их копии в группе «Переделка» (со своими вариантами из redo_act1.json)."""
    lines = load_lines()
    by = {x["id"]: x for x in lines}
    out = []
    for h, spec in redo_spec().items():
        if h in by:
            out.append({**by[h], "group": REDO, "group_title": "Переделка", "emotion": spec.get("emotion", by[h]["emotion"]),
                        "ref_emotion": spec.get("emotion", by[h]["ref_emotion"]), "why": spec["why"], "redo": spec})
    return out + lines


def groups_order(lines):
    return list(dict.fromkeys(x["group"] for x in lines))


def model_variants(model, ln):
    if ln.get("redo"):
        return sorted(int(k) for k in ln["redo"][model])
    if model == "breeze":
        return [1, 2]
    return [1, 2, 3] if ln["index_variants"] == 3 else [1, 3]


def vtag(ln):
    return "r" if ln.get("redo") else "v"


def redo_custom(vw, model, spec):
    """Параметры вариантов переделки для обёртки модели: пути образцов — абсолютные, текст с экранированием."""
    out = {}
    for k, c in spec[model].items():
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
        for model in args.models:
            out = gen / group / model
            jobs = []
            for ln in todo:
                emo = ln["ref_emotion"]
                refs.setdefault(emo, cm.pick_ref(vw, emo))
                ks = [k for k in model_variants(model, ln) if not wav_ok(out / f"line{ln['id']}_v{k}.wav")]
                if ks:
                    job = {"id": ln["id"], "text": ln["text"], "instruct": ln["instruct"], "emo_vector": ln["emo_vector"],
                           "tags": ln["tags"], "variants": ks, **refs[emo]}
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
        items = []
        for ln in todo:
            ref = cm.pick_ref(vw, ln["ref_emotion"])["ref_wav"]
            for model in MODELS:
                for k in model_variants(model, ln):
                    w = gen / group / model / f"line{ln['id']}_v{k}.wav"
                    if wav_ok(w):
                        items.append({"key": f"{ln['id']}|{model}|{k}", "wav": str(w), "text": ln["text"], "ref": ref})
        if not items:
            print(f"{group}: нечего оценивать")
            continue
        ij = gen / group / "metrics_items.json"
        mj = gen / group / "metrics.json"
        ij.write_text(json.dumps({"voice_set": cm.voice_set(vw), "items": items, "cache": str(vw / "cache" / "metrics"),
                                  "names": NAMES},
                                 ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([str(models / cm.METRICS_PY), str(cm.TTS / "metrics.py"), str(ij), str(mj)], env=cm.model_env(vw),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            sys.exit(f"{group}: метрики упали\n{r.stdout[-2000:]}\n{r.stderr[-3000:]}")
        met = {m["key"]: m for m in json.loads(mj.read_text(encoding="utf-8"))["items"]}
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
.remark{font-style:italic;margin:2px 0 6px;color:var(--ink)}.hid{font-size:11px;color:var(--mute);margin-top:6px}
.opt{display:grid;grid-template-columns:22px 170px 1fr;gap:8px;align-items:start;padding:6px;border-radius:6px;border-top:1px solid var(--line)}
.opt:has(input:checked){background:var(--pick)}.opt label{font-size:14px;font-weight:600}.opt audio{width:100%;height:32px}
.how{font-size:14px;margin-top:2px}
.warn{color:var(--bad);font-size:13px}.ref{font-size:13px;color:var(--mute)}.ref audio{height:28px;vertical-align:middle;width:260px;max-width:60%}
textarea{width:100%;height:160px}#out{display:none;margin-top:8px}
@media (max-width:600px){.opt{grid-template-columns:22px 1fr}.opt audio{grid-column:1/-1}}
"""

JS = """
const KEY='alfira-voice-act1';
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return {}}}
function save(){try{const s={};document.querySelectorAll('input[type=radio]:checked').forEach(r=>{if(!r.defaultChecked)s[r.name]=r.value});localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
function restore(){const s=load();for(const [n,v] of Object.entries(s)){const r=document.querySelector(`input[name="${n}"][value="${v}"]`);if(r)r.checked=true}}
function result(){const out=[];document.querySelectorAll('.line').forEach(d=>{const r=d.querySelector('input[type=radio]:checked');out.push(d.dataset.handle+'='+(r?r.value:'?'))});return out.join('\\n')}
async function copyChoice(){const t=result();const ta=document.getElementById('out');ta.value=t;ta.style.display='block';
 try{await navigator.clipboard.writeText(t);flash('Скопировано: '+t.split('\\n').length+' строк')}catch(e){ta.select();document.execCommand('copy');flash('Скопировано (выделено ниже)')}}
function flash(m){const f=document.getElementById('msg');f.textContent=m;setTimeout(()=>f.textContent='',4000)}
function resetAll(){try{localStorage.removeItem(KEY)}catch(e){}document.querySelectorAll('input[type=radio]').forEach(r=>r.checked=r.defaultChecked)}
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
    for gi, g in enumerate(ready, 1):
        score = json.loads((gen / g / "score.json").read_text(encoding="utf-8"))
        folder = f"{order.index(g) + 1:02d} " + re.sub(r'[<>:"/\|?*]', "", titles[g].split(".")[0]).strip()
        (PAGE_DIR / folder).mkdir(exist_ok=True)
        anchor = f"g{order.index(g) + 1:02d}"
        nav.append(f'<a href="#{anchor}">{html.escape(titles[g])}</a>')
        body.append(f'<h2 id="{anchor}">{html.escape(titles[g])}</h2>')
        for ln in (x for x in lines if x["group"] == g):
            s = score.get(ln["id"])
            if not s or not s["cands"]:
                continue
            s["default"] = default_pick(s["cands"], ln["emotion"], vtag(ln))
            total += 1
            emo = ln["ref_emotion"]
            if emo not in ref_rel:
                ref = cm.pick_ref(vw, emo)
                dst = refdir / f"{emo}.wav"
                norm.append([ref["ref_wav"], str(dst)])
                ref_rel[emo] = (f"_образцы/{emo}.wav", ref["ref_text"], Path(ref["ref_wav"]).name[:9] + "….wav")
            short = ln["id"][:9]
            # у переделки показываем всё: на обрывках вроде «I - we -» Whisper ошибается чаще модели
            shown = ([c for c in s["cands"] if not c["reject"]] if not (s["all_rejected"] or ln.get("redo"))
                     else s["cands"])
            dropped = [c for c in s["cands"] if c["reject"] and c not in shown]
            opts = []
            for c in sorted(shown, key=lambda c: (c["model"], c["k"])):
                val = f"{c['model']}_{vtag(ln)}{c['k']}"
                name = f"{short}_{val}.wav"
                norm.append([c["wav"], str(PAGE_DIR / folder / name)])
                chk = " checked" if val == s["default"] else ""
                warn = f'<div class="warn">{html.escape("; ".join(c["reject"]))}</div>' if c["reject"] else ""
                star = " ★" if val == s["default"] else ""
                how = variant_how(c["model"], c["k"], ln, ref_rel[emo][2])
                if ln.get("redo"):
                    how = redo_how(c["model"], c["k"], ln)
                opts.append(f'<div class="opt"><input type="radio" name="{ln["id"]}" id="{ln["id"]}_{val}" value="{val}"{chk}>'
                            f'<label for="{ln["id"]}_{val}">{TITLE[c["model"]]} v{c["k"]}{star}<br>'
                            f'<small>похожесть {c["sim"]:.3f}, {c["dur"]:.1f} с</small></label>'
                            f'<div><audio controls preload="none" src="{rel(folder + "/" + name)}"></audio>'
                            f'<div class="how">{html.escape(how)}</div>{warn}</div></div>')
            opts.append(f'<div class="opt"><input type="radio" name="{ln["id"]}" id="{ln["id"]}_redo" value="переделать">'
                        f'<label for="{ln["id"]}_redo">переделать</label><div></div></div>')
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
            refemo = EMO_RU.get(emo, emo)
            body.append(
                f'<div class="line" data-handle="{ln["id"]}">'
                f'<div class="en"><span class="emo">{html.escape(EMO_RU.get(ln["emotion"], ln["emotion"]))}</span>'
                f'{html.escape(ln["text"])}</div>'
                f'<div class="remark">{html.escape(remark)}</div>'
                f'<div class="ru">{html.escape(re.sub(r"<[^>]+>", "", ln["ru"]))}</div>'
                f'<div class="ref">её образец «{html.escape(refemo)}» ({rn}): <audio controls preload="none" src="{rel(rp)}"></audio> '
                f'«{html.escape(rt[:90])}»</div>'
                f'{allrej}{"".join(opts)}{drop}<div class="hid">{ln["id"]}{extra}</div></div>')
    nj = act / "page_normalize.json"
    todo = [p for p in norm if not Path(p[1]).exists() or Path(p[1]).stat().st_mtime < Path(p[0]).stat().st_mtime]
    nj.write_text(json.dumps(todo, ensure_ascii=False), encoding="utf-8")
    if todo:
        subprocess.run([str(models / cm.METRICS_PY), str(cm.TTS / "normalize.py"), str(nj)], env=cm.model_env(vw), check=True)
    pending = [titles[g] for g in order if g not in ready]
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
    voice-work/game/voice.json: handle → файл, длина, модель, вариант, группа (для build_pak --voice clone)."""
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
            m = re.fullmatch(r"(breeze|indextts)_([vr])(\d)", v)
            folder = REDO if m and m.group(2) == "r" else ln["group"]      # r — вариант из «Переделки»
            src = gen / folder / m.group(1) / f"line{h}_v{m.group(3)}.wav" if m else None
            if not src or not wav_ok(src):
                bad.append(f"{h}={v}: нет файла")
                continue
            redo.discard(h)
            for hh in ln["handles"]:
                jobs.append([str(src), str(game / f"{hh}.wav")])
                chosen.append((hh, m.group(1), f"{m.group(2)}{m.group(3)}", ln["group"], h))
    if jobs:
        nj = act / "pick_normalize.json"
        nj.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
        subprocess.run([str(models / cm.METRICS_PY), str(cm.TTS / "normalize.py"), str(nj)], env=cm.model_env(vw), check=True)
    for hh, model, k, group, h in chosen:
        with wave.open(str(game / f"{hh}.wav")) as w:
            length = w.getnframes() / w.getframerate()
        meta[hh] = {"file": f"{hh}.wav", "seconds": round(length, 3), "model": model, "variant": k, "group": group,
                    "text_handle": h}
    meta_p.write_text(json.dumps(dict(sorted(meta.items())), ensure_ascii=False, indent=1), encoding="utf-8")
    redo_p.write_text("\n".join(sorted(redo)) + ("\n" if redo else ""), encoding="utf-8")
    print(f"выбрано {len({c[4] for c in chosen})} реплик → {len(chosen)} handle в {game}; переделать: {len(redo)}; "
          f"всего в voice.json: {len(meta)}")
    for b in bad:
        print("  !", b)


def cmd_all(args):
    lines = load_lines()
    for g in [x for x in groups_order(lines) if x != REDO]:
        if args.skip_done and (act1_paths()[3] / g / "score.json").exists():
            continue
        cmd_gen(argparse.Namespace(groups=[g], models=list(MODELS)))
        cmd_score(argparse.Namespace(groups=[g]))
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
