# Этап 2. Вербовка: что сделано и как проверить

Статус: **собрано, в игре не проверено.** Этап закрывается только после
проверки по списку ниже (CLAUDE.md §2).

Альфира (`S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c`) становится
«поздней спутницей» по схеме Хальсина и Минтары (см. [ARCHITECTURE.md](ARCHITECTURE.md)).
Мод работает сам, без Script Extender. SE нужен только как отладочная консоль.
Все реплики — заглушки с пометкой `[PH]`, финальные тексты пишутся отдельно.

## 1. Файлы

| Файл | Что это |
|------|---------|
| `mod/Mods/_MOD_/Story/RawFiles/Goals/ALFSV_Companion.txt` | Сценарий Osiris: вербовка, защита от сюжетных скриптов, отладка |
| `mod/Mods/_MOD_/Story/DialogsBinary/Companions/ALFSV_Alfira_Recruitment.lsx` | Диалог вербовки (в пак идёт как `.lsf`) |
| `mod/Mods/_MOD_/Story/DialogsBinary/Companions/ALFSV_Alfira_InParty.lsx` | Диалог в отряде и в лагере |
| `mod/Public/_MOD_/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsx` | Банк диалогов: два ресурса и ссылки на вложенные диалоги обмена |
| `mod/Mods/_MOD_/Localization/English/AlfiraSecondVerse_en.xml`, `…/Russian/AlfiraSecondVerse_ru.xml` | Тексты-заглушки |
| `scripts/build_pak.py` | Подстановка `_MOD_` внутри ресурсов, `.lsj`→`DialogsBinary/.lsf`, проверка текстов диалогов, проверка списка файлов пака |
| `scripts/check_story.py`, `scripts/osiheader/` | Проверка goals мода компилятором LSLib вместе с ванильными |
| `config/tools.json` | Версия мода 0.2.0 (см. §4) |

Идентификаторы ресурсов (на них ссылается Osiris, в сохранениях они остаются —
**не менять**):

| Ресурс | ID в банке диалогов |
|--------|---------------------|
| `ALFSV_Alfira_Recruitment` | `009896a5-580c-4135-98db-99234865b61d` |
| `ALFSV_Alfira_InParty` | `b2950129-fdd2-4cda-8182-cf41cfd5d809` |

Пак 0.2.0 (7 файлов):

```
Mods/AlfiraSecondVerse_<uuid>/Localization/English/AlfiraSecondVerse_en.xml
Mods/AlfiraSecondVerse_<uuid>/Localization/Russian/AlfiraSecondVerse_ru.xml
Mods/AlfiraSecondVerse_<uuid>/meta.lsx
Mods/AlfiraSecondVerse_<uuid>/Story/DialogsBinary/Companions/ALFSV_Alfira_InParty.lsf
Mods/AlfiraSecondVerse_<uuid>/Story/DialogsBinary/Companions/ALFSV_Alfira_Recruitment.lsf
Mods/AlfiraSecondVerse_<uuid>/Story/RawFiles/Goals/ALFSV_Companion.txt
Public/AlfiraSecondVerse_<uuid>/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsf
```

## 2. Как устроено

### 2.1 Вербовка

В игре, где Альфиру не завербовали, мод ничего не меняет. Все факты о ней как о
спутнице ставит `PROC_ALFSV_MakeCompanion()` в момент первой вербовки, то есть
когда на неё ставится флаг `OriginAddToParty` или `GLO_ORI_Event_InvitedToCamp_Walk`:

- `DB_ALFSV_IsCompanion(1)` — наш признак «она спутница»;
- `DB_CompanionOnlyFaction(Alfira, Companion14)` и `DB_OriginNPCAlignment(Alfira, ACT1_DEN_TieflingBard)`;
- `DB_OriginInPartyDialog(Alfira, ALFSV_Alfira_InParty)`;
- ванильные флаги из заготовки Тёмного Соблазна: `DB_OriginPartOfTheTeamFlag(…, ORI_Alfira_ControlledByUser)`
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
`RaidersAtDen`, `RaidersInDen`, `RaiderVictory`), она мертва, она — жертва ночи Тёмного Соблазна,
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

### 2.5 Тёмный Соблазн

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

## 3. Как проверить в игре

Подготовка (игра и BG3 Mod Manager закрыты):

```
python scripts/check_story.py    # ошибок в goal мода быть не должно
python scripts/build_pak.py      # 7 файлов, версия 0.2.0
python scripts/install.py
```

Запуск — `bg3_dx11.exe`. Отладочная вербовка без условий — из консоли Script Extender
(контекст сервера): `Osi.PROC_ALFSV_Debug_Recruit()`. Альфира телепортируется к хосту и входит
в отряд, а при полном отряде уходит в лагерь. То же делает `TextEvent("alfsv_recruit")`, но в
обычной игре этот текст ввести негде. Полезные проверки в консоли SE:
`Osi.DB_ALFSV_IsCompanion:Get(nil)`, `Osi.DB_Players:Get(nil)`, `Osi.DB_PartOfTheTeam:Get(nil)`.

Шаги:

1. **Загрузка.** Возьмите сейв, сделанный до установки мода (акт 1, тифлинги ещё в Роще).
   Игра загружается, в журнале нет ошибок сюжета. Вербовка (шаг 2) работает — значит, goal
   добавился к сохранению (§4).
2. **Вербовка.** Штатно: закончить песню с Альфирой, затем щёлкнуть по ней аватаром →
   «[PH] Lihala's song is finished…» → «[PH] Come with me.» Или отладкой.
   Проверить: портрет в отряде, управление, **класс Бард (Коллегия знаний)** в листе
   персонажа, **уровень = уровню отряда**.
3. **Разговор в отряде.** Щёлкнуть по ней → «[PH] Need something?», варианты «Жди меня в
   лагере» и «Уйти».
4. **Лагерь.** «[PH] Wait for me at camp.» → уходит. В лагере стоит на своём месте
   (`S_ORI_DarkUrge_AlfiraPosition_*` для WLDMAIN), с ней можно поговорить → «[PH] Come with me.» → снова в отряде.
5. **Полный отряд.** С четырьмя в отряде позвать её из лагеря → вложенный ванильный диалог
   обмена → выбрать, кого отправить. Обратно: позвать другого спутника → вариант «Ты можешь
   занять место Альфиры». Отдельно: вербовка из Рощи при полном отряде → «Встретимся в лагере» → она в лагере.
6. **Повышение уровня** на следующем уровне отряда: доступно, выбор как у барда.
7. **Смерть и Иссохший.** Дать ей умереть в отряде → Иссохший в лагере предлагает воскресить
   (слот игрока) и отпустить мёртвую из отряда.
8. **Сохранение и загрузка** в отряде и в лагере: состояние сохраняется, диалог наш.
9. **Праздник тифлингов** (если успели завербовать до него): вместо Альфиры играет
   дублёр, сама она после ночи на месте и в отряде.
10. **Тёмный Соблазн** (отдельное прохождение): завербовать до ночи убийства → ночью приходит
    Квил → утром Альфира жива → сохранить, загрузить — жива.

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
  Иначе на уже начатом сохранении останутся старые правила. Поэтому версия сейчас 0.2.0
  (0.0.1 был пустой мод).
- **[проверить в игре]** что BG3 делает story patching так же, как DOS2 (документ Larian —
  про Divinity Engine); проверяется шагом 1.

## 5. Известные пробелы и риски

1. **Диалог без таймлайна** (§2.3). Если по клику ничего не открывается, открывается пустое
   окно или игра падает: сначала попробовать `EnableTimeline=False` в банке, затем делать
   таймлайн.
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
6. Одобрения нет. В данных персонажа нет `HasPlayerApprovalRating` (у Хальсина и Минтары есть),
   стартового бонуса и диалогов предупреждения/ухода тоже нет. Это этап 4.
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
11. Несовместим с Alfira Joins The Party: оба мода делают её спутницей.

## 6. [проверить в игре]

- [ ] goal добавляется к старому сейву (story patching), игра грузится без ошибок сюжета;
- [ ] диалоги без таймлайна открываются и показывают варианты ответа;
- [ ] класс Бард (Коллегия знаний) и уровень отряда после `RequestInitialLevel`;
- [ ] повышение уровня и респек у Иссохшего;
- [ ] «Жди в лагере» / возврат, место в лагере WLDMAIN;
- [ ] обмен при полном отряде в обе стороны (её реплики во вложенном диалоге могут быть пустыми);
- [ ] смерть в отряде → воскрешение у Иссохшего;
- [ ] конфиг Anubis `DefaultCharacter` в лагере (стоит на месте, не уходит в Рощу);
- [ ] фракция `Companion14` в отряде, `ACT1_DEN_TieflingBard` в лагере, нет враждебности тифлингов;
- [ ] праздник тифлингов с дублёром;
- [ ] Тёмный Соблазн: Квил вместо неё, после загрузки Альфира жива;
- [ ] срабатывают ли правила-охранники на факты из INIT актовых goals (акт 2);
- [ ] отладка из консоли SE: `Osi.PROC_ALFSV_Debug_Recruit()`.

## 7. Поправки к разбору и архитектуре

- `Companion15` занята Джахейрой. Свободны `Companion13` и `Companion14`
  (vanilla-companions.md §2.2, §7.2 предлагали 15).
- Класс Альфиры назначать не нужно: Origin «Alfira» есть в `Origins.lsx` (ARCHITECTURE.md,
  «Что проверить», п. 3).
- В ARCHITECTURE.md (таблица «Точки конфликта») стоит внести: ответ на GUSX-11941 (§2.5),
  праздник тифлингов (дублёр), `PROC_DEN_AttackOnDen_KillKids` (§5, п. 2).
