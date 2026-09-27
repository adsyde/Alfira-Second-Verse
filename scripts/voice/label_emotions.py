#!/usr/bin/env python3
"""Размечает реплики Альфиры по эмоциям и собирает библиотеку референсов для клонирования голоса.

Для каждого handle из voice-work/dataset/metadata.csv (его делает extract_voice.py):
  - узел диалога игры, где его произносит Альфира: имя диалога, акт, ID узла;
  - ремарки актрисе и постановщику из editorData узла: VOContext (прямая ремарка актрисе,
    «embarrassed - trying to find the right words»), NodeContext, CinematicNodeContext,
    InternalNodeContext, stateContext, поля Emotion / Attitude; синопсис диалога;
  - эмоции её лица в таймлайне на этой реплике: TLEmotionEvent её актёра в окне её TLVoice
    (так же их находит scripts/dialogs/staging.py → voice_window), через bg3moddinglib;
  - проверка звука: пик, клиппинг, тишина по краям, уровень фона между словами.

По ремаркам и эмоциям реплика получает категорию (CATEGORIES, первая совпавшая по самому
точному источнику) и список всех совпавших. Исключаются из референсов: пение и строки,
где пение переходит в речь, рыдания, короткие выкрики, «Разговор с мёртвыми», повторы
текста (canon §8).

Результат (всё в voice-work/, в git не попадает):
  dataset/labels.csv                 — вся разметка, по строке на handle;
  refs/<категория>/<handle>.wav|.txt — лучшие чистые фрагменты 3–12 с (края тишины подрезаны),
  refs/<категория>/index.csv, refs/README.txt — сводка;
  (реплики из holdout.json — отложенная выборка — не попадают ни в референсы, ни в датасет)
  dataset/finetune/                  — ровная речь для дообучения: wav + списки в форматах моделей.

  python scripts/voice/label_emotions.py
  python scripts/voice/label_emotions.py --no-timeline     # без bg3moddinglib (только ремарки)
  python scripts/voice/label_emotions.py --refs-per-cat 10
  python scripts/voice/label_emotions.py --speaker 23129d6c-8d39-4a4c-a4f6-cfc6637b597c --name lakrissa   # NPC:
      датасет voice-work/dataset_<guid[:8]>/ (extract_voice.py --speaker), образцы voice-work/refs_<имя>/, без дообучения
"""
import argparse
import csv
import json
import re
import shutil
import sys
import wave
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dialogs"))
from common import config, enable_utf8_stdout, game_data_dir, resolve  # noqa: E402
from gamedb import ALFIRA, text  # noqa: E402

enable_utf8_stdout()

# Категории: (папка, по-русски, регулярка по ремаркам на английском). Порядок — приоритет:
# при нескольких совпадениях в одном источнике главной становится первая по списку.
CATEGORIES = [
    ("singing", "пение", r"$^"),                   # определяется отдельно: is_singing()
    ("whisper", "шёпот, тихо", r"whisper|hushed|under (?:her|your|his) breath|murmur|\bquietly\b|\bsoftly\b"),
    # в её банке нет ремарок «пьяная»; сюда же попадают весёлые реплики праздника (PARTY_TIPSY)
    ("drunk", "навеселе (праздник)",r"drunk|tipsy|\bmerry\b|slurr|intoxicat|booz|wasted|sloshed"),
    ("hungover", "похмелье", r"hung ?over|hangover"),
    ("laugh", "смех, веселье", r"laugh|giggl|chuckl|amused|snort|\bgrin"),
    ("embarrassed", "смущение", r"embarrass|\bshy\b|shyly|bashful|blush|fluster|awkward|sheepish|self-conscious|coy"),
    ("flirty", "флирт, нежность", r"flirt|seduct|tender|affection|loving|\bfond|intimate|sweetly|longing|smitten"),
    ("tearful", "сквозь слёзы", r"\bsob|crying|\bcries\b|\bcry\b|in tears|brink of tears|tearful|tearing up|choked|weeping|\bweeps?\b"),
    ("teasing", "подначка, ирония", r"teas|sarcas|playful|mock|joking|\bjokes?\b|\bwry|deadpan|banter|cheeky"),
    ("angry", "злость, раздражение", r"angry|anger|furious|snap|irritat|annoy|frustrat|\brage|hostile|bitter|scoff|indignant|outrag|exasperat|disgust"),
    ("fear", "страх", r"\bfear|afraid|scared|terrif|panic|nervous|anxious|horrif|\bshock|frighten|dread"),
    ("sad", "грусть, горе", r"\bsad|grief|griev|mourn|heartbroken|upset|dejected|despair|\blost\b|melanchol|sorrow|somber|sombre|downcast|hopeless|defeated|ashamed|failure"),
    ("tired", "усталость", r"\btired|exhaust|weary|end of (?:my|her) rope|drained|worn out"),
    ("excited", "воодушевление", r"excit|enthusias|thrill|eager|delight|elat|\bjoy|ecstatic|energ|inspired|triumph|passion|\bproud|pride|confident|determin|hopeful|cheer|happ"),
    ("grateful", "благодарность, тепло", r"grateful|gratitude|thank|relie[fv]|warm|reassur|kind|gentle|comfort|sympath|concern"),
    ("surprise", "удивление", r"surpris|startl|gasp|taken aback|astonish"),
    ("neutral", "нейтраль", r"$^"),
]
CAT_RE = [(slug, re.compile(rx, re.I)) for slug, _, rx in CATEGORIES]
CAT_RU = {slug: ru for slug, ru, _ in CATEGORIES}
# Поле Emotion узла (редактор Larian) → категория
EDITOR_EMOTION = {"Sadness": "sad", "Happiness": "excited", "Anger": "angry", "Fear": "fear", "Surprise": "surprise",
                  "Coyness": "embarrassed", "Determination": "excited", "Disgust": "angry", "Pleading": "sad",
                  "Arrogance": "teasing"}
# Коды эмоций лица (Public/Shared/Animation/Emotions.lsf, как в scripts/dialogs/dsl.py)
FACE = {1: "neutral", 2: "happy", 4: "thinking", 8: "angry", 16: "fear", 32: "sad", 64: "surprise",
        128: "disgust", 256: "sleeping", 512: "dead", 1024: "confusion", 2048: "pain"}
FACE_CAT = {"happy": "excited", "angry": "angry", "fear": "fear", "sad": "sad", "surprise": "surprise", "disgust": "angry"}
# Источники ремарок по убыванию точности: прямая ремарка актрисе → узел → сцена → диалог целиком
SOURCES = ("VOContext", "VOContextAfter", "NodeContext", "stateContext", "CinematicNodeContext", "InternalNodeContext")

# canon §8: строки, где пение переходит в речь (по началу handle), и декламация стихов на празднике —
# это речь, хотя в тексте стихи
MIXED_SINGING = ("hd99e112c", "h7eeb0097", "he4c8a05a")
DECLAMATION = ("h8f83a60d", "had48b82b", "h894acf1e", "h59f26c5a", "h25c154c1")
# строки «Плача рассвета» (The Weeping Dawn): по ним узнаётся пение вне DEN_TieflingBard_AD_FullSong
LYRICS = re.compile(r"words of mine|last light|reminds? me of your grace|moon\. sun|dance upon the stars|"
                    r"faith\. care|love i can't repay|farewell, my dear|rest and know|smile and pain", re.I)
# весёлые реплики праздника → «навеселе»: она пьёт вино («This might be the wine talking»)
PARTY_TIPSY = {"excited", "laugh", "teasing", "surprise", "flirty", "neutral"}
SPEAK_WITH_DEAD = "DEN_TieflingBard_Dead"
# отложенная выборка для сравнения моделей на том же тексте (compare_models.py): не референс и не датасет
HOLDOUT = {x["handle"] for x in json.loads((Path(__file__).parent / "holdout.json").read_text(encoding="utf-8"))["lines"]}
SHORT_SEC = 1.6          # короче — выкрик/вздох, в референсы не берём
REF_MIN, REF_MAX = 3.0, 12.0
EDGE_KEEP = 0.12         # сколько тишины оставить по краям при подрезке, с
FLOOR_NOISY = -55.0      # паузы между словами громче этого (дБFS) — подозрение на музыку/шум под голосом
LEAD_NOISY = -60.0       # тишина по краям громче этого — шум
# Для дообучения: «ровная речь» — всё чистое, кроме крайних подач
FINETUNE_SKIP = {"singing", "whisper", "drunk", "tearful", "laugh"}


def block_of(path: Path, dialog: str) -> tuple[str, str]:
    """(акт, блок) по пути диалога — как в таблице canon §8."""
    p = path.as_posix()
    if "/Act1/" in p:
        return "1", "роща"
    if "GoblinHuntCelebration" in dialog:
        return "1", "праздник"
    if "/Act2/" in p:
        return "2", "акт 2"
    if "/Act3/" in p:
        return "3", "акт 3"
    return "1", "Тёмный соблазн"


def editor(node):
    return {d["key"]["value"]: d["val"]["value"] for b in node.get("editorData", []) for d in b.get("data", [])}


def node_handles(node):
    return [x["TagText"]["handle"] for tt in node.get("TaggedTexts", []) for t in tt.get("TaggedText", [])
            for texts in t.get("TagTexts", []) for x in texts.get("TagText", [])]


def scan_dialogs(wanted, speaker=ALFIRA):
    """handle → список мест, где его говорит speaker (по умолчанию Альфира)."""
    found = defaultdict(list)
    for p in sorted(game_data_dir().rglob("*.lsj")):
        if "Story/Dialogs" not in p.as_posix():
            continue
        raw = p.read_text(encoding="utf-8")
        if speaker not in raw:
            continue
        regions = json.loads(raw)["save"]["regions"]
        dlg = regions["dialog"]
        synopsis = ""
        ed_top = regions.get("editorData", {})
        if isinstance(ed_top.get("synopsis"), dict):
            synopsis = ed_top["synopsis"].get("value", "")
        her = set()
        for sl in dlg.get("speakerlist", []):
            for s in sl.get("speaker", []):
                if speaker in s.get("list", {}).get("value", ""):
                    her.add(int(s["index"]["value"]))
        act, block = block_of(p, p.stem)
        for n in dlg["nodes"][0].get("node", []):
            if n.get("speaker", {}).get("value", -1) not in her:
                continue
            ed = editor(n)
            for h in node_handles(n):
                if h in wanted:
                    found[h].append({"dialog": p.stem, "path": p, "act": act, "block": block,
                                     "node": n["UUID"]["value"], "node_id": ed.get("ID", ""),
                                     "speaker": n["speaker"]["value"], "ed": ed, "synopsis": synopsis})
    return found


# --- таймлайны ---------------------------------------------------------------------------------

def timeline_emotions(places):
    """{(диалог, узел): [(секунда от начала реплики, эмоция, вариация, мимика)]} по TLEmotionEvent её актёра."""
    from bg3lib import Lib
    from staging import TC, actor_of, attr, fattr, keys_of
    lib = Lib()
    out = {}
    by_dialog = defaultdict(list)
    for pl in places:
        by_dialog[pl["dialog"]].append(pl)
    for name, pls in sorted(by_dialog.items()):
        try:
            tl = lib.assets.get_timeline_object(name)
        except Exception as e:  # у части AD таймлайна может не быть
            print(f"  [таймлайн] {name}: нет ({type(e).__name__})")
            continue
        speakers = {}
        sp = tl.xml.find(TC + '/node[@id="TimelineSpeakers"]')
        for s in (sp.iter("node") if sp is not None else []):
            if attr(s, "MapKey") is not None and attr(s, "MapValue") is not None:
                speakers[int(attr(s, "MapKey"))] = attr(s, "MapValue")
        comps = tl.all_effect_components
        voices = {}
        for c in comps:
            if attr(c, "Type") == "TLVoice":
                for k in ("DialogNodeId", "ReferenceId"):
                    if attr(c, k):
                        voices.setdefault(attr(c, k), c)
        emos = [c for c in comps if attr(c, "Type") == "TLEmotionEvent"]
        for pl in pls:
            v = voices.get(pl["node"])
            if v is None:
                continue
            actor = speakers.get(pl["speaker"]) or actor_of(v)
            pidx = int(attr(v, "PhaseIndex", 0))
            vs, ve = fattr(v, "StartTime"), fattr(v, "EndTime")
            res = []
            for c in emos:
                if int(attr(c, "PhaseIndex", 0)) != pidx or actor_of(c) != actor:
                    continue
                if fattr(c, "EndTime") < vs or fattr(c, "StartTime") > ve:
                    continue
                mim = attr(c, "IsMimicry") == "True"
                for k in keys_of(c):
                    t = fattr(k, "Time", fattr(c, "StartTime"))
                    if t > ve:
                        continue
                    res.append((float(max(t - vs, 0)), FACE.get(int(attr(k, "Emotion") or 1), "?"),
                                int(attr(k, "Variation", 0) or 0), mim))
            out[(name, pl["node"])] = sorted(res)
    return out


# --- звук --------------------------------------------------------------------------------------

def read_wav(path):
    with wave.open(str(path)) as w:
        sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
    if ch > 1:
        x = x.reshape(-1, ch).mean(axis=1)
    return x, sr


def audio_stats(path):
    x, sr = read_wav(path)
    hop = int(sr * 0.02)
    frames = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)
    peak = float(np.abs(x).max()) if len(x) else 0.0
    thr = max(-45.0, float(db.max()) - 40.0)
    voiced = np.where(db > thr)[0]
    first, last = (int(voiced[0]), int(voiced[-1])) if len(voiced) else (0, len(db) - 1)
    inner = db[first:last + 1]
    gaps = inner[inner <= thr]
    lead = db[:first] if first > 2 else db[:0]
    trail = db[last + 1:] if len(db) - last > 3 else db[:0]
    edges = np.concatenate([lead, trail])
    return {
        "sr": sr,
        "dur": len(x) / sr,
        "peak_db": round(20 * np.log10(peak + 1e-9), 1),
        "clip": int((np.abs(x) >= 0.999).sum()),
        "lead_s": round(first * 0.02, 2),
        "trail_s": round((len(db) - 1 - last) * 0.02, 2),
        "speech_s": round((last - first + 1) * 0.02, 2),
        # паузы между словами (кадры тише порога речи): у студийной записи там цифровая тишина,
        # музыка или шум под голосом поднимают этот уровень. Нет пауз — -99 (не проверить).
        "floor_db": round(float(np.median(gaps)), 1) if len(gaps) >= 5 else -99.0,
        "edge_db": round(float(edges.mean()), 1) if len(edges) else -99.0,
        "first": first, "last": last,
    }


def write_trimmed(src, dst, st):
    x, sr = read_wav(src)
    a = max(0, int((st["first"] * 0.02 - EDGE_KEEP) * sr))
    b = min(len(x), int(((st["last"] + 1) * 0.02 + EDGE_KEEP) * sr))
    y = (np.clip(x[a:b], -1, 1) * 32767).astype(np.int16)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())
    return (b - a) / sr


# --- разметка ----------------------------------------------------------------------------------

def match(s):
    return [slug for slug, rx in CAT_RE if s and rx.search(s)]


def classify(places, face):
    """(главная категория, все совпавшие, откуда главная, ремарка)."""
    hits, primary, src, remark = [], None, "", ""
    for field in SOURCES:
        for pl in places:
            s = (pl["ed"].get(field) or "").strip()
            m = match(s)
            hits += m
            if m and primary is None:
                primary, src, remark = m[0], field, s
    for pl in places:
        e = pl["ed"].get("Emotion", "Default")
        if e in EDITOR_EMOTION:
            hits.append(EDITOR_EMOTION[e])
            if primary is None:
                primary, src, remark = EDITOR_EMOTION[e], "Emotion", e
    # лицо в таймлайне: преобладающая эмоция по ключам; neutral/thinking/confusion — нейтраль
    faces = Counter(f for _t, f, _v, _m in face)
    if faces:
        top_face = faces.most_common(1)[0][0]
        top = FACE_CAT.get(top_face, "neutral")
        hits.append(top)
        if primary is None:
            primary, src, remark = top, "таймлайн", top_face
    for pl in places:  # синопсис — про весь диалог: только в «also», главной не становится
        hits += match(pl["synopsis"])
    return primary or "neutral", list(dict.fromkeys(hits)), src, remark


def is_singing(h, line, places):
    if h.startswith(DECLAMATION):
        return False
    if any("FullSong" in pl["dialog"] for pl in places) or LYRICS.search(line):
        return True
    return False


def norm_text(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-timeline", action="store_true", help="не открывать таймлайны (без bg3moddinglib)")
    ap.add_argument("--refs-per-cat", type=int, default=8)
    ap.add_argument("--speaker", default=ALFIRA, help="GUID говорящего; датасет — от extract_voice.py --speaker")
    ap.add_argument("--name", default="", help="имя для папки образцов: refs_<имя> (для NPC)")
    args = ap.parse_args()
    cfg = config()
    work = resolve(cfg["paths"]["voice_work"])
    npc = args.speaker != ALFIRA
    if npc and not args.name:
        sys.exit("для NPC нужно --name (папка voice-work/refs_<имя>)")
    ds = work / (f"dataset_{args.speaker.replace('-', '')[:8]}" if npc else "dataset")
    meta = list(csv.DictReader((ds / "metadata.csv").open(encoding="utf-8"), delimiter="|"))
    handles = {r["file"][:-4]: r for r in meta}
    print(f"реплик в metadata.csv: {len(handles)}")

    found = scan_dialogs(set(handles), args.speaker)
    print(f"найдено в диалогах: {len(found)}")
    face = {} if args.no_timeline else timeline_emotions([pl for pls in found.values() for pl in pls])

    rows, seen_text = [], {}
    for h, r in sorted(handles.items(), key=lambda kv: kv[0]):
        places = found.get(h, [])
        fl = [e for pl in places for e in face.get((pl["dialog"], pl["node"]), [])]
        cat, hits, src, remark = classify(places, fl)
        if is_singing(h, r["text"], places):
            cat, src = "singing", "текст песни"
        elif any(pl["block"] == "праздник" for pl in places) and cat in PARTY_TIPSY:
            hits.append(cat)
            cat = "drunk"
        st = audio_stats(ds / "wav" / r["file"])
        line = r["text"]
        dialogs = sorted({pl["dialog"] for pl in places})
        excl = []
        if h in HOLDOUT and not npc:
            excl.append("отложено")
        if any(d == SPEAK_WITH_DEAD for d in dialogs):
            excl.append("мёртвые")
        if h.startswith(MIXED_SINGING):
            excl.append("пение+речь")
        elif cat == "singing":
            excl.append("пение")
        if re.fullmatch(r"\W*\*?\s*sob\w*\W*", line, re.I) or re.search(r"\*sob", line, re.I):
            excl.append("рыдание")
        if st["speech_s"] < SHORT_SEC or len(norm_text(line).split()) <= 2:
            excl.append("выкрик")
        key = norm_text(line)
        if key in seen_text:
            excl.append(f"повтор {seen_text[key][:9]}")
        else:
            seen_text[key] = h
        noise = []
        if st["clip"] > 4:
            noise.append(f"клиппинг {st['clip']}")
        if st["floor_db"] > FLOOR_NOISY:
            noise.append(f"паузы {st['floor_db']} дБ")
        if st["edge_db"] > LEAD_NOISY:
            noise.append(f"края {st['edge_db']}")
        emo_str = " ".join(f"{t:.1f}:{f}{'/' + str(v) if v else ''}{'*' if m else ''}" for t, f, v, m in fl)
        pl0 = places[0] if places else {}
        ed0 = pl0.get("ed", {})
        rows.append({
            "handle": h, "category": cat, "category_ru": CAT_RU[cat], "also": " ".join(x for x in hits if x != cat),
            "label_source": src, "exclude": "; ".join(excl), "noise": "; ".join(noise),
            "seconds": f"{st['dur']:.2f}", "speech_s": st["speech_s"], "lead_s": st["lead_s"], "trail_s": st["trail_s"],
            "peak_db": st["peak_db"], "floor_db": st["floor_db"], "edge_db": st["edge_db"],
            "act": pl0.get("act", ""), "block": pl0.get("block", ""), "dialog": " ".join(dialogs),
            "node_id": " ".join(sorted({pl["node_id"] for pl in places})),
            "vo_context": ed0.get("VOContext", ""), "node_context": ed0.get("NodeContext", ""),
            "cine_context": ed0.get("CinematicNodeContext", ""), "editor_emotion": ed0.get("Emotion", ""),
            "attitude": ed0.get("Attitude", ""), "timeline_emotions": emo_str, "remark": remark, "text": line,
            "_st": st,
        })

    fields = [k for k in rows[0] if not k.startswith("_")]
    with (ds / "labels.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    build_refs(rows, ds, work / (f"refs_{args.name}" if npc else "refs"), args.refs_per_cat)
    if not npc:          # дообучение — только для Альфиры
        build_finetune(rows, ds, ds / "finetune")

    cats = Counter(r["category"] for r in rows)
    usable = Counter(r["category"] for r in rows if not r["exclude"])
    print("\nкатегория            всего  без исключений")
    for slug, ru, _ in CATEGORIES:
        if cats[slug]:
            print(f"  {ru:<22} {cats[slug]:>4}  {usable[slug]:>4}")
    ex = Counter(e.split(" ")[0] for r in rows for e in r["exclude"].split("; ") if e)
    print("исключено:", dict(ex), "| с замечаниями к звуку:", sum(1 for r in rows if r["noise"]))
    print(f"→ {ds / 'labels.csv'}")


def ref_score(r):
    """Чем меньше, тем лучше: точность ремарки, чистота звука, длина ближе к 6–9 с."""
    src_rank = {"VOContext": 0, "VOContextAfter": 0, "NodeContext": 1, "stateContext": 1, "CinematicNodeContext": 2,
                "InternalNodeContext": 2, "Emotion": 3, "таймлайн": 4, "текст песни": 9, "": 6}[r["label_source"]]
    st = r["_st"]
    length = abs(st["speech_s"] - 7.5) / 3
    return src_rank + length + max(0.0, st["floor_db"] + 70) / 20 + (2 if r["noise"] else 0)


def build_refs(rows, ds, refs, per_cat):
    if refs.exists():
        shutil.rmtree(refs)
    summary = []
    for slug, ru, _ in CATEGORIES:
        if slug == "singing":
            continue
        cand = [r for r in rows if r["category"] == slug and not r["exclude"] and not r["noise"]
                and REF_MIN <= r["_st"]["speech_s"] + 2 * EDGE_KEEP <= REF_MAX]
        # лицо таймлайна — слабый признак (Larian ставит fear и на радостное «Really? Oh, this is wonderful!»),
        # поэтому сначала только реплики с ремаркой; таймлайн — если с ремаркой меньше трёх
        precise = [r for r in cand if r["label_source"] not in ("таймлайн", "")]
        cand = precise if len(precise) >= 3 else cand
        cand.sort(key=ref_score)
        chosen = cand[:per_cat]
        if not chosen:
            continue
        d = refs / slug
        d.mkdir(parents=True)
        with (d / "index.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["file", "seconds", "dialog", "remark", "text"])
            for r in chosen:
                sec = write_trimmed(ds / "wav" / f"{r['handle']}.wav", d / f"{r['handle']}.wav", r["_st"])
                (d / f"{r['handle']}.txt").write_text(r["text"] + "\n", encoding="utf-8")
                w.writerow([f"{r['handle']}.wav", f"{sec:.2f}", r["dialog"], r["remark"], r["text"]])
        summary.append(f"{slug:<12} {ru:<22} {len(chosen):>2} из {len(cand)} подходящих")
    (refs / "README.txt").write_text(
        "Референсы голоса Альфиры по эмоциям (scripts/voice/label_emotions.py). Только для личной сборки.\n"
        "В каждой папке: <handle>.wav (48 кГц, моно, края тишины подрезаны), <handle>.txt — текст,\n"
        "index.csv — длина, диалог, ремарка. Отбор: без исключений (пение, выкрики, мёртвые, повторы),\n"
        "без замечаний к звуку, 3–12 с, сначала реплики с прямой ремаркой актрисе (VOContext).\n\n"
        + "\n".join(summary) + "\n", encoding="utf-8")
    print("\nреференсы:\n  " + "\n  ".join(summary))


def build_finetune(rows, ds, out):
    """Ровная речь для дообучения: wav с подрезанными краями и списки в форматах моделей."""
    if out.exists():
        shutil.rmtree(out)
    wav_dir = out / "wav"
    chosen = [r for r in rows if not r["exclude"] and not r["noise"] and r["category"] not in FINETUNE_SKIP]
    total, lines = 0.0, []
    for r in chosen:
        sec = write_trimmed(ds / "wav" / f"{r['handle']}.wav", wav_dir / f"{r['handle']}.wav", r["_st"])
        total += sec
        lines.append((r["handle"], r["text"], sec, r["category"]))
    txt = lambda s: re.sub(r"<[^>]+>", "", s).replace("|", " ").strip()  # noqa: E731
    # LJSpeech-подобный: file|text (F5-TTS, Coqui, большинство скриптов)
    (out / "metadata.csv").write_text("".join(f"{h}.wav|{txt(t)}\n" for h, t, _s, _c in lines), encoding="utf-8")
    # GPT-SoVITS: абсолютный путь|спикер|язык|текст
    (out / "gptsovits.list").write_text(
        "".join(f"{(wav_dir / (h + '.wav')).resolve()}|alfira|en|{txt(t)}\n" for h, t, _s, _c in lines), encoding="utf-8")
    # JSONL: {"audio": ..., "text": ..., "duration": ...} (CosyVoice/IndexTTS/прочие конвертеры)
    (out / "train.jsonl").write_text("".join(
        json.dumps({"audio": str((wav_dir / (h + '.wav')).resolve()), "text": txt(t), "duration": round(s, 2),
                    "speaker": "alfira", "emotion": c}, ensure_ascii=False) + "\n" for h, t, s, c in lines),
        encoding="utf-8")
    by = Counter(c for *_x, c in lines)
    (out / "README.txt").write_text(
        f"Датасет для дообучения: {len(lines)} реплик, {total / 60:.1f} мин (48 кГц, моно).\n"
        f"Без пения, выкриков, мёртвых, повторов, шума и крайних подач ({', '.join(sorted(FINETUNE_SKIP))}).\n"
        f"По категориям: {dict(by)}\n"
        "metadata.csv — file|text; gptsovits.list — путь|спикер|язык|текст; train.jsonl — по строке на реплику.\n",
        encoding="utf-8")
    print(f"\nдообучение: {len(lines)} реплик, {total / 60:.1f} мин → {out}")


if __name__ == "__main__":
    main()
