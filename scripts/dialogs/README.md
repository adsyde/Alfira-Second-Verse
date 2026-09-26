# Исходники сцен: формат

Сцена — это файл `scripts/dialogs/scenes/<имя>.py` с объектом `SCENE`. Из него
`scripts/dialogs/build.py` собирает диалог, таймлайн с постановкой, сцену, записи
банков, тексты EN/RU, реакции одобрения и новые флаги (подробно — `docs/STAGING.md`).
Новую сцену нужно добавить в список `SCENES` в `build.py`.

Формат повторяет сценарий из `design/dialogs/*.md`: блоки реплик Альфиры, варианты
героя, переходы. Пример — `scenes/recruitment.py` (сцена A, 13 вариантов, проверка,
общие меню, озвученные реплики).

## Сцена

```python
from dsl import ALFIRA, PLAYER, Join, Scene, check, new_flag, opt, outcome, say, voice
from vanilla import DC, F, NESTED, T

SCENE = Scene(
    name="ALFSV_Alfira_Recruitment",           # имя ресурса и файлов
    dialog_id="009896a5-…",                     # ID в банке диалогов; на него ссылается Osiris, не менять
    base="DEN_Bard_InParty",                    # ванильный диалог: его сцена, камеры, актёры
    voice_from=["CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives", …],  # где искать озвученные реплики
    nested=[NESTED.SwapRecruitment],            # вложенные диалоги (меню замены при полном отряде)
)
S = SCENE
```

## Блоки

| Вызов | Что это |
|---|---|
| `S.greeting("id", строки…, when=[условия], <переход>)` | Приветствие (корень). Порядок вызовов = приоритет: игра берёт первое, чьи условия выполнены |
| `S.block("id", строки…, <переход>)` | Реплики Альфиры подряд |
| `S.menu("id", варианты…)` | Меню вариантов без реплики. На него ведут `go="id"` из разных мест: это одни и те же узлы, поэтому «один раз» и петли работают как в игре |

**Переход** — ровно один из аргументов:
- `go="A3"` — дальше блок A3 (если A3 — меню, сразу его варианты);
- `choices=[opt(…), …]` — варианты прямо здесь;
- `end=True` — конец диалога;
- `join=Join(...)` — вступление в отряд (см. ниже).

У `greeting`/`block` есть `set=[…]` — флаги на последней реплике блока.

## Реплики Альфиры

```python
say("Stop it. No - actually, don't stop…", "Перестань. Нет — вообще-то не переставай…",
    emo="happy/2>happy", shot="alfira_close", note="(краснеет)")
voice("h4d653a62g29e7g4ce3g813fg184db5a4e691")      # её реплика из игры: голос, текст и перевод Larian
```

- `*курсив*` → `<i>курсив</i>` игры. Ремарки («(краснеет)») в текст не пишутся — их роль
  играет `emo`; сам текст ремарки можно оставить в `note` для людей.
- Род обращения к герою в русском: `{мужской|женский}` — «Ты {спел|спела}». Мужская форма
  идёт в `AlfiraSecondVerse_ru.xml`, женская — в `AlfiraSecondVerse_ru_to_F.xml`.
- `emo` — эмоции лица по ходу реплики: `"happy"`, `"surprise>happy"` (делят фазу поровну),
  `"happy/2"` (вариация 2), или список `[(0.0, "fear"), (2.5, "sad/1")]` (секунды).
  Имена: neutral, happy, thinking, angry, fear, sad, surprise, disgust, sleeping, dead,
  confusion, pain (коды — из `Public/Shared/Animation/Emotions.lsf`, сверяются при сборке).
- `shot` — план камеры: `alfira` (из-за плеча героя, по умолчанию), `alfira_close`
  (крупный план), `player` (на героя).
- `voice(handle)` — handle ищется в диалогах `voice_from`. Постановка (эмоции, взгляды,
  позы, планы камеры) берётся из ванильной фазы этой реплики; `emo`/`shot` не нужны.
- У любой реплики: `set=[…]` (флаги), `approve=±N` (одобрение Альфиры).

## Варианты героя

```python
opt("Почему именно со мной?", "Why me, of all people?",   # русский, английский
    when=[T.BARD(PLAYER)],          # условия показа
    once=True,                      # показать один раз (ShowOnce игры)
    approve=+2, set=[SPARK(PLAYER)],
    reply=[voice("h1ab…"), voice("h2b0…")],                # её ответ (может не быть)
    go="A4")                        # переход после ответа
```

Проверка навыка (ActiveRoll, как в игре — вариант показывается один раз):

```python
check("*Присмотреться к ней внимательнее.*", "*Look at her more closely.*",
      skill="Insight", ability="Wisdom", dc=DC.Act1_Medium,
      success=outcome(approve=+2, reply=[say(…), voice(…)], go="A4"),
      failure=outcome(reply=[say(…)], go="A4"))
```

## Флаги и условия

- Ванильные — в `vanilla.py` (`F.FinishedSong`, `T.BARD`, …) с именем, типом и uuid из данных
  игры. При каждой сборке `build.py` сверяет имя и тип с файлами `Flags`/`Tags` игры.
- Новые: `new_flag("ALFSV_Имя", "Global" | "Object" | "Dialog", "описание")`; uuid выдаётся
  детерминированно от имени, файл флага пишется в `Public/_MOD_/Flags/`.
- Запись: глобальный `F.X.on` / `F.X.off`; на персонаже `FLAG(ALFIRA)` / `FLAG(PLAYER)`,
  снять — `FLAG(ALFIRA, False)`. «Dialog» хранится на персонаже (как `DEN_TieflingBard_HasMet`).
- В `when` — условия (все должны выполняться), в `set` — что поставить/снять.

## Вступление в отряд

```python
Join(nested=NESTED.SwapRecruitment,                       # меню замены при полном отряде
     to_camp_line=say("I'll find your camp…", "Я найду твой лагерь…"),  # если герой отправил её в лагерь
     to_camp_flag=F.SwapToCamp,
     reply=None)                                          # реплика при вступлении (или узел без текста)
```

Даёт ту же структуру, что у вербовки Уилла и Лаэ'зель: при `GEN_MaxPlayerCountReached` —
вложенный диалог замены, иначе узел, ставящий `OriginAddToParty` на Альфиру.

## Сборка и проверка

```
python scripts/dialogs/build.py      # генерация в mod/ (запускается и из build_pak.py)
python scripts/dialogs/validate.py   # ссылки, фазы, круг lsx↔lsf через Divine, сверка с игрой
python scripts/dialogs/tree.py       # дерево диалога в build/dialogs/<сцена>.md для вычитки
```

UUID узлов, handle текстов и id компонентов таймлайна выводятся из ключей (id блока и номер
реплики/варианта), поэтому повторная сборка даёт те же файлы. Если переставить варианты
местами, их UUID поменяются — это безопасно, пока диалог не открыт в сохранении.
