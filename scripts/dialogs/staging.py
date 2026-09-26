"""Постановка: фазы таймлайна для узлов диалога.

Таймлайн нового диалога — копия таймлайна ванильного диалога-основы (Scene.base) без фаз:
его сцена (_Scene), актёры, свет и стандартные камеры остаются. Для каждой реплики Альфиры
создаётся фаза:

* озвученная реплика игры (voice) — фаза вырезается из ванильного таймлайна, где эта реплика
  звучит: голос (TLVoice с её оригинальными fade/mocap), эмоции, взгляды, позы и планы камеры
  Альфиры и героя. Актёры переводятся на актёров нашего таймлайна, камеры из общей сцены
  bnz_standing_Px1 — на такие же камеры (недостающие добавляются), локальные камеры чужой
  сцены заменяются стандартным планом;
* текстовая реплика (say) — фаза строится по шаблонной фазе основы (позы, взгляды,
  оружие, физика, эмоции «зрителей»), голос без звука длиной по объёму текста, эмоции из
  сценария, план камеры по shot;
* ремарка рассказчика (narrate) — как текстовая, но голос у актёра рассказчика (Speaker −666).
Фразы героя (варианты ответа) фаз не имеют — как в игре.
"""
from __future__ import annotations

import copy
import uuid
import xml.etree.ElementTree as et
from decimal import Decimal

from dsl import ALFIRA, PLAYER, emotion_keys, render

# Длительность фразы без озвучки: как быстро читается субтитр (символов в секунду) + запас.
READ_CPS = 14.0
MIN_TEXT_PHASE = 2.5
MAX_TEXT_PHASE = 14.0
TAIL = 0.6

# Планы камеры для текстовых реплик: камера общей сцены bnz_standing_Px1 и к кому она
# привязана / куда смотрит. Такие же пары использует ванильный DEN_Bard_InParty.
CAMERAS = {
    "alfira": ("2fad736c-047d-4964-a8d6-0f1d8fb085b1", PLAYER, ALFIRA),        # из-за плеча героя на неё
    "alfira_close": ("62dc4211-3d45-4e20-b6bc-62e18087b085", ALFIRA, ALFIRA),  # крупный план
    "player": ("788e3996-fcf7-4113-9dc0-e4b971935c06", ALFIRA, PLAYER),        # на героя
}
SHARED_SCENE = "Public/Shared/Timeline/Scenes/Default/bnz_standing_Px1_Shipping.lsf"
NARRATOR_ACTOR = "a346318f-15b3-49ad-ab97-ddf8283dc339"   # актёр рассказчика у Larian (vanilla.NARRATOR_SPEAKER)
KEYED = ("TLEmotionEvent", "TLLookAtEvent", "TLAttitudeEvent")
TC = './region[@id="TimelineContent"]/node[@id="TimelineContent"]/children'


def D(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.0001"))


def attr(e, name, default=None):
    a = e.find(f'./attribute[@id="{name}"]')
    return default if a is None else a.get("value")


def fattr(e, name, default=0.0) -> Decimal:
    v = attr(e, name)
    return D(default) if v is None else D(v.replace(",", "."))


def set_attr(e, name, value, typ):
    a = e.find(f'./attribute[@id="{name}"]')
    if a is None:
        a = et.SubElement(e, "attribute", {"id": name, "type": typ})
        # атрибуты перед children, как в файлах игры
        ch = e.find("./children")
        if ch is not None:
            e.remove(a)
            e.insert(list(e).index(ch), a)
    a.set("type", typ)
    a.set("value", str(value))


def del_attr(e, name):
    a = e.find(f'./attribute[@id="{name}"]')
    if a is not None:
        e.remove(a)


def actor_of(comp):
    a = comp.find('./children/node[@id="Actor"]')
    return None if a is None else attr(a, "UUID")


def keys_of(comp):
    return comp.findall('./children/node[@id="Keys"]/children/node[@id="Key"]')


class TimelineView:
    """Роли актёров и камеры одного таймлайна (нашего или ванильного)."""

    def __init__(self, tl, dialog, alfira_template, player_speaker):
        self.tl = tl
        self.root = tl.xml
        speakers = {}
        for s in self.root.find(TC + '/node[@id="TimelineSpeakers"]').iter("node"):
            if attr(s, "MapKey") is not None and attr(s, "MapValue") is not None:
                speakers[int(attr(s, "MapKey"))] = attr(s, "MapValue")
        listed = dialog.get_speakers()
        self.role = {}                      # actor uuid → ALFIRA | PLAYER
        self.actor = {}                     # ALFIRA | PLAYER → actor uuid
        actors = tl.get_timeline_actors()
        for idx, actor in speakers.items():
            val = actors.get(actor)
            if idx < len(listed) and listed[idx] == alfira_template and ALFIRA not in self.actor:
                self.actor[ALFIRA] = actor
            elif val is not None and attr(val, "IsPlayer") == "True" and PLAYER not in self.actor:
                self.actor[PLAYER] = actor
        if len(self.actor) != 2:
            raise RuntimeError(f"{tl.filename}: не нашёл актёров Альфиры и героя ({self.actor})")
        self.role = {v: k for k, v in self.actor.items()}
        self.peanuts = set(tl.get_timeline_actors("peanut"))
        self.cams = {}                      # (camera, attach role, look role) → scenecam actor uuid
        self.cam_info = {}                  # scenecam actor uuid → (camera, attach role, look role)
        for cid, val in tl.get_timeline_actors("scenecam").items():
            key = (attr(val, "Camera"), self.role.get(attr(val, "AttachTo")), self.role.get(attr(val, "LookAt")))
            self.cam_info[cid] = key
            self.cams.setdefault(key, cid)

    def phase_components(self, index):
        return [c for c in self.tl.all_effect_components if int(attr(c, "PhaseIndex", 0)) == index]


class Stager:
    def __init__(self, lib, tl, dialog, base_tl, base_dialog, alfira_template, player_speaker, uid):
        self.lib = lib
        self.tl = tl
        self.dialog = dialog
        self.uid = uid                      # uid(key) → детерминированный UUID
        self.alfira_template = alfira_template
        self.player_speaker = player_speaker
        self.me = TimelineView(tl, dialog, alfira_template, player_speaker)
        self.base = TimelineView(base_tl, base_dialog, alfira_template, player_speaker)
        self.template = self._pick_template()
        self.sources = {}                   # имя диалога → (TimelineView, dialog_object)
        self.shared_cams = self._shared_cameras()
        self.added_cams = []
        self.report = []                    # (узел, откуда фаза, длительность) для документации

    # --- подготовка ---

    def _pick_template(self):
        """Шаблон для текстовых реплик: первая фаза основы с одним голосом Альфиры."""
        tl = self.base.tl
        for i in range(tl.get_number_of_phases()):
            comps = self.base.phase_components(i)
            voices = [c for c in comps if attr(c, "Type") == "TLVoice"]
            if len(voices) == 1 and actor_of(voices[0]) == self.base.actor[ALFIRA]:
                return i
        raise RuntimeError("в основе нет фазы с одной репликой Альфиры")

    def _shared_cameras(self):
        f = self.lib.game_file(SHARED_SCENE)
        top = f.root_node.find('./region[@id="TLScene"]/node[@id="TLScene"]')
        return {attr(c, "MapKey") for c in top.findall('./children/node[@id="TLCameras"]/children/node')}

    def source(self, name):
        if name not in self.sources:
            d = self.lib.assets.get_dialog_object(name)
            t = self.lib.assets.get_timeline_object(name)
            self.sources[name] = (TimelineView(t, d, self.alfira_template, self.player_speaker), d)
        return self.sources[name]

    # --- камеры ---

    def camera(self, key):
        """scenecam нашего таймлайна для (камера, привязка, взгляд); при необходимости добавляет."""
        if key in self.me.cams:
            return self.me.cams[key]
        cam, att, look = key
        if cam not in self.shared_cams or att is None:
            return None
        root = self.tl.xml.find(TC + '/node[@id="TimelineActorData"]/children/node[@id="TimelineActorData"]/children')
        proto = next(iter(self.tl.get_timeline_actors("scenecam")))
        node = copy.deepcopy(root.find(f'./node[@id="Object"][@key="MapKey"]/attribute[@value="{proto}"]/..'))
        new_id = self.uid(f"camera/{cam}/{att}/{look}")
        set_attr(node, "MapKey", new_id, "guid")
        val = node.find('./children/node[@id="Value"]')
        set_attr(val, "Camera", cam, "guid")
        set_attr(val, "AttachTo", self.me.actor[att], "guid")
        if look is None:
            del_attr(val, "LookAt")
        else:
            set_attr(val, "LookAt", self.me.actor[look], "guid")
        root.append(node)
        self.me.cams[key] = new_id
        self.me.cam_info[new_id] = key
        self.added_cams.append(new_id)
        return new_id

    def named_camera(self, shot):
        return self.camera(CAMERAS[shot])

    # --- фазы ---

    def _clone(self, comp, src_view, ws, we, start, dur, phase, stretch):
        """Копия компонента из окна [ws, we) чужой фазы в нашу фазу [start, start+dur)."""
        new = copy.deepcopy(comp)
        typ = attr(comp, "Type")
        cs, ce = fattr(comp, "StartTime"), fattr(comp, "EndTime")
        if stretch:
            ns, ne = start, start + dur
        else:
            ns = start + max(D(0), cs - ws)
            ne = start + min(dur, ce - ws)
        if ne - ns < D("0.01"):
            return None
        set_attr(new, "ID", self.uid(f"tl/{phase}/{typ}/{attr(comp, 'ID')}"), "guid")
        set_attr(new, "StartTime", ns, "float")
        set_attr(new, "EndTime", ne, "float")
        if phase > 0:
            set_attr(new, "PhaseIndex", phase, "int64")
        else:
            del_attr(new, "PhaseIndex")
        a = new.find('./children/node[@id="Actor"]')
        if a is not None:
            old = attr(a, "UUID")
            if old in src_view.role:
                set_attr(a, "UUID", self.me.actor[src_view.role[old]], "guid")
        if keys_of(new):
            keys = keys_of(new)
            before = [k for k in keys if fattr(k, "Time", cs) <= ws]
            inside = [k for k in keys if ws < fattr(k, "Time", cs) < we]
            keep = ([before[-1]] if before else []) + (inside if not stretch else [])
            if not keep and keys:
                keep = [keys[0]]
            parent = new.find('./children/node[@id="Keys"]/children')
            for k in keys:
                if k not in keep:
                    parent.remove(k)
            for i, k in enumerate(keep):
                t = start if (i == 0 and (stretch or fattr(k, "Time", cs) <= ws)) else start + (fattr(k, "Time", cs) - ws)
                set_attr(k, "Time", t, "float")
                for tgt in ("Target", "EyeLookAtTargetId"):
                    tv = attr(k, tgt)
                    if tv is not None:
                        role = src_view.role.get(tv)
                        if role is None:   # смотрела на того, кого в нашей сцене нет — на собеседника
                            role = PLAYER if src_view.role.get(attr(comp.find('./children/node[@id="Actor"]'), "UUID")) == ALFIRA else ALFIRA
                        set_attr(k, tgt, self.me.actor[role], "guid")
        return new

    def _shot(self, cam, start, end, phase, key, snapped):
        e = et.fromstring('<node id="EffectComponent"><attribute id="Type" type="LSString" value="TLShot" /></node>')
        set_attr(e, "ID", self.uid(f"tl/{phase}/shot/{key}"), "guid")
        set_attr(e, "StartTime", start, "float")
        set_attr(e, "EndTime", end, "float")
        if phase > 0:
            set_attr(e, "PhaseIndex", phase, "int64")
        if snapped:
            set_attr(e, "IsSnappedToEnd", "True", "bool")
        ch = et.SubElement(e, "children")
        cc = et.SubElement(ch, "node", {"id": "CameraContainer"})
        et.SubElement(cc, "attribute", {"id": "Object", "type": "guid", "value": cam})
        self.tl.insert_new_tl_node(e)

    def _template_parts(self, start, dur, phase, skip_roles_types):
        """Компоненты шаблонной фазы основы, растянутые на новую фазу (первый ключ в начале)."""
        comps = self.base.phase_components(self.template)
        ws = min(fattr(c, "StartTime") for c in comps)
        we = max(fattr(c, "EndTime") for c in comps)
        for c in comps:
            typ = attr(c, "Type")
            if typ in ("TLVoice", "TLShot"):
                continue
            role = self.base.role.get(actor_of(c))
            if (role, typ) in skip_roles_types:
                continue
            new = self._clone(c, self.base, ws, we, start, dur, phase, stretch=True)
            if new is not None:
                self.tl.insert_new_tl_node(new)

    def _voice(self, node_uuid, start, end, phase, speaker_actor, proto=None):
        if proto is not None:
            e = copy.deepcopy(proto)
        else:
            e = et.fromstring('<node id="EffectComponent"><attribute id="Type" type="LSString" value="TLVoice" /></node>')
        set_attr(e, "ID", self.uid(f"tl/{phase}/voice/{node_uuid}"), "guid")
        set_attr(e, "StartTime", start, "float")
        set_attr(e, "EndTime", end, "float")
        if phase > 0:
            set_attr(e, "PhaseIndex", phase, "int64")
        else:
            del_attr(e, "PhaseIndex")
        set_attr(e, "IsSnappedToEnd", "True", "bool")
        set_attr(e, "DialogNodeId", node_uuid, "guid")
        set_attr(e, "ReferenceId", node_uuid, "guid")
        if proto is None:
            for n in ("PerformanceFade", "FadeIn", "FadeOut"):
                set_attr(e, n, 0, "double")
            ch = et.SubElement(e, "children")
            a = et.SubElement(ch, "node", {"id": "Actor"})
            et.SubElement(a, "attribute", {"id": "UUID", "type": "guid", "value": speaker_actor})
        else:
            set_attr(e.find('./children/node[@id="Actor"]'), "UUID", speaker_actor, "guid")
        self.tl.insert_new_tl_node(e)

    def narrator_phase(self, node_uuid, line):
        """Фаза ремарки рассказчика: как текстовая, но TLVoice у актёра-рассказчика (Speaker −666).

        Актёра рассказчика в таймлайне основы нет — добавляется один раз, как у Larian
        (DEN_TieflingBard_Bard: тот же uuid, ActorTypeId narrator). Лицо и камера — на Альфире.
        """
        self.tl.create_narrator_timeline_actor_data()
        self.text_phase(node_uuid, line, speaker_actor=NARRATOR_ACTOR)

    def text_phase(self, node_uuid, line, speaker_actor=None):
        """Фаза текстовой реплики Альфиры (или ремарки рассказчика — speaker_actor)."""
        chars = max(len(render(line.en)), len(render(line.ru)))
        dur = D(min(MAX_TEXT_PHASE, max(MIN_TEXT_PHASE, chars / READ_CPS + TAIL)))
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        self._template_parts(start, dur, phase, {(ALFIRA, "TLEmotionEvent")})
        self._voice(node_uuid, start, start + dur, phase, speaker_actor or self.me.actor[ALFIRA])
        keys = [self.tl.create_emotion_key(t, code, variation=var) for t, code, var in emotion_keys(line.emo, float(dur))]
        self.tl.create_tl_actor_node("TLEmotionEvent", self.me.actor[ALFIRA], "0", dur, keys,
                                     node_uuid=self.uid(f"tl/{phase}/emo"), is_snapped_to_end=True)
        self._shot(self.named_camera(line.shot), start, start + dur, phase, "main", True)
        self.report.append((node_uuid, "ремарка" if speaker_actor else "текст", float(dur)))

    def voiced_phase(self, node_uuid, src_name, src_node, fallback_shot="alfira"):
        """Фаза озвученной реплики: окно вокруг её TLVoice в ванильном таймлайне."""
        view, _ = self.source(src_name)
        tl = view.tl
        voices = [c for c in tl.all_effect_components if attr(c, "Type") == "TLVoice"
                  and src_node in (attr(c, "DialogNodeId"), attr(c, "ReferenceId"))]
        if not voices:
            raise RuntimeError(f"{src_name}: нет TLVoice для узла {src_node}")
        v = voices[0]
        pidx = int(attr(v, "PhaseIndex", 0))
        ph = tl.get_timeline_phase(pidx)
        comps = view.phase_components(pidx)
        ws = fattr(v, "StartTime")
        later = sorted(fattr(c, "StartTime") for c in comps if attr(c, "Type") == "TLVoice" and fattr(c, "StartTime") > ws)
        we = later[0] if later else D(ph.start) + D(ph.duration)
        if we - fattr(v, "EndTime") > D(3):          # длинная пауза после реплики: хвост 1 с
            we = fattr(v, "EndTime") + D(1)
        dur = we - ws
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        have = set()
        for c in comps:
            typ = attr(c, "Type")
            if typ == "TLVoice" or typ == "TLShot":
                continue
            role = view.role.get(actor_of(c))
            if role is None or typ not in KEYED:
                continue
            if fattr(c, "EndTime") <= ws or fattr(c, "StartTime") >= we:
                continue
            if not keys_of(c):            # пустое событие чужой фазы: возьмём шаблонное
                continue
            new = self._clone(c, view, ws, we, start, dur, phase, stretch=False)
            if new is not None:
                self.tl.insert_new_tl_node(new)
                have.add((role, typ))
        self._template_parts(start, dur, phase, have)
        self._voice(node_uuid, start, start + (fattr(v, "EndTime") - ws), phase, self.me.actor[ALFIRA], proto=v)
        shots = []
        for c in comps:
            if attr(c, "Type") != "TLShot" or fattr(c, "EndTime") <= ws or fattr(c, "StartTime") >= we:
                continue
            cc = c.find('./children/node[@id="CameraContainer"]')
            src_cam = attr(cc, "Object") if cc is not None else None
            cam = self.camera(view.cam_info[src_cam]) if src_cam in view.cam_info else None
            shots.append((max(D(0), fattr(c, "StartTime") - ws), min(dur, fattr(c, "EndTime") - ws), cam))
        shots = [s for s in sorted(shots) if s[1] - s[0] > D("0.05")]
        if not shots or all(s[2] is None for s in shots):
            shots = [(D(0), dur, None)]
        default = self.named_camera(fallback_shot)
        t = D(0)
        for i, (s, e, cam) in enumerate(shots):
            e = dur if i == len(shots) - 1 else e
            if e <= t:
                continue
            self._shot(cam or default, start + t, start + e, phase, f"s{i}", i == len(shots) - 1)
            t = e
        self.report.append((node_uuid, f"{src_name} фаза {pidx}", float(dur)))
