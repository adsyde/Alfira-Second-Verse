# Этап 2. Вербовка: что сделано и как проверить

Статус: **собрано, в игре не проверено.** Этап закрывается только после
проверки по списку ниже (CLAUDE.md §2).

Альфира (`S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c`) становится
«поздней спутницей» по схеме Хальсина и Минтары (см. [ARCHITECTURE.md](ARCHITECTURE.md)).
Мод работает сам, без Script Extender. SE нужен только как отладочная консоль.

**Версия 0.3.0: диалоги с постановкой.** Заглушки `[PH]` без таймлайна заменены
сгенерированными диалогами с таймлайном, камерой, эмоциями и взглядами (конвейер —
[STAGING.md](STAGING.md)): вербовка — сцена A «Ученица без наставницы» из
`design/dialogs/01_recruitment.md` (черновик v3), разговор в отряде — её озвученные реплики
из игры. Включено одобрение Альфиры (§2.6).

## 1. Файлы

| Файл | Что это |
|------|---------|
| `mod/Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Companion.txt` | Сценарий Osiris: вербовка, защита от сюжетных скриптов, отладка |
| `scripts/dialogs/scenes/recruitment.py`, `…/inparty.py` | Источник двух диалогов (формат — `scripts/dialogs/README.md`) |
| `scripts/dialogs/*.py` | Генератор: диалог, таймлайн, сцена, банки, тексты, реакции, флаги ([STAGING.md](STAGING.md)) |
| `mod/Mods/_MOD_/Story/DialogsBinary/Companions/ALFSV_Alfira_Recruitment.lsx`, `…_InParty.lsx` | Диалоги (генерируются; в пак — `.lsf`) |
| `mod/Public/_MOD_/Timeline/Generated/*` | Таймлайны и сцены (генерируются при сборке, в git не идут) |
| `mod/Public/_MOD_/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsx` | Банк диалогов: два ресурса и ссылки на вложенные диалоги обмена |
| `mod/Public/_MOD_/Content/Generated/[PAK]_GeneratedDialogTimelines/_merged.lsx` | Банк таймлайнов (генерируется при сборке) |
| `mod/Public/_MOD_/ApprovalRatings/Reactions/*.lsx` | Реакции одобрения Альфиры: +1, +2, +3, −1 |
| `mod/Public/_MOD_/Flags/*.lsx` | Новые флаги: `ALFSV_Recruitment_Postponed/Refused`, `ALFSV_Romance_Spark`, `ALFSV_HeroMotive_*`, ротация приветствий |
| `mod/Mods/_MOD_/Globals/WLD_Main_A/Characters/4a405fba-….lsx` | Её глобальный персонаж с `HasPlayerApprovalRating` (генерируется, в git не идёт) |
| `mod/Mods/_MOD_/Localization/English/AlfiraSecondVerse_en.xml`, `…/Russian/AlfiraSecondVerse_ru.xml`, `…_ru_to_F.xml` | Новые тексты; женские формы обращения |
| `scripts/build_pak.py` | Генератор диалогов, подстановка `_MOD_`, `.lsf.lsx`→`.lsf`, проверка текстов диалогов, проверка списка файлов пака |
| `scripts/check_story.py`, `scripts/osiheader/` | Проверка goals мода компилятором LSLib вместе с ванильными |
| `config/tools.json` | Версия мода 0.3.0 (см. §4) |

Идентификаторы ресурсов (на них ссылается Osiris, в сохранениях они остаются —
**не менять**):

| Ресурс | ID в банке диалогов |
|--------|---------------------|
| `ALFSV_Alfira_Recruitment` | `009896a5-580c-4135-98db-99234865b61d` |
| `ALFSV_Alfira_InParty` | `b2950129-fdd2-4cda-8182-cf41cfd5d809` |

Пак 0.3.0 (29 файлов, 221 КБ):

```
Mods/AlfiraSecondVerse_<uuid>/Globals/WLD_Main_A/Characters/4a405fba-3000-4c63-97e5-a8001ebb883c.lsf
Mods/AlfiraSecondVerse_<uuid>/Localization/English/AlfiraSecondVerse_en.xml
Mods/AlfiraSecondVerse_<uuid>/Localization/Russian/AlfiraSecondVerse_ru.xml
Mods/AlfiraSecondVerse_<uuid>/Localization/Russian/AlfiraSecondVerse_ru_to_F.xml
Mods/AlfiraSecondVerse_<uuid>/meta.lsx
Mods/AlfiraSecondVerse_<uuid>/Story/DialogsBinary/Companions/ALFSV_Alfira_InParty.lsf
Mods/AlfiraSecondVerse_<uuid>/Story/DialogsBinary/Companions/ALFSV_Alfira_Recruitment.lsf
Mods/AlfiraSecondVerse_<uuid>/Story/RawFiles/Goals/ALFSV_Companion.txt
Public/AlfiraSecondVerse_<uuid>/ApprovalRatings/Reactions/<uuid>.lsx          (4 файла)
Public/AlfiraSecondVerse_<uuid>/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsf
Public/AlfiraSecondVerse_<uuid>/Content/Generated/[PAK]_GeneratedDialogTimelines/_merged.lsf
Public/AlfiraSecondVerse_<uuid>/Flags/<uuid>.lsf                               (9 файлов)
Public/AlfiraSecondVerse_<uuid>/Timeline/Generated/ALFSV_Alfira_InParty.lsf
Public/AlfiraSecondVerse_<uuid>/Timeline/Generated/ALFSV_Alfira_InParty_Scene.lsf
Public/AlfiraSecondVerse_<uuid>/Timeline/Generated/ALFSV_Alfira_InParty_Scene.lsx
Public/AlfiraSecondVerse_<uuid>/Timeline/Generated/ALFSV_Alfira_Recruitment.lsf
Public/AlfiraSecondVerse_<uuid>/Timeline/Generated/ALFSV_Alfira_Recruitment_Scene.lsf
Public/AlfiraSecondVerse_<uuid>/Timeline/Generated/ALFSV_Alfira_Recruitment_Scene.lsx
```

## 2. Как устроено

### 2.1 Вербовка

В игре, где Альфиру не завербовали, мод ничего не меняет. Все факты о ней как о
спутнице ставит `PROC_ALFSV_MakeCompanion()` в момент первой вербовки, то есть
когда на неё ставится флаг `OriginAddToParty` или `GLO_ORI_Event_InvitedToCamp_Walk`:

- `DB_ALFSV_IsCompanion(1)` — наш признак «она спутница»;
- `DB_CompanionOnlyFaction(Alfira, Companion14)` и `DB_OriginNPCAlignment(Alfira, ACT1_DEN_TieflingBard)`;
- `DB_OriginInPartyDialog(Alfira, ALFSV_Alfira_InParty)`;
- ванильные флаги из заготовки Темного Соблазна: `DB_OriginPartOfTheTeamFlag(…, ORI_Alfira_ControlledByUser)`
  и `DB_OriginKickFromPartyFlags(…, ORI_Alfira_Event_KickCompanion, ORI_Alfira_State_CanBeKicked)`.
  Поэтому ванильные меню обмена показывают «Ты можешь занять место Альфиры»;
- `DB_Origins` и `DB_Origins_UnavailableForRandom`, как у Минска и Хальсина в `_StartPostEA.txt`;
- `PROC_GLO_PartyMembers_Initialize`, `PROC_DEN_RemoveFromDenNPCs` (так Рощу покидает Уилл),
  конфиг Anubis `DefaultCharacter` вместо `DEN_Bard` (иначе в лагере она, скорее всего, пойдёт к своему камню в Роще).

Дальше работает ванильный конвейер: `DialogEnded` → `PROC_GLO_PartyMembers_CheckAdd` →
`PROC_GLO_PartyMembers_Add`. При первом входе в отряд `PROC_ORI_SetupCamp(Alfira, 0)`
(как у Хальсина), при каждом входе — `SetFaction(Companion14)`.

**Фракция.** Из `CompanionN` действительно свободны `Companion13` и `Companion14`. Их нет ни в
одном сценарии (кроме общего списка `DB_CompanionFactions`), ни в шаблонах, ни в данных уровней.
`Companion15`, которую предлагал разбор, занята: с ней размещена Джахейра
(`GustavDev/Globals/SCL_Main_A/Characters/_merged.lsx`). Выбрана `Companion14`: другие
моды-спутники чаще берут первую свободную.

**Условие вербовки** (`QRY_ALFSV_CanOfferRecruitment`) действует в акте 1, пока она ещё не спутница:
уровень `WLD_Main_A`, `DEN_TieflingBard_State_FinishedSong`. Вербовка закрыта, если выполнено любое из условий:
`ConvincedToQuit`, `SmashedLute`, тифлинги ушли (`DEN_TieflingRefugees_State_LeftDen`),
враждебность тифлингов, поход рейдеров (`GOB_DrowCommander_Event_RaidersLeftForAttack`,
`RaidersAtDen`, `RaidersInDen`, `RaiderVictory`), она мертва, она — жертва ночи Темного Соблазна,
она сейчас на празднике тифлингов. Пока условие выполнено, по клику аватара вместо её
ванильного диалога открывается `ALFSV_Alfira_Recruitment` (`QRY_SelectCustomDialog`).

### 2.2 Уровень и класс

Ни статы, ни шаблон трогать не пришлось. В `Gustav.pak → Public/GustavDev/Origins/Origins.lsx`
у Larian уже есть Origin **«Alfira»**: `UUID 38357c93-b437-4f03-88d0-a67bd4c0e3e9`,
`GlobalTemplate 4a405fba-…` (это она), класс **Бард** (`92cd50b6-…`), подкласс **Коллегия
знаний** (`d21368ac-…`), раса Тифлинг (потомок Асмодея), предыстория Артист (Entertainer),
`ReallyTags = REALLY_ALFIRA`. Так же устроены Хальсин (NPC-статблок `DEN_Archdruid_Boss`,
Origin «Halsin») и Минтара (`GOB_DrowCommander`, Origin «Minthara»): класс при вступлении
берётся из Origin-записи по `GlobalTemplate`. Вызов `RequestInitialLevel` делает ванильный
`PROC_CheckFirstTimeRecruited` (один раз). Раз она в `DB_Origins`, `PROC_GLO_DataGetOriginTags`
ставит ей теги из этой записи.

Тот же Origin UUID нужен и дальше: реакции одобрения (`Public/*/ApprovalRatings/Reactions/*.lsx`)
привязаны к спутникам по UUID Origin-записи. Альфира `38357c93-…` уже есть в 4 ванильных
реакциях. Этим займётся этап 4.

### 2.3 Диалоги: минимальный набор файлов

> 0.3.0: диалоги теперь с таймлайном, сценой и записью в `GeneratedDialogTimelines`, как у
> игры; всё генерируется ([STAGING.md](STAGING.md)). Ниже — как было в 0.2.0.

Новому диалогу нужны:
1. `Story/DialogsBinary/**/<Имя>.lsf` — узлы. Пишем в `.lsx`, сборка конвертирует в `.lsf`.
   Файл `Story/Dialogs/*.lsj` не нужен (руководство Milo Magnetuning на wiki.bg3.community).
2. Запись `Resource` в банке `Public/<мод>/Content/**/_merged.lsf` (регион `DialogBank`):
   `ID` = идентификатор ресурса для Osiris, `SourceFile` = путь к `.lsj` (так делает игра, файла
   может не быть), `childResources` = вложенные диалоги.
3. Реплики в loca xml.

Таймлайн, сцену и запись в `GeneratedDialogTimelines` **не делали**: у наших диалогов нет
`TimelineId`. Такие диалоги в игре есть (`END_GatherYourAllies_Act1GroupAllyAwards`,
reflection dialogs), а в движке есть путь без таймлайна (`DialogTimelinesEnabled`,
`GameCameraEnableCloseUpDialog`). Но у всех ванильных диалогов с выбором ответа, которые
действительно запускаются, таймлайн есть. **Это главный риск этапа** (§5, пункт 1). Если
диалог без таймлайна не покажется, таймлайн придётся генерировать. Тогда решаем: свой
генератор по образцу `DEN_Bard_InParty` или `bg3moddinglib` (MIT, не скачивали).

Вложенные диалоги обмена при полном отряде — ванильные. В вербовке это
`GLO_CompanionSwap_Recruitment` (`f02d36d9-…`, как у Уилла и Лаэ'зель), в лагере —
`GLO_CompanionSwap_Camp` (`002e501b-…`, как у Минска). В узле `Nested Dialog`
`NestedDialogNodeUUID` — это ID ресурса вложенного диалога в банке, а не внутренний UUID.

### 2.4 Защита от сюжетных скриптов

Реакции на вставку фактов (Osiris запускает правило при вставке факта в любую базу из условия).
Действуют, пока `DB_ALFSV_IsCompanion(1)`:

| Скрипт игры | Что сделал бы | Наш ответ |
|---|---|---|
| `Act1_ORI_DarkUrge.txt`, `MakeNPCHook` | ставит `DEN_Bard_InParty` при каждом увольнении | возвращаем `ALFSV_Alfira_InParty` (приём из `GLO_Companion_Halsin.txt`) |
| `Act1_DEN_TieflingRefugees.txt`, уход тифлингов | `SetHasDialog 0`, `SetOnStage 0` | убираем из `DB_DEN_AttackOnDen_LeaveNPCs` |
| `Act1_DEN_Misc.txt`, `PROC_DEN_KillTieflings` | телепорт и `Die` | убираем из `DB_FOR_SlaughteredTieflingTriggers` |
| `Act1_DEN_DruidAttack.txt` | роль «Cower», фракция, диалог | убираем из `DB_DEN_DruidAttack_NonDruids` |
| `Act1_CAMP_GoblinHuntCelebration.txt` | её диалог, телепорт, `SetOnStage 0` во сне | убираем её, выходит дублёр `S_CAMP_TieflingBackup_001` (ванильная ветка «Альфира недоступна») |
| `Act*_GLO_LevelTravelers.txt` | Anubis `DEN_Bard`/`HAV_Bard`/`SCE_Alfira`/`LOW_Alfira` | убираем `DB_GLO_LevelTraveler` |
| `Act2_HAV_TieflingSurvivors.txt` | фракция, диалог, телепорт, `SetLevel(4)` | убираем из `DB_HAV_TieflingSurvivors` |
| `Act2_HAV_General`, `…ShadowSiege(_Combat)`, `…TakingIsobel_InnAttack` | роли тифлинга, рой нежити, нокаут | убираем из соответствующих баз |
| `Act2_SCE_EndBrief.txt`, `Act2_SCE_TieflingFollowUp.txt` | выводит из отряда на «дебриф» | убираем из `DB_SCE_Debrief_Participant(_Config)`, `DB_SCE_TieflingFollowUp_Tieflings` |
| `Act3b_LOW_ElfsongTavern.txt`, `PROC_LOW_AlfiraSetup` | телепорт на крышу, фракция, диалог | отменить нельзя: по вставке `DB_Dialogs(…LOW_Elfsong_Alfira)` возвращаем диалог, фракцию и место (в отряде — к хосту, в лагере — `PROC_ORI_SetupCamp`) |

### 2.4a Вербовка: сцена A (0.3.0)

Дерево — `python scripts/dialogs/tree.py` → `build/dialogs/ALFSV_Alfira_Recruitment.md`.
74 узла, 46 фаз (21 — её озвученные реплики игры, 25 — новые тексты), ~5 минут всех фаз.

- **Приветствие** (первое подходящее): после «Нет» — «Changed your mind?…»; после «Не сейчас» —
  её озвученная «I want to join you…» и сразу выбор; лютню крали и вернули
  (`DEN_TieflingBard_State_ReturnedInstrument`) — холодное; был дуэт
  (`DEN_TieflingBard_Event_GiveProficiency` на герое) — «аккомпаниатор»; герой-бард (тег `BARD`)
  — «ты спел ту строку»; иначе — «что бы я ей сказала».
- A2 → A3 (две её озвученные реплики) → A4: 13 вариантов. «Узнать о ней» и «Сомнение» —
  один раз (`ShowOnce`), возвращают к выбору; проверка Проницательности `Act1_Medium` (10).
- «Не сейчас» / «Нет» ставят `ALFSV_Recruitment_Postponed` / `…_Refused` (флаги на ней) и
  закрывают диалог; позвать можно снова, пока выполнено условие вербовки.
- A5: её вопрос «зачем ты это делаешь» → флаг мотива на герое (`ALFSV_HeroMotive_Duty /
  Modesty / Honesty / Profit`) → «придётся о тебе песню сложить» → Маттис → вступление:
  при полном отряде `GLO_CompanionSwap_Recruitment`, иначе `OriginAddToParty`.
- Искра ✨ — `ALFSV_Romance_Spark` на герое (тёплый ответ в A2, «Почему именно со мной?»,
  честный мотив).

### 2.4b Разговор в отряде (0.3.0)

Приветствия — её озвученные реплики из `DEN_Bard_InParty` по кругу (N5→N9, N18, N13);
холодная N17 — только при одобрении ниже 0. Варианты: «Пойдём со мной» (с меню замены
`GLO_CompanionSwap_Camp`), «Жди меня в лагере», «Уйти». Новые тексты — только два её
коротких ответа (черновик).

### 2.5 Темный Соблазн

- Завербованная Альфира никогда не становится жертвой. Наша ветка `QRY_ORI_DarkUrge_ReplaceAlfira`
  срабатывает при `DB_ALFSV_IsCompanion(1)`, и игра сама подставляет Квил (`S_DEN_Bard_Backup`).
  Альфиру также убираем из случайных спикеров этой ночи (`DB_ORI_DarkUrge_MurderOfAlfiraRandom`).
- **Патч GUSX-11941** (`BG3_Act3_SavegamePatches.txt:6060-6095`). При каждой загрузке
  (`BG3_SavegamePatchHelpers.txt:394-398`) он убивает Альфиру, если она в `DB_Players` и ночь
  убийства завершена. **Кто был жертвой, патч не проверяет**, то есть убил бы её и после ночи
  с Квил. Защита: `PROC_ApplySavegamePatches` вызывается внутри `DB_BG3_PatchingSavegame(1)`.
  Пока этот факт стоит, мы на время убираем `DB_CampNight_Completed(NIGHT_DarkUrge_MurderOfAlfira)`
  и сразу возвращаем его после снятия факта. Условия: она наша спутница, в отряде и
  не `DB_ORI_DarkUrge_AlfiraMurderVictim`. На вставку `DB_CampNight_Completed` этой ночи ни одно
  правило игры не реагирует. Во время патча эту базу читает только GUSX-11941.
- Если к ночи убийства Альфира ещё не завербована, жертва она. Тогда вербовка закрыта и
  работает ванильный сценарий. Сценарий «Квил в первую ночь, Альфира во вторую» из
  решений автора — работа этапа сценария.

### 2.6 Одобрение (0.3.0)

- `HasPlayerApprovalRating` — переопределение её глобального персонажа (у Хальсина и
  Минтары атрибут стоит в их персонажах). Точка конфликта с другими модами на Альфиру.
- Стартовое одобрение +20, если песня закончена и лютню не крали — при первой вербовке
  (`PROC_ALFSV_MakeCompanion`, по образцу Джахейры), один раз на аватара.
- Реакции в диалоге вербовки: A2 +1/+1/+1/0/0; A4: «Пойдём» +2, бард +3, тифлинг +2,
  «Попроси» +1, «Почему со мной» +2, Лихейла +1, «Там опасно» +1, Проницательность (успех) +2,
  «Лишний рот» −1, «Нет» −1; мотив: долг +1, честность +2.

## 3. Как проверить в игре

### 3.0. Режим проверки

Отдельного профиля в BG3 не создать: меню профилей Larian убрали. Второе
прохождение внутри сохранения тоже не сделать: имя героя хранится в двоичных
данных `Globals.lsf`, и править их вслепую опасно. Поэтому проверка идёт в
основном профиле, но **обратимо** — `scripts/test_mode.py`:

1. Закрыть игру и BG3 Mod Manager.
2. `python scripts/build_pak.py` и `python scripts/test_mode.py on`:
   - копия списка модов (modsettings + два файла менеджера);
   - **копия всех сохранений** (~2,8 ГБ);
   - выключает Alfira Joins The Party, его перевод и патч Redux;
   - ставит наш мод.
3. Игра через `bg3_dx11.exe` → загрузить **Леший AutoSave_51 (26.09, 14:40)**:
   акт 1, Альфира ещё не в отряде, Alfira Joins The Party поставлен позже.
   Более поздние сохранения «Лешего» без него не загрузятся — их не открывать.
4. Проверить (§3.1 и далее), закрыть игру.
5. `python scripts/test_mode.py off`: список модов возвращается побайтно, сохранения
   за время проверки переносятся в папку копии, удалённые игрой автосохранения
   возвращаются из копии.

Копии лежат в `%LOCALAPPDATA%/Larian Studios/Baldur's Gate 3/ALFSV_test/<время>/`.

## 4. Компилируются ли goals мода и выполняется ли INITSECTION на старом сейве

- **Компиляция.** Игра поставляет свои goals текстом (`Mods/*/Story/RawFiles/Goals/*.txt`) рядом
  с готовым `story.div.osi`, а заголовка `story_header.div` в паках нет: игра собирает сюжет
  своим встроенным компилятором. Моды со сценариями Osiris без SE так и работают. Ошибка в
  goal мода может сорвать сборку сюжета, поэтому перед каждой сборкой запускаем
  `scripts/check_story.py`. Для текущего goal: 0 ошибок, 0 предупреждений.
- **Старый сейв.** В сохранении лежит скомпилированный сюжет. Если версия мода выше той, что
  записана в сохранении (или мода там не было), Osiris выполняет **story patching**
  (Larian, «Modding: Versioning», раздел Story/Osiris): факты баз сохраняются, правила
  заменяются новыми, новые **goals верхнего уровня** (или с завершённым родителем)
  инициализируются, их INITSECTION выполняется. `ALFSV_Companion` — goal верхнего уровня.
  INIT у него пустой, вся логика в KB и срабатывает на события.
- **Правило для нас:** любое изменение Osiris — с повышением версии мода в `config/tools.json`.
  Иначе на уже начатом сохранении останутся старые правила. Поэтому версия сейчас 0.3.0
  (0.0.1 — пустой мод, 0.2.0 — заглушки, 0.3.0 — стартовое одобрение в goal).
- **[проверить в игре]** что BG3 делает story patching так же, как DOS2 (документ Larian —
  про Divinity Engine); проверяется шагом 1.

## 5. Известные пробелы и риски

1. ~~**Диалог без таймлайна** (§2.3).~~ В 0.3.0 у диалогов есть таймлайн и сцена. Риски
   постановки — [STAGING.md §6](STAGING.md#6-известные-ограничения).
2. **Путь гоблинов после вербовки.** `PROC_DEN_AttackOnDen_KillKids` безусловно вызывает
   `Die(S_DEN_Bard)`. Если игрок завербовал её, а потом пошёл с рейдерами на Рощу, она умрёт
   и в отряде. Отменить PROC нельзя. Решение за сценарием (например, она уходит при переходе
   на сторону гоблинов).
3. Пока условие вербовки выполнено, диалог вербовки заменяет её ванильный диалог после песни.
4. Точек в лагере нет для `CREMAIN`, `CREINSIDE`, `INTMAIN`, `FARM`, `SLUMS`, `ELFSONG`. Там она
   встанет у входа в лагерь (`QRY_Camp_GetCamperPos` → вход).
5. Иссохший не воскрешает её, если она умерла **вне отряда**. Для этого нужны флаги
   `DB_GLO_Jergal_CompanionResurrectionFlags` и опция в `CAMP_Jergal`, то есть переопределение
   чужого диалога (точка конфликта).
6. Одобрение (0.3.0) держится на переопределении её глобального персонажа. Работает ли оно
   на сохранении, где она уже загружена без атрибута, — проверить (возможно, нужна новая
   игра). Диалогов предупреждения/ухода при низком одобрении нет — это этап 4.
7. Побочные ветки `DB_Origins`: её могут выбрать случайным спикером в CFM, inclusion-узлах и
   «признании Дейзи», где у неё нет реплик. `PROC_LOW_BhaalTemple_KillVictim` для `DB_Origins`
   ведёт к `CompanionLeavePermanently` (жертвы Орин выбираются из фиксированного списка,
   Альфиры в нём нет). Эпилог считает её «частью команды».
8. Акты 2–3: её сцены («Последний свет», осада, дебриф, крыша «Эльфийской песни», письма
   эпилога) для завербованной Альфиры выключены или не имеют смысла. Замена — отдельный этап.
   Если её не завербовали, всё идёт как в игре.
9. Сидит ли она после вербовки на камне барда (`Use(S_DEN_Bard, S_DEN_BardSeat)` в INIT
   `Act1_DEN_TieflingBard`) — неизвестно.
10. Удаление мода посреди прохождения: в сохранении остаются `DB_Players(Alfira)` и наши факты.
    Процедуры «отпустить навсегда» перед удалением пока нет.
11. Несовместим с Alfira Joins The Party: оба мода делают её спутницей. С Alfira Redone —
    оба переопределяют её глобального персонажа: чей мод ниже в порядке загрузки, того и
    персонаж (у нас — одобрение, у Redone — внешность).
12. Одобрение из диалога вербовки начисляется до вступления в отряд. Засчитывает ли игра
    реакции спутнику не из отряда — проверить по всплывающим сообщениям.

## 6. [проверить в игре]

- [ ] goal добавляется к старому сейву (story patching), игра грузится без ошибок сюжета;
- [ ] диалоги с таймлайном открываются: камера, эмоции, взгляды, её голос в озвученных репликах;
- [ ] текстовые реплики держатся достаточно долго и не «застревают»;
- [ ] женские формы (`…_ru_to_F.xml`) у героини, мужские у героя;
- [ ] одобрение: всплывающие реакции, стартовые +20, она в листе отношений;
- [ ] класс Бард (Коллегия знаний) и уровень отряда после `RequestInitialLevel`;
- [ ] повышение уровня и респек у Иссохшего;
- [ ] «Жди в лагере» / возврат, место в лагере WLDMAIN;
- [ ] обмен при полном отряде в обе стороны (её реплики во вложенном диалоге могут быть пустыми);
- [ ] смерть в отряде → воскрешение у Иссохшего;
- [ ] конфиг Anubis `DefaultCharacter` в лагере (стоит на месте, не уходит в Рощу);
- [ ] фракция `Companion14` в отряде, `ACT1_DEN_TieflingBard` в лагере, нет враждебности тифлингов;
- [ ] праздник тифлингов с дублёром;
- [ ] Темный Соблазн: Квил вместо неё, после загрузки Альфира жива;
- [ ] срабатывают ли правила-охранники на факты из INIT актовых goals (акт 2);
- [ ] отладка из консоли SE: `Osi.PROC_ALFSV_Debug_Recruit()`.

## 7. Поправки к разбору и архитектуре

- `Companion15` занята Джахейрой. Свободны `Companion13` и `Companion14`
  (vanilla-companions.md §2.2, §7.2 предлагали 15).
- Класс Альфиры назначать не нужно: Origin «Alfira» есть в `Origins.lsx` (ARCHITECTURE.md,
  «Что проверить», п. 3).
- В ARCHITECTURE.md (таблица «Точки конфликта») стоит внести: ответ на GUSX-11941 (§2.5),
  праздник тифлингов (дублёр), `PROC_DEN_AttackOnDen_KillKids` (§5, п. 2).
