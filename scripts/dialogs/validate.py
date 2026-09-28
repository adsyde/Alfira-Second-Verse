#!/usr/bin/env python3
"""Проверка сгенерированных диалогов без игры: ссылки, фазы, тексты, круг lsx↔lsf, сверка с игрой.

  python scripts/dialogs/validate.py

1. Ссылки внутри диалога: дети, корни, вложенные диалоги, реакции одобрения, новые флаги,
   тексты (в loca мода на всех языках или озвученная реплика игры из manifest).
2. Таймлайн ↔ диалог: у каждой реплики персонажа (Альфиры, третьего участника) и ремарки есть фаза и TLVoice; фазы ссылаются на
   существующие узлы; компоненты лежат в границах своей фазы; актёры, камеры и цели взгляда есть
   среди актёров таймлайна; длительность эффекта = сумме фаз; банки ссылаются друг на друга.
3. Круг через Divine: каждый ресурс lsx → lsf → lsx без ошибок и без потерь (сравнение деревьев).
4. Сверка структуры с ванильной основой (build/dialogs/reference, пишет build.py): какие виды
   узлов и атрибутов есть у игры и нет у нас.
"""
from __future__ import annotations

import json
import sys
import tempfile
import xml.etree.ElementTree as et
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import config, divine, enable_utf8_stdout, resolve  # noqa: E402
sys.path.insert(0, str(HERE))
from vanilla import NESTED  # noqa: E402

VANILLA_NESTED = {v for k, v in vars(NESTED).items() if not k.startswith("_")}

enable_utf8_stdout()


def A(e, k, d=None):
    x = e.find(f'./attribute[@id="{k}"]')
    return d if x is None else (x.get("value") if x.get("value") is not None else x.get("handle"))


def num(v):
    return Decimal(str(v).replace(",", ".")) if v is not None else Decimal(0)


def load(p):
    return et.parse(p).getroot()


class Report:
    def __init__(self):
        self.errors, self.notes = [], []

    def err(self, m):
        self.errors.append(m)

    def note(self, m):
        self.notes.append(m)


def check_scene(name, dlg_path, tl_path, bank_res, tl_res, loca, vanilla, reactions, new_flags, rep, ours=()):
    d = load(dlg_path)
    nodes = {A(n, "UUID"): n for n in d.iter("node") if n.get("id") == "node"}
    roots = [A(r, "RootNodes") for r in d.iter("node") if r.get("id") == "RootNodes"]
    nested_ok = {A(c, "Object") for c in bank_res.findall('./children/node[@id="childResources"]')}
    for r in roots:
        if r not in nodes or A(nodes[r], "Root") != "True":
            rep.err(f"{name}: корень {r} не узел с Root=True")
    for u, n in nodes.items():
        for c in n.findall('./children/node[@id="children"]/children/node[@id="child"]'):
            if A(c, "UUID") not in nodes:
                rep.err(f"{name}: {u} → нет ребёнка {A(c, 'UUID')}")
        jt = A(n, "jumptarget")
        if jt and jt not in nodes:
            rep.err(f"{name}: прыжок {u} → нет {jt}")
        nd = A(n, "NestedDialogNodeUUID")
        if nd and nd not in nested_ok:
            rep.err(f"{name}: вложенный диалог {nd} не указан в childResources банка")
        if nd and nd not in VANILLA_NESTED and nd not in ours:
            rep.err(f"{name}: вложенный диалог {nd} — не ванильный обмен и не наш ресурс из банка")
        ar = A(n, "ApprovalRatingID")
        if ar and ar not in reactions:
            rep.err(f"{name}: реакция {ar} не найдена")
        for g in n.findall('./children/node[@id="setflags"]/children/node[@id="flaggroup"]') + \
                n.findall('./children/node[@id="checkflags"]/children/node[@id="flaggroup"]'):
            for f in g.findall('./children/node[@id="flag"]'):
                fu = A(f, "UUID")
                if fu in new_flags and new_flags[fu] != A(g, "type"):
                    rep.err(f"{name}: флаг {fu} типа {new_flags[fu]} стоит в группе {A(g, 'type')}")
                if A(g, "type") != "Global" and A(f, "paramval") is None:
                    rep.err(f"{name}: флаг {fu} в группе {A(g, 'type')} без paramval")
        for t in n.iter("node"):
            if t.get("id") == "TagText":
                h = A(t, "TagText")
                if h in vanilla:
                    continue
                missing = [lang for lang, hs in loca.items() if h not in hs]
                if missing:
                    rep.err(f"{name}: нет текста {h} в {missing}")
    # таймлайн
    t = load(tl_path)
    tc = t.find('./region[@id="TimelineContent"]/node[@id="TimelineContent"]/children')
    eff = tc.find('./node[@id="Effect"]')
    phases = eff.findall('./children/node[@id="Phases"]/children/node[@id="Phase"]')
    starts, s = [], Decimal(0)
    for p in phases:
        starts.append(s)
        s += num(A(p, "Duration"))
        if A(p, "DialogNodeId") not in nodes:
            rep.err(f"{name}: фаза для несуществующего узла {A(p, 'DialogNodeId')}")
    if abs(s - num(A(eff, "Duration"))) > Decimal("0.01"):
        rep.err(f"{name}: Duration эффекта {A(eff, 'Duration')} ≠ сумме фаз {s}")
    pmap = {}
    for o in tc.find('./node[@id="TimelinePhases"]').iter("node"):
        if A(o, "MapKey") is not None:
            pmap[A(o, "MapKey")] = int(A(o, "MapValue"))
    for k, v in pmap.items():
        if k not in nodes or v >= len(phases):
            rep.err(f"{name}: TimelinePhases {k} → {v} неверно")
    actors = {}
    for o in tc.find('./node[@id="TimelineActorData"]').iter("node"):
        if o.get("id") == "Object" and o.get("key") == "MapKey":
            actors[A(o, "MapKey")] = A(o.find('./children/node[@id="Value"]'), "ActorTypeId")
    comps = eff.findall('./children/node[@id="EffectComponents"]/children/node[@id="EffectComponent"]')
    voiced = set()
    for c in comps:
        pi = int(A(c, "PhaseIndex", 0))
        if pi >= len(phases):
            rep.err(f"{name}: компонент {A(c, 'ID')} в несуществующей фазе {pi}")
            continue
        ps, pe = starts[pi], starts[pi] + num(A(phases[pi], "Duration"))
        cs, ce = num(A(c, "StartTime", 0)), num(A(c, "EndTime"))
        if cs < ps - Decimal("0.001") or ce > pe + Decimal("0.001") or ce <= cs:
            rep.err(f"{name}: {A(c, 'Type')} {cs}–{ce} вне фазы {pi} ({ps}–{pe})")
        act = c.find('./children/node[@id="Actor"]')
        if act is not None and A(act, "UUID") not in actors:
            rep.err(f"{name}: актёр {A(act, 'UUID')} ({A(c, 'Type')}) не описан в TimelineActorData")
        cam = c.find('./children/node[@id="CameraContainer"]')
        if cam is not None and actors.get(A(cam, "Object")) != "scenecam":
            rep.err(f"{name}: камера {A(cam, 'Object')} не scenecam")
        for k in c.iter("node"):
            if k.get("id") == "Key":
                for tgt in ("Target", "EyeLookAtTargetId"):
                    if A(k, tgt) and A(k, tgt) not in actors:
                        rep.err(f"{name}: цель взгляда {A(k, tgt)} не актёр")
                kt = A(k, "Time")
                if kt is not None and not (ps - Decimal("0.001") <= num(kt) <= pe + Decimal("0.001")):
                    rep.err(f"{name}: ключ {A(c, 'Type')} в {kt} вне фазы {pi}")
        if A(c, "Type") == "TLVoice":
            voiced.add(A(c, "DialogNodeId"))
            if A(c, "DialogNodeId") not in nodes:
                rep.err(f"{name}: TLVoice для несуществующего узла")
    for u, n in nodes.items():
        has_text = any(t.get("id") == "TagText" for t in n.iter("node"))
        # реплики персонажей (Альфира, третий участник сцены) и ремарки рассказчика; у вариантов героя фаз нет
        if A(n, "constructor") in ("TagAnswer", "TagGreeting") and has_text:
            if u not in pmap:
                rep.err(f"{name}: у реплики {u} нет фазы")
            if u not in voiced:
                rep.err(f"{name}: у реплики {u} нет TLVoice")
    ch = len(tc.find('./node[@id="CombatTimelineHandlers"]').findall('./children/node'))
    if ch != len(phases):
        rep.note(f"{name}: CombatTimelineHandlers {ch} при {len(phases)} фазах")
    # банки
    if A(d.find('.//node[@id="dialog"]'), "TimelineId") != A(tl_res, "ID"):
        rep.err(f"{name}: TimelineId диалога не совпадает с банком таймлайнов")
    if A(tl_res, "DialogResourceId") != A(bank_res, "ID"):
        rep.err(f"{name}: DialogResourceId таймлайна ≠ ID ресурса диалога")
    rep.note(f"{name}: узлов {len(nodes)}, корней {len(roots)}, фаз {len(phases)}, компонентов {len(comps)}, "
             f"длительность {s:.1f} с")


def canon(e):
    """Дерево без форматирования: (тег, id, атрибуты с нормализованными числами, дети)."""
    attrs = []
    for a in e.findall("attribute"):
        v = a.get("value", a.get("handle"))
        if a.get("type") in ("float", "double") and v is not None:
            v = f"{float(v.replace(',', '.')):.4f}"
        attrs.append((a.get("id"), a.get("type"), v, a.get("version")))
    kids = [canon(k) for k in e.findall("./children/node")] if e.tag == "node" else \
        [canon(k) for k in e.findall("./node")]
    return (e.tag, e.get("id"), tuple(sorted(attrs)), tuple(kids))


LSX_ONLY_DIRS = ("Reactions", "DefaultValues", "CharacterCreationPresets")


def round_trip(path: Path, rep: Report, tmp: Path):
    lsf, back = tmp / (path.stem + ".lsf"), tmp / (path.stem + ".back.lsx")
    divine("-a", "convert-resource", "-s", path, "-d", lsf)
    divine("-a", "convert-resource", "-s", lsf, "-d", back)
    a = [canon(r) for r in load(path).findall("region")]
    b = [canon(r) for r in load(back).findall("region")]
    if a != b:
        # В LSF имя региона = имя корневого узла. Реакции, DefaultValues и пресеты характеристик
        # у игры — region «Reactions» / «DefaultValues» / «AbilityDistributionPresets» с узлом
        # «root»: такие файлы существуют только как lsx и в пак идут как lsx (у нас так же).
        if [x[2:] for x in a] == [x[2:] for x in b] and path.parent.name in LSX_ONLY_DIRS:
            rep.note(f"{path.name}: в lsf меняется только имя региона — файл идёт в пак как lsx, как у игры")
        else:
            rep.err(f"круг lsx↔lsf меняет {path.name}")
    return lsf.stat().st_size


def same_but_identifier(a: Path, b: Path) -> bool:
    ra, rb = load(a), load(b)
    for r in (ra, rb):
        for x in r.iter("attribute"):
            if x.get("id") == "Identifier" and x.get("type") == "guid":
                x.set("value", "-")
    def c(e):
        return (e.tag, tuple(sorted(e.attrib.items())), tuple(c(k) for k in e))
    return c(ra) == c(rb)


def schema(root):
    out = set()

    def walk(e, prefix):
        for a in e.findall("attribute"):
            out.add(f"{prefix}@{a.get('id')}")
        for k in (e.findall("./children/node") if e.tag == "node" else e.findall("./node")):
            walk(k, f"{prefix}/{k.get('id')}")
    for r in root.findall("region"):
        walk(r, r.get("id"))
    return out


def main():
    cfg = config()
    src = resolve(cfg["paths"]["mod_src"])
    build = resolve(cfg["paths"]["build"]) / "dialogs"
    man_path = build / "manifest.json"
    if not man_path.exists():
        sys.exit("Нет build/dialogs/manifest.json — сначала python scripts/dialogs/build.py")
    man = json.loads(man_path.read_text(encoding="utf-8"))
    rep = Report()
    loca = {}
    for x in (src / "Mods/_MOD_/Localization").glob("*/*.xml"):
        if x.stem.endswith("_to_F"):
            continue
        loca.setdefault(x.parent.name, set()).update(c.get("contentuid") for c in load(x).findall("content"))
        if b"<!--" in x.read_bytes():
            rep.err(f"{x.name}: XML-комментарий")
    for x in (src / "Mods/_MOD_/Localization").glob("*/*_to_F.xml"):
        base = {c.get("contentuid") for c in load(x).findall("content")}
        extra = base - loca.get(x.parent.name, set())
        if extra:
            rep.err(f"{x.name}: женские варианты без основной строки {sorted(extra)[:3]}")
    reactions = {A(r, "UUID") for p in (src / "Public/_MOD_/ApprovalRatings/Reactions").glob("*.lsx")
                 for r in load(p).iter("node") if r.get("id") == "Reaction" and A(r, "Scope") is not None}
    kinds = {5: "Global", 4: "Object", 6: "Dialog"}
    new_flags = {A(n, "UUID"): kinds[int(A(n, "Usage"))] for p in (src / "Public/_MOD_/Flags").glob("*.lsx")
                 for n in load(p).iter("node") if n.get("id") == "Flags"}
    dbank = load(next((src / "Public/_MOD_/Content/Assets/Dialogs").glob("*/_merged.lsx")))
    tbank = load(next((src / "Public/_MOD_/Content/Generated").glob("*/_merged.lsx")))
    dres = {A(r, "Name"): r for r in dbank.iter("node") if r.get("id") == "Resource"}
    tres = {A(r, "Name"): r for r in tbank.iter("node") if r.get("id") == "Resource"}
    vanilla = set(man["vanilla_handles"])
    ours = {A(r, "ID") for r in dres.values()}
    for num, ch in man.get("chapters", {}).items():
        if ch["dialog"] not in ours:
            rep.err(f"глава {num}: диалога {ch['dialog']} нет в банке")
        if ch["available"] not in new_flags or ch["done"] not in new_flags:
            rep.err(f"глава {num}: нет файлов флагов Available/Done")
    goal = src / "Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Chapters.txt"
    if man.get("chapters"):
        text = goal.read_text(encoding="utf-8") if goal.exists() else ""
        for num, ch in man["chapters"].items():
            if ch["available"] not in text:
                rep.err(f"глава {num}: флаг Available не открывается в {goal.name} (перегенерируйте)")
    for name in man["scenes"]:
        dlg = next((src / "Mods/_MOD_/Story/DialogsBinary").rglob(f"{name}.lsx"))
        tl = src / "Public/_MOD_/Timeline/Generated" / f"{name}.lsf.lsx"
        check_scene(name, dlg, tl, dres[name], tres[name], loca, vanilla, reactions, new_flags, rep, ours)
    # круг через Divine
    # _Scene.lsx игра хранит в формате редактора (mat4x4 текстом): LSLib его не конвертирует даже
    # у ванильных файлов. Такие файлы сверяем с ванильным оригиналом: отличаться может только Identifier.
    files = [p for p in src.rglob("*.lsx") if "Localization" not in p.parts]
    with tempfile.TemporaryDirectory(prefix="alfsv_rt_") as t:
        for p in sorted(files):
            if p.name.endswith("_Scene.lsx") and not p.name.endswith(".lsf.lsx"):
                ok = any(same_but_identifier(p, r / "scene_editor.lsx") for r in (build / "reference").glob("*"))
                (rep.note if ok else rep.err)(f"{'сцена = оригинал' if ok else 'сцена отличается от оригинала'}: {p.name}")
                continue
            size = round_trip(p, rep, Path(t))
            rep.note(f"круг ok: {p.relative_to(src).as_posix()} ({size} Б lsf)")
    # сверка структуры с ванильной основой
    for ref in sorted((build / "reference").glob("*")):
        pairs = [("dialog.lsx", "Mods/_MOD_/Story/DialogsBinary", "{}.lsx"),
                 ("timeline.lsx", "Public/_MOD_/Timeline/Generated", "{}.lsf.lsx"),
                 ("scene.lsx", "Public/_MOD_/Timeline/Generated", "{}_Scene.lsf.lsx")]
        for fname, folder, pattern in pairs:
            van = schema(load(ref / fname))
            for name in man["scenes"]:
                ours_p = next((src / folder).rglob(pattern.format(name)), None)
                if ours_p is None:
                    continue
                ours = schema(load(ours_p))
                missing = sorted(van - ours)
                rep.note(f"сверка {name} / {fname} с {ref.name}: у игры есть, у нас нет — "
                         f"{len(missing)}: {missing[:12]}")
    for n in rep.notes:
        print("  " + n)
    if rep.errors:
        print("\nОШИБКИ:")
        for e in rep.errors:
            print("  " + e)
        sys.exit(1)
    print("Проверка пройдена.")


if __name__ == "__main__":
    main()
