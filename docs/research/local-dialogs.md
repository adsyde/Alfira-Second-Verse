# Локальные диалоги спутников вне лагеря: как это сделано у Larian и что взять для Альфиры

Patch 8 Hotfix 9. Всё ниже проверено по распакованным данным. Непроверенное помечено **[проверить]**,
предположения — **[догадка]**. Пути к goals:

| Метка | Путь |
|---|---|
| `[G]` | `game-data/Gustav/Mods/Gustav/Story/RawFiles/Goals/` |
| `[GD]` | `game-data/Gustav/Mods/GustavDev/Story/RawFiles/Goals/` |
| `[H]` | `game-data/Patch8_HotFix9/Mods/Shared/Story/RawFiles/Goals/` (хотфикс перекрывает Shared) |
| `[S]` | `game-data/Shared/Mods/Shared/Story/RawFiles/Goals/` |

Что распаковал сверх проекта (только в scratchpad, в репозиторий не клал): банки диалогов
`Public/*/Content/Assets/Dialogs/**/_merged.lsf`, банки голосовых реплик
`Public/Gustav/Content/Assets/Voicebarks/**/_merged.lsf` и сами ресурсы `Mods/Gustav/Story/VoiceBarks/**/*.lsj`
(644 файла). Без них не видно, как `StartVoiceBark` выбирает говорящего. Совет: добавить в
`config/tools.json` набор `voicebarks` (`*Story/VoiceBarks/*`) и банки `*Content/*Dialogs*/_merged.lsf`.

---

## 0. Коротко

Вне лагеря у Larian **четыре** механизма «спутник сам реагирует на местное событие», а не один:

| # | Механизм | Как выглядит в игре | Вызов Osiris | Длина |
|---|---|---|---|---|
| A | **«!» над головой** (World Relationship Dialog, WRD) | Над спутником загорается восклицательный знак. Герой кликает, начинается разговор. Если отойти дальше 30 м, знак гаснет | `PROC_RelationshipDialog(спутник, диалог, флаг, якорь[, только_партнёр, мин_одобрение])` | 10–110 узлов, всегда с выбором героя |
| B | **Автостарт короткой сцены** (Party Origin Moment, POM; прямой `QRY_StartDialog_Fixed`) | Сцена начинается сама: спутник заговаривает с героем | `PROC_StartPartyOriginMoment(спутник, ACM, AOM, COM, OOM)` или `QRY_StartDialog_Fixed(диалог, спутник, аватар)` | 20–110 узлов |
| C | **Перехват диалога NPC** (Origin Moment, OM) | Герой заговаривает с NPC, а вместо обычного диалога идёт сцена «NPC + спутник + герой». Потом NPC-диалог перезапускается | `PROC_DefineSingleOriginMoment(диалог_NPC, ТЕГ, AOM, COM, OOM)` | 20–330 узлов, выбор и одобрение |
| D | **Реплика над головой** (PAD/VB/AD) | Одна строка текстом и голосом, без выбора | `StartVoiceBark(VB, игрок)`, `PROC_TryStartAD(AD, спутник)`, `DB_OneShot_VoiceBarkTrigger`, `DB_ItemDialog_PlayerVB` | 1–13 узлов, без выбора |

Плюс «тематическое приветствие» (Topical Greeting): после события у всех спутников в отряде стоит
флаг темы, и при клике спутник начинает разговор с реплики о событии. Знака нет.

---

## 1. Главный вопрос: восклицательный знак вне лагеря

Всё в одной общей цели `[H] _GLOBAL_Shared_RelationshipDialogs.txt`. Она общая для **всех** спутников,
своих процедур у ориджинов нет.

### 1.1 Постановка

1. Сценарий спутника вызывает
   `PROC_RelationshipDialog(_Companion, _Dialog, _Flag, _Anchor, _PartnerDateOnly, _MinApproval)` (:99–121;
   укороченные формы :89–97 подставляют `NULL`-флаг, `0`, `-100`).
   Условия: спутник не аватар (`NOT DB_Avatars`), не повержен, этот `(_Dialog,_Flag)` ещё не завершён
   (`DB_RelationshipDialogsFinished`), спутник ближе 30 м к `_Anchor` (:113–115), есть аватар
   с одобрением ≥ `_MinApproval` (`QRY_IsValidAvatarAvailableForRelationshipDialog`, :147–184).
   Результат — очередь `DB_RelationshipDialog_Queue(..., "WORLD", ...)` и таймер 1,5 с (:186–197).
2. `PROC_Test_RelationshipDialog_Queue()` (:332–349) показывает знак, если спутник свободен:
   нет другого текущего RD, `NOT DB_CantTalk`, **`NOT DB_InCamp`** (:342), разрешено подавлением
   партийных диалогов. Тогда `PROC_ExclamationMark_Show(_Companion)` и запись
   `DB_HandlingRelationshipDialog`.
3. Сам знак (:787–806): петля VFX `VFX_UI_ExclamationMark_01_a3018cf0-3a25-06ee-206a-3dd079332d80`
   на кости `Dummy_OverheadFX` с идентификатором `"RelationshipMarker"` и тег
   `HAS_EXCLAMATION_DIALOG_e45ea222-a86f-4e00-a1ca-98d8b258b1ce`. В бою VFX глушится
   (`DB_LoopEffectDisabledInCombat`, INIT :6).
4. Если передан флаг, он ставится **на спутника** (`SetFlag(_Flag,_Companion,0)`, :71–76) и снимается,
   когда RD закончился или отменён (:78–84).

### 1.2 Клик и связь с диалогом

`[S] __GLOBAL_Dialogs.txt:2128–2156`, порядок выбора диалога при клике:
`QRY_SelectCrimeBusyDialog` → `QRY_SelectCustomDialog` → `QRY_SelectADForRequest` →
`QRY_SelectReflectionDialog` → `QRY_SelectCompanionFallback` → **`QRY_SelectRelationShipDialog`** →
`QRY_SelectCustomDialog_AfterGenerics` → `DB_Dialogs` (обычный InParty) → default.

`QRY_SelectRelationShipDialog` (`[H] …RelationshipDialogs.txt:19–30`) берёт `DB_HandlingRelationshipDialog`
и выдаёт `DB_SelectedDialog(_Dialog, спутник, герой)`. Одобрение ниже порога → вместо него
`GLO_PAD_NotEnoughApprovalForCRD` (:42–52); «только для партнёра» без романа →
`GLO_AD_NonBondedCompanionDialog` (:32–40).

Два варианта `_Dialog`:
- **Отдельный WRD-диалог** (свой ресурс): `DEN_HarpyMeal_WRD_Gale`, `PLA_PaladinsOfTyr_WRD_Karlach`,
  `CRE_Laezel_WRD_PostZaithisk`. В банках 32 ресурса `*_WRD_*`, из них по акту 1 — 11.
- **InParty-диалог + флаг темы (IPRD)**: `_Dialog = Karlach_InParty`, `_Flag = ORI_Karlach_IPRD_…`. В
  InParty есть корневой `TagGreeting` с проверкой этого флага `[Object]` на спутнике. Пример:
  `Karlach_InParty` N2015 проверяет `ORI_Karlach_IPRD_GoblinPriestOutcome`, `Laezel_InParty2`
  N2667/N2784/N6837 — `ORI_Laezel_IPRD_CrecheMarkings`.

### 1.3 Снятие

- `DialogStarted` этого диалога → знак скрыт (:272–276); `DialogEnded` → `DB_RelationshipDialogsFinished`,
  повторно не встанет (:278–284).
- Ушли: при постановке запоминается позиция спутника, каждые 3 с проверка; дальше 30 м от неё или
  телепорт → `PROC_CancelRelationshipDialog` (:396–467). Исключение — `DB_ExclamationDialog_NeverStop(диалог, флаг)`:
  такие при входе в лагерь возвращаются в очередь и загорятся снова (:622–643).
- Смерть спутника → в очередь (:852–858); подавление партийных диалогов → отмена (:603–613).
- Одобрение упало ниже порога → отмена (:199–225).

### 1.4 Отличие от лагерного «нам нужно поговорить»

Знак тот же (`RelationshipMarker`), очередь другая:
- **Лагерь (CRD):** `PROC_CampRelationshipDialog(...)` или `DB_CampNight_CRD(ночь, спутник, диалог, флаг)`
  ставят очередь `"CAMP"` только при `DB_InCamp` (:688–700). Знак показывает `PROC_Try_CampRelationshipDialog`
  (:725–733, `QRY_ValidForCRD`), либо ночная система (:371–387). При уходе из лагеря и на отдыхе
  RD снимается (:645–668).
- **Мир или лагерь днём:** `DB_RelationshipDialog_WRD_TriggerInCamp(диалог, флаг)` → категория
  `"WORLDORCAMP"` (:123–145): знак может загореться и в лагере, но не ночью (:352–369).
  Пример — `ORI_Resurrected_WRD_Gale` (`[G] Act1_ORI_Gale.txt:35`).
- **Обязательный разговор перед сном:** `DB_Camp_RequiredTalks(персонаж[, диалог])` →
  `PROC_ExclamationMark_Show(_, "GLO_Camp_RequiredTalk")` (`[H] GLO_Camp.txt:1341–1349`). Это отдельный
  идентификатор знака, к RD не относится.
- **Автостарт вместо знака:** `DB_RelationshipDialog_Autostart(диалог, флаг)` — диалог стартует сам,
  как только спутник видит аватара (`DB_Sees`, :486–512). `…_AutostartTryOnce` — одна попытка, потом
  обычный знак (INIT :8–11, :473–484).

### 1.5 Разобранные примеры

**Пример 1. Гейл: спасли ребёнка от гарпий → «!» → отдельный WRD.** `[G] Act1_ORI_Gale.txt`
- :19–23 — таблица «добрых дел»: `DB_ORI_Gale_TrustMoments(флаг_события, WRD, флаг_одобрения)`, например
  `DEN_HarpyMeal_State_RescuedChild_7a90f576-f762-4710-aa4d-9a81905bd971` → `DEN_HarpyMeal_WRD_Gale_d6eb7a2e-…`.
- :301–308 — `FlagSet(_Flag,_,_ID)` внутри **чужого** диалога (с Мирконом) запоминает `(ID диалога, WRD)`.
- :333–356 — одобрение +8, если Гейл был в том диалоге, иначе +6 после его конца (`ChangeApprovalRating`).
- :358–374 — `DialogEnded(_, _ID)`, Гейл в отряде и не аватар → `PROC_RelationshipDialog(Gale, _WRD, _Player)`.
- Диалог: 37 узлов, 12 выборов героя. Гейл вспоминает детство, Тару, мефита; одобрение в самом
  диалоге не меняется. Так же устроены ещё три WRD Гейла в Роще: Арабелла, Нетти, гоблинша Сазза (:20–22).

**Пример 2. Карлах: жрица Гут повержена → «!» на InParty с флагом темы.** `[GD] Act1_OriginMoments_Karlach.txt`
- :548–565 — `DialogEnded(GOB_GoblinPriest_Chapel)` + флаг `ORI_Karlach_Event_SetUpGoblinPriestBranch`
  из того диалога → `DB_ORI_Karlach_CheckWithPlayerOnSight(герой)`.
- :572–591 — когда Карлах видит героя (`DB_Sees`) и стоит `GOB_GoblinPriest_State_Defeated`, если не в бою →
  `PROC_RelationshipDialog(Karlach, Karlach_InParty, ORI_Karlach_IPRD_GoblinPriestOutcome, Karlach)`.
- В `Karlach_InParty` корень N2015 проверяет этот флаг. Отдельного файла нет.

**Пример 3. Лаэ'зель у гитских знаков: автостарт → запасная реплика → «!».** `[GD] Act1b_OriginMoments_Laezel.txt`
- :8 — `TriggerRegisterForCharacter(S_CRE_GithMarkingsArea_c80368e0-…, Laezel)`; :83–95 —
  `DB_InRegion(Laezel, эта зона)`, не аватар, `QRY_OnlyOnce`.
- :113–129 — сначала флаг темы на неё и попытка сразу начать `Laezel_InParty2` с лучшим аватаром
  (`QRY_StartDialog_Fixed`), разговор стартует сам.
- :131–140 — не вышло (аватар далеко или занят): флаг снят, реплика над головой
  `ORI_Laezel_AD_CrecheMarkings` («Wait.») и `PROC_RelationshipDialog(..., Laezel_InParty2, ORI_Laezel_IPRD_CrecheMarkings, ...)`: «!».

**Пример 4 (для сравнения, без знака). Шэдоухарт читает дневник в Вымершей деревне → автостарт POM.**
`[GD] Act1_OriginMoments_Shadowheart_PostEA.txt:139–149` — `AddedTo(дневник, игрок)` → `StartVoiceBark`;
:151–160 — `GameBookInterfaceClosed(дневник)` + `DB_InRegion(S_FOR_VillageArea)` → `PROC_StartPartyOriginMoment`
(4 версии сцены — ACM/AOM/COM/OOM, `[H] _GLO_Shared_PartyOriginMoments.txt:8–13`);
:162–168 — то же при `EnteredTrigger(Шэдоухарт, S_FOR_ShadowheartOM_FindStatue)`.

### 1.6 Сколько «!» в акте 1

Вызовов `PROC_RelationshipDialog` в целях акта 1 мало, примерно 20:
- Гейл — 4 WRD в Роще и WRD после воскрешения.
- Лаэ'зель — 6: знаки Яслей (IPRD), Влаакит (IPRD), Зайт'иск, уничтожение Яслей, Восс на перевале, WRD о Яслях после тифлинга.
- Карлах — 6: паладины (WRD), ярость, Гут, набег на Рощу, напоминание о паладинах (IPRD).
- Шэдоухарт — 3 IPRD после снов.
- Минтара — 2 IPRD о личинке.
- Уилл — 4 вызова в `[G] Act1_OriginMoments_Wyll.txt` (`GOB_PostTorturer_WRD_Wyll` и др.). Ресурсов с такими
  именами **нет** ни в одном банке: это мёртвый код раннего доступа.

Основной объём реакций — реплики над головой (D) и перехваты диалогов NPC (C), см. §4.

---

## 2. Остальные механизмы

### 2.1 Реплики над головой (PAD/VB)

- `StartVoiceBark(VB, игрок)` — **VB-ресурс** (`Story/VoiceBarks/*.lsj`) — это список
  `VoiceBarkData{DialogResourceId, Tags[Allow/Deny по слотам]}`. Движок сам выбирает, кто из отряда
  скажет и какой PAD-диалог сыграть. Внутри PAD у одного узла несколько `TagText` с правилами по тегам
  `REALLY_ASTARION`, `REALLY_GALE` и т. д. и строка без правила. Пример: `UND_CavePainting_PAD` — шесть
  строк по ориджинам и одна общая.
- Ключ в Osiris — **имя VB**, файл диалога часто переименован: Osiris зовёт `DEN_General_VB_ShadowheartBook`
  (`e3b43370…`), VB-ресурс ссылается на диалог `DEN_General_PAD_ShadowheartBook`. Из 213 PAD без
  прямой ссылки 157 находятся по имени `_VB_`/`_AD_`.
- Обёртки: `DB_OneShot_VoiceBarkTrigger(триггер, VB[, режим])` — один раз при входе в триггер
  (`[S] _GLO_OneshotDialogs.txt:115–192`, триггер снимается после срабатывания).
  `DB_ItemDialog_PlayerVB(предмет, VB)` — по `UseStarted` (`[S] _GLOBAL_ItemEvents.txt:780–829`).
  `DB_KnowledgeCheckTrigger_AD/Item_AD` — после скрытой проверки.
  `PROC_TryStartAD(AD, спутник)` — конкретному спутнику.
- Типичные события-поводы (из 322 PAD акта 1): `UseStarted` 26, `GameBookInterfaceClosed` 9,
  `AddedTo` 10, `EnteredTrigger`/`DB_InRegion` 25, `DialogEnded`/`AutomatedDialogEnded`/`PROC_FlagReactionAfterDialog` 39,
  `FlagSet` 11, `ObjectTimerFinished` 17, проверки знаний и восприятия 15, `CombatEnded`/`TurnStarted`/`AttackedBy`.

### 2.2 Реакция на флаг из чужого диалога

`DB_FlagReactionAfterDialog(флаг, диалог)` / `DB_GlobalFlagReactionAfterDialog(флаг, диалог)` → после
`DialogEnded` вызывается `PROC_FlagReactionAfterDialog(объект, флаг)` / `PROC_GlobalFlagReactionAfterDialog(...)`
(`[S] _Greevers_Little_Helpers.txt:2600–2700`). Это **PROC**: мод может добавить своё тело правила с тем же
флагом, ничего не переопределяя. Пример — Карлах и каша Окты:
`[GD] Act1_OriginMoments_Karlach.txt:603–613` → `DEN_RefugeeChef_PAD_KarlachReactsToFood`.

### 2.3 Тематические приветствия

`[S] GLO_TopicalGreetings.txt:16–80`: флаг темы из `DB_TopicalGreeting(флаг)` ставится всем из
`DB_OriginPartOfTheTeamFlag`, кто в `DB_PartOfTheTeam` и не аватар. Живёт одна тема, срок жизни задают
`…EndCondition_LongRest/LeaveCamp/LeaveTrigger/FlagSet`. Темы — `[GD] GLO_TopicalGreetings_Gustav.txt`;
в акте 1 их всего несколько: `TG_GOB_GoblinCamp_Entered` (:15–17), `TG_UND_Underdark_Entered` (:20–22),
`TG_UND_NereIsTrapped` (:25–28), `TG_PLA_GithChokepoint_EncounteredGith` (:11–12), `TG_CRE_*` (:43–83),
`TG_GLO_FirstUseTadpole` (:4).

---

## 3. Интерджекции: реплика спутника в чужом диалоге

### 3.1 Как у Larian

Спутник вписан в `speakerlist` диалога NPC отдельным слотом. Например, `DEN_TieflingLeader` (Зевлор):
слоты 2–7 — Лаэ'зель, Шэдоухарт, Карлах, Астарион, Уилл, Гейл. Реплика — узел с этим спикером **без
проверки флагов**, стоящий в цепочке «пустых» узлов слота игрока (`e0d1ff71…`, группа спикеров). Пример:
N8795 → [N8799 Карлах «I knew I liked you.» | N8722 пустой → N8775 Лаэ'зель]. Движок берёт первого ребёнка,
чей спикер есть в диалоге, иначе идёт дальше по пустому узлу. Спутника в диалог добавляет движок, если
он в отряде и рядом (`[H] GLO_InclusionNodes.txt:14–75`, `DB_Inclusion_SpeakerCandidate`).

### 3.2 Что можно без переопределения чужих файлов

1. **Перехват OM на диалог NPC**: `PROC_DefineSingleOriginMoment(диалог_NPC, (TAG)ALFIRA_c93d7c45-ff8f-4565-b4de-5b5eb48207bb, AOM, COM, OOM)`.
   Это строка в нашем goal. Когда кто-то начинает диалог NPC, `QRY_StartOverrideDialog` → `QRY_PlayOriginMoment`
   (`[S] __GLOBAL_Dialogs.txt:1905–1916`) ищет спутника с тегом в `DB_Players`, не аватара, в радиусе
   (`[H] _GLO_Shared_OriginMoments.txt:255–282`, `QRY_IsTaggedForOM` :950–967). Находит — играет наш диалог
   «NPC + Альфира + герой» (:592–607), потом перезапускает обычный диалог NPC (`OM_Relaunch_Dialog`, :788–812).
   Так Larian делают Лаэ'зель у стражника-тифлинга (`[G] Act1_OriginMoments_Laezel.txt:7`) и Уилла у
   Ашарака (`[GD] Act1_DEN_WyllRecruitment.txt:57`).
   Ограничения: реплика получается **перед** диалогом NPC, а не внутри него. На один запуск играет один OM (по
   приоритету): на Даммоне уже висит OM Карлах (`[GD] Act1_OriginMoments_Karlach.txt:64`), это конфликт
   приоритетов, а не файлов. Стоит ли тег `ALFIRA` на её персонаже — **[проверить]**. Если нет,
   `SetTag(S_DEN_Bard_…, ALFIRA_…)` в нашем goal (так ставит тег и сама игра, `[H] …RelationshipDialogs.txt:805`).
2. **После диалога** (`DialogEnded(диалог_NPC)` или `PROC_FlagReactionAfterDialog(_, флаг)`) — свой AD,
   свой WRD «!» или автостарт своей короткой сцены (как у Гейла и Карлах).
3. **Своя реплика над головой во время события**: `PROC_TryStartAD(ALFSV_AD, Альфира)` — так уже работает этап 5.
4. **Реплика в её InParty по флагу чужого события** (IPRD или тематическое приветствие) — только её ресурс.

### 3.3 Что требует переопределения (точки конфликта)

- **Реплика внутри чужого диалога** (узел Альфиры в `DEN_TieflingLeader` и т. п.) — только копией всего
  `.lsj` с тем же ресурсом в банке. Файл целиком заменяется. Конфликтует с любым модом, который правит
  этот диалог, и со следующими хотфиксами Larian.
- **Её строка в ванильной PAD** (чтобы на `StartVoiceBark` игры говорила она, а не Гейл) — правка и PAD-диалога
  (новый `TagText` с её тегом), и VB-ресурса. Тоже замена ресурса.
- **Риск [догадка, проверить в игре]:** в VB-ресурсах без тегов (`FOR_KidsGame_VB`, `HAG_Campsite_VB`,
  `DEN_TieflingLeader_VB_ZevlorsMap`: Allow/Deny пустые) движок может выбрать говорящей Альфиру, и она скажет
  общую строку без правила (для Тава). Проверить на месте с отрядом «Альфира + герой».

---

## 4. Статистика по акту 1

Считал диалоги с префиксами TUT/CRA/CHA/DEN/FOR/GOB/HAG/PLA/UND/CRE, а также ORI/GLO, которые запускают цели
акта 1. Лагерь не считал. Диалог засчитан спутнику, если он в нём спикер или у него есть строка по своему
тегу. Скрипт `scratchpad/stats4.py`.

| Спутник | PAD | VB | AD | OM (перехват/POM) | WRD-файлы | «!» всего (§1.6) |
|---|---|---|---|---|---|---|
| Шэдоухарт | 310 | 50 | 18 | 14 | 5 | 3 |
| Астарион | 300 | 39 | 12 | 11 | 4 | 0 |
| Гейл | 303 | 33 | 13 | 7 | 8 | 5 |
| Лаэ'зель | 302 | 43 | 39 | 15 | 6 | 6 |
| Уилл | 302 | 37 | 17 | 12 | 4 | 0 рабочих |
| Карлах | 307 | 33 | 12 | 10 | 5 | 6 |
| Хальсин | 16 | — | 3 | 3 | 3 | 0 |
| Минтара | 3 | 1 | 14 | 3 | 3 | 2 |
| Джахейра | 16 | — | 1 | 3 | 3 | 0 |
| Минск | 2 | 1 | — | 1 | 3 | 0 |

(PAD и VB общие, в каждом строки для всех шести ориджинов. WRD-файлы в колонке могут быть из поздних
актов, если их запускает общая GLO-цель.)

Размер по типам: PAD 322 файла, медиана 2 узла, выбора нет. AD 73, медиана 2. VB 57, медиана 2.
OM 28, медиана 82 узла, 25 из 28 с выбором, 14 с одобрением. WRD 11 (акт 1), медиана 37 узлов, все с выбором,
одобрение в 4 (у Гейла одобрение даёт Osiris). POM 1, 26 узлов.

**Жанр:** почти всё — одна строка «увидел, взял, прочёл». Сцены с выбором появляются только там, где событие
задевает личную историю спутника: 10–15 OM на ориджина и 3–6 «!» за акт.

### 4.1 Типичные поводы (35), из данных

| Повод (данные) | Кто | Тип | О чём |
|---|---|---|---|
| Карта Зевлора, `UseStarted` (`[G] Act1_DEN_TieflingRefugees.txt:190–204`) | все | VB | дорога беженцев к Вратам |
| Ритуал у Священного пруда, `DialogEnded` (`[G]` и хотфикс `Patch8_HotFix9/Mods/Gustav/…/Act1_DEN_SacredPond.txt:281`) | друид первым | VB | ритуал Шипов |
| Книга о храме Шар, `GameBookInterfaceClosed` (`[G] Act1_CHA_ShadowHeartRecruitment.txt:33–44`) | Шэдоухарт | VB | «Храм Шар? Где?» |
| Каша Окты, `PROC_FlagReactionAfterDialog` (`[GD] …Karlach.txt:603`) | Карлах | AD | «Что за каша!» |
| Спасли Миркона / Арабеллу / Сазза / Нетти (`[G] Act1_ORI_Gale.txt:20–23`) | Гейл | WRD «!» | доверие, детство |
| Тифлинг-стражник видел гита (`[G] Act1_OriginMoments_Laezel.txt:7`) | Лаэ'зель | OM | допрос, «поклонись» |
| Ашарак и дети с мечами (`[GD] Act1_DEN_WyllRecruitment.txt:57`) | Уилл-аватар | OM | история для детей |
| Даммон чувствует её двигатель (`[GD] …Karlach.txt:64`) | Карлах | OM | починка сердца |
| Лаэ'зель о хрупкости тифлингов, `EnteredTrigger` (`[G] …Laezel.txt:244`) | Лаэ'зель + ответ | VB-перепалка | «рыба на суше» |
| Разгромленная деревня: дневник, ожерелье, статуя (`[GD] …Shadowheart_PostEA.txt:121–168`) | Шэдоухарт | POM/VB | налёт шарран на Лунный Дол |
| Детская игра на полу (`[G] Act1_FOR_Misc.txt:7`) | все | VB | «мы в такое играли» |
| Вино в пустой книге (`[G] Act1_FOR_Boosters.txt:733–741`) | все | VB | находка |
| Некрономикон Тэя (`FOR_DangerousBook_*`) | Гейл, Астарион | VB | опасная книга |
| Святилище Селуны в пещере медвесыча (`[G] Act1_FOR_Boosters.txt:525`) | Шэдоухарт | POM | подношения Селуне |
| Кабан-тушка, `CharacterLootedCharacter` (`[G] Act1_Origin_Astarion.txt:234`) | Астарион | POM | «не трогай свинью» (голод) |
| Лагерь гоблинов, вход (`[G] Act1_GOB_GeneralFestivities.txt:202`) | все | VB | как тут выжить |
| Фреска, статуя, храм Селуны у гоблинов (`[G] Act1_GOB_Misc.txt:34–36`) | Шэдоухарт | VB, OM | храм врага её богини |
| Игрок бьёт в барабаны на посту (`[G] Act1_GOB_Checkpoint.txt:234–244`) | другой член отряда | VB | оценка «песни» |
| Боевая раскраска навозом варга, `StatusApplied` (`[G] Act1_GOB_Checkpoint.txt:212`) | 5 ориджинов | VB | брезгливость |
| Воло поёт гоблинам (`[G] Act1_GOB_VoloBallad.txt:145–152`) | все | VB | «кто это поёт?» |
| Убита Гут / Минтара (`[G] Act1_GOB_GoblinThrone_Misc.txt:84–85`) | все | PAD | итог |
| Гут повержена (`[GD] …Karlach.txt:548–591`) | Карлах | «!» IPRD | разговор о жрице |
| Охотник на гуров (`[G] Act1_Origin_Astarion.txt:23`) | Астарион | OM | за ним охотятся |
| Выдал / защитил Астариона (`[G] Act1_Origin_Astarion.txt:340–379`) | остальные | VB | осуждение или облегчение |
| Кровавый разорённый лагерь (`[G] Act1_HAG_Boosters.txt:14`) | все | VB | красные колпаки |
| Личинка вылезла из трупа, `DialogEnded` (`[GD] GLO_Tadpole_PostEA.txt:272–290`) | все | VB | отчаяние или решимость |
| Стая гиен: одна бежит за гноллами (`[G] Act1_PLA_DyingHyenas.txt:409`) | все | PAD | «зовёт своих» |
| Гноллы мертвы у Заставы (`[G] Act1_PLA_KarlachRecruitment.txt:389–398`) | все | VB | бойня |
| «Беженцы» — культисты Зариэль (`[G] Act1_PLA_KarlachRecruitment.txt:560–575`) | все | VB | сделка с дьяволом |
| Паладины Тира (`[GD] …Karlach.txt:53`) | Карлах | OM + WRD | ярость |
| Пламенный кулак у горящего трактира (`[G] Act1_PLA_TavernInvestigation.txt:34`) | Уилл | OM | узнают сына герцога |
| Гитский патруль, знаки на перекрёстке (`[GD] Act1b_OriginMoments_Laezel.txt:83–140`) | Лаэ'зель | автостарт/«!» | путь к Яслям |
| Статуя Латандера, проверка религии (`[GD] Act1b_CRE_Exterior.txt:355, 362`) | все | PAD | Утренний Лорд |
| Манекены и учебка юных гитов (`[GD] Act1b_CRE_Creche_Misc.txt:139–142`) | Лаэ'зель / любой | VB | воспитание гитов |
| Стихи в Тайной башне, `GameBookInterfaceClosed` (`[G] Act1_UND_ArcaneTower.txt:702–714`) | все | AD | в стихах пароли |

---

## 5. Поводы для Альфиры в акте 1

Она может быть в отряде почти весь акт 1: найм сразу после `DEN_TieflingBard_State_FinishedSong`
(`mod/…/ALFSV_Companion.txt:120–156`). Не повторяю 41 место этапа 5 и 17 реакций (`design/reactions/01_act1.md`).
Там, где повод совпадает, это отмечено как «апгрейд»: реплику над головой или реакцию можно превратить в
разговор.

Способы запуска (все без переопределения ванильных файлов):
- **«!»** = `PROC_RelationshipDialog(S_DEN_Bard_4a405fba-…, ALFSV_WRD_<имя>, NULL, S_DEN_Bard_4a405fba-…)`
  или `(…, ALFSV_Alfira_InParty_b2950129-…, ALFSV_IPRD_<флаг>, …)` + корень в её InParty.
- **OM** = `PROC_DefineSingleOriginMoment(диалог_NPC, (TAG)ALFIRA_c93d7c45-ff8f-4565-b4de-5b5eb48207bb, AOM, COM, OOM)`.
- **AD** = `PROC_TryStartAD` (конвейер этапа 5).
- **После ванильной VB** = `VoiceBarkEnded(VB,_)` / `VoiceBarkFailed(VB)` (события движка,
  `[S] _GLO_OneshotDialogs.txt:207–278`). Одноразовые VB-триггеры игра снимает, поэтому надёжнее ловить конец VB,
  а не `EnteredTrigger` Альфиры.

| # | Повод | Запуск (данные игры) | Что | Канон |
|---|---|---|---|---|
| 1 | **Карта Зевлора: дорога из Элтуриэля** | `UseStarted(_, S_DEN_TieflingLeaderMap_1ba813e9-28cc-4be2-96de-c7f50d2ee445)` (`[G] Act1_DEN_TieflingRefugees.txt:190–204`), после ванильной VB `DEN_TieflingLeader_VB_ZevlorsMap_01989476-e829-11ea-37e6-c05528eaffc0` | «!» WRD | Элтуриэль, бегство |
| 2 | **Ашарак учит детей деревянным мечам** | OM на `DEN_Thieflings_Trainer_f2596c8f-2b4f-0c9c-f371-e7940f4405d4` (для компаньонов не занят; у Уилла только AOM, `[GD] Act1_DEN_WyllRecruitment.txt:57`) | OM COM | она описывает Ашарака в акте 2 |
| 3 | **Лакрисса на посту** | OM на `DEN_General_TieflingGuard10_d43304e2-1268-7715-0d15-e28e52108970` (`DB_Dialogs(S_DEN_Tiefling_010…)`, `[G] Act1_DEN_Misc.txt:295`) | OM COM, короткий, «первый взгляд» до праздника | роман с Лакриссой |
| 4 | **Даммон и Аверно** | OM на `DEN_Weaponsmith_PostEA_f2e19bab-4804-9a49-c7ee-0a190f1fcafd` (`[G] Act1_DEN_Misc.txt:294`); с Карлах в отряде её OM важнее (`[GD] …Karlach.txt:64`), тогда запасной вариант — «!» после `DialogEnded` этого диалога | OM или «!» | мать сгорела в Аверно |
| 5 | Миркон в убежище детей | OM на `DEN_HarpyMeal_InHideout` (`[G] Act1_DEN_HarpyMeal.txt:224`, клик по `S_DEN_CharmedKid_3b92c689-…`) | OM COM | дети, её убежище (апгрейд реакции 7) |
| 6 | Спасли Миркона от гарпий | `FlagSet(DEN_HarpyMeal_State_RescuedChild_7a90f576-f762-4710-aa4d-9a81905bd971)` → `DialogEnded` → «!», как у Гейла (`[G] Act1_ORI_Gale.txt:23, 301–374`) | «!» WRD | гарпии заманивают песней (`GLO_HarpySong_State_Stationary`, `[G] Act1_DEN_HarpyMeal.txt:37`); апгрейд реакции 7 |
| 7 | Арабелла отпущена | `DEN_ShadowDruid_State_FreedChild_e0db3e8d-497d-33bb-ce67-91dff9fb1c67`, та же схема (`Act1_ORI_Gale.txt:21`) | «!» WRD | апгрейд реакции 5 |
| 8 | Каша Окты | `PROC_FlagReactionAfterDialog(_, DEN_Thieflings_Event_TookGruel_e9166e18-05a7-16da-0b43-dd1ff8674e0a)` и `…TookGruel2_cbf45767-7dac-0bdc-1f0f-8203b44798d9` (`[GD] …Karlach.txt:603–624`) | AD | жизнь беженцев, юмор |
| 9 | Ритуал Шипов у пруда | `DialogEnded` диалога ритуального друида, если Кагха ещё не объяснила ритуал (`DEN_ShadowDruid_Knows_KaghaExplainedRite_79678e1b-2002-b357-1ebb-b3f059d1643c` = 0), ванильная VB `DEN_SacredPond_VB_RecognizeRite_4e4159e0-…` (`Act1_DEN_SacredPond.txt:281`, хотфикс перекрывает) | «!», апгрейд места `SacredPool` | их выгонят из Рощи |
| 10 | **Гноллы впервые** | `PLA_ConflictedFlind_Knows_Gnolls_c353a7d3-7561-05dc-c725-32e363ce6bf3` (ставится при входе в `S_PLA_ZhentShipment_GnollBehaviorCommentArea_2895b396-…` или в первом бою с ними, `[G] Act1_PLA_ConflictedFlind.txt:1195–1231`) | AD сразу, «!» после боя | Лихейлу убили гноллы |
| 11 | **Стая гноллов перебита** | `PLA_ConflictedFlind_State_RegularGnollsDead_7415a408-ed52-4e7c-8a96-fe697647e24a` (`…ConflictedFlind.txt:1167–1174`) | «!» WRD: главный разговор о Лихейле | «There was so much blood» |
| 12 | Гиена убегает звать стаю | `VoiceBarkStarted(PLA_DyingHyena_VB_HyenaRunning…)`, запуск `[G] Act1_PLA_DyingHyenas.txt:409` | AD в бою | «Run when they shriek. They call for others» |
| 13 | Мёртвые гноллы у Заставы | `PLA_KarlachRecruitmentTollhouse_Knows_GnollsDead_9dab2061-e12d-435e-99f0-d9dbe075813d` (`[G] Act1_PLA_KarlachRecruitment.txt:389–398`, триггер зарегистрирован :15) | AD, тёмный тон | гноллы |
| 14 | **«Беженцы» из Заставы — культисты Зариэль** | `PLA_KarlachRecruitmentTollhouse_Knows_RefugeesAreCultists_8b18c014-7558-4bab-aa35-37d135fc8630`; ванильная рефлексия — `LeftTrigger(S_PLA_TollhouseInterior…)` (`…KarlachRecruitment.txt:560–575`) | «!» WRD | Зариэль утащила Элтуриэль в Аверно |
| 15 | Детская игра на полу деревни | `VoiceBarkEnded(FOR_KidsGame_VB_37723c9c-7012-7c11-7d53-64e736a8d75c)` (`[G] Act1_FOR_Misc.txt:7`) | AD или короткий «!» | детство в Элтуриэле [вымысел в деталях] |
| 16 | Вино в пустой книге | `UseStarted(_, S_FOR_HoleBook_da2a1502-399f-440d-93be-db6930231525)` (`[G] Act1_FOR_Boosters.txt:733–741`) | AD | «наставница не давала вина» |
| 17 | Кровавый разорённый лагерь у болота | `VoiceBarkEnded(HAG_Campsite_VB_c34d5084-a2b4-63ec-9e03-75df85e54617)` (триггер `S_HAG_CampsiteBox_15dcab17-…`, `[G] Act1_HAG_Boosters.txt:14`) | «!» WRD | караван, засада |
| 18 | **Воло поёт гоблинам** | `EnteredTrigger(_, S_GOB_VoloBallad_FirstHeardArea_7d714a14-2d80-44d4-ba90-479e8510c024)` + `GOB_VoloBallad_State_OnStage_0bc1d7d7-9129-4c6e-188d-054640cea3b9` (`[G] Act1_GOB_VoloBallad.txt:5, 145–152`) | AD сразу, «!» потом | бард о барде; она знает Воло по лагерю |
| 19 | Разговор с Воло на сцене | OM на `GOB_VoloBallad_Volo_FestivitiesArea_30ce4472-a341-1b45-48ef-1913293b80ed` (`…VoloBallad.txt:98`) | OM COM | интерджекция без переопределения |
| 20 | **Герой играет на барабанах на посту** | `PROC_FlagReactionAfterDialog(_, GOB_Checkpoint_Event_ReactOnPlayerPerformingSong_fa4c345b-b443-4d6f-8ae7-51144b29f261)` (`[G] Act1_GOB_Checkpoint.txt:234–244`) | AD или «!» | профессиональная оценка |
| 21 | Лагерь гоблинов (клик) | тема `TG_GOB_GoblinCamp_Entered` (`[GD] GLO_TopicalGreetings_Gustav.txt:15–17`) на ней | приветствие в InParty | страх, ирония |
| 22 | Некрономикон Тэя / опасная книга | ванильный `FOR_DangerousBook_VB_BookDestroyed` по `DestroyedBy` (`[G] FOR_DangerousBook.txt:156`) | AD | «в сказаниях злодеи — тифлинги» |
| 23 | Личинка вылезла из трупа культиста | `DialogEnded(GLO_Tadpole_TrueSoulCorpse_8ceb5646-8c9b-f8f9-cfea-7e6a9f94159e)` (`[GD] GLO_Tadpole_PostEA.txt:272`) | «!» | «погребальные песни нужны живым»; есть ли у неё личинка — **[проверить]** в моде |
| 24 | Стихи в Тайной башне | `GameBookInterfaceClosed(_Book,_)` + `DB_UND_ArcaneTower_Poems(_Book,_)` (`[G] Act1_UND_ArcaneTower.txt:702–714`) | AD, 2–3 реплики | разбор чужих стихов |
| 25 | Подземье (клик) | тема `TG_UND_Underdark_Entered` (`[GD] GLO_TopicalGreetings_Gustav.txt:20–22`) | приветствие | место уже есть как AD; тут — разговор |
| 26 | Статуя Латандера у Яслей | `PROC_GLO_KnowledgeCheckSuccess(_, "CRE_Exterior_ArrivalStatuePlaque_Religion", …)` / `"CRE_Exterior_CourtyardStatue_Religion"` (`[GD] Act1b_CRE_Exterior.txt:355, 362`); это PROC — своё правило добавляется | AD | «The Weeping Dawn» — рассвет |
| 27 | Учебка юных гитов | конец VB из `DB_CRE_ClickableItemVBs` (`[GD] Act1b_CRE_Creche_Misc.txt:139–142`) | AD или «!» | дети-гиты против детей с мечами Ашарака |
| 28 | Ясли, клик после Зайт'иска | тема `TG_CRE_DidZaithisk` (`[GD] GLO_TopicalGreetings_Gustav.txt:49–51`) | приветствие | — |

Самое сильное по канону: 1, 2, 3, 4, 10–11, 14, 17, 18. Там её личная история — Элтуриэль и Аверно,
Лихейла и гноллы, дети, Лакрисса, музыка. Эти стоит делать «!»-разговорами на 15–40 узлов с выбором
и одобрением (узлы с `ApprovalRatingID` в самом диалоге или `ChangeApprovalRating` в goal, как у Гейла).
Остальное — реплики над головой или приветствия.

---

## 6. Для сборки: что проверить до реализации

1. Стоит ли тег `ALFIRA` (`c93d7c45-…`) на `S_DEN_Bard` в отряде. Если нет — `SetTag` в `ALFSV_Companion`.
   Без тега OM (№2–5, 19) не найдут её.
2. Показывается ли VFX «!» на её модели (кость `Dummy_OverheadFX`) — проверить в игре на одном WRD.
3. Наш `QRY_SelectCustomDialog` для Альфиры (найм, праздник, `ALFSV_Companion.txt:153, 396, 405`) стоит
   раньше `QRY_SelectRelationShipDialog`. В ночь праздника он перехватит клик, днём в мире не мешает.
4. Порог одобрения: `_MinApproval` по умолчанию `-100`. Одобрение Альфиры есть (`ALFSV_Companion.txt:58`,
   `ChangeApprovalRating`).
5. Риск «говорит строку Тава» в ванильных VB без тегов (§3.3) — проверить в игре.
6. Имена в Osiris ≠ имена файлов: WRD Уилла из `[G] Act1_OriginMoments_Wyll.txt` в банках не существуют,
   на них не ориентироваться.
