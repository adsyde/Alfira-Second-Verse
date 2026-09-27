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
* ремарка рассказчика (narrate) — как текстовая, но голос у актёра рассказчика (Speaker −666);
* кат-узел (cinematic) — копия всей фазы узла TagCinematic ванильного диалога (поцелуй, объятие): TLAnimation,
  TLTransform, TLSwitchStageEvent, TLShot, звуки, эмоции, взгляды. Сцена основы (стадии, свои камеры) переходит
  в наш таймлайн целиком при копии основы, актёры и камеры переводятся на наших.
Фразы героя (варианты ответа) фаз не имеют — как в игре.

Лицо Альфиры в текстовых репликах и ремарках — её собственное, по каталогу её реплик у Larian (style.py,
alfira_style.json). Сидя у костра (Scene.seated / block(seated=…)) — позы DIAG_Pose_SitGround_* (SEATED).
В сцене на троих шаблонная фаза своя у каждого говорящего, планы — из неё (как у Larian).
Длина фазы текстовой реплики — phase_duration(): здесь же — точка для длины по аудио (голос, docs/VOICE.md).
"""
from __future__ import annotations

import copy
import uuid
from collections import Counter
import xml.etree.ElementTree as et
from decimal import Decimal

from dsl import ALFIRA, OTHER, PLAYER, emotion_keys, render
from style import STYLE

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
    # третий участник сцены (Scene.other): те же камеры, привязанные к нему
    "other": ("2fad736c-047d-4964-a8d6-0f1d8fb085b1", PLAYER, OTHER),          # из-за плеча героя на него
    "other_close": ("62dc4211-3d45-4e20-b6bc-62e18087b085", OTHER, OTHER),     # крупный план
}
SHARED_SCENE = "Public/Shared/Timeline/Scenes/Default/bnz_standing_Px1_Shipping.lsf"
NARRATOR_ACTOR = "a346318f-15b3-49ad-ab97-ddf8283dc339"   # актёр рассказчика у Larian (vanilla.NARRATOR_SPEAKER)
KEYED = ("TLEmotionEvent", "TLLookAtEvent", "TLAttitudeEvent")
TC = './region[@id="TimelineContent"]/node[@id="TimelineContent"]/children'

# Позы «сидя на земле» — атрибуты диалога игры (Public/Shared/Animation/Attitudes.lsf, имена — ShortNames.lsx).
# Так сидят спутник и герой в лагерных сценах Larian поверх обычной сцены bnz_standing_Px1: переход — DIAG_T_Pose
# («без перехода»), поза держится всю фазу (CAMP_GalesLastNightAlive_SD_ROM, CAMP_DaisyCourseCorrection_AvD,
# CAMP_DarkUrge_SparedIsobel_SD). Сводка — docs/research/alfira-staging.md §4.
T_POSE = "375d49d9-707a-42fb-a7f5-7bccba35a6ea"              # DIAG_T_Pose
SIT = {
    "HandsDn": "d2c93757-6617-4459-a1b5-1d1f6f59f734",       # DIAG_Pose_SitGround_HandsDn_01
    "CrossLegs": "7b952786-db29-406b-9670-e26ffc712cbf",     # DIAG_Pose_SitGround_CrossLegs_01
    "2KneesUp": "d892fccc-a5af-47ab-bd61-499c3e34c5e1",      # DIAG_Pose_SitGround_2KneesUp_01
    "LKneeUp": "23704a3d-3541-4c8d-924f-b50f569e3586",       # DIAG_Pose_SitGround_LKneeUp_01
    "RKneeUp": "066dd6ba-f9c0-4b72-bd65-3512af843db9",       # DIAG_Pose_SitGround_RKneeUp_01
}
# Scene.seated / block(seated=…): ключ → (поза Альфиры, поза героя); None — стоит, как в основе.
SEATED = {
    "fire": ("HandsDn", "CrossLegs"),       # у костра: спутник и герой как Гейл и герой (CAMP_GalesLastNightAlive_SD_ROM)
    "knees": ("2KneesUp", "CrossLegs"),     # колени к груди (глава 1, «подтягивает колени к груди»)
    "knee": ("RKneeUp", "LKneeUp"),         # колено вверх (CAMP_DaisyCourseCorrection_AvD: RKneeUp / LKneeUp у героя)
}


def text_duration(line) -> Decimal:
    """Длина фазы реплики без озвучки: по объёму текста (READ_CPS), от MIN до MAX_TEXT_PHASE."""
    chars = max(len(render(line.en)), len(render(line.ru)))
    return D(min(MAX_TEXT_PHASE, max(MIN_TEXT_PHASE, chars / READ_CPS + TAIL)))


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

    def __init__(self, tl, dialog, alfira_template, player_speaker, other_template="", alfira_as=""):
        """alfira_as — спикер чужого диалога, которого у нас играет Альфира (основа с другим спутником: поцелуй
        Шэдоухарт). Актёры спикеров, которых у нас нет (зрители), в role не попадают."""
        self.tl = tl
        self.root = tl.xml
        speakers = {}
        for s in self.root.find(TC + '/node[@id="TimelineSpeakers"]').iter("node"):
            if attr(s, "MapKey") is not None and attr(s, "MapValue") is not None:
                speakers[int(attr(s, "MapKey"))] = attr(s, "MapValue")
        listed = dialog.get_speakers()
        self.role = {}                      # actor uuid → ALFIRA | PLAYER | OTHER
        self.actor = {}                     # ALFIRA | PLAYER | OTHER → actor uuid
        actors = tl.get_timeline_actors()
        for idx, actor in speakers.items():
            val = actors.get(actor)
            if idx < len(listed) and listed[idx] == (alfira_as or alfira_template) and ALFIRA not in self.actor:
                self.actor[ALFIRA] = actor
            elif other_template and idx < len(listed) and listed[idx] == other_template and OTHER not in self.actor:
                self.actor[OTHER] = actor
            elif val is not None and attr(val, "IsPlayer") == "True" and PLAYER not in self.actor:
                self.actor[PLAYER] = actor
        if ALFIRA not in self.actor or PLAYER not in self.actor or (other_template and OTHER not in self.actor):
            raise RuntimeError(f"{tl.filename}: не нашёл актёров Альфиры, героя"
                               f"{' и третьего участника' if other_template else ''} ({self.actor})")
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
    def __init__(self, lib, tl, dialog, base_tl, base_dialog, alfira_template, player_speaker, uid, other_template="",
                 base_scene_file="", alfira_base="", base_name="", other_base=""):
        self.lib = lib
        self.base_name = base_name
        self.base_scene_file = base_scene_file   # _Scene.lsf основы: из неё — общая сцена с камерами
        self.tl = tl
        self.dialog = dialog
        self.uid = uid                      # uid(key) → детерминированный UUID
        self.alfira_template = alfira_template
        self.player_speaker = player_speaker
        self.other_template = other_template
        self.me = TimelineView(tl, dialog, alfira_template, player_speaker, other_template)
        # other_base — спикер основы, на место которого встал третий участник (Scene.other_base): в основе он под своим uuid
        self.base = TimelineView(base_tl, base_dialog, alfira_template, player_speaker, other_base or other_template, alfira_base)
        self.templates = {}                 # роль говорящего → шаблонная фаза основы (_pick_template)
        self.sources = {}                   # имя диалога → (TimelineView, dialog_object)
        # Точка для голоса: uuid узла → длина аудио реплики, с. Если задана, фаза текстовой реплики — по ней
        # (phase_duration), TLVoice — на длину звука. Заполняет build.py в личной сборке (build_pak --voice clone,
        # docs/VOICE.md).
        self.voice_durations = {}
        self.shared_cams = self._shared_cameras()
        self.added_cams = []
        self.report = []                    # (узел, откуда фаза, длительность) для документации

    # --- подготовка ---

    def template(self, role=ALFIRA):
        if role not in self.templates:
            self.templates[role] = self._pick_template(role)
        return self.templates[role]

    def _pick_template(self, role):
        """Шаблон для текстовых реплик говорящего role: первая фаза основы с одним его голосом, где никто не
        ходит (без TLAnimation/TLTransform персонажей: шаги и повороты входа в сцену повторялись бы на каждой
        реплике); если таких нет — первая фаза с одним его голосом. В сцене на троих у Лакриссы своя шаблонная
        фаза: взгляды слушателей и планы — на неё, как у Larian."""
        tl = self.base.tl
        first = None
        for i in range(tl.get_number_of_phases()):
            comps = self.base.phase_components(i)
            voices = [c for c in comps if attr(c, "Type") == "TLVoice"]
            if len(voices) != 1 or actor_of(voices[0]) != self.base.actor.get(role):
                continue
            first = i if first is None else first
            if not any(attr(c, "Type") in ("TLAnimation", "TLTransform") and actor_of(c) in self.base.role
                       for c in comps):
                return i
        if first is None:
            raise RuntimeError(f"в основе нет фазы с одной репликой {'Альфиры' if role == ALFIRA else 'третьего'}")
        return first

    def _shared_cameras(self):
        """Камеры общих сцен: bnz_standing_Px1 и общая сцена, от которой наследует сцена основы (у сцены
        на троих это bnz_standing_Px2 — в ней те же камеры subject1/player и ещё камеры subject2)."""
        files = [SHARED_SCENE]
        if self.base_scene_file:
            sc = self.lib.game_file(self.base_scene_file)
            top = sc.root_node.find('./region[@id="TLScene"]/node[@id="TLScene"]')
            for inh in top.findall('./children/node[@id="TLInheritedScenes"]/children/node'):
                path = attr(inh, "Object") or ""
                if "/Scenes/Default/bnz_" in path:
                    files.append(path[:-4] + ".lsf" if path.endswith(".lsx") else path)
        out = set()
        for fn in dict.fromkeys(files):
            f = self.lib.game_file(fn)
            top = f.root_node.find('./region[@id="TLScene"]/node[@id="TLScene"]')
            out |= {attr(c, "MapKey") for c in top.findall('./children/node[@id="TLCameras"]/children/node')}
        return out

    def source(self, name):
        """(TimelineView, dialog) ванильного диалога-источника; у AD (один спикер, без героя) — (timeline, None)."""
        if name not in self.sources:
            d = self.lib.assets.get_dialog_object(name)
            t = self.lib.assets.get_timeline_object(name)
            if self.alfira_template in d.get_speakers() and (len(d.get_speakers()) == 1
                                                             or self.player_speaker not in d.get_speakers()):
                # AD (без героя: одна Альфира или Альфира и NPC, как CAMP_Bard_AD_Volo) — фаза по её голосу
                self.sources[name] = (t, None)
            else:
                other = self.other_template if self.other_template in d.get_speakers() else ""
                self.sources[name] = (TimelineView(t, d, self.alfira_template, self.player_speaker, other), d)
        return self.sources[name]

    def voice_window(self, src_name, src_node):
        """(TLVoice, эмоции Альфиры в её фазе) реплики из таймлайна автоматического диалога (AD)."""
        tl, _ = self.source(src_name)
        voices = [c for c in tl.all_effect_components if attr(c, "Type") == "TLVoice"
                  and src_node in (attr(c, "DialogNodeId"), attr(c, "ReferenceId"))]
        if not voices:
            raise RuntimeError(f"{src_name}: нет TLVoice для узла {src_node}")
        v = voices[0]
        actor = actor_of(v)
        pidx = int(attr(v, "PhaseIndex", 0))
        emo = []
        for c in tl.all_effect_components:
            if attr(c, "Type") == "TLEmotionEvent" and int(attr(c, "PhaseIndex", 0)) == pidx and actor_of(c) == actor:
                for k in keys_of(c):
                    e = attr(k, "Emotion")
                    t = fattr(k, "Time", fattr(c, "StartTime")) - fattr(v, "StartTime")
                    emo.append((max(D(0), t), int(e or 1), int(attr(k, "Variation", 0) or 0)))
        return v, sorted(emo) or [(D(0), 1, 0)]

    def _voiced_from_ad(self, node_uuid, src_name, src_node, seat=""):
        """Её озвученная реплика из AD (у AD нет сцены и камер): голос, длина по голосу, её эмоции из AD,
        остальное — шаблонная фаза основы и стандартный план."""
        v, emo = self.voice_window(src_name, src_node)
        vdur = fattr(v, "EndTime") - fattr(v, "StartTime")
        dur = vdur + D(TAIL)
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        self._template_parts(start, dur, phase, {(ALFIRA, "TLEmotionEvent")} | (self._seated_skip() if seat else set()))
        if seat:
            self._seat(seat, dur, phase)
        self._voice(node_uuid, start, start + vdur, phase, self.me.actor[ALFIRA], proto=v)
        keys = [self.tl.create_emotion_key(float(t), code, variation=var) for t, code, var in emo]
        self.tl.create_tl_actor_node("TLEmotionEvent", self.me.actor[ALFIRA], "0", dur, keys,
                                     node_uuid=self.uid(f"tl/{phase}/emo"), is_snapped_to_end=True)
        self._shot(self.named_camera("alfira"), start, start + dur, phase, "main", True)
        self.report.append((node_uuid, f"{src_name} (AD, голос)" + (f", сидя ({seat})" if seat else ""), float(dur)))

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
                        if role is None or role not in self.me.actor:
                            # смотрела на того, кого в нашей сцене нет — на собеседника
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

    def _template_parts(self, start, dur, phase, skip_roles_types, role=ALFIRA):
        """Компоненты шаблонной фазы основы, растянутые на новую фазу (первый ключ в начале)."""
        comps = self.base.phase_components(self.template(role))
        ws = min(fattr(c, "StartTime") for c in comps)
        we = max(fattr(c, "EndTime") for c in comps)
        for c in comps:
            typ = attr(c, "Type")
            if typ in ("TLVoice", "TLShot"):
                continue
            role = self.base.role.get(actor_of(c))
            if (role, typ) in skip_roles_types:
                continue
            if actor_of(c) in self.base.cam_info:
                # движение, фокус и угол локальной камеры основы (TLTransform/TLCameraFoV/TLCameraDoF у сцены
                # на троих): их ключи лежат во вложенных каналах и привязаны к её плану — у нас свой TLShot
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

    def narrator_phase(self, node_uuid, line, seat=""):
        """Фаза ремарки рассказчика: как текстовая, но TLVoice у актёра-рассказчика (Speaker −666).

        Актёра рассказчика в таймлайне основы нет — добавляется один раз, как у Larian
        (DEN_TieflingBard_Bard: тот же uuid, ActorTypeId narrator). Лицо и камера — на Альфире.
        """
        self.tl.create_narrator_timeline_actor_data()
        self.text_phase(node_uuid, line, speaker_actor=NARRATOR_ACTOR, seat=seat)

    def phase_duration(self, node_uuid, line):
        """Длина фазы текстовой реплики или ремарки.

        С голосом клона (build_pak --voice clone) длина аудио (с) лежит в voice_durations[uuid узла] — фаза
        длиной голоса + TAIL, как у озвученных реплик игры; ключи эмоций и планы растягиваются по ней.
        Без аудио — по объёму текста (text_duration)."""
        v = self.voice_durations.get(node_uuid)
        return D(v) + D(TAIL) if v else text_duration(line)

    def text_phase(self, node_uuid, line, speaker_actor=None, seat=""):
        """Фаза текстовой реплики Альфиры или третьего участника сцены (line.speaker == OTHER), или
        ремарки рассказчика (speaker_actor). Эмоции из сценария — на лице говорящего (у ремарки — Альфиры);
        у Альфиры — её собственные вариации и ход ключей (style.py)."""
        dur = self.phase_duration(node_uuid, line)
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        face = OTHER if line.speaker == OTHER and not speaker_actor else ALFIRA
        role = face if self.other_template else ALFIRA
        skip = {(face, "TLEmotionEvent")} | (self._seated_skip() if seat else set())
        self._template_parts(start, dur, phase, skip, role=role)
        # с голосом (личная сборка, docs/VOICE.md) TLVoice — на длину звука, как у озвученных реплик игры
        vdur = self.voice_durations.get(node_uuid)
        self._voice(node_uuid, start, start + (D(vdur) if vdur else dur), phase, speaker_actor or self.me.actor[face])
        if face == ALFIRA:
            emo = STYLE.keys(line, float(dur), node_uuid)
        else:
            emo = emotion_keys(line.emo, float(dur))
        keys = [self.tl.create_emotion_key(t, code, variation=var) for t, code, var in emo]
        self.tl.create_tl_actor_node("TLEmotionEvent", self.me.actor[face], "0", dur, keys,
                                     node_uuid=self.uid(f"tl/{phase}/emo"), is_snapped_to_end=True)
        if seat:
            self._seat(seat, dur, phase)
        if not (self.other_template and line.shot_default and self._template_shots(role, start, dur, phase)):
            self._shot(self.named_camera(line.shot), start, start + dur, phase, "main", True)
        self.report.append((node_uuid, ("ремарка" if speaker_actor else ("текст (3-й)" if face == OTHER else "текст"))
                            + (", голос клона" if vdur else "") + (f", сидя ({seat})" if seat else ""), float(dur)))

    # --- сидя у костра ---

    def _seated_skip(self):
        return {(ALFIRA, "TLAttitudeEvent"), (PLAYER, "TLAttitudeEvent")}

    def _seat(self, seat, dur, phase):
        """Позы сидя на всю фазу: один ключ в начале, переход DIAG_T_Pose (как у Larian в лагерных сценах)."""
        if seat not in SEATED:
            raise KeyError(f"поза {seat!r} не описана в staging.SEATED; есть {sorted(SEATED)}")
        for role, pose in zip((ALFIRA, PLAYER), SEATED[seat]):
            if pose is None:
                continue
            key = self.tl.create_attitude_key(0, SIT[pose], T_POSE)
            self.tl.create_tl_actor_node("TLAttitudeEvent", self.me.actor[role], "0", dur, [key],
                                         node_uuid=self.uid(f"tl/{phase}/seat/{role}"), is_snapped_to_end=True)

    # --- сцена на троих: планы Larian из шаблонной фазы говорящего ---

    def _template_shots(self, role, start, dur, phase):
        """Планы шаблонной фазы основы (у сцены на троих — свои камеры Larian), по времени — в долях фазы.
        False — если ни одну камеру не удалось перевести (тогда план по shot)."""
        i = self.template(role)
        comps = self.base.phase_components(i)
        ph = self.base.tl.get_timeline_phase(i)
        ws, wd = D(ph.start), D(ph.duration)
        shots = []
        for c in sorted((c for c in comps if attr(c, "Type") == "TLShot"), key=lambda c: fattr(c, "StartTime")):
            cc = c.find('./children/node[@id="CameraContainer"]')
            src = attr(cc, "Object") if cc is not None else None
            cam = self.camera(self.base.cam_info[src]) if src in self.base.cam_info else None
            if cam is not None:
                shots.append(((fattr(c, "StartTime") - ws) / wd, cam))
        if not shots:
            return False
        for n, (frac, cam) in enumerate(shots):
            s = D(0) if n == 0 else D(frac * dur)
            e = dur if n == len(shots) - 1 else D(shots[n + 1][0] * dur)
            if e - s < D("0.3"):
                continue
            self._shot(cam, start + s, start + e, phase, f"t{n}", n == len(shots) - 1)
        return True

    def voiced_phase(self, node_uuid, src_name, src_node, fallback_shot="alfira", seat=""):
        """Фаза озвученной реплики: окно вокруг её TLVoice в ванильном таймлайне. seat — сидя (SEATED):
        позы из ванильной фазы не берутся, вместо них — позы сидя."""
        view, d = self.source(src_name)
        if d is None:
            return self._voiced_from_ad(node_uuid, src_name, src_node, seat)
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
        have = set(self._seated_skip()) if seat else set()
        for c in comps:
            typ = attr(c, "Type")
            if typ == "TLVoice" or typ == "TLShot":
                continue
            role = view.role.get(actor_of(c))
            if role is None or typ not in KEYED or (role, typ) in have:
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
        if seat:
            self._seat(seat, dur, phase)
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
        self.report.append((node_uuid, f"{src_name} фаза {pidx}" + (f", сидя ({seat})" if seat else ""), float(dur)))

    # --- кат-узлы: поцелуй, объятие (STAGE4.md §13) ---

    def cine_source(self, name):
        """TimelineView ванильного диалога с кат-фазами. Альфиры среди его спикеров нет — её играет спикер 0
        (у ShadowHeart_InParty2_Nested_ShadowheartKiss это Шэдоухарт); у основы сцены — Scene.alfira_base."""
        if not name or name == self.base_name:
            return self.base
        key = ("cine", name)
        if key not in self.sources:
            d = self.lib.assets.get_dialog_object(name)
            t = self.lib.assets.get_timeline_object(name)
            sp = d.get_speakers()
            alfira_as = "" if self.alfira_template in sp else sp[0]
            self.sources[key] = TimelineView(t, d, self.alfira_template, self.player_speaker, alfira_as=alfira_as)
        return self.sources[key]

    def cinematic_phase(self, node_uuid, src_name, src_node):
        """Фаза кат-узла (TagCinematic): копия ВСЕХ компонентов фазы узла src_node ванильного диалога.

        TLAnimation, TLTransform, TLSwitchStageEvent, TLShot, TLSoundEvent, TLShowArmor, TLPhysics, эмоции, позы,
        взгляды — как у Larian, со сдвигом времени на начало нашей фазы. Актёры переводятся по ролям (спикер,
        который у нас Альфира, → её актёр; герой → герой), камеры — на наши с той же камерой и привязкой, пинатсы
        (массовка отряда) и камеры одной и той же сцены — как есть. Компоненты актёров, которых у нас нет
        (зрители-спутники основы), не переносятся. Стадии (TLStages) и свои камеры сцены действуют, если
        источник — основа сцены: её _Scene копируется в наш таймлайн целиком."""
        view = self.cine_source(src_name)
        tl = view.tl
        pidx = tl.get_timeline_phase_index(src_node)
        if pidx is None:
            raise RuntimeError(f"{src_name or self.base_name}: нет фазы для узла {src_node}")
        ph = tl.get_timeline_phase(pidx)
        comps = view.phase_components(pidx)
        dur = D(ph.duration)
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        shift = start - D(ph.start)
        same = view is self.base
        idmap = {view.actor[r]: self.me.actor[r] for r in view.actor if r in self.me.actor}
        ours = set(self.tl.get_timeline_actors())
        for a in view.peanuts:
            if a in ours:
                idmap[a] = a
        for cam, key in view.cam_info.items():
            if same and cam in ours:
                idmap[cam] = cam
            else:
                mapped = self.camera(key)
                if mapped is not None:
                    idmap[cam] = mapped
        dropped = Counter()
        for c in comps:
            typ = attr(c, "Type")
            a = actor_of(c)
            if a is not None and a not in idmap:
                dropped[typ] += 1
                continue
            if typ == "TLShot":
                cc = c.find('./children/node[@id="CameraContainer"]')
                if cc is None or attr(cc, "Object") not in idmap:
                    dropped[typ] += 1
                    continue
            new = copy.deepcopy(c)
            set_attr(new, "ID", self.uid(f"tl/{phase}/cine/{attr(c, 'ID')}"), "guid")
            if phase > 0:
                set_attr(new, "PhaseIndex", phase, "int64")
            else:
                del_attr(new, "PhaseIndex")
            for e in new.iter("node"):
                if e is new or e.get("id") == "Key":
                    for name in (("StartTime", "EndTime") if e is new else ("Time",)):
                        v = attr(e, name)
                        set_attr(e, name, (D(v) if v is not None else D(0)) + shift, "float")
            for at in new.iter("attribute"):
                if at.get("type") == "guid" and at.get("value") in idmap:
                    at.set("value", idmap[at.get("value")])
            self.tl.insert_new_tl_node(new)
        self.report.append((node_uuid, f"{src_name or self.base_name} кат-фаза {pidx}"
                            + (f" (не перенесено: {dict(dropped)})" if dropped else ""), float(dur)))
