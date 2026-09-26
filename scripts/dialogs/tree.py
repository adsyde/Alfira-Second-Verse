#!/usr/bin/env python3
"""Распечатка сгенерированного диалога деревом: реплики EN/RU, условия, флаги, одобрение, фазы.

  python scripts/dialogs/tree.py                 # все сцены → build/dialogs/<сцена>.md
  python scripts/dialogs/tree.py ALFSV_Alfira_InParty

Для вычитки и для проверки в игре. Тексты озвученных реплик — из loca игры (game-data).
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as et
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import config, enable_utf8_stdout, resolve  # noqa: E402

enable_utf8_stdout()


def A(e, k):
    x = e.find(f'./attribute[@id="{k}"]')
    return None if x is None else (x.get("value") or x.get("handle"))


def main():
    cfg = config()
    src = resolve(cfg["paths"]["mod_src"])
    out_dir = resolve(cfg["paths"]["build"]) / "dialogs"
    man = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    try:
        import gamedb
        gtext, gname = gamedb.text, gamedb.name
    except Exception:
        gtext, gname = (lambda h, lang="en": ""), (lambda g: g[:8])
    loca = {}
    for lang, pat in (("en", "English/*.xml"), ("ru", "Russian/*_ru.xml"), ("ru_f", "Russian/*_to_F.xml")):
        for x in (src / "Mods/_MOD_/Localization").glob(pat):
            for c in et.parse(x).getroot().findall("content"):
                loca.setdefault(lang, {})[c.get("contentuid")] = c.text or ""
    sys.path.insert(0, str(HERE))
    import vanilla
    names = {f.uuid: f.name for cls in (vanilla.F, vanilla.T) for f in vars(cls).values()
             if isinstance(f, vanilla.Flag)}
    for p in (src / "Public/_MOD_/Flags").glob("*.lsx"):
        n = et.parse(p).getroot().find(".//node[@id='Flags']")
        names[A(n, "UUID")] = A(n, "Name")
    react = {}
    for p in (src / "Public/_MOD_/ApprovalRatings/Reactions").glob("*.lsx"):
        r = et.parse(p).getroot()
        top = [n for n in r.iter("node") if n.get("id") == "Reaction" and A(n, "Scope") is not None][0]
        val = [A(n, "value") for n in r.iter("node") if n.get("id") == "Reaction" and A(n, "value") is not None][0]
        react[A(top, "UUID")] = int(val)
    ours = {m["dialog"]: name for name, m in man["scenes"].items()}
    only = sys.argv[1:] or list(man["scenes"])
    for scene in only:
        dlg = next((src / "Mods/_MOD_/Story/DialogsBinary").rglob(f"{scene}.lsx"))
        tl = src / "Public/_MOD_/Timeline/Generated" / f"{scene}.lsf.lsx"
        d = et.parse(dlg).getroot()
        nodes = {A(n, "UUID"): n for n in d.iter("node") if n.get("id") == "node"}
        roots = [A(r, "RootNodes") for r in d.iter("node") if r.get("id") == "RootNodes"]
        phase_dur = {}
        if tl.exists():
            t = et.parse(tl).getroot()
            for p in t.iter("node"):
                if p.get("id") == "Phase":
                    phase_dur[A(p, "DialogNodeId")] = Decimal(A(p, "Duration"))
        num = {}
        lines = [f"# {scene}", "", "Сгенерировано scripts/dialogs/tree.py. 🔊 — голос игры, ✍️ — текст мода.", ""]

        def flags(n, kind):
            out = []
            for g in n.findall(f'./children/node[@id="{kind}"]/children/node[@id="flaggroup"]'):
                for f in g.findall('./children/node[@id="flag"]'):
                    u = A(f, "UUID")
                    nm = names.get(u) or gname(u)
                    who = {"0": "Альфира", "1": "герой"}.get(A(f, "paramval") or "", "")
                    out.append(("" if A(f, "value") == "True" else "!") + nm + (f" [{who}]" if who else ""))
            return out

        def text(n):
            tt = [t for t in n.iter("node") if t.get("id") == "TagText"]
            if not tt:
                return None
            h = A(tt[0], "TagText")
            if h in man["vanilla_handles"]:
                return "🔊", gtext(h, "en"), gtext(h, "ru"), None
            return "✍️", loca.get("en", {}).get(h, "?"), loca.get("ru", {}).get(h, "?"), loca.get("ru_f", {}).get(h)

        def walk(u, depth):
            n = nodes[u]
            pad = "  " * depth
            if u in num:
                lines.append(f"{pad}- ↩ N{num[u]}")
                return
            num[u] = len(num) + 1
            con = A(n, "constructor")
            who = {"0": "**Альфира**", "1": "**Герой**", "-666": "*Рассказчик*"}.get(A(n, "speaker") or "", "")
            head = f"{pad}- N{num[u]} {con}"
            tx = text(n)
            if tx:
                mark, en, ru, ruf = tx
                head += f" {mark} {who}: {en}"
                lines.append(head)
                lines.append(f"{pad}  _{ru}_" + (f" / жен.: _{ruf}_" if ruf else ""))
            else:
                if con == "Nested Dialog":
                    nd = A(n, "NestedDialogNodeUUID")
                    head += f" → {ours.get(nd) or gname(nd)}"
                elif con == "ActiveRoll":
                    head += f" 🎲 {A(n, 'Skill')}"
                elif con == "RollResult":
                    head += " успех" if A(n, "Success") == "True" else " провал"
                else:
                    head += " (без текста)"
                lines.append(head)
            extra = []
            if flags(n, "checkflags"):
                extra.append("если: " + ", ".join(flags(n, "checkflags")))
            if flags(n, "setflags"):
                extra.append("ставит: " + ", ".join(flags(n, "setflags")))
            if A(n, "ApprovalRatingID"):
                extra.append(f"одобрение {react.get(A(n, 'ApprovalRatingID'), '?'):+d}")
            if A(n, "ShowOnce") == "True":
                extra.append("один раз")
            if A(n, "endnode") == "True":
                extra.append("конец")
            if u in phase_dur:
                extra.append(f"фаза {phase_dur[u]:.1f} с")
            if extra:
                lines.append(f"{pad}  · " + " · ".join(extra))
            for c in n.findall('./children/node[@id="children"]/children/node[@id="child"]'):
                walk(A(c, "UUID"), depth + 1)

        for r in roots:
            walk(r, 0)
            lines.append("")
        out = out_dir / f"{scene}.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        print(out)


if __name__ == "__main__":
    main()
