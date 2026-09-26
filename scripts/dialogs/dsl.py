"""Исходный формат сцен: из этих объектов build.py собирает диалог, таймлайн, сцену и тексты.

Сцена — это набор именованных блоков. Блок — реплики Альфиры подряд и переход дальше.
Переход (у блока, у варианта ответа, у исхода проверки) задаётся одним из аргументов:
    go="A3"        дальше блок A3 (если A3 — меню вариантов, то сразу варианты);
    choices=[...]  варианты ответа героя прямо здесь;
    end=True       конец диалога;
    join=JOIN      вступление в отряд (с меню замены при полном отряде).
go может быть списком блоков: игра берёт первый, чьи условия (block(..., when=...)) выполнены.
Главы разговоров (этап 4) — chapter(...) в сцене главы; вход в них генерируется в разговоре в
отряде (Scene.chapter_entries) и в Osiris (goal ALFSV_Chapters). Формат — scripts/dialogs/README.md.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

ALFIRA = 0   # индексы спикеров во всех наших диалогах (как в ванильном DEN_Bard_InParty)
PLAYER = 1

# Эмоции таймлайна. Числа — из Public/Shared/Animation/Emotions.lsf (узел EmotionToAnimSet);
# build.py сверяет таблицу с файлом игры при каждой сборке.
EMOTIONS = {"neutral": 1, "happy": 2, "thinking": 4, "angry": 8, "fear": 16, "sad": 32,
            "surprise": 64, "disgust": 128, "sleeping": 256, "dead": 512, "confusion": 1024, "pain": 2048}

# Планы камеры для текстовых реплик (см. staging.py: CAMERAS).
SHOTS = ("alfira", "alfira_close", "player")


# --- флаги и условия ------------------------------------------------------------------------

@dataclass(frozen=True)
class Flag:
    """Флаг игры (uuid из данных игры) или новый флаг мода (new=True, uuid выдаёт build.py).

    kind: Global | Object | Dialog | Tag. Для Object/Dialog/Tag нужен спикер: FLAG(ALFIRA).
    """
    name: str
    kind: str
    uuid: str = ""
    new: bool = False
    description: str = ""

    def __call__(self, speaker: int | None = None, value: bool = True) -> "FlagRef":
        if self.kind in ("Object", "Dialog", "Tag") and speaker is None:
            raise ValueError(f"{self.name}: флагу типа {self.kind} нужен спикер")
        return FlagRef(self, value, speaker)

    @property
    def on(self) -> "FlagRef":            # глобальный флаг установлен
        return self()

    @property
    def off(self) -> "FlagRef":           # глобальный флаг не установлен
        return self(value=False)


@dataclass(frozen=True)
class FlagRef:
    flag: Flag
    value: bool = True
    speaker: int | None = None

    def __invert__(self) -> "FlagRef":
        return FlagRef(self.flag, not self.value, self.speaker)


def new_flag(name: str, kind: str, description: str) -> Flag:
    return Flag(name, kind, new=True, description=description)


# --- реплики -----------------------------------------------------------------------------------

@dataclass
class Line:
    """Реплика Альфиры.

    Текстовая: say(en, ru). Озвученная реплика игры: voice(handle) — берутся её handle, голос
    и постановка из ванильного таймлайна (build.py находит узел по handle в voice_from сцены).
    """
    en: str = ""
    ru: str = ""
    handle: str = ""                     # задан — это озвученная реплика игры
    emo: str | list = "neutral"
    shot: str = "alfira"
    set: list = field(default_factory=list)
    approve: int = 0
    note: str = ""                       # для людей: ремарка из сценария
    narrator: bool = False               # ремарка рассказчика (narrate)


def say(en: str, ru: str, *, emo="neutral", shot="alfira", set=(), approve=0, note="") -> Line:
    """Новая текстовая реплика. В ru можно писать {мужской|женский} род обращения к герою.

    *слово* превращается в курсив игры (<i>слово</i>). Ремарки в текст не пишутся — их роль
    играет emo.
    """
    return Line(en=en, ru=ru, emo=emo, shot=shot, set=list(set), approve=approve, note=note)


def voice(handle: str, *, set=(), approve=0, note="") -> Line:
    return Line(handle=handle, set=list(set), approve=approve, note=note)


def narrate(en: str, ru: str, *, emo="neutral", shot="alfira", set=(), approve=0, note="") -> Line:
    """Ремарка рассказчика: действие без слов («Она смотрит на свои сапоги»).

    Так игра показывает действия в диалоге: узел рассказчика (speaker -666), текст в звёздочках
    (*...* — так в loca игры). Звёздочки build добавит сам; текст без озвучки. emo — лицо Альфиры,
    shot — план камеры на время ремарки.
    """
    return Line(en=en, ru=ru, emo=emo, shot=shot, set=list(set), approve=approve, note=note, narrator=True)


# --- переходы и варианты -----------------------------------------------------------------------

@dataclass
class Join:
    """Вступление в отряд: при полном отряде — ванильное меню замены (вложенный диалог)."""
    nested: str                          # ID ресурса вложенного диалога замены (в банке игры)
    to_camp_line: Line | None = None     # её ответ, если герой отправил её в лагерь
    to_camp_flag: Flag | None = None     # флаг «герой выбрал лагерь» (ставит вложенный диалог)
    reply: Line | None = None            # её реплика при вступлении (если нет — узел без текста)


@dataclass
class Next:
    go: str | list = ""                  # блок или список блоков-альтернатив (первый подходящий)
    choices: list = field(default_factory=list)
    end: bool = False
    join: Join | None = None
    set: list = field(default_factory=list)      # флаги на последнем узле ветки

    def check(self, where: str) -> None:
        n = bool(self.go) + bool(self.choices) + self.end + (self.join is not None)
        if n != 1:
            raise ValueError(f"{where}: нужен ровно один переход (go / choices / end / join), задано {n}")


def _next(where, go="", choices=(), end=False, join=None, set=()) -> Next:
    nx = Next(go=list(go) if isinstance(go, (list, tuple)) else go, choices=list(choices), end=end,
              join=join, set=list(set))
    nx.check(where)
    return nx


@dataclass
class Option:
    """Вариант ответа героя."""
    ru: str
    en: str
    when: list = field(default_factory=list)
    once: bool = False
    approve: int = 0
    set: list = field(default_factory=list)
    reply: list = field(default_factory=list)
    next: Next | None = None
    roll: "Roll | None" = None
    key: str = ""
    game_line: tuple = ()                # (handle, version) реплики героя из игры: её текст и перевод Larian


def opt(ru: str, en: str, *, when=(), once=False, approve=0, set=(), reply=(), key="",
        go="", choices=(), end=False, join=None, game_line=()) -> Option:
    """game_line=(handle, version) — взять готовую реплику героя из игры (ru/en тогда для чтения)."""
    o = Option(ru=ru, en=en, when=list(when), once=once, approve=approve, set=list(set),
               reply=list(reply), key=key, game_line=tuple(game_line))
    o.next = _next(f"вариант «{ru}»", go, choices, end, join)
    return o


@dataclass
class Outcome:
    reply: list
    next: Next
    approve: int = 0
    set: list = field(default_factory=list)


def outcome(*, reply=(), approve=0, set=(), go="", choices=(), end=False, join=None) -> Outcome:
    return Outcome(list(reply), _next("исход проверки", go, choices, end, join), approve, list(set))


@dataclass
class Roll:
    skill: str
    ability: str
    dc: str                              # uuid класса сложности (vanilla.DC)
    success: Outcome
    failure: Outcome
    target: int = ALFIRA


def check(ru: str, en: str, *, skill: str, ability: str, dc: str, success: Outcome,
          failure: Outcome, when=(), key="") -> Option:
    """Вариант с проверкой навыка (ActiveRoll): показывается один раз, как в игре."""
    o = Option(ru=ru, en=en, when=list(when), once=True, key=key)
    o.roll = Roll(skill, ability, dc, success, failure)
    return o


# --- сцена -------------------------------------------------------------------------------------

@dataclass
class Block:
    id: str
    lines: list
    next: Next | None
    when: list = field(default_factory=list)
    root: bool = False
    chapters: bool = False               # место входов в главы (Scene.chapter_entries)


# --- главы разговоров (этап 4) -----------------------------------------------------------------

@dataclass
class Chapter:
    """Глава разговора с Альфирой (design/APPROVAL.md §4). Объявляется в файле сцены главы.

    Жизнь главы — два глобальных флага мода, их uuid выдаёт build:
      ALFSV_ChapterNN_Available — ставит Osiris (goal ALFSV_Chapters, генерируется), когда глава
                                  открылась: предыдущая глава сыграна, выполнены условия story и
                                  (если after_rest) только что был долгий отдых;
      ALFSV_ChapterNN_Done      — ставит сама сцена главы (set=[CH.done]) там, где глава считается
                                  сыгранной. До этого глава предлагается при каждом разговоре.
    В разговоре в отряде вход в главу — корень без текста с условиями Available, !Done, when и
    порогом одобрения, дальше — вложенный диалог главы (как ShadowHeart_InParty2 → *_Nested_*Chapter).
    """
    number: int
    title: str
    after_rest: bool = True              # открывается только после долгого отдыха (иначе — сразу)
    story: list = field(default_factory=list)   # глобальные флаги: проверяет Osiris при открытии
    when: list = field(default_factory=list)    # условия входа при каждом разговоре (флаги диалога)
    approval: int | None = None          # мин. одобрение собеседника на входе (Approval_AtLeast_N_For_Sp1)

    @property
    def available_flag(self) -> Flag:
        return Flag(f"ALFSV_Chapter{self.number:02d}_Available", "Global", new=True,
                    description=f"Alfira chapter {self.number} is unlocked")

    @property
    def done_flag(self) -> Flag:
        return Flag(f"ALFSV_Chapter{self.number:02d}_Done", "Global", new=True,
                    description=f"Alfira chapter {self.number} has been played")

    @property
    def done(self) -> FlagRef:           # set=[CH.done] — глава сыграна
        return self.done_flag.on


def chapter(number: int, title: str, *, after_rest=True, story=(), when=(), approval=None) -> Chapter:
    """Объявление главы: номер (порядок), название, условия открытия и входа. См. Chapter."""
    for r in story:
        if not isinstance(r, FlagRef) or r.flag.kind != "Global":
            raise ValueError(f"глава {number}: в story только глобальные флаги (F.X.on / F.X.off), получено {r!r}")
    return Chapter(number, title, after_rest, list(story), list(when), approval)


@dataclass
class Scene:
    name: str                            # имя диалога и ресурса (ALFSV_...)
    dialog_id: str                       # ID ресурса в банке диалогов (на него ссылается Osiris)
    base: str                            # ванильный диалог-основа: его сцена, камеры, актёры
    subfolder: str = "Companions"
    voice_from: list = field(default_factory=list)   # где искать озвученные реплики (по handle)
    nested: list = field(default_factory=list)       # ID вложенных диалогов (childResources банка)
    status: str = ""
    chapter: Chapter | None = None                   # сцена — глава разговора (вложенный диалог)
    blocks: dict = field(default_factory=dict)
    roots: list = field(default_factory=list)

    def _add(self, b: Block) -> Block:
        if b.id in self.blocks:
            raise ValueError(f"{self.name}: блок {b.id} уже есть")
        self.blocks[b.id] = b
        if b.root:
            self.roots.append(b.id)
        return b

    def greeting(self, id: str, *lines: Line, when=(), go="", choices=(), end=False, join=None, set=()):
        """Приветствие (корневой узел). Порядок вызовов = приоритет: первое подходящее по when."""
        if not lines:
            raise ValueError(f"{id}: приветствию нужна реплика")
        return self._add(Block(id, list(lines), _next(id, go, choices, end, join, set), list(when), root=True))

    def block(self, id: str, *lines: Line, when=(), go="", choices=(), end=False, join=None, set=()):
        """Реплики подряд. when — условия (для альтернатив в go=[...]: берётся первый подходящий)."""
        if not lines:
            raise ValueError(f"{id}: блоку нужна реплика (для одних вариантов — menu())")
        return self._add(Block(id, list(lines), _next(id, go, choices, end, join, set), list(when)))

    def chapter_entries(self):
        """Здесь (между приветствиями, по приоритету) встают входы во все главы из scenes/ch*.py.

        Для каждой главы build создаёт корень без текста с условиями главы и вложенный диалог главы.
        После главы разговор заканчивается.
        """
        return self._add(Block("@chapters", [], None, root=True, chapters=True))

    def menu(self, id: str, *options: Option):
        """Меню вариантов без реплик: на него ведут go="id" из разных мест (общие узлы)."""
        return self._add(Block(id, [], Next(choices=list(options))))


# --- текст -------------------------------------------------------------------------------------

_GENDER = re.compile(r"\{([^{}|]*)\|([^{}|]*)\}")
_ITALIC = re.compile(r"\*([^*]+)\*")


def render(text: str, female: bool = False, narrator: bool = False) -> str:
    """{спел|спела} → нужный род; *курсив* → <i>курсив</i>. Ремарка рассказчика — *в звёздочках*."""
    text = _GENDER.sub(lambda m: m.group(2 if female else 1), text)
    if narrator:
        return f"*{text}*"
    return _ITALIC.sub(r"<i>\1</i>", text)


def has_gender(text: str) -> bool:
    return bool(_GENDER.search(text))


def emotion_keys(emo, duration: float) -> list[tuple[float, int, int]]:
    """"happy" | "surprise>happy" | "happy/2" | [(0.0, "fear"), (1.5, "sad/1")] →
    [(секунда от начала фазы, код эмоции, вариация)]. Через «>» ключи делят фазу поровну."""
    def one(tok: str):
        name, _, var = tok.strip().partition("/")
        if name not in EMOTIONS:
            raise ValueError(f"неизвестная эмоция {name!r}; есть {sorted(EMOTIONS)}")
        return EMOTIONS[name], int(var or 0)
    if isinstance(emo, str):
        toks = emo.split(">")
        return [(round(duration * i / len(toks), 2), *one(t)) for i, t in enumerate(toks)]
    return [(float(t), *one(e)) for t, e in emo]
