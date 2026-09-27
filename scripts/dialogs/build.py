#!/usr/bin/env python3
"""Генератор диалогов с постановкой: сцены из scripts/dialogs/scenes/*.py → файлы мода в mod/.

  python scripts/dialogs/build.py            # все сцены
  python scripts/dialogs/build.py --dump     # плюс распечатка дерева и фаз в build/dialogs/

Что пишет (всё в mod/, руками эти файлы не правятся — они перезаписываются целиком):
  Mods/_MOD_/Story/DialogsBinary/<папка>/<сцена>.lsx                 диалог (в пак — .lsf)
  Public/_MOD_/Timeline/Generated/<сцена>.lsf.lsx, <сцена>_Scene.lsf.lsx, <сцена>_Scene.lsx
                                                                     таймлайн и сцена (в git не идут)
  Public/_MOD_/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsx банк диалогов
  Public/_MOD_/Content/Generated/[PAK]_GeneratedDialogTimelines/_merged.lsx  банк таймлайнов
  Public/_MOD_/ApprovalRatings/Reactions/<uuid>.lsx                  реакции одобрения
  Public/_MOD_/Flags/<uuid>.lsx                                      новые флаги мода
  Mods/_MOD_/Globals/WLD_Main_A/Characters/<Альфира>.lsx             её глобальный персонаж с
                                                                     HasPlayerApprovalRating (в git не идёт)
  Mods/_MOD_/Localization/English|Russian/AlfiraSecondVerse_*.xml    тексты
  Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Chapters.txt                 Osiris глав разговоров (этап 4)
  Mods/_MOD_/Story/RawFiles/Goals/ALFSV_World.txt                    Osiris реплик на местах и в пути (AD, этап 5)
  Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Reactions.txt                Osiris реакций на поступки (reactions.py)
  build/dialogs/manifest.json                                        ванильные handle (для build_pak)
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import shutil
import sys
import uuid
import xml.etree.ElementTree as et
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

from common import config, enable_utf8_stdout, resolve  # noqa: E402
import bg3lib  # noqa: E402
import dsl  # noqa: E402
from dsl import ACT_LEVELS, ALFIRA, OTHER, PLAYER, Flag, FlagRef, Line, Option, Osi, has_gender, render  # noqa: E402
from staging import Stager  # noqa: E402
import ads  # noqa: E402
import reactions as act_reactions  # noqa: E402
from vanilla import ALFIRA_ORIGIN, ALFIRA_TEMPLATE, APPROVAL_SP1, NARRATOR_SPEAKER, PLAYER_SPEAKER, F  # noqa: E402

enable_utf8_stdout()

# Сцены: вербовка, разговор в отряде и все главы разговоров scenes/chNN_*.py (подхватываются сами).
SCENES = ["recruitment", "inparty"] + sorted(p.stem for p in (HERE / "scenes").glob("ch[0-9][0-9]_*.py"))
CHAPTERS_GOAL = "Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Chapters.txt"
WORLD_GOAL = "Mods/_MOD_/Story/RawFiles/Goals/ALFSV_World.txt"
REACTIONS_GOAL = "Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Reactions.txt"
# Женские формы обращения к героине: отдельный файл <имя>_to_F.xml рядом с русским (как
# russian_to_F.loca у игры). Проверить в игре; если игра не различает — выключить.
FEMALE_VARIANTS = True
LOCA_NAME = "AlfiraSecondVerse"
BANK_DIR = "Public/_MOD_/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs"
TL_BANK_DIR = "Public/_MOD_/Content/Generated/[PAK]_GeneratedDialogTimelines"
# Папки, которыми генератор владеет целиком (очищаются перед записью).
OWNED = ["Mods/_MOD_/Story/DialogsBinary", "Public/_MOD_/Timeline", "Public/_MOD_/Content",
         "Public/_MOD_/ApprovalRatings", "Public/_MOD_/Flags", "Mods/_MOD_/Globals"]
SPEAKER_UUID = {ALFIRA: ALFIRA_TEMPLATE, PLAYER: PLAYER_SPEAKER}
NULL = "NULL_00000000-0000-0000-0000-000000000000"
ALFIRA_OSI_NAME = "S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c"
FLAG_USAGE = {"Global": 5, "Object": 4, "Dialog": 6}


class Ids:
    def __init__(self, mod_uuid: str):
        self.ns = uuid.UUID(mod_uuid)

    def uid(self, key: str) -> str:
        return str(uuid.uuid5(self.ns, key))

    def handle(self, key: str) -> str:
        return "h" + self.uid(key + "/text").replace("-", "g")

    def flag(self, f: Flag) -> str:
        return f.uuid if not f.new else self.uid(f"flag/{f.name}")

    def reaction(self, value: int) -> str:
        return self.uid(f"reaction/alfira/{value:+d}")


class Compiler:
    """Одна сцена → диалог, таймлайн, сцена, записи банков, тексты."""

    def __init__(self, lib: bg3lib.Lib, scene: dsl.Scene, ids: Ids, voice_meta: set[str], chapters=()):
        self.lib, self.b, self.s, self.ids = lib, lib.b, scene, ids
        self.voice_meta = voice_meta
        # сцены глав со входом в разговоре в отряде (hub); главы-события (hub=False) запускает их Osiris
        self.chapters = sorted((c for c in chapters if c.chapter.hub), key=lambda c: c.chapter.number)
        self.slot = {ALFIRA: ALFIRA, PLAYER: PLAYER}   # логический спикер → слот основы (run() уточняет)
        self.speaker_uuid = dict(SPEAKER_UUID)
        self.loca = {}           # handle → (en, ru_m, ru_f | None)
        self.vanilla_handles = set()
        self.reactions = set()
        self.flags = set()
        self.npc = []            # (uuid, Line) в порядке появления — для фаз
        self.done_blocks = set()
        self.done_opts = {}
        self.alt_ends = set()
        self.voices = {}         # handle → (диалог, узел, версия)

    def uid(self, key):
        return self.ids.uid(f"{self.s.name}/{key}")

    # --- флаги ---

    def groups(self, refs):
        by = {}
        for r in refs:
            if not isinstance(r, FlagRef):
                raise TypeError(f"{self.s.name}: ожидался флаг вида FLAG(спикер), получено {r!r}")
            if r.flag.new:
                self.flags.add(r.flag)
            spk = None if r.flag.kind == "Global" else self.slot[r.speaker]
            by.setdefault(r.flag.kind, []).append(self.b.flag(self.ids.flag(r.flag), r.value, spk))
        return [self.b.flag_group(k, v) for k, v in by.items()]

    def approval(self, value):
        if not value:
            return None
        self.reactions.add(value)
        return self.ids.reaction(value)

    # --- тексты ---

    def text(self, key, en, ru, line_key, narrator=False):
        h = self.ids.handle(f"{self.s.name}/{key}")
        female = render(ru, True, narrator) if has_gender(ru) else None
        self.loca[h] = (render(en, narrator=narrator), render(ru, narrator=narrator), female)
        return self.b.text_content(h, 1, self.uid(f"{line_key}/line"))

    def line_text(self, key, line: Line):
        if line.handle:
            if line.handle not in self.voices:
                raise RuntimeError(f"{self.s.name}: реплика {line.handle} не найдена в {self.s.voice_from}")
            if line.handle not in self.voice_meta:
                raise RuntimeError(f"{self.s.name}: у реплики {line.handle} нет озвучки Альфиры (VoiceMeta)")
            _, _, version = self.voices[line.handle]
            self.vanilla_handles.add(line.handle)
            return self.b.text_content(line.handle, version, self.uid(f"{key}/line"))
        return self.text(key, line.en, line.ru, key, narrator=line.narrator)

    # --- узлы ---

    def entry(self, block_id):
        if block_id not in self.s.blocks:
            raise KeyError(f"{self.s.name}: нет блока {block_id!r}")
        blk = self.s.blocks[block_id]
        if not blk.lines:
            return [self.option(o, f"{block_id}.o{i}") for i, o in enumerate(blk.next.choices)]
        if block_id not in self.done_blocks:
            self.done_blocks.add(block_id)
            self.lines(block_id, blk.lines, blk.next, when=blk.when)
        return [self.uid(f"{block_id}.0")]

    def after(self, nx, prefix):
        if isinstance(nx.go, list):
            # альтернативы: игра берёт первого ребёнка, чьи условия выполнены; если у последнего
            # есть условия — в конце пустой узел «конец», как у Larian
            out = [u for g in nx.go for u in self.entry(g)]
            if self.s.blocks[nx.go[-1]].when:
                end = self.uid(f"{prefix}.altend")
                if end not in self.alt_ends:
                    self.alt_ends.add(end)
                    self.d.create_standard_dialog_node(end, ALFIRA_TEMPLATE, [], None, end_node=True)
                out.append(end)
            return out
        if nx.go:
            return self.entry(nx.go)
        if nx.choices:
            return [self.option(o, f"{prefix}.o{i}") for i, o in enumerate(nx.choices)]
        if nx.join:
            return self.join(nx.join, prefix)
        return []

    def lines(self, prefix, lines, nx, *, root=False, when=(), first_set=(), first_approve=0):
        ids = [self.uid(f"{prefix}.{i}") for i in range(len(lines))]
        self.npc.extend(zip(ids, lines))      # фазы в порядке чтения сцены
        for i, (nid, line) in enumerate(zip(ids, lines)):
            last = i == len(lines) - 1
            children = self.after(nx, prefix) if last else [ids[i + 1]]
            sets = list(line.set) + (list(first_set) if i == 0 else []) + (list(nx.set) if last else [])
            self.d.create_standard_dialog_node(
                nid, NARRATOR_SPEAKER if line.narrator else self.speaker_uuid[line.speaker], children,
                self.line_text(f"{prefix}.{i}", line),
                constructor=self.b.dialog_object.GREETING if root and i == 0 else self.b.dialog_object.ANSWER,
                setflags=self.groups(sets), checkflags=self.groups(when) if i == 0 else [],
                root=root and i == 0, end_node=last and nx.end,
                approval_rating_uuid=self.approval(line.approve + (first_approve if i == 0 else 0)))
        return ids[0]

    def option(self, o: Option, key):
        key = o.key or key
        if id(o) in self.done_opts:
            return self.done_opts[id(o)]
        nid = self.uid(key)
        self.done_opts[id(o)] = nid
        if o.game_line:
            handle, version = o.game_line
            self.vanilla_handles.add(handle)
            text = self.b.text_content(handle, version, self.uid(f"{key}/line"))
        else:
            text = self.text(key, o.en, o.ru, key)
        if o.roll:
            r = o.roll
            ok = self.lines(f"{key}.ok", r.success.reply, r.success.next, first_set=r.success.set,
                            first_approve=r.success.approve)
            fail = self.lines(f"{key}.fail", r.failure.reply, r.failure.next, first_set=r.failure.set,
                              first_approve=r.failure.approve)
            self.d.create_roll_dialog_node(
                nid, PLAYER_SPEAKER, self.speaker_uuid[r.target], r.ability, r.skill, r.dc, ok, fail, text,
                checkflags=self.groups(o.when), transition_mode=True, show_once=True, validated_has_value=False)
            return nid
        nx = o.next
        if o.reply:
            children = [self.lines(f"{key}.r", o.reply, nx)]
            sets = list(o.set)
        else:
            children = self.after(nx, key)
            sets = list(o.set) + list(nx.set)
        self.d.create_standard_dialog_node(
            nid, PLAYER_SPEAKER, children, text, constructor=self.b.dialog_object.QUESTION,
            setflags=self.groups(sets), checkflags=self.groups(o.when), show_once=o.once,
            end_node=not o.reply and nx.end, approval_rating_uuid=self.approval(o.approve),
            validated_has_value=False)
        return nid

    def join(self, j: dsl.Join, prefix):
        """Как в вербовке Уилла/Лаэ'зель: при полном отряде — вложенный диалог замены."""
        nested, add = self.uid(f"{prefix}.swap"), self.uid(f"{prefix}.join")
        swap_children = []
        if j.to_camp_line is not None:
            camp = self.uid(f"{prefix}.camp")
            self.d.create_standard_dialog_node(
                camp, ALFIRA_TEMPLATE, [], self.line_text(f"{prefix}.camp", j.to_camp_line),
                setflags=self.groups([F.InvitedToCampWalk(ALFIRA)]),
                checkflags=self.groups([j.to_camp_flag(PLAYER)]), end_node=True)
            self.npc.append((camp, j.to_camp_line))
            swap_children.append(camp)
        end = self.uid(f"{prefix}.swapend")
        self.d.create_standard_dialog_node(end, ALFIRA_TEMPLATE, [], None, end_node=True)
        swap_children.append(end)
        self.nested_node(nested, j.nested, swap_children, self.groups([F.MaxPlayerCount.on]))
        reply = j.reply
        self.d.create_standard_dialog_node(
            add, ALFIRA_TEMPLATE, [], self.line_text(f"{prefix}.join", reply) if reply else None,
            setflags=self.groups([F.OriginAddToParty(ALFIRA)]), end_node=True)
        if reply:
            self.npc.append((add, reply))
        return [nested, add]

    def chapter_entries(self):
        """Входы в главы (Scene.chapter_entries): корень без текста → вложенный диалог главы → конец.

        Так устроены главы Шэдоухарт: корень ShadowHeart_InParty2 с условиями темы и без текста,
        под ним узел Nested Dialog на ShadowHeart_InParty2_Nested_*Chapter.
        """
        out = []
        for sc in self.chapters:
            ch, key = sc.chapter, f"@chapter{sc.chapter.number:02d}"
            when = [ch.available_flag.on, ch.done_flag.off, *ch.when]
            if ch.approval is not None:
                if ch.approval not in APPROVAL_SP1:
                    raise ValueError(f"глава {ch.number}: порога одобрения {ch.approval} у игры нет; есть {sorted(APPROVAL_SP1)}")
                when.append(APPROVAL_SP1[ch.approval](ALFIRA))
            nested, end = self.uid(f"{key}.nested"), self.uid(f"{key}.end")
            self.d.create_standard_dialog_node(end, ALFIRA_TEMPLATE, [], None, end_node=True)
            self.nested_node(nested, sc.dialog_id, [end], [])
            # when_any — «или» как у Larian: по корню на каждый вариант, под ними один и тот же вложенный диалог
            for i, extra in enumerate(ch.when_any or [[]]):
                entry = self.uid(key if i == 0 else f"{key}.any{i}")
                self.d.create_standard_dialog_node(
                    entry, ALFIRA_TEMPLATE, [nested], None, constructor=self.b.dialog_object.GREETING,
                    checkflags=self.groups(when + list(extra)), root=True)
                out.append(entry)
        return out

    def nested_node(self, nid, nested, children, checkflags):
        n = et.fromstring(
            '<node id="node" key="UUID"><attribute id="constructor" type="FixedString" value="Nested Dialog" />'
            f'<attribute id="UUID" type="FixedString" value="{nid}" />'
            f'<attribute id="NestedDialogNodeUUID" type="guid" value="{nested}" /><children>'
            '<node id="children"><children>'
            + "".join(f'<node id="child"><attribute id="UUID" type="FixedString" value="{c}" /></node>' for c in children)
            + '</children></node><node id="Tags" /><node id="setflags" /><node id="checkflags"><children>'
            + "".join(et.tostring(g.to_xml()).decode() for g in checkflags)
            + '</children></node><node id="SpeakerLinking"><children>'
            + "".join(f'<node id="SpeakerLinkingEntry"><attribute id="Key" type="int32" value="{k}" />'
                      f'<attribute id="Value" type="int32" value="{k}" /></node>'
                      for k in (self.slot[ALFIRA], self.slot[PLAYER]))
            + '</children></node></children></node>')
        self.d.add_dialog_node(n)

    # --- сцена целиком ---

    def base_scene_file(self):
        tl_uuid = self.lib.assets.index.get_entry(self.s.base)["timeline_uuid"]
        src = self.lib.assets.index.get_timeline_resource(tl_uuid).find('./attribute[@id="SourceFile"]').get("value")
        return src[:-4] + "_Scene.lsf"

    def index_voices(self):
        for name in self.s.voice_from:
            d = self.lib.assets.get_dialog_object(name)
            for n in d.get_dialog_nodes():
                nid = n.find('./attribute[@id="UUID"]').get("value")
                for t in d.get_tagged_texts(nid):
                    a = t.find('./attribute[@id="TagText"]')
                    self.voices.setdefault(a.get("handle"), (name, nid, int(a.get("version") or 1)))

    def run(self):
        s, b, lib = self.s, self.b, self.lib
        bg3lib.seed_uuids(b, s.name)
        self.index_voices()
        timeline_id = self.ids.uid(f"{s.name}/timeline")
        bundle = lib.assets.create_new_empty_dialog_from_another(s.base, s.name, s.dialog_id, timeline_id, s.subfolder)
        self.bundle = bundle
        self.d = b.dialog_object(bundle.dialog)
        # слоты спикеров — из основы: у основ на двоих Альфира 0 и герой 1, у сцены на троих — как у Larian
        speakers = list(self.d.get_speakers())
        want = {ALFIRA: ALFIRA_TEMPLATE} if s.kind == "ad" else {ALFIRA: ALFIRA_TEMPLATE, PLAYER: PLAYER_SPEAKER}
        if s.other:
            want[OTHER] = s.other
            self.speaker_uuid[OTHER] = s.other
        for role, u in want.items():
            if u not in speakers:
                raise RuntimeError(f"{s.name}: в основе {s.base} нет спикера {u} (спикеры: {speakers})")
            self.slot[role] = speakers.index(u)
        if len(speakers) != len(want):
            raise RuntimeError(f"{s.name}: у основы {s.base} {len(speakers)} спикеров, в сцене описано {len(want)}")
        # актёр-«таймлайн» (если есть в основе) должен указывать на новый таймлайн
        base_tl_id = lib.assets.index.get_entry(s.base)["timeline_uuid"]
        for actor in bundle.timeline.root_node.iter("node"):
            if actor.get("id") == "Object" and actor.get("key") == "MapKey":
                a = actor.find('./attribute[@id="MapKey"]')
                if a is not None and a.get("value") == base_tl_id:
                    a.set("value", timeline_id)
        # обработчики боя: по одному на фазу (их добавляет create_new_phase), от основы не нужны
        cth = bundle.timeline.root_node.find('.//node[@id="CombatTimelineHandlers"]/children')
        if cth is not None:
            for h in list(cth):
                cth.remove(h)
        roots = []
        for bid in s.roots:
            blk = s.blocks[bid]
            self.done_blocks.add(bid)
            if blk.chapters:
                roots.extend(self.chapter_entries())
                continue
            roots.append(self.lines(bid, blk.lines, blk.next, root=True, when=blk.when))
        for r in roots:
            self.d.add_root_node(r)
        # постановка
        tl = b.timeline_object(bundle.timeline, self.d)
        if s.kind == "ad":
            return self.run_ad(tl)
        base_tl = lib.assets.get_timeline_object(s.base)
        base_d = lib.assets.get_dialog_object(s.base)
        self.stager = st = Stager(lib, tl, self.d, base_tl, base_d, ALFIRA_TEMPLATE, PLAYER_SPEAKER,
                                  lambda k: self.uid(k), other_template=s.other,
                                  base_scene_file=self.base_scene_file())
        for nid, line in self.npc:
            if line.handle:
                src, src_node, _ = self.voices[line.handle]
                st.voiced_phase(nid, src, src_node)
            elif line.narrator:
                st.narrator_phase(nid, line)
            else:
                st.text_phase(nid, line)
        # записи банков
        dres = lib.assets.get_dialog_resource(s.dialog_id)
        sub = f"{s.subfolder}/" if s.subfolder else ""
        set_attr(dres, "Name", s.name, "LSString")
        set_attr(dres, "SourceFile", f"Mods/_MOD_/Story/Dialogs/{sub}{s.name}.lsj", "LSString")
        ch = dres.find("./children")
        for old in ch.findall('./node[@id="childResources"]'):
            ch.remove(old)
        nested = list(s.nested)
        if any(b.chapters for b in s.blocks.values()):
            nested += [c.dialog_id for c in self.chapters]      # только главы со входом в отряде (hub)
        for n in nested:
            et.SubElement(et.SubElement(ch, "node", {"id": "childResources"}), "attribute",
                          {"id": "Object", "type": "guid", "value": n})
        tres = lib.assets.get_timeline_resource(timeline_id)
        set_attr(tres, "Name", s.name, "LSString")
        set_attr(tres, "SourceFile", f"Public/_MOD_/Timeline/Generated/{s.name}.lsf", "LSString")
        set_attr(tres, "EditorSourceFile", f"Editor/Mods/_MOD_/Timeline/Generated/{s.name}.tml", "LSString")
        tch = tres.find("./children")
        for cam in st.added_cams:
            et.SubElement(et.SubElement(tch, "node", {"id": "DependencyCache"}), "attribute",
                          {"id": "Object", "type": "guid", "value": cam})
        self.dres, self.tres = dres, tres
        return self

    def run_ad(self, tl):
        """AD: категория как у Larian, фазы — ADStager (голос и эмоции, без камер), записи банков."""
        s, lib = self.s, self.lib
        dnode = self.bundle.dialog.root_node.find('./region[@id="dialog"]/node[@id="dialog"]')
        if s.category:
            set_attr(dnode, "category", s.category, "LSString")
        self.stager = st = ads.ADStager(lib, tl, lambda k: self.uid(k))
        for nid, line in self.npc:
            if line.handle:
                src, src_node, _ = self.voices[line.handle]
                st.voiced_phase(nid, src, src_node)
            else:
                st.text_phase(nid, line)
        dres = lib.assets.get_dialog_resource(s.dialog_id)
        sub = f"{s.subfolder}/" if s.subfolder else ""
        set_attr(dres, "Name", s.name, "LSString")
        set_attr(dres, "SourceFile", f"Mods/_MOD_/Story/Dialogs/{sub}{s.name}.lsj", "LSString")
        timeline_id = self.ids.uid(f"{s.name}/timeline")
        tres = lib.assets.get_timeline_resource(timeline_id)
        set_attr(tres, "Name", s.name, "LSString")
        set_attr(tres, "SourceFile", f"Public/_MOD_/Timeline/Generated/{s.name}.lsf", "LSString")
        set_attr(tres, "EditorSourceFile", f"Editor/Mods/_MOD_/Timeline/Generated/{s.name}.tml", "LSString")
        self.dres, self.tres = dres, tres
        return self


def set_attr(e, name, value, typ):
    a = e.find(f'./attribute[@id="{name}"]')
    if a is None:
        a = et.SubElement(e, "attribute", {"id": name, "type": typ})
        c = e.find("./children")
        if c is not None:
            e.remove(a)
            e.insert(list(e).index(c), a)
    a.set("type", typ)
    a.set("value", value)


# --- запись файлов -------------------------------------------------------------------------------

def write_xml(root, path: Path, declaration=True):
    root = copy.deepcopy(root)
    et.indent(root, space="\t")
    path.parent.mkdir(parents=True, exist_ok=True)
    body = et.tostring(root, encoding="unicode")
    path.write_text(('<?xml version="1.0" encoding="utf-8"?>\n' if declaration else "") + body + "\n",
                    encoding="utf-8", newline="\n")


def bank(region, resources, meta):
    root = et.fromstring(f'<save><version major="4" minor="0" revision="9" build="0" lslib_meta="{meta}" />'
                         f'<region id="{region}"><node id="{region}"><children /></node></region></save>')
    ch = root.find(f'./region/node/children')
    for r in resources:
        ch.append(copy.deepcopy(r))
    return root


def loca_xml(entries):
    root = et.Element("contentList")
    for h in sorted(entries):
        c = et.SubElement(root, "content", {"contentuid": h, "version": "1"})
        c.text = entries[h]
    return root


def reaction_xml(ruid, value):
    return et.fromstring(
        '<save><version major="4" minor="0" revision="9" build="320"/><region id="Reactions"><node id="root"><children>'
        f'<node id="Reaction"><attribute id="Scope" type="uint8" value="1"/><attribute id="UUID" type="guid" value="{ruid}"/>'
        '<children><node id="Reactions"><children><node id="Reaction">'
        f'<attribute id="id" type="guid" value="{ALFIRA_ORIGIN}"/><attribute id="value" type="int32" value="{value}"/>'
        '</node></children></node></children></node></children></node></region></save>')


def flag_xml(fuid, f: Flag):
    return et.fromstring(
        '<save><version major="4" minor="5" revision="0" build="0" lslib_meta="v1,bswap_guids,lsf_keys_adjacency" />'
        f'<region id="Flags"><node id="Flags"><attribute id="UUID" type="guid" value="{fuid}" />'
        f'<attribute id="Name" type="FixedString" value="{f.name}" />'
        f'<attribute id="Description" type="LSString" value="{f.description}" />'
        f'<attribute id="Usage" type="uint8" value="{FLAG_USAGE[f.kind]}" /></node></region></save>')


def character_override(lib):
    """Её глобальный персонаж из игры + HasPlayerApprovalRating (как у Хальсина и Минтары)."""
    f = lib.game_file("Mods/Gustav/Globals/WLD_Main_A/Characters/_merged.lsf")
    for go in f.root_node.iter("node"):
        if go.get("id") == "GameObjects" and (go.find('./attribute[@id="MapKey"]') is not None) \
                and go.find('./attribute[@id="MapKey"]').get("value") == ALFIRA_TEMPLATE:
            obj = copy.deepcopy(go)
            break
    else:
        raise RuntimeError("не нашёл S_DEN_Bard в Globals/WLD_Main_A")
    if obj.find('./attribute[@id="HasPlayerApprovalRating"]') is not None:
        raise RuntimeError("у S_DEN_Bard в игре уже есть HasPlayerApprovalRating — переопределение не нужно")
    set_attr(obj, "HasPlayerApprovalRating", "True", "bool")
    ver = copy.deepcopy(f.root_node.find("./version"))
    root = et.fromstring('<save><region id="Templates"><node id="Templates"><children /></node></region></save>')
    root.insert(0, ver)
    root.find("./region/node/children").append(obj)
    return root


# --- проверки по данным игры -------------------------------------------------------------------

def check_vanilla(lib, scenes):
    errors = []
    emo = lib.game_file("Public/Shared/Animation/Emotions.lsf")
    table = {}
    for o in emo.root_node.iter("node"):
        k, v = o.find('./attribute[@id="MapKey"]'), o.find('./attribute[@id="MapValue"]')
        if k is not None and v is not None and k.get("type") == "int32":
            table[v.get("value").lower()] = int(k.get("value"))
    if table != dsl.EMOTIONS:
        errors.append(f"таблица эмоций не совпадает с Emotions.lsf: {table}")
    reg = lib.b.flag_registry(lib.tool)
    used = set()
    for s in scenes:
        for blk in s.blocks.values():
            stack = [blk]
            while stack:
                x = stack.pop()
                for fld in ("when", "set"):
                    for r in getattr(x, fld, []) or []:
                        used.add(r.flag)
                for ln in getattr(x, "lines", []) + getattr(x, "reply", []):
                    stack.append(ln)
                nx = getattr(x, "next", None)
                if nx is not None:
                    for r in nx.set:
                        used.add(r.flag)
                    stack.extend(nx.choices)
                roll = getattr(x, "roll", None)
                if roll:
                    stack.extend([roll.success, roll.failure])
        if s.chapter is not None:
            for r in s.chapter.story + s.chapter.story_any + s.chapter.when + [x for w in s.chapter.when_any for x in w]:
                if isinstance(r, FlagRef):
                    used.add(r.flag)
            if s.chapter.approval is not None:
                used.add(APPROVAL_SP1[s.chapter.approval])
    for fl in [v for v in vars(F).values() if isinstance(v, Flag)]:
        used.add(fl)
    for fl in used:
        if fl.new:
            continue
        if fl.kind == "Tag":
            for pack in ("Shared", "Gustav", "GustavDev"):     # REALLY_DARK_URGE — в GustavDev
                path = f"Public/{pack}/Tags/{fl.uuid}.lsf"
                try:
                    lib.assets.index.get_pak_by_file(path)
                    break
                except RuntimeError:
                    continue
            else:
                errors.append(f"тег {fl.name} ({fl.uuid}) не найден в Public/*/Tags игры")
                continue
            t = lib.game_file(path)
            name = t.root_node.find('.//attribute[@id="Name"]').get("value")
            if name != fl.name:
                errors.append(f"тег {fl.uuid}: в игре {name}, у нас {fl.name}")
            continue
        try:
            fo = reg.get_flag(fl.uuid)
        except KeyError:
            errors.append(f"флаг {fl.name} ({fl.uuid}) не найден в игре")
            continue
        if fo.name != fl.name:
            errors.append(f"флаг {fl.uuid}: в игре {fo.name}, у нас {fl.name}")
        want = {"Global": (5,), "Object": (4, 5, 6), "Dialog": (6,)}[fl.kind]
        if fo.usage not in want:
            errors.append(f"флаг {fl.name}: Usage {fo.usage}, а используется как {fl.kind}")
    return errors


def voice_meta_handles(lib):
    sb = lib.files.get_soundbank_file(ALFIRA_TEMPLATE)
    return {n.find('./attribute[@id="MapKey"]').get("value") for n in sb.root_node.iter("node")
            if n.get("id") == "VoiceTextMetaData"}


# --- main --------------------------------------------------------------------------------------

OSIRIS_FLAGS = []   # новые флаги, которые ставит или читает только Osiris (файлы флагов нужны всё равно)


def load_scenes():
    """Сцены из SCENES. Модуль сцены может добавить EXTRA_SCENES (ещё диалоги той же главы, например
    сцену на троих) и OSIRIS_FLAGS (флаги, которые ставит только его Osiris)."""
    out = []
    OSIRIS_FLAGS.clear()
    for name in SCENES:
        mod = importlib.import_module(f"scenes.{name}")
        out.append(mod.SCENE)
        out += list(getattr(mod, "EXTRA_SCENES", []))
        OSIRIS_FLAGS.extend(getattr(mod, "OSIRIS_FLAGS", []))
    places, trv = load_world()
    out += [p.scene for p in places] + [trv.scene]
    chapters = [s for s in out if s.chapter is not None]
    nums = sorted(s.chapter.number for s in chapters)
    if nums != list(range(1, len(nums) + 1)):
        sys.exit(f"Номера глав должны идти подряд с 1, сейчас {nums}")
    hubs = [s.name for s in out if any(b.chapters for b in s.blocks.values())]
    if chapters and len(hubs) != 1:
        sys.exit(f"Входы в главы (Scene.chapter_entries) должны быть ровно в одной сцене, сейчас: {hubs}")
    return out


def load_world():
    """Реплики на местах (scenes/places.py) и фразы в пути (scenes/travel.py)."""
    from scenes.places import PLACES
    from scenes.travel import TRAVEL
    keys = [p.key for p in PLACES]
    if len(keys) != len(set(keys)):
        sys.exit(f"Повторяются ключи мест: {sorted(k for k in keys if keys.count(k) > 1)}")
    return PLACES, TRAVEL


# --- Osiris глав -------------------------------------------------------------------------------

def chapters_goal(chapters, ids) -> str:
    """Goal ALFSV_Chapters: когда глава становится доступной. Генерируется из chapter(...) сцен.

    Правила, а не факты INIT: при обновлении мода Osiris заменяет правила в уже начатой игре
    (story patching), а INIT существующего goal повторно не выполняет. Поэтому новые главы
    доходят до старых сохранений. Единственный вызов в INIT — для сохранений, где goal новый.

    Очередь (scripts/dialogs/README.md, «Очередь глав»): глава N открывается, когда никакая глава не
    ждёт (Available и не Done), сыграны все обязательные главы до неё, выполнены story/story_any, акт тот
    и (after_rest) это проверка после отдыха. Правила глав идут по номерам: первая открывшаяся глава
    «ждёт», и следующие в той же проверке уже не открываются — одна новая глава за проверку.
    """
    def fl(f):
        return f"(FLAG){f.name}_{ids.flag(f)}"

    def cond(r):
        if isinstance(r, Osi):
            return r.condition
        return f"{'' if r.value else 'NOT '}DB_GlobalFlag({fl(r.flag)})"

    acts = sorted({sc.chapter.act for sc in chapters if sc.chapter.act is not None})
    out = ["Version 1", "SubGoalCombiner SGC_AND", "INITSECTION",
           "// GENERATED by scripts/dialogs/build.py from scripts/dialogs/scenes/ch*.py (chapter(...)).",
           "// Do not edit: change the chapter declaration and rebuild. See scripts/dialogs/README.md.",
           "// Alfira's conversation chapters (design/APPROVAL.md section 4): one new chapter at a time, in order;",
           "// optional chapters whose story condition is not met do not hold the queue.",
           "// ALFSV_ChapterNN_Available is set here, ALFSV_ChapterNN_Done by the chapter dialog itself.",
           "// A save made before chapters existed (Alfira already recruited): the goal is new there, so this",
           "// INIT runs on story patching and opens the chapters that do not wait for a rest.",
           "PROC_ALFSV_Chapters_Unlock(0);",
           "KBSECTION",
           "//REGION When to look for a new chapter", "",
           "// After every long rest (GLO_Camp.txt: PROC_Camp_EveryoneAwake -> PROC_LongRest)",
           "PROC", "PROC_LongRest()", "AND", "DB_ALFSV_IsCompanion(1)", "THEN",
           "PROC_ALFSV_Chapters_Unlock(1);", "",
           "// Chapters that do not wait for a rest: at recruitment and when a chapter has been played",
           "IF", "DB_ALFSV_IsCompanion(1)", "THEN", "PROC_ALFSV_Chapters_Unlock(0);", ""]
    for sc in chapters:
        out += ["IF", f"FlagSet({fl(sc.chapter.done_flag)}, {NULL}, _)", "AND", "DB_ALFSV_IsCompanion(1)",
                "THEN", "PROC_ALFSV_Chapters_Unlock(0);", ""]
    # главы, которые не ждут отдыха, открываются, как только наступило их событие сюжета (флаг)
    seen = set()
    for sc in chapters:
        if sc.chapter.after_rest:
            continue
        for r in sc.chapter.story + sc.chapter.story_any:
            if isinstance(r, FlagRef) and r.value and r.flag not in seen:
                seen.add(r.flag)
                out += [f"// Chapter {sc.chapter.number} does not wait for a rest: its story event opens it",
                        "IF", f"FlagSet({fl(r.flag)}, {NULL}, _)", "AND", "DB_ALFSV_IsCompanion(1)",
                        "THEN", "PROC_ALFSV_Chapters_Unlock(0);", ""]
    if acts:
        out += ["// A new level (e.g. the next act): act-bound chapters stop waiting",
                "IF", "LevelGameplayStarted(_, _)", "AND", "DB_ALFSV_IsCompanion(1)", "THEN",
                "PROC_ALFSV_Chapters_Unlock(0);", ""]
    out += ["// Debug (Script Extender console): Osi.PROC_ALFSV_Debug_UnlockChapter() - as if a long rest had passed",
            "PROC", "PROC_ALFSV_Debug_UnlockChapter()", "THEN", "PROC_ALFSV_Chapters_Unlock(1);", "",
            "//END_REGION", "", "//REGION Queue: a chapter is waiting (unlocked, not played yet)", ""]
    for sc in chapters:
        ch = sc.chapter
        out += ["QRY", "QRY_ALFSV_Chapters_Waiting()", "AND", f"DB_GlobalFlag({fl(ch.available_flag)})", "AND",
                f"NOT DB_GlobalFlag({fl(ch.done_flag)})", "THEN", "DB_NOOP(1);", ""]
    out += ["//END_REGION", ""]
    if any(sc.chapter.optional and (sc.chapter.approval or 0) > 0 for sc in chapters):
        out += ["//REGION Approval of any avatar (DB_ApprovalRating) for optional chapters with an entry threshold", "",
                "QRY", "QRY_ALFSV_Chapters_Approval((INTEGER)_AtLeast)", "AND", "DB_Avatars(_Avatar)", "AND",
                f"DB_ApprovalRating({ALFIRA_OSI_NAME}, _Avatar, _Value)", "AND", "_Value >= _AtLeast", "THEN",
                "DB_NOOP(1);", "", "//END_REGION", ""]
    if acts:
        out += ["//REGION Acts (DB_CurrentLevel; levels per act - scripts/dialogs/dsl.py ACT_LEVELS)", ""]
        for a in acts:
            for lvl in ACT_LEVELS[a]:
                out += ["QRY", "QRY_ALFSV_Chapters_InAct((INTEGER)_Act)", "AND", f"_Act == {a}", "AND",
                        f'DB_CurrentLevel("{lvl}")', "THEN", "DB_NOOP(1);", ""]
        out += ["//END_REGION", ""]
    out += ["//REGION Chapters", ""]
    for sc in chapters:
        ch = sc.chapter
        if ch.story_any:
            out.append(f"// Chapter {ch.number}: any of these story events")
            for r in ch.story_any:
                out += ["QRY", f"QRY_ALFSV_Chapter{ch.number:02d}_StoryAny()", "AND", cond(r), "THEN", "DB_NOOP(1);", ""]
    for sc in chapters:
        ch = sc.chapter
        # закрыть главу, которая открылась, но больше не может быть сыграна: кончился её акт или снят флаг story
        if ch.act is not None:
            out += [f"// Chapter {ch.number} is bound to act {ch.act}: unlocked but not played before the act ended -"
                    " it no longer waits",
                    "PROC", "PROC_ALFSV_Chapters_Unlock((INTEGER)_AtRest)", "AND",
                    f"DB_GlobalFlag({fl(ch.available_flag)})", "AND", f"NOT DB_GlobalFlag({fl(ch.done_flag)})", "AND",
                    f"NOT QRY_ALFSV_Chapters_InAct({ch.act})", "THEN",
                    f"PROC_GlobalClearFlagAndCache({fl(ch.available_flag)});", ""]
        if ch.expire:
            for r in ch.story:
                if isinstance(r, FlagRef) and r.value:
                    out += [f"// Chapter {ch.number} expires: its story flag is cleared before it was played",
                            "IF", f"FlagCleared({fl(r.flag)}, {NULL}, _)", "AND",
                            f"DB_GlobalFlag({fl(ch.available_flag)})", "AND",
                            f"NOT DB_GlobalFlag({fl(ch.done_flag)})", "THEN",
                            f"PROC_GlobalClearFlagAndCache({fl(ch.available_flag)});", ""]
    for sc in sorted(chapters, key=lambda c: (-c.chapter.priority, c.chapter.number)):
        ch = sc.chapter
        required = [p.chapter for p in chapters if p.chapter.number < ch.number and not p.chapter.optional]
        when = "after a long rest" if ch.after_rest else "immediately"
        head = f"// Chapter {ch.number}: {sc.name} - {'optional, ' if ch.optional else ''}unlocks {when}"
        if required:
            head += f", after chapter{'s' if len(required) > 1 else ''} {', '.join(str(p.number) for p in required)}"
        if ch.act is not None:
            head += f", only in act {ch.act}"
        if ch.priority:
            head += f", priority {ch.priority} (checked before the others)"
        out.append(head)
        c = ["PROC", "PROC_ALFSV_Chapters_Unlock((INTEGER)_AtRest)", "AND", "DB_ALFSV_IsCompanion(1)",
             "AND", f"NOT DB_GlobalFlag({fl(ch.available_flag)})",
             "AND", f"NOT DB_GlobalFlag({fl(ch.done_flag)})",
             "AND", "NOT QRY_ALFSV_Chapters_Waiting()"]
        for p in required:
            c += ["AND", f"DB_GlobalFlag({fl(p.done_flag)})"]
        if ch.after_rest:
            c += ["AND", "_AtRest == 1"]
        for r in ch.story:
            c += ["AND", cond(r)]
        if ch.story_any:
            c += ["AND", f"QRY_ALFSV_Chapter{ch.number:02d}_StoryAny()"]
        if ch.act is not None:
            c += ["AND", f"QRY_ALFSV_Chapters_InAct({ch.act})"]
        if ch.optional and ch.approval is not None and ch.approval > 0:
            # порог входа проверяется и при открытии: иначе необязательная глава ждала бы одобрения, держа очередь
            c += ["AND", f"QRY_ALFSV_Chapters_Approval({ch.approval})"]
        out += c + ["THEN", f"PROC_GlobalSetFlagAndCache({fl(ch.available_flag)});", ""]
    out += ["//END_REGION", "EXITSECTION", "", "ENDEXITSECTION", ""]
    return "\n".join(out)


def generate(dump=False):
    cfg = config()
    src = resolve(cfg["paths"]["mod_src"])
    ids = Ids(cfg["mod"]["uuid"])
    scenes = load_scenes()
    print("bg3moddinglib: загрузка индекса игры…")
    lib = bg3lib.Lib(cfg)
    errors = check_vanilla(lib, scenes)
    if errors:
        sys.exit("Данные сцен не сходятся с игрой:\n  " + "\n  ".join(errors))
    vm = voice_meta_handles(lib)
    chapters = sorted((s for s in scenes if s.chapter is not None), key=lambda s: s.chapter.number)
    results = [Compiler(lib, s, ids, vm, chapters).run() for s in scenes]

    for d in OWNED:
        p = src / d
        if p.exists():
            shutil.rmtree(p)
    loca_en, loca_ru, loca_ru_f = {}, {}, {}
    flags, reactions, vanilla = set(), set(), set()
    for c in results:
        s = c.s
        sub = f"{s.subfolder}/" if s.subfolder else ""
        write_xml(c.bundle.dialog.root_node, src / f"Mods/_MOD_/Story/DialogsBinary/{sub}{s.name}.lsx")
        gen = src / "Public/_MOD_/Timeline/Generated"
        write_xml(c.bundle.timeline.root_node, gen / f"{s.name}.lsf.lsx")
        write_xml(c.bundle.scene_lsf.root_node, gen / f"{s.name}_Scene.lsf.lsx")
        write_xml(c.bundle.scene_lsx.root_node, gen / f"{s.name}_Scene.lsx")
        for h, (en, ru, ruf) in c.loca.items():
            loca_en[h], loca_ru[h] = en, ru
            if ruf is not None:
                loca_ru_f[h] = ruf
        flags |= c.flags
        reactions |= c.reactions
        vanilla |= c.vanilla_handles
        if dump:
            dump_scene(c, cfg)
        # эталон для scripts/dialogs/validate.py: ванильная основа (только в build/, не в git)
        ref = resolve(cfg["paths"]["build"]) / "dialogs" / "reference" / s.base
        base = lib.assets.index.get_entry(s.base)
        tl_path = lib.assets.index.get_timeline_resource(base["timeline_uuid"]).find('./attribute[@id="SourceFile"]').get("value")
        write_xml(lib.game_file(base["lsf_path"]).root_node, ref / "dialog.lsx")
        write_xml(lib.game_file(tl_path).root_node, ref / "timeline.lsx")
        write_xml(lib.game_file(tl_path[:-4] + "_Scene.lsf").root_node, ref / "scene.lsx")
        write_xml(lib.game_file(tl_path[:-4] + "_Scene.lsx").root_node, ref / "scene_editor.lsx")
    write_xml(bank("DialogBank", [c.dres for c in results], "v1,bswap_guids,lsf_adjacency"),
              src / BANK_DIR / "_merged.lsx")
    write_xml(bank("TimelineBank", [c.tres for c in results], "v1,bswap_guids,lsf_adjacency"),
              src / TL_BANK_DIR / "_merged.lsx")
    for v in sorted(reactions):
        write_xml(reaction_xml(ids.reaction(v), v), src / f"Public/_MOD_/ApprovalRatings/Reactions/{ids.reaction(v)}.lsx")
    for f in sorted(flags, key=lambda x: x.name):
        write_xml(flag_xml(ids.flag(f), f), src / f"Public/_MOD_/Flags/{ids.flag(f)}.lsx")
    write_xml(character_override(lib), src / f"Mods/_MOD_/Globals/WLD_Main_A/Characters/{ALFIRA_TEMPLATE}.lsx")
    goal = src / CHAPTERS_GOAL
    if chapters:
        goal.write_text(chapters_goal(chapters, ids), encoding="utf-8", newline="\n")
    elif goal.exists():
        goal.unlink()
    # реплики на местах и в пути (AD) — свой goal
    places, trv = load_world()
    (src / WORLD_GOAL).write_text(ads.world_goal(places, trv, ids), encoding="utf-8", newline="\n")
    # реакции на поступки (акт 1) — свой goal (scripts/dialogs/reactions.py)
    (src / REACTIONS_GOAL).write_text(act_reactions.goal(ids), encoding="utf-8", newline="\n")
    from scenes.recruitment import ROMANCE as romance_flag        # флаг только из Osiris: файл нужен всё равно
    osiris_only = [romance_flag] + list(act_reactions.FLAGS.values()) + OSIRIS_FLAGS + [r.flag for s in chapters for r in s.chapter.story + s.chapter.story_any
                                                   if isinstance(r, FlagRef)]
    # флаги глав есть в goal глав всегда, а в диалогах Available — только у глав со входом в отряде
    osiris_only += [f for s in chapters for f in (s.chapter.available_flag, s.chapter.done_flag)]
    for f in osiris_only:
        if f.new and f not in flags:
            flags.add(f)
            write_xml(flag_xml(ids.flag(f), f), src / f"Public/_MOD_/Flags/{ids.flag(f)}.lsx")
    loc = src / "Mods/_MOD_/Localization"
    write_xml(loca_xml(loca_en), loc / "English" / f"{LOCA_NAME}_en.xml")
    write_xml(loca_xml(loca_ru), loc / "Russian" / f"{LOCA_NAME}_ru.xml")
    f_path = loc / "Russian" / f"{LOCA_NAME}_ru_to_F.xml"
    if FEMALE_VARIANTS and loca_ru_f:
        write_xml(loca_xml(loca_ru_f), f_path)
    elif f_path.exists():
        f_path.unlink()
    manifest = {
        "vanilla_handles": sorted(vanilla),
        "scenes": {c.s.name: {"dialog": c.s.dialog_id, "timeline": c.tres.find('./attribute[@id="ID"]').get("value"),
                              "phases": len(c.stager.report), "nodes": len(c.d.get_dialog_nodes())}
                   for c in results},
        "chapters": {s.chapter.number: {"scene": s.name, "dialog": s.dialog_id, "title": s.chapter.title,
                                         "available": ids.flag(s.chapter.available_flag),
                                         "done": ids.flag(s.chapter.done_flag), "optional": s.chapter.optional,
                                         "act": s.chapter.act, "hub": s.chapter.hub} for s in chapters},
        "places": {p.key: {"dialog": p.scene.dialog_id, "name": p.scene.name, "act": p.act, "title": p.title,
                           "triggers": p.triggers, "flags": p.flags, "levels": p.levels, "custom": p.custom}
                   for p in places},
        "travel": {"dialog": trv.scene.dialog_id, "name": trv.scene.name, "lines": len(trv.played)},
        "female_variants": sorted(loca_ru_f) if FEMALE_VARIANTS else [],
        "bg3moddinglib": lib.commit,
    }
    out = resolve(cfg["paths"]["build"]) / "dialogs"
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, m in manifest["scenes"].items():
        print(f"  {name}: узлов {m['nodes']}, фаз {m['phases']}")
    print(f"  текстов {len(loca_en)} (женских вариантов {len(loca_ru_f)}), озвученных реплик игры {len(vanilla)}, "
          f"реакций {len(reactions)}, новых флагов {len(flags)}")
    return manifest


def dump_scene(c, cfg):
    """Читаемая распечатка: узлы, тексты, фазы — для проверки глазами."""
    out = resolve(cfg["paths"]["build"]) / "dialogs" / f"{c.s.name}.txt"
    lines = [f"# {c.s.name}"]
    for nid, src, dur in c.stager.report:
        lines.append(f"phase {nid}  {dur:5.2f}s  {src}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", action="store_true")
    args = ap.parse_args()
    generate(args.dump)


if __name__ == "__main__":
    main()
