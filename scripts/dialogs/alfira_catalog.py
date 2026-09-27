#!/usr/bin/env python3
"""Каталог постановки Альфиры: как Larian ставит её реплики (эмоции, позы, взгляды, анимации, камеры).

  python scripts/dialogs/alfira_catalog.py            # все диалоги игры, где она говорит
  python scripts/dialogs/alfira_catalog.py --rescan   # заново найти эти диалоги в game-data

Источники:
  * диалоги .lsj из game-data (распакованы scripts/unpack_game.py, наборы dialogs-all / dialogs-alfira):
    кто говорит, ремарки редактора (NodeContext, CinematicNodeContext, Emotion, Attitude, AnimationTags);
  * таймлайны и сцены — из паков игры через bg3moddinglib (scripts/dialogs/bg3lib.py).

По каждой её реплике (TLVoice её актёра) — окно фазы от начала голоса до следующего голоса или конца фазы:
  * TLEmotionEvent — ключи Emotion/Variation, время от начала голоса, длительность до следующего ключа;
  * TLAttitudeEvent — позы (Pose, Transition);
  * TLLookAtEvent — на кого смотрит (роль: герой, NPC) и кость;
  * TLAnimation — AnimationSourceId, слот, начало и длина, скорость;
  * TLShot — камера (имя из сцены: cam_subject1_CU и т. п.), к кому привязана и куда смотрит.
Её фазы без голоса (TagCinematic и паузы), где у неё есть TLAnimation, — отдельным списком.

Результат (локально, в git не идёт — это данные и тексты Larian):
  reports/staging/alfira_catalog.json   сырой каталог по репликам;
  reports/staging/alfira_catalog.md     читаемая распечатка с ремарками.
Словарь для генератора — scripts/dialogs/alfira_style.json (только идентификаторы и частоты, в git):
  по эмоции сценария (dsl.EMOTIONS) — её вариации лица и ход ключей; по ремарке сценария — её эмоции,
  позы и жесты из реплик, у которых такая ремарка в редакторе Larian. Сводка — docs/research/alfira-staging.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from common import enable_utf8_stdout, game_data_dir, resolve  # noqa: E402
import bg3lib  # noqa: E402
from dsl import EMOTIONS  # noqa: E402
from staging import TC, actor_of, attr, fattr, keys_of  # noqa: E402
from vanilla import ALFIRA_TEMPLATE  # noqa: E402

enable_utf8_stdout()

OUT = resolve("reports/staging")
STYLE = HERE / "alfira_style.json"
CODES = {v: k for k, v in EMOTIONS.items()}
SHARED_SCENES = "Public/Shared/Timeline/Scenes/Default/"

# Ремарки сценария (design/dialogs/*.md, note=… в сценах) → слова, которыми то же самое описывает редактор
# Larian в NodeContext / CinematicNodeContext / AnimationTags её реплик. Ключ — как ремарка звучит у нас.
REMARKS = {
    "краснеет": ["blush", "embarrass", "fluster", "bashful", "shy", "sheepish"],
    "смеётся": ["laugh", "giggl", "chuckl", "snort"],
    "улыбается": ["smil", "grin", "beam"],
    "грустно": ["sad", "melanchol", "wistful", "somber", "sombre", "sorrow", "grief", "griev", "mourn"],
    "тихо": ["quiet", "soft", "hush", "whisper", "gentl"],
    "плачет": ["cry", "crying", "tear", "sob"],
    "испуг": ["scared", "afraid", "fear", "frighten", "nervous", "anxious", "panic", "terrified", "worried"],
    "злится": ["angry", "anger", "annoy", "irritat", "frustrat", "furious", "hostile", "indignant"],
    "думает": ["think", "ponder", "consider", "thought", "reflect", "musing", "hesitat"],
    "удивлена": ["surprise", "shock", "taken aback", "startl", "astonish"],
    "нежно": ["tender", "warm", "fond", "affection", "sweet", "grateful", "touched"],
    "дразнит": ["tease", "teasing", "playful", "flirt", "cheek", "mischiev", "coy", "wink"],
    "гордо": ["proud", "pride", "confident", "triumph"],
    "восторг": ["excit", "thrill", "delight", "enthusias", "eager", "overjoy", "ecstatic"],
    "устала": ["tired", "exhaust", "weary", "sleepy", "yawn"],
    "пожимает плечами": ["shrug"],
    "вздыхает": ["sigh"],
    "пьяная": ["drunk", "tipsy", "wine"],
    # слова целиком: sing нашло бы single, play — player, hum — human
    "поёт": ["sings", "singing", "song", "hums", "humming"],
    "играет на лютне": ["lute", "strum", "pluck"],
}


# --- поиск её диалогов ---------------------------------------------------------------------------

def find_dialogs(rescan=False) -> list[Path]:
    cache = OUT / "_alfira_dialogs.json"
    if cache.exists() and not rescan:
        return [Path(p) for p in json.loads(cache.read_text(encoding="utf-8"))]
    root = game_data_dir()
    hits = []
    for pak in sorted(p for p in root.iterdir() if p.is_dir()):
        for p in sorted((pak / "Mods").glob("*/Story/Dialogs/**/*.lsj")):
            if ALFIRA_TEMPLATE in p.read_text(encoding="utf-8", errors="replace"):
                hits.append(p)
    OUT.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps([str(p) for p in hits], ensure_ascii=False, indent=1), encoding="utf-8")
    return hits


def v(node, key, default=""):
    x = node.get(key)
    return x.get("value", default) if isinstance(x, dict) else default


def editor(node):
    out = {}
    for block in node.get("editorData", []):
        for d in block.get("data", []):
            out[d["key"]["value"]] = d["val"]["value"]
    return out


def read_lsj(path: Path):
    """{узел: {speaker, constructor, context, emotion, attitude, anim_tags, id}}, её номера спикера."""
    d = json.loads(path.read_text(encoding="utf-8"))["save"]["regions"]["dialog"]
    alfira_idx = set()
    for sl in d.get("speakerlist", []):
        for s in sl.get("speaker", []):
            if ALFIRA_TEMPLATE in s.get("list", {}).get("value", ""):
                alfira_idx.add(int(s["index"]["value"]))
    nodes = {}
    for n in d["nodes"][0].get("node", []):
        ed = editor(n)
        handles = [x["TagText"]["handle"] for tt in n.get("TaggedTexts", []) for t in tt.get("TaggedText", [])
                   for texts in t.get("TagTexts", []) for x in texts.get("TagText", [])]
        nodes[n["UUID"]["value"]] = {
            "speaker": v(n, "speaker", -1), "constructor": v(n, "constructor"), "id": ed.get("ID", ""),
            "context": " ".join(x.strip() for x in (ed.get("NodeContext", ""), ed.get("CinematicNodeContext", "")) if x.strip()),
            "emotion": ed.get("Emotion", ""), "attitude": ed.get("Attitude", ""),
            "anim_tags": ed.get("AnimationTags", ""), "handles": handles}
    return nodes, alfira_idx


# --- таймлайн ------------------------------------------------------------------------------------

class Names:
    """Имена поз и анимаций (ShortNames.lsx игры: uuid → имя ресурса) и камер (TLCameras сцен)."""

    def __init__(self, lib):
        self.lib = lib
        self.poses = {}                 # uuid позы или анимации → имя (DIAG_Pose_…, HUM_F_…)
        f = lib.game_file("Public/Shared/Animation/ShortNames.lsx")
        for n in f.root_node.iter("node"):
            if n.get("id") == "ShortName":
                self.poses[attr(n, "UUID")] = attr(n, "Name")
        self.scene_cams = {}

    def cameras(self, scene_path: str) -> dict:
        """camera uuid → имя в сцене и в сценах, от которых она наследует."""
        if scene_path in self.scene_cams:
            return self.scene_cams[scene_path]
        out = {}
        self.scene_cams[scene_path] = out
        try:
            f = self.lib.game_file(scene_path)
        except RuntimeError:
            return out
        top = f.root_node.find('./region[@id="TLScene"]/node[@id="TLScene"]')
        if top is None:
            return out
        for inh in top.findall('./children/node[@id="TLInheritedScenes"]/children/node'):
            p = attr(inh, "Object") or ""
            if p:
                out.update(self.cameras(p[:-4] + ".lsf" if p.endswith(".lsx") else p))
        for c in top.findall('./children/node[@id="TLCameras"]/children/node'):
            cam = c.find('./children/node[@id="TLCameras"]')
            if cam is not None:
                local = not scene_path.startswith(SHARED_SCENES)
                out[attr(c, "MapKey")] = (attr(cam, "Name") or "?") + ("" if not local else " (своя)")
        return out


def speakers_of(tl):
    out = {}
    for s in tl.xml.find(TC + '/node[@id="TimelineSpeakers"]').iter("node"):
        if attr(s, "MapKey") is not None and attr(s, "MapValue") is not None:
            out[attr(s, "MapValue")] = int(attr(s, "MapKey"))
    return out


def catalog_dialog(lib, names: Names, path: Path):
    name = path.stem
    nodes, alfira_idx = read_lsj(path)
    if not lib.assets.index.has_entry(name):
        return None, f"{name}: нет в индексе bg3moddinglib"
    entry = lib.assets.index.get_entry(name)
    if not entry.get("timeline_uuid"):
        return None, f"{name}: без таймлайна"
    try:
        tl = lib.assets.get_timeline_object(name)
    except Exception as e:                              # noqa: BLE001 — у части AD таймлайна нет
        return None, f"{name}: таймлайн не читается ({e})"
    spk = speakers_of(tl)
    actors = tl.get_timeline_actors()
    alfira = {a for a, i in spk.items() if i in alfira_idx}
    if not alfira:
        return None, f"{name}: её актёра в таймлайне нет"
    role = {}
    for a, val in actors.items():
        if a in alfira:
            role[a] = "alfira"
        elif attr(val, "IsPlayer") == "True":
            role[a] = "player"
        elif attr(val, "ActorTypeId") == "character":
            role[a] = f"npc{spk.get(a, '')}"
        elif attr(val, "ActorTypeId") == "peanut":
            role[a] = "peanut"
    src = lib.assets.index.get_timeline_resource(entry["timeline_uuid"]).find('./attribute[@id="SourceFile"]').get("value")
    cam_names = names.cameras(src[:-4] + "_Scene.lsf")
    scenecam = {}
    for a, val in tl.get_timeline_actors("scenecam").items():
        scenecam[a] = (cam_names.get(attr(val, "Camera"), attr(val, "Camera")), role.get(attr(val, "AttachTo"), "?"),
                       role.get(attr(val, "LookAt"), "-"))
    by_phase = defaultdict(list)
    for c in tl.all_effect_components:
        by_phase[int(attr(c, "PhaseIndex", 0))].append(c)
    phase_node = {}
    for i in range(tl.get_number_of_phases()):
        ph = tl.get_timeline_phase(i)
        phase_node[i] = (ph.dialog_node_uuid, ph.start, ph.start + ph.duration)
    lines, cine = [], []
    for pidx, comps in sorted(by_phase.items()):
        voices = sorted((c for c in comps if attr(c, "Type") == "TLVoice"), key=lambda c: fattr(c, "StartTime"))
        node_uuid, pstart, pend = phase_node.get(pidx, ("", 0, 0))
        mine = [c for c in voices if actor_of(c) in alfira]
        for vc in mine:
            ws = fattr(vc, "StartTime")
            later = [fattr(c, "StartTime") for c in voices if fattr(c, "StartTime") > ws]
            we = later[0] if later else fattr(vc, "EndTime") if pend <= ws else min(pend, fattr(vc, "EndTime") + 3)
            nid = attr(vc, "DialogNodeId") or node_uuid
            lines.append(window(name, nid, nodes.get(nid, {}), comps, alfira, role, scenecam, ws, we,
                                fattr(vc, "EndTime") - ws))
        if not mine:
            anims = [c for c in comps if attr(c, "Type") == "TLAnimation" and actor_of(c) in alfira]
            if anims:
                n = nodes.get(node_uuid, {})
                cine.append({"dialog": name, "node": node_uuid, "id": n.get("id", ""), "constructor": n.get("constructor", ""),
                             "context": n.get("context", ""), "phase": pidx, "duration": round(float(pend - pstart), 2),
                             "animations": [anim(c, pstart) for c in anims],
                             "poses": [k for c in comps if attr(c, "Type") == "TLAttitudeEvent" and actor_of(c) in alfira
                                       for k in pose_keys(c, pstart, names)]})
    return {"dialog": name, "path": str(path.relative_to(game_data_dir())), "lines": lines, "cinematic": cine,
            "scene": src[:-4] + "_Scene.lsf"}, None


def anim(c, t0):
    return {"id": attr(c, "AnimationSourceId"), "name": NAMES.poses.get(attr(c, "AnimationSourceId"), "") if NAMES else "",
            "slot": attr(c, "AnimationSlot", ""),
            "start": round(float(fattr(c, "StartTime") - t0), 2),
            "length": round(float(fattr(c, "EndTime") - fattr(c, "StartTime")), 2),
            "rate": attr(c, "AnimationPlayRate", ""), "root_motion": attr(c, "EnableRootMotion", "") == "True",
            "group": attr(c, "AnimationGroup", "")}


def pose_keys(c, t0, names):
    out = []
    for k in keys_of(c):
        p = attr(k, "Pose")
        if p:
            out.append({"t": round(float(fattr(k, "Time", fattr(c, "StartTime")) - t0), 2), "pose": p,
                        "name": names.poses.get(p, ""), "transition": attr(k, "Transition", "")})
    return out


def window(dialog, nid, node, comps, alfira, role, scenecam, ws, we, vdur):
    names = NAMES
    rec = {"dialog": dialog, "node": nid, "id": node.get("id", ""), "constructor": node.get("constructor", ""),
           "context": node.get("context", ""), "emotion_label": node.get("emotion", ""),
           "attitude_label": node.get("attitude", ""), "anim_tags": node.get("anim_tags", ""),
           "handle": (node.get("handles") or [""])[0], "voice": round(float(vdur), 2),
           "window": round(float(we - ws), 2), "emotions": [], "poses": [], "looks": [], "animations": [], "shots": []}
    for c in comps:
        typ = attr(c, "Type")
        cs, ce = fattr(c, "StartTime"), fattr(c, "EndTime")
        if ce <= ws or cs >= we:
            continue
        a = actor_of(c)
        if typ == "TLShot":
            cc = c.find('./children/node[@id="CameraContainer"]')
            cam = attr(cc, "Object") if cc is not None else None
            nm = scenecam.get(cam, (cam, "?", "?"))
            rec["shots"].append({"t": round(float(max(cs, ws) - ws), 2), "length": round(float(min(ce, we) - max(cs, ws)), 2),
                                 "camera": nm[0], "attach": nm[1], "look": nm[2]})
            continue
        if a not in alfira:
            continue
        if typ == "TLEmotionEvent":
            ks = keys_of(c)
            times = [fattr(k, "Time", cs) for k in ks]
            for i, k in enumerate(ks):
                t, nxt = times[i], (times[i + 1] if i + 1 < len(ks) else ce)
                if nxt <= ws or t >= we:
                    continue
                code = int(attr(k, "Emotion") or 1)
                rec["emotions"].append({"t": round(float(max(t, ws) - ws), 2), "length": round(float(min(nxt, we) - max(t, ws)), 2),
                                        "emotion": CODES.get(code, str(code)), "code": code,
                                        "variation": int(attr(k, "Variation", 0) or 0),
                                        "sustained": attr(k, "IsSustainedEmotion", "") != "False"})
        elif typ == "TLAttitudeEvent":
            ks = pose_keys(c, ws, names)
            before = [k for k in ks if k["t"] <= 0]
            rec["poses"] += ([before[-1] | {"t": 0.0}] if before else []) + [k for k in ks if 0 < k["t"] < float(we - ws)]
        elif typ == "TLLookAtEvent":
            for k in keys_of(c):
                t = fattr(k, "Time", cs)
                if t >= we:
                    continue
                rec["looks"].append({"t": round(float(max(t, ws) - ws), 2), "target": role.get(attr(k, "Target"), "?"),
                                     "bone": attr(k, "Bone", ""), "eyes": role.get(attr(k, "EyeLookAtTargetId"), "")})
        elif typ == "TLAnimation":
            rec["animations"].append(anim(c, ws))
    rec["emotions"].sort(key=lambda e: e["t"])
    rec["looks"].sort(key=lambda e: e["t"])
    rec["shots"].sort(key=lambda e: e["t"])
    return rec


NAMES: Names | None = None


# --- сводка и словарь ------------------------------------------------------------------------------

def dominant(rec):
    """Главная эмоция реплики — дольше всех на лице (neutral не считается, если есть другие)."""
    dur = Counter()
    for e in rec["emotions"]:
        dur[e["emotion"]] += e["length"]
    if not dur:
        return "neutral"
    top = [k for k, _ in dur.most_common() if k != "neutral"]
    return top[0] if top and dur[top[0]] >= 0.25 * sum(dur.values()) else dur.most_common(1)[0][0]


def matches(rec, words):
    text = " ".join((rec["context"], rec["anim_tags"], rec["emotion_label"])).lower()
    return any(re.search(r"\b" + re.escape(w), text) for w in words)


def pattern(rec):
    """Ход её лица по реплике: [(доля реплики, эмоция/вариация)], соседние одинаковые ключи сливаются."""
    out = []
    w = max(rec["window"], 0.01)
    for e in rec["emotions"]:
        tok = f"{e['emotion']}/{e['variation']}"
        if out and out[-1][1] == tok:
            continue
        out.append((round(min(e["t"] / w, 0.95), 2), tok))
    return out


def summarize(lines, cine):
    """Словарь для генератора (alfira_style.json): только идентификаторы и частоты."""
    style = {"_note": "Сгенерировано scripts/dialogs/alfira_catalog.py из данных игры: её реплики у Larian. "
                      "Только идентификаторы (коды эмоций, uuid поз и анимаций) и частоты. Руками не править.",
             "lines": len(lines), "emotions": {}, "remarks": {}, "poses_standing": {}, "gestures": {}}
    # 1. По главной эмоции реплики: вариации, ход ключей, позы, взгляды
    groups = defaultdict(list)
    for r in lines:
        groups[dominant(r)].append(r)
    for emo, rs in sorted(groups.items()):
        var = Counter()
        for r in rs:
            for e in r["emotions"]:
                if e["emotion"] == emo:
                    var[e["variation"]] += 1
        seqs = Counter(tuple(t for _, t in pattern(r)) for r in rs)
        poses = Counter(p["pose"] for r in rs for p in r["poses"])
        keys_per_sec = sum(len(r["emotions"]) for r in rs) / max(0.01, sum(r["window"] for r in rs))
        style["emotions"][emo] = {
            "lines": len(rs), "variations": var.most_common(), "keys_per_second": round(keys_per_sec, 3),
            "sequences": [[list(s), n] for s, n in seqs.most_common(8)],
            "poses": poses.most_common(6),
            "labels": Counter(r["emotion_label"] for r in rs if r["emotion_label"]).most_common(6),
            "examples": [f"{r['dialog']}:{r['id'] or r['node'][:8]}" for r in rs[:5]]}
    # 2. По ремаркам сценария: её эмоции, позы и анимации в репликах с такой ремаркой у Larian
    for key, words in REMARKS.items():
        rs = [r for r in lines if matches(r, words)]
        if not rs:
            continue
        emo = Counter()
        for r in rs:
            for e in r["emotions"]:
                emo[f"{e['emotion']}/{e['variation']}"] += e["length"]
        style["remarks"][key] = {
            "lines": len(rs), "words": words,
            "dominant": Counter(dominant(r) for r in rs).most_common(4),
            "faces": [[k, round(s, 1)] for k, s in emo.most_common(6)],
            "sequences": [[list(s), n] for s, n in Counter(tuple(t for _, t in pattern(r)) for r in rs).most_common(4)],
            "poses": Counter(p["pose"] for r in rs for p in r["poses"]).most_common(4),
            "animations": Counter(a["id"] for r in rs for a in r["animations"]).most_common(4),
            "examples": [f"{r['dialog']}:{r['id'] or r['node'][:8]}" for r in rs[:6]]}
    # 3. Позы: частоты по всем её репликам
    style["poses_standing"] = Counter(p["pose"] for r in lines for p in r["poses"]).most_common(20)
    # 4. Жесты: TLAnimation в её репликах (не в кат-сценах) — по частоте, с длиной и слотом
    g = defaultdict(list)
    for r in lines:
        for a in r["animations"]:
            g[a["id"]].append((r, a))
    for aid, uses in sorted(g.items(), key=lambda x: -len(x[1])):
        r, a = uses[0]
        style["gestures"][aid] = {"name": a["name"], "uses": len(uses), "slot": a["slot"], "length": a["length"], "rate": a["rate"],
                                  "root_motion": a["root_motion"],
                                  "emotions": Counter(dominant(r) for r, _ in uses).most_common(3),
                                  "dialogs": sorted({r["dialog"] for r, _ in uses})[:4]}
    style["cinematic_animations"] = Counter(a["id"] for c in cine for a in c["animations"]).most_common(20)
    return style


def write_md(lines, cine, errors, names):
    from gamedb import text
    out = ["# Каталог постановки Альфиры (локально, не в git: тексты и ремарки Larian)", "",
           f"Реплик: {len(lines)}, фаз без голоса с её анимацией: {len(cine)}.", ""]
    if errors:
        out += ["Пропущено:", *[f"- {e}" for e in errors], ""]
    cur = None
    for r in lines:
        if r["dialog"] != cur:
            cur = r["dialog"]
            out += ["", f"## {cur}", ""]
        emo = " → ".join(f"{e['emotion']}/{e['variation']}@{e['t']}" for e in r["emotions"]) or "—"
        poses = ", ".join(f"{p['name'] or p['pose'][:8]}@{p['t']}" for p in r["poses"]) or "—"
        looks = ", ".join(sorted({x["target"] for x in r["looks"]})) or "—"
        shots = ", ".join(f"{s['camera']}({s['attach']}→{s['look']})" for s in r["shots"]) or "—"
        anims = ", ".join(f"{a['name'] or a['id'][:8]}@{a['start']}+{a['length']}" for a in r["animations"])
        out.append(f"- **{r['id'] or r['node'][:8]}** {r['voice']}/{r['window']} с — {text(r['handle']) if r['handle'] else ''}")
        if r["context"] or r["emotion_label"]:
            out.append(f"  - ремарка: {r['context']} [{r['emotion_label']}{'/' + r['attitude_label'] if r['attitude_label'] else ''}]")
        out.append(f"  - лицо: {emo}")
        out.append(f"  - поза: {poses}; взгляд: {looks}; камера: {shots}")
        if anims:
            out.append(f"  - анимации: {anims}")
    if cine:
        out += ["", "## Фазы без голоса с её анимацией", ""]
        for c in cine:
            out.append(f"- {c['dialog']} {c['id'] or c['node'][:8]} ({c['constructor']}, {c['duration']} с): {c['context']} — "
                       + ", ".join(f"{a['name'] or a['id'][:8]}+{a['length']}" for a in c["animations"]))
    (OUT / "alfira_catalog.md").write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    global NAMES
    ap = argparse.ArgumentParser()
    ap.add_argument("--rescan", action="store_true", help="заново найти её диалоги в game-data")
    args = ap.parse_args()
    paths = find_dialogs(args.rescan)
    print(f"диалогов с Альфирой: {len(paths)}")
    lib = bg3lib.Lib()
    NAMES = Names(lib)
    lines, cine, errors = [], [], []
    for p in paths:
        rec, err = catalog_dialog(lib, NAMES, p)
        if err:
            errors.append(err)
            continue
        lines += rec["lines"]
        cine += rec["cinematic"]
        print(f"  {rec['dialog']}: реплик {len(rec['lines'])}, кат-фаз {len(rec['cinematic'])}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "alfira_catalog.json").write_text(json.dumps({"lines": lines, "cinematic": cine, "skipped": errors,
                                                        "poses": NAMES.poses}, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    write_md(lines, cine, errors, NAMES)
    style = summarize(lines, cine)
    style["pose_names"] = {p: NAMES.poses.get(p, "") for p in
                           {x for e in style["emotions"].values() for x, _ in e["poses"]}
                           | {x for e in style["remarks"].values() for x, _ in e["poses"]}
                           | {x for x, _ in style["poses_standing"]}}
    STYLE.write_text(json.dumps(style, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"реплик {len(lines)}, фаз без голоса с анимацией {len(cine)}, пропущено {len(errors)}")
    print(f"  {OUT / 'alfira_catalog.json'}\n  {OUT / 'alfira_catalog.md'}\n  {STYLE}")


if __name__ == "__main__":
    main()
