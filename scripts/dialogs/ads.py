"""Реплики над головой (AD): реплики на местах и фразы в пути. Формат — scripts/dialogs/README.md, «Реплики над головой».

AD (automated dialog) — диалог без выбора: игра показывает реплику текстом над головой говорящего
(у озвученной — с голосом) и не останавливает игру. Так у Larian устроены реплики спутников на
местах: например IRN_IronThrone_AD_WyllSeesDeadRavengard — диалог категории «Voice bark» с одним
спикером-спутником, его запускает Osiris через PROC_TryStartAD(диалог, спутник)
(Act3_OriginMoments_Wyll.txt). У каждого AD есть свой таймлайн: фаза на реплику — TLVoice и эмоции
(CAMP_Bard_AD, SCE_AD_Alfira), без сцены и камер.

Здесь:
  * описание (DSL) — place(...), variant(...), travel(...) и флаги настроения MOOD;
  * ADStager — фазы таймлайна AD;
  * world_goal(...) — goal Osiris ALFSV_World.txt (генерируется): когда какой AD запускать.

Варианты реплики выбирает сама игра: корни диалога идут по приоритету 💞 > ✨ > ❄️ > обычный
(первый, чьи условия выполнены). Условия — флаги «настроения» на Альфире (MOOD), их ставит Osiris
перед каждым запуском AD по состоянию героев: так AD обходится одним спикером (Альфира), а
флаги героя (искра, роман, зарубка) и одобрение проверяются в Osiris.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from dsl import ALFIRA, Flag, Line, Scene, new_flag, render

# Основа всех AD мода: её AD в Last Light (один спикер — Альфира, свой таймлайн: TLVoice + эмоции).
AD_BASE = "SCE_AD_Alfira"
# Категории — как у Larian: реакция спутника на место/событие — «Voice bark»
# (IRN_IronThrone_AD_WyllSeesDeadRavengard); повторяемая болтовня — «Repeated automated NPC Dialog»
# (её CAMP_Bard_AD, который игра запускает много раз, каждый раз — следующий корень).
PLACE_CATEGORY = "Voice bark"
TRAVEL_CATEGORY = "Repeated automated NPC Dialog"
# Где искать её озвученные реплики для AD (по handle).
AD_VOICE_FROM = ["DEN_TieflingBard_Bard", "CAMP_Bard_AD"]
MOD_NS = uuid.UUID("d2bf8bd7-0c6e-4aa5-8c78-84ae31e14f5b")     # UUID мода (config/tools.json), не менять

# Пороги одобрения для настроения (одобрение Альфиры к герою, DB_ApprovalRating в Osiris).
COLD_BELOW = 0          # ❄️ «одобрение низкое» — ниже 0, как холодная реплика разговора в отряде
WARM_AT_LEAST = 40      # «одобрение высокое» — [решение сборки] 40, порог первого поцелуя (APPROVAL.md §2)

# Фразы в пути: пауза между попытками (мс) — от MIN до MIN+SPREAD, случайно (Random в Osiris).
TRAVEL_MIN_MS = 180000
TRAVEL_SPREAD_MS = 180000
# Сколько секунд ждать возможности сказать реплику места (бой, разговор, катсцена), потом забыть.
PLACE_WAIT_S = 60
TICK_MS = 5000


class MOOD:
    """Флаги настроения на Альфире: Osiris ставит их перед запуском AD (PROC_ALFSV_AD_SetMood)."""
    Romance = new_flag("ALFSV_AD_Romance", "Object", "AD mood: a hero has started a romance with Alfira")
    Spark = new_flag("ALFSV_AD_Spark", "Object", "AD mood: a hero has a romance spark (or a romance) with Alfira")
    Cold = new_flag("ALFSV_AD_Cold", "Object", "AD mood: Alfira's approval of a hero is below 0")
    Warm = new_flag("ALFSV_AD_Warm", "Object", "AD mood: Alfira's approval of a hero is 40 or more")
    NotchCity = new_flag("ALFSV_AD_NotchCity", "Object", "AD mood: a hero promised to cut the 13th notch in the city")

    @staticmethod
    def on(f: Flag):
        return f(ALFIRA)

    @staticmethod
    def off(f: Flag):
        return f(ALFIRA, False)


R, S_, C, W, N = (MOOD.on(MOOD.Romance), MOOD.on(MOOD.Spark), MOOD.on(MOOD.Cold), MOOD.on(MOOD.Warm),
                  MOOD.on(MOOD.NotchCity))
ROMANCE, SPARK, COLD, WARM, NOTCH = R, S_, C, W, N       # для файлов сцен: when=[ROMANCE]


@dataclass
class Variant:
    lines: list
    when: list = field(default_factory=list)


def variant(*lines: Line, when=()) -> Variant:
    """Вариант реплики места: одна или несколько реплик подряд, условия — флаги MOOD (ROMANCE, SPARK…)."""
    return Variant(list(lines), list(when))


@dataclass
class Place:
    key: str
    title: str                           # по-русски, как в design/banter/02_places.md
    act: int
    scene: Scene
    triggers: list = field(default_factory=list)   # Osiris-имена триггеров: EnteredTrigger(Альфира, триггер)
    flags: list = field(default_factory=list)      # глобальные флаги игры: FlagSet(флаг)
    levels: list = field(default_factory=list)     # имена уровней: LevelGameplayStarted(уровень)
    custom: str = ""                     # особый запуск, описан в world_goal (фуникулёр Яслей)
    source: str = ""                     # откуда взят триггер (файл:строка) — для документации


def _ad_scene(name, category, status=""):
    s = Scene(name=name, dialog_id=str(uuid.uuid5(MOD_NS, f"ad/{name}")), base=AD_BASE, subfolder="Companions/ADs",
              voice_from=list(AD_VOICE_FROM), status=status, kind="ad", category=category)
    return s


def place(key, title, *variants: Variant, act, triggers=(), flags=(), levels=(), custom="", source="") -> Place:
    """Реплика на месте. Варианты — по приоритету (💞, ✨, ❄️, обычный последним, без условий)."""
    if not variants or variants[-1].when:
        raise ValueError(f"{key}: последним должен быть обычный вариант без условий")
    if not (triggers or flags or levels or custom):
        raise ValueError(f"{key}: нет ни триггера, ни флага, ни уровня — такие места пишутся в GAPS")
    s = _ad_scene(f"ALFSV_AD_Place_{key}", PLACE_CATEGORY)
    for i, v in enumerate(variants):
        s.greeting(f"v{i}", *v.lines, when=v.when, end=True)
    return Place(key, title, act, s, list(triggers), list(flags), list(levels), custom, source)


@dataclass
class Travel:
    scene: Scene
    played: list                         # флаги «сказано» по одному на фразу


def travel(*lines: tuple) -> Travel:
    """Фразы в пути: (реплика, [условия]) в порядке приоритета. Каждая звучит один раз (флаг на Альфире)."""
    s = _ad_scene("ALFSV_AD_Travel", TRAVEL_CATEGORY)
    played = []
    for i, (ln, when) in enumerate(lines):
        f = new_flag(f"ALFSV_Travel_{i + 1:02d}_Played", "Object", f"Travel line {i + 1} has been said")
        played.append(f)
        s.greeting(f"t{i + 1:02d}", ln, when=[f(ALFIRA, False), *when], set=[f(ALFIRA)], end=True)
    return Travel(s, played)


# --- постановка AD -------------------------------------------------------------------------------

READ_CPS, MIN_PHASE, MAX_PHASE, TAIL = 14.0, 2.5, 10.0, 0.6


def D(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.0001"))


def _attr(e, name, default=None):
    a = e.find(f'./attribute[@id="{name}"]')
    return default if a is None else a.get("value")


class ADStager:
    """Фазы таймлайна AD: на каждую реплику Альфиры — TLVoice и её эмоции. Камер, поз и сцены у AD нет.

    Озвученная реплика — TLVoice ванильной фазы (с её fade), длина по голосу, эмоции Альфиры из той же
    фазы; текстовая — TLVoice без звука, длина по тексту (как у Larian для строк без озвучки), эмоции
    из сценария.
    """

    def __init__(self, lib, tl, uid):
        self.lib, self.tl, self.uid = lib, tl, uid
        tc = tl.xml.find('./region[@id="TimelineContent"]/node[@id="TimelineContent"]/children')
        spk = {}
        for s in tc.find('./node[@id="TimelineSpeakers"]').iter("node"):
            if _attr(s, "MapKey") is not None and _attr(s, "MapValue") is not None:
                spk[int(_attr(s, "MapKey"))] = _attr(s, "MapValue")
        self.actor = spk[0]
        self.report = []
        self.added_cams = []
        self._src = {}

    def _voice(self, node_uuid, start, end, phase, proto=None):
        from staging import set_attr, del_attr
        import copy
        import xml.etree.ElementTree as et
        e = copy.deepcopy(proto) if proto is not None else et.fromstring(
            '<node id="EffectComponent"><attribute id="Type" type="LSString" value="TLVoice" /></node>')
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
            et.SubElement(a, "attribute", {"id": "UUID", "type": "guid", "value": self.actor})
        else:
            set_attr(e.find('./children/node[@id="Actor"]'), "UUID", self.actor, "guid")
        self.tl.insert_new_tl_node(e)

    def _emotions(self, dur, keys):
        ks = [self.tl.create_emotion_key(float(t), code, variation=var) for t, code, var in keys]
        self.tl.create_tl_actor_node("TLEmotionEvent", self.actor, "0", dur, ks,
                                     node_uuid=self.uid(f"tl/emo/{len(self.report)}"), is_snapped_to_end=True)

    def text_phase(self, node_uuid, line):
        from dsl import emotion_keys
        chars = max(len(render(line.en)), len(render(line.ru)))
        dur = D(min(MAX_PHASE, max(MIN_PHASE, chars / READ_CPS + TAIL)))
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        self._voice(node_uuid, start, start + dur, phase)
        self._emotions(dur, emotion_keys(line.emo, float(dur)))
        self.report.append((node_uuid, "текст", float(dur)))

    def voiced_phase(self, node_uuid, src_name, src_node):
        if src_name not in self._src:
            self._src[src_name] = self.lib.assets.get_timeline_object(src_name)
        src = self._src[src_name]
        comps = src.all_effect_components
        voices = [c for c in comps if _attr(c, "Type") == "TLVoice"
                  and src_node in (_attr(c, "DialogNodeId"), _attr(c, "ReferenceId"))]
        if not voices:
            raise RuntimeError(f"{src_name}: нет TLVoice для узла {src_node}")
        v = voices[0]
        vs, ve = D(_attr(v, "StartTime", 0)), D(_attr(v, "EndTime"))
        actor = v.find('./children/node[@id="Actor"]/attribute[@id="UUID"]').get("value")
        pidx = _attr(v, "PhaseIndex", "0")
        keys = []
        for c in comps:
            a = c.find('./children/node[@id="Actor"]/attribute[@id="UUID"]')
            if _attr(c, "Type") != "TLEmotionEvent" or a is None or a.get("value") != actor or _attr(c, "PhaseIndex", "0") != pidx:
                continue
            for k in c.findall('./children/node[@id="Keys"]/children/node[@id="Key"]'):
                t = D(_attr(k, "Time", _attr(c, "StartTime", 0))) - vs
                if t < ve - vs:
                    keys.append((max(D(0), t), int(_attr(k, "Emotion", 1)), int(_attr(k, "Variation", 0))))
        keys = sorted(keys) or [(D(0), 1, 0)]
        first = [k for k in keys if k[0] == 0]
        keys = (first[-1:] or [(D(0), keys[0][1], keys[0][2])]) + [k for k in keys if k[0] > 0]
        dur = ve - vs + D(TAIL)
        phase = self.tl.create_new_phase(node_uuid, dur)
        start = self.tl.get_phase_start_time(phase)
        self._voice(node_uuid, start, start + (ve - vs), phase, proto=v)
        self._emotions(dur, keys)
        self.report.append((node_uuid, f"{src_name} (голос)", float(dur)))


# --- Osiris: goal ALFSV_World ---------------------------------------------------------------------

ALFIRA_OSI = "S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c"

# Фуникулёр Яслей Иллек (Act1b_CRE_Exterior.txt): платформа S_LTN_PLT_CRE_RailLift_000 ходит между
# триггерами S_CRE_RailLift000_Down/_Up; каждый рейс начинает PROC_CRE_Dungeon_ElevatorMove(платформа, X,Y,Z)
# (PlatformMoveTo со скоростью 5 и событием "CRE_Dungeon_ElevatorMoved"), кончает
# PlatformMovementFinished(платформа, "CRE_Dungeon_ElevatorMoved"). Рычаг кабины S_CRE_ElevatorLever_000
# стоит на платформе: если Альфира в 10 м от него в момент отправления — она едет. Рейсы отслеживаются,
# пока не сказана верхняя реплика (начальная и средняя — каждая один раз, как все места).
# Середина пути — опрос раз в секунду: расстояние от неё до точки назначения меньше половины начального.
LIFT_BLOCK = """//REGION Crèche Y'llek funicular: a 3-line mini-scene (start / midway / top)
PROC
PROC_CRE_Dungeon_ElevatorMove((LEVELTEMPLATE)S_LTN_PLT_CRE_RailLift_000_70bb740a-76eb-4255-b607-e2dcad69dbeb, (REAL)_X, (REAL)_Y, (REAL)_Z)
AND
QRY_ALFSV_Place_Wanted("CRE_LiftTop")
AND
GetDistanceTo({A}, S_CRE_ElevatorLever_000_893fcb67-a68d-4471-8dd5-28e66f907ae3, _OnBoard)
AND
_OnBoard < 10.0
AND
GetDistanceToPosition({A}, _X, _Y, _Z, _Dist)
AND
RealDivide(_Dist, 2.0, _Half)
THEN
DB_ALFSV_Lift_Ride(_X, _Y, _Z, _Half);
PROC_ALFSV_Place_Request("CRE_LiftStart");
TimerLaunch("ALFSV_Lift_Poll", 1000);

IF
TimerFinished("ALFSV_Lift_Poll")
AND
DB_ALFSV_Lift_Ride(_X, _Y, _Z, _Half)
AND
GetDistanceToPosition({A}, _X, _Y, _Z, _Dist)
AND
_Dist < _Half
THEN
NOT DB_ALFSV_Lift_Ride(_X, _Y, _Z, _Half);
DB_ALFSV_Lift_Midway(1);
PROC_ALFSV_Place_Request("CRE_LiftMid");

IF
TimerFinished("ALFSV_Lift_Poll")
AND
DB_ALFSV_Lift_Ride(_, _, _, _)
THEN
TimerLaunch("ALFSV_Lift_Poll", 1000);

IF
PlatformMovementFinished(S_LTN_PLT_CRE_RailLift_000_70bb740a-76eb-4255-b607-e2dcad69dbeb, "CRE_Dungeon_ElevatorMoved")
AND
DB_ALFSV_Lift_Midway(1)
THEN
NOT DB_ALFSV_Lift_Midway(1);
PROC_ALFSV_Place_Request("CRE_LiftTop");

// Arrived before the midway poll fired (short ride, reload): no top line without the middle one
IF
PlatformMovementFinished(S_LTN_PLT_CRE_RailLift_000_70bb740a-76eb-4255-b607-e2dcad69dbeb, "CRE_Dungeon_ElevatorMoved")
AND
DB_ALFSV_Lift_Ride(_X, _Y, _Z, _Half)
THEN
NOT DB_ALFSV_Lift_Ride(_X, _Y, _Z, _Half);

//END_REGION
"""


def world_goal(places, trv: Travel, ids) -> str:
    """ALFSV_World.txt: реплики на местах (разово) и фразы в пути (по таймеру)."""
    def fl(f):
        return f"(FLAG){f.name}_{ids.flag(f)}"

    def dlg(s):
        return f"(DIALOGRESOURCE){s.name}_{s.dialog_id}"

    from scenes.recruitment import ROMANCE as R_FLAG, SPARK as S_FLAG
    from scenes.ch02_lute import NOTCH_CITY
    A = ALFIRA_OSI
    o = ["Version 1", "SubGoalCombiner SGC_AND", "INITSECTION",
         "// GENERATED by scripts/dialogs/build.py from scripts/dialogs/scenes/places.py and travel.py.",
         "// Do not edit: change the declarations and rebuild. See scripts/dialogs/README.md.",
         "// Alfira's overhead lines (ADs): one-shot place lines and travel lines. The data is (re)inserted by",
         "// PROC_ALFSV_World_Data at every level start, so new places reach existing saves (INIT does not rerun).",
         "PROC_ALFSV_World_Data();",
         "KBSECTION",
         "//REGION Data", "",
         "IF", "LevelGameplayStarted(_, _)", "THEN", "PROC_ALFSV_World_Data();", "PROC_ALFSV_Travel_Start();", "",
         "PROC", "PROC_ALFSV_World_Data()", "THEN"]
    for p in places:
        o.append(f'DB_ALFSV_Place("{p.key}", {dlg(p.scene)});')
        for t in p.triggers:
            o.append(f'DB_ALFSV_PlaceTrigger((TRIGGER){t}, "{p.key}");')
        for f in p.flags:
            o.append(f'DB_ALFSV_PlaceFlag((FLAG){f}, "{p.key}");')
        for lv in p.levels:
            o.append(f'DB_ALFSV_PlaceLevel("{lv}", "{p.key}");')
    o.append(f"DB_ALFSV_TravelAD({dlg(trv.scene)});")
    o += ["", "//END_REGION", "",
          "//REGION Place lines: event -> request -> first free moment within the wait window", "",
          "IF", f"EnteredTrigger({A}, _Trigger)", "AND", "DB_ALFSV_PlaceTrigger(_Trigger, _Key)", "THEN",
          "PROC_ALFSV_Place_Request(_Key);", "",
          "IF", "FlagSet(_Flag, NULL_00000000-0000-0000-0000-000000000000, _)", "AND", "DB_ALFSV_PlaceFlag(_Flag, _Key)",
          "THEN", "PROC_ALFSV_Place_Request(_Key);", "",
          "IF", "LevelGameplayStarted(_Level, _)", "AND", "DB_ALFSV_PlaceLevel(_Level, _Key)", "THEN",
          "PROC_ALFSV_Place_Request(_Key);", "",
          "// Alfira is a companion, in the active party, and has not said this line yet",
          "QRY", "QRY_ALFSV_Place_Wanted((STRING)_Key)", "AND", "DB_ALFSV_IsCompanion(1)", "AND", f"DB_Players({A})",
          "AND", "DB_ALFSV_Place(_Key, _)", "AND", "NOT DB_ALFSV_PlaceDone(_Key)", "THEN", "DB_NOOP(1);", "",
          "PROC", "PROC_ALFSV_Place_Request((STRING)_Key)", "AND", "QRY_ALFSV_Place_Wanted(_Key)", "AND",
          "NOT DB_ALFSV_PlacePending(_Key, _)", "THEN", f"DB_ALFSV_PlacePending(_Key, {PLACE_WAIT_S * 1000 // TICK_MS});",
          "PROC_ALFSV_AD_Try();", "", "//END_REGION", "",
          "//REGION One AD at a time: requested -> started (done) or failed (retry on the next tick)", "",
          "QRY", "QRY_ALFSV_AD_Free()", "AND", "NOT DB_ALFSV_AD_Requested(_, _)", "AND", "NOT DB_ALFSV_AD_Playing(_)",
          "AND", f"QRY_SpeakerIsAvailable({A})", "THEN", "DB_NOOP(1);", "",
          "PROC", "PROC_ALFSV_AD_Try()", "AND", "DB_ALFSV_PlacePending(_Key, _)", "AND", "DB_ALFSV_Place(_Key, _Dialog)",
          "AND", f"DB_Players({A})", "AND", "QRY_ALFSV_AD_Free()", "THEN", "DB_ALFSV_AD_Requested(_Dialog, _Key);",
          "PROC_ALFSV_AD_SetMood();", f"PROC_TryStartAD(_Dialog, {A});", "",
          "PROC", "PROC_ALFSV_AD_Try()", "AND", "DB_ALFSV_PlacePending(_, _)", "THEN",
          'TimerCancel("ALFSV_World_Tick");', f'TimerLaunch("ALFSV_World_Tick", {TICK_MS});', "",
          "IF", "AutomatedDialogStarted(_Dialog, _)", "AND", "DB_ALFSV_AD_Requested(_Dialog, _Key)", "THEN",
          "NOT DB_ALFSV_AD_Requested(_Dialog, _Key);", "DB_ALFSV_AD_Playing(_Dialog);", "PROC_ALFSV_Place_Done(_Key);", "",
          "PROC", "PROC_ALFSV_Place_Done((STRING)_Key)", "AND", "DB_ALFSV_Place(_Key, _)", "THEN",
          "DB_ALFSV_PlaceDone(_Key);", "", "PROC", "PROC_ALFSV_Place_Done((STRING)_Key)", "AND",
          "DB_ALFSV_PlacePending(_Key, _N)", "THEN", "NOT DB_ALFSV_PlacePending(_Key, _N);", "",
          "IF", "AutomatedDialogEnded(_Dialog, _)", "AND", "DB_ALFSV_AD_Playing(_Dialog)", "THEN",
          "NOT DB_ALFSV_AD_Playing(_Dialog);", "PROC_ALFSV_AD_Try();", "",
          "// Tick: forget a request that did not start, age the pending lines, try again",
          "IF", 'TimerFinished("ALFSV_World_Tick")', "AND", "DB_ALFSV_AD_Requested(_Dialog, _Key)", "THEN",
          "NOT DB_ALFSV_AD_Requested(_Dialog, _Key);", "",
          "IF", 'TimerFinished("ALFSV_World_Tick")', "AND", "DB_ALFSV_PlacePending(_Key, _N)", "AND",
          "IntegerSubtract(_N, 1, _Left)", "THEN", "NOT DB_ALFSV_PlacePending(_Key, _N);", "PROC_ALFSV_Place_Age(_Key, _Left);", "",
          "PROC", "PROC_ALFSV_Place_Age((STRING)_Key, (INTEGER)_Left)", "AND", "_Left > 0", "THEN",
          "DB_ALFSV_PlacePending(_Key, _Left);", "",
          "IF", 'TimerFinished("ALFSV_World_Tick")', "THEN", "PROC_ALFSV_AD_Try();", "",
          "// A dialog that ends without AutomatedDialogEnded (level change) must not block the next ones",
          "IF", "LevelGameplayStarted(_, _)", "AND", "DB_ALFSV_AD_Playing(_Dialog)", "THEN", "NOT DB_ALFSV_AD_Playing(_Dialog);",
          "", "//END_REGION", "",
          f"//REGION Mood flags on Alfira for the AD roots (union over all avatars): {ROMANCE_ICON}", ""]
    mood = [(MOOD.Romance, f"GetFlag({fl(R_FLAG)}, _Avatar, 1)"),
            (MOOD.Spark, f"GetFlag({fl(S_FLAG)}, _Avatar, 1)"),
            (MOOD.Spark, f"GetFlag({fl(R_FLAG)}, _Avatar, 1)"),     # ✨ «искра или роман» (01_act1_world.md §2)
            (MOOD.NotchCity, f"GetFlag({fl(NOTCH_CITY)}, _Avatar, 1)"),
            (MOOD.Cold, f"DB_ApprovalRating({A}, _Avatar, _Value)\nAND\n_Value < {COLD_BELOW}"),
            (MOOD.Warm, f"DB_ApprovalRating({A}, _Avatar, _Value)\nAND\n_Value >= {WARM_AT_LEAST}")]
    o += ["PROC", "PROC_ALFSV_AD_SetMood()", "THEN"] + [f"ClearFlag({fl(f)}, {A});" for f in dict.fromkeys(f for f, _ in mood)] + [""]
    for f, cond in mood:
        o += ["PROC", "PROC_ALFSV_AD_SetMood()", "AND", "DB_Avatars(_Avatar)", "AND", cond, "THEN",
              f"SetFlag({fl(f)}, {A});", ""]
    o += ["//END_REGION", "", LIFT_BLOCK.replace("{A}", A),
          f"//REGION Travel lines: every {TRAVEL_MIN_MS // 60000}-{(TRAVEL_MIN_MS + TRAVEL_SPREAD_MS) // 60000} min while "
          "she walks with the party; each line once (flags in the dialog)", "",
          "PROC", "PROC_ALFSV_Travel_Start()", "AND", "DB_ALFSV_IsCompanion(1)", "AND",
          f"Random({TRAVEL_SPREAD_MS}, _Extra)", "AND", f"IntegerSum({TRAVEL_MIN_MS}, _Extra, _Ms)", "THEN",
          'TimerCancel("ALFSV_Travel");', 'TimerLaunch("ALFSV_Travel", _Ms);', "",
          "IF", "DB_ALFSV_IsCompanion(1)", "THEN", "PROC_ALFSV_Travel_Start();", "",
          "IF", 'TimerFinished("ALFSV_Travel")', "AND", "DB_ALFSV_TravelAD(_Dialog)", "AND", f"DB_Players({A})",
          "AND", f"NOT DB_PlayerInCamp({A})", "AND", "NOT DB_ALFSV_PlacePending(_, _)", "AND", "QRY_ALFSV_AD_Free()",
          "THEN", "PROC_ALFSV_AD_SetMood();", f"PROC_TryStartAD(_Dialog, {A});", "",
          "IF", 'TimerFinished("ALFSV_Travel")', "THEN", "PROC_ALFSV_Travel_Start();", "",
          "IF", "AutomatedDialogStarted(_Dialog, _)", "AND", "DB_ALFSV_TravelAD(_Dialog)", "THEN",
          "DB_ALFSV_AD_Playing(_Dialog);", "",
          "// After a place line the next travel line waits a full interval",
          "IF", "AutomatedDialogStarted(_Dialog, _)", "AND", "DB_ALFSV_Place(_, _Dialog)", "THEN",
          "PROC_ALFSV_Travel_Start();", "", "//END_REGION", "",
          "//REGION Debug (Script Extender console)",
          "// Osi.PROC_ALFSV_Debug_Place(\"CRE_LiftMid\") - play a place line now (ignores 'done')",
          "PROC", "PROC_ALFSV_Debug_Place((STRING)_Key)", "AND", "DB_ALFSV_PlaceDone(_Key)", "THEN",
          "NOT DB_ALFSV_PlaceDone(_Key);", "", "PROC", "PROC_ALFSV_Debug_Place((STRING)_Key)", "THEN",
          "PROC_ALFSV_Place_Request(_Key);", "",
          "// Osi.PROC_ALFSV_Debug_Travel() - the next travel line in 5 s",
          "PROC", "PROC_ALFSV_Debug_Travel()", "THEN", 'TimerCancel("ALFSV_Travel");', 'TimerLaunch("ALFSV_Travel", 5000);',
          "", "//END_REGION", "EXITSECTION", "", "ENDEXITSECTION", ""]
    return "\n".join(o)


ROMANCE_ICON = "romance > spark > cold > normal"
