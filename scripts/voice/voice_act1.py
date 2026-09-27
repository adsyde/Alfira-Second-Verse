#!/usr/bin/env python3
"""Озвучка новых реплик Альфиры акта 1 выбранными моделями и страница для выбора дублей.

Решение автора (2026-09-27, слепое сравнение): Breeze TTS 2 + IndexTTS-2.5, без дообучения.

  python scripts/voice/list_lines.py                         # voice-work/act1/lines.json
  python scripts/voice/voice_act1.py gen ch01_first_night ch02_lute   # генерация групп
  python scripts/voice/voice_act1.py score ch01_first_night ch02_lute # метрики и предотбор
  python scripts/voice/voice_act1.py page                    # страница по всему, что оценено
  python scripts/voice/voice_act1.py all                     # все группы по очереди: gen → score → page

На реплику: Breeze — 2 варианта (v1 клон по образцу эмоции, v2 то же + инструкция подачи, cfg 4;
у похмелья инструкция «hungover, groggy» поверх образца «усталость»); IndexTTS — 2 (v1 эмоция из
образца, v3 без отдельной эмоции, другой seed), для смеха, флирта и воодушевления — 3 (+ v2 вектор эмоций).
Образец (он же тембр) — лучший фрагмент voice-work/refs/<эмоция>/ (как в compare_models.py).

Предотбор: брак отбрасывается — WER Whisper > 0,15 (у реплик до 6 слов — больше одного слова ошибки),
длина не по тексту, клиппинг, обрыв в конце, пауза длиннее 2 с (3 с, если в тексте «...»); имена мира
(NAMES) подсказываются Whisper и не считаются ошибкой. Из остальных по умолчанию выбран
самый похожий на неё (ECAPA + WavLM к центру её голоса). Если брак у всех — выбран лучший из брака,
с пометкой.

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
from urllib.parse import quote

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
from common import enable_utf8_stdout  # noqa: E402
import compare_models as cm  # noqa: E402

enable_utf8_stdout()

MODELS = ("breeze", "indextts")
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


def groups_order(lines):
    return list(dict.fromkeys(x["group"] for x in lines))


def model_variants(model, ln):
    if model == "breeze":
        return [1, 2]
    return [1, 2, 3] if ln["index_variants"] == 3 else [1, 3]


def cmd_gen(args):
    vw, models, act, gen = act1_paths()
    lines = load_lines()
    refs = {}
    for group in args.groups:
        todo = [x for x in lines if x["group"] == group]
        for model in args.models:
            out = gen / group / model
            jobs = []
            for ln in todo:
                emo = ln["ref_emotion"]
                refs.setdefault(emo, cm.pick_ref(vw, emo))
                ks = [k for k in model_variants(model, ln) if not (out / f"line{ln['id']}_v{k}.wav").exists()]
                if ks:
                    jobs.append({"id": ln["id"], "text": ln["text"], "instruct": ln["instruct"], "emo_vector": ln["emo_vector"],
                                 "tags": ln["tags"], "variants": ks, **refs[emo]})
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


def cmd_score(args):
    vw, models, act, gen = act1_paths()
    lines = load_lines()
    for group in args.groups:
        todo = [x for x in lines if x["group"] == group]
        items = []
        for ln in todo:
            ref = cm.pick_ref(vw, ln["ref_emotion"])["ref_wav"]
            for model in MODELS:
                for k in model_variants(model, ln):
                    w = gen / group / model / f"line{ln['id']}_v{k}.wav"
                    if w.exists():
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
            pick = max(ok or cands, key=lambda c: c["sim"]) if cands else None
            score[ln["id"]] = {"cands": cands, "default": f"{pick['model']}_v{pick['k']}" if pick else "",
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
.en{font-weight:600}.ru{color:var(--mute);font-style:italic}.meta{font-size:13px;color:var(--mute);margin:4px 0 8px}
.emo{display:inline-block;background:var(--pick);color:var(--accent);border-radius:10px;padding:0 8px;margin-right:6px}
.opt{display:grid;grid-template-columns:22px 150px 1fr;gap:8px;align-items:center;padding:4px 6px;border-radius:6px}
.opt:has(input:checked){background:var(--pick)}.opt label{font-size:13px}.opt audio{width:100%;height:32px}
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
    return "/".join(quote(part) for part in Path(p).as_posix().split("/"))


def cmd_page(_args):
    vw, models, act, gen = act1_paths()
    lines = load_lines()
    order = groups_order(lines)
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
            total += 1
            emo = ln["ref_emotion"]
            if emo not in ref_rel:
                ref = cm.pick_ref(vw, emo)
                dst = refdir / f"{emo}.wav"
                norm.append([ref["ref_wav"], str(dst)])
                ref_rel[emo] = (f"_образцы/{emo}.wav", ref["ref_text"])
            short = ln["id"][:9]
            shown = [c for c in s["cands"] if not c["reject"]] if not s["all_rejected"] else s["cands"]
            dropped = [c for c in s["cands"] if c["reject"] and c not in shown]
            opts = []
            for c in sorted(shown, key=lambda c: (c["model"], c["k"])):
                val = f"{c['model']}_v{c['k']}"
                name = f"{short}_{val}.wav"
                norm.append([c["wav"], str(PAGE_DIR / folder / name)])
                chk = " checked" if val == s["default"] else ""
                warn = f'<div class="warn">{html.escape("; ".join(c["reject"]))}</div>' if c["reject"] else ""
                star = " ★" if val == s["default"] else ""
                opts.append(f'<div class="opt"><input type="radio" name="{ln["id"]}" id="{ln["id"]}_{val}" value="{val}"{chk}>'
                            f'<label for="{ln["id"]}_{val}">{TITLE[c["model"]]} v{c["k"]}{star}<br>'
                            f'<small>похожесть {c["sim"]:.3f}, {c["dur"]:.1f} с</small></label>'
                            f'<div><audio controls preload="none" src="{rel(folder + "/" + name)}"></audio>{warn}</div></div>')
            opts.append(f'<div class="opt"><input type="radio" name="{ln["id"]}" id="{ln["id"]}_redo" value="переделать">'
                        f'<label for="{ln["id"]}_redo">переделать</label><div></div></div>')
            extra = f' · ещё {len(ln["handles"]) - 1} handle с тем же текстом' if len(ln["handles"]) > 1 else ""
            drop = (f'<div class="warn">отброшено {len(dropped)}: ' + html.escape("; ".join(
                f'{TITLE[c["model"]]} v{c["k"]} — {c["reject"][0]}' for c in dropped)) + "</div>") if dropped else ""
            allrej = '<div class="warn">у всех вариантов брак — выбран лучший из них</div>' if s["all_rejected"] else ""
            rp, rt = ref_rel[emo]
            body.append(
                f'<div class="line" data-handle="{ln["id"]}"><div class="en">{html.escape(ln["text"])}</div>'
                f'<div class="ru">{html.escape(re.sub(r"<[^>]+>", "", ln["ru"]))}</div>'
                f'<div class="meta"><span class="emo">{html.escape(EMO_RU.get(ln["emotion"], ln["emotion"]))}</span>'
                f'{html.escape(ln["note"] or "")} <code>{ln["id"]}</code>{extra}</div>'
                f'<div class="ref">её образец: <audio controls preload="none" src="{rel(rp)}"></audio> «{html.escape(rt[:90])}»</div>'
                f'{allrej}{"".join(opts)}{drop}</div>')
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


def cmd_all(args):
    lines = load_lines()
    for g in groups_order(lines):
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
    args = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score, "page": cmd_page, "all": cmd_all}[args.cmd](args)


if __name__ == "__main__":
    main()
