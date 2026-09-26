# Как устроены компаньоны в BG3 (Patch 8 Hotfix 9): разбор ванильных скриптов Osiris

Цель: понять, из каких частей Osiris собран компаньон, чтобы сделать Альфиру
(`S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c`) полноценным компаньоном отдельным модом.
Всё ниже взято из распакованных goal-файлов; догадки помечены **[догадка]**, непроверенное —
**[проверить]**.

## 0. Источники и обозначения

| Метка | Путь |
|---|---|
| `[G]` | `game-data/Gustav/Mods/Gustav/Story/RawFiles/Goals/` |
| `[GD]` | `game-data/Gustav/Mods/GustavDev/Story/RawFiles/Goals/` |
| `[H]` | `game-data/Patch8_HotFix9/Mods/Shared/Story/RawFiles/Goals/` (хотфикс перекрывает одноимённые goals из Shared.pak) |
| `[HG]`, `[HGD]` | `game-data/Patch8_HotFix9/Mods/Gustav/…`, `…/GustavDev/…` |
| `[SP]`, `[SPD]` | **Shared.pak** → `Mods/Shared/Story/RawFiles/Goals/`, `Mods/SharedDev/Story/RawFiles/Goals/` |

Важно: базовые goals мода **Shared** (в т.ч. `_GLO_Shared_PartyMembers.txt` с `PROC_GLO_PartyMembers_Add`,
`Hirelings.txt`, `__GLOBAL_Dialogs.txt`) **в `game-data/` не распакованы** — набор `unpack.sets.goals`
в `config/tools.json` берёт только `Gustav.pak`, `GustavX.pak`, `Patch8_HotFix9.pak`. Для этого разбора
они извлечены Divine во временную папку сессии (135 файлов). Рекомендация: добавить `Shared.pak` в
набор `goals` (в этом задании конфиг не менялся). Хотфиксная версия `_GLO_Shared_Origins.txt` отличается
от Shared.pak только редактированной ссылкой в строке 4 (в оригинале — Confluence-страница
«Companion Setup in 19 easy steps»; сама страница нам недоступна).

Иерархия goals: `ParentTargetEdge "X"` — goal инициализируется, когда X выполнил `GoalCompleted`.
`ModWrapper_Gustav` завершается на `GameModeStarted("Campaign")`, `Act1` — на загрузке `WLD_Main_A`
(`[G] Act1.txt`). Дочерние goals после инициализации **остаются активными до конца игры**, если сами не
вызывают `GoalCompleted` (у `Act1_ORI_DarkUrge`, `Act1_DEN_TieflingBard`, `Act3b_LOW_ElfsongTavern`
такого нет) — поэтому правила про Альфиру из актовых goals продолжают срабатывать и в поздних актах.

---

## 1. Жизненный цикл компаньона

### 1.1 Объявление: какие БД описывают компаньона

| БД | Смысл | Где видно |
|---|---|---|
| `DB_Origins(char)` | «Персонаж-ориджин/компаньон». Для 5 ориджинов — `[G] Start.txt:4-8`; Karlach, Minsc, Minthara, Halsin, Jaheira — `[GD] _StartPostEA.txt:4-8` (с комментарием «Not an origin, just a companion»). Используется Withers, эпилогом, тадпол-логикой, лагерем. | см. §2 |
| `DB_Origins_UnavailableForRandom(char)` | исключить из случайного выбора ориджина | `[GD] _StartPostEA.txt:10-13` |
| `DB_OriginNPCAlignment(char, FACTION)` | фракция, в которую персонаж возвращается, будучи NPC; копируется в `DB_GLO_PartyMembers_OriginalAlignment` | `[H] _GLO_Shared_Origins.txt:236-241` |
| `DB_CompanionOnlyFaction(char, FACTION)` | «игровая» фракция CompanionN для НЕ-ориджинов (Minsc=Companion3, Halsin=Companion10, Minthara=Companion12; DU использует Companion11) | `[GD] GLO_Companion_Minsc.txt:13`, `…Halsin.txt:9`, `…Minthara.txt:10`, `GLO_Origin_DarkUrge.txt` |
| `DB_GLO_PartyMembers_DefaultFaction(char, FACTION)` | фракция, которая ставится при входе в отряд. Заполняется `PROC_GLO_PartyMembers_Initialize` / `MakeNPC`. **Без неё `PROC_GLO_PartyMembers_Add` не сработает** | `[SP] _GLO_Shared_PartyMembers.txt:512, 1282, 1291, 1313` |
| `DB_OriginRecruitmentDialog(char, DIALOG)` | диалог вербовки, пока персонаж ещё не в команде | Minsc `:16`, Jaheira `:11`, Minthara `:14` |
| `DB_OriginInPartyDialog(char, DIALOG)` | «InParty»-диалог; после первой вербовки он же служит диалогом в лагере | `[H] _GLO_Shared_Origins.txt:328-337` |
| `DB_OriginWarning1Dialog / Warning2Dialog / LeavingDialog` | диалоги при низком одобрении | Minsc `:18-20` |
| `DB_OriginMayLeaveDialog(char, DIALOG)` | другие диалоги, после которых компаньон может уйти/умереть | Minsc `:48`, Jaheira `:54-57` |
| `DB_OriginInPartyGlobal(char, FLAG)` | глобальный флаг «X в отряде» (ставится в AddHook, снимается в MakeNPCHook) | `[SP] …PartyMembers.txt:573-578`, `[H] …Origins.txt:452-457` |
| `DB_OriginPartOfTheTeamFlag(char, PartOfTeamFlag, AvatarFlag, ControlledByUserFlag)` | флаги для диалогов: «в команде», «аватар», «управляется тем же игроком» | `[H] …Origins.txt:2534-2630` |
| `DB_OriginKickFromPartyFlags(char, KickEventFlag, CanBeKickedFlag)` | опция «выгнать X» в диалогах обмена при полном отряде | `[H] …Origins.txt:2632-2823` |
| `DB_OriginCampFlags(char, BASE, AVATAR, COMPANION, PARTY, CAMP)` | глобальные флаги присутствия в лагере для лагерных ночей (`MINSC`, `MINSCCAMP`…) | `[H] GLO_CampNights.txt:2757-2946` |
| `DB_ORI_OriginCampData(char, "CAMPNAME", TRIGGER)` | точка стоянки в каждом лагере | `[H] GLO_Camp.txt:3350-3455`, данные — `[G] _Gustav_CampFollowers.txt` |
| `DB_Camp_PersonalCornerLevelTemplate / …Gear` | личный «уголок» (палатка/вещи) по лагерям | `[H] GLO_Camp.txt:3003-3348`, данные в `Act1a_Camp.txt`, `Act2_CAMP.txt`, `Act3b_Camp.txt` |
| `DB_Inclusion_Object(char, StartFlag, EndFlag)` | флаги «включения» компаньона в чужие диалоги | Minsc `:22`, `[H] GLO_InclusionNodes.txt` |
| `DB_CompanionCanPartner`, `DB_CompanionIsDating`, `DB_ORI_FreeDating` | романтика (§5.2) | Halsin `:21-22`, Minthara `:31,67-68` |
| `DB_PermaDefeatedFlag`, `DB_GLO_CharacterCorpseDialog`, `DB_KilledByPartyEvent` | смерть | Minsc `:37-41`, Jaheira `:59` |
| `DB_GLO_PartyMembers_BlockRecruitmentDialog(char)` | «пока не вербуем» (диалог вербовки заблокирован) | Minsc `:49`, Minthara `:13`; `[H] …Origins.txt:321-326` |
| `DB_Debug_CharacterAddFlags`, `DB_Debug_CharacterRemoveHideFlags` | книга отладки | Minsc `:24-25` |

### 1.2 Инициализация «компаньона в роли NPC»

`[SP] _GLO_Shared_PartyMembers.txt:1261-1292` — `PROC_GLO_PartyMembers_Initialize(char)`:
`MakeNPC`, `DB_NoLowAttitudeDialog`, `NOT DB_Players`, `NOT DB_PartyMembers`; затем
- если **нет** `DB_CompanionOnlyFaction`: `SetFaction(char, DB_OriginNPCAlignment)` и
  `DB_GLO_PartyMembers_DefaultFaction(char, <фракция, в которой персонаж стоял до этого>)`
  (для ориджинов, размещённых с игровой фракцией);
- если **есть** `DB_CompanionOnlyFaction(char, F)`: фракция не трогается, `DefaultFaction = F`.

Вызов: `[H] _GLO_Shared_Origins.txt:202-216` — на `PROC_PlayersSelected("Initial")` (конец создания
персонажа) для каждого `DB_Origins`, не ставшего аватаром. **Следствие:** для уже идущей игры мод должен
вызвать `Initialize` сам (так делает ванильный DU-сценарий для Альфиры, §2.3).

### 1.3 Вербовка: флаги диалога → PROC

Путь «в отряд сразу» (`[H] _GLO_Shared_Origins.txt:349-383`, `[SP] …PartyMembers.txt:467-482`):

1. В диалоге узел ставит object-флаг **`OriginAddToParty`** (`4870b2cd-…`) на персонажа.
2. `FlagSet` → `DB_GLO_PartyMembers_RecruitAfterDialog(ID, char, Avatar)` (берётся аватар из диалога).
3. `DialogEnded` → `PROC_GLO_PartyMembers_CheckAdd(char, Avatar)`.
4. `CheckAdd` добавляет **только если глобальный `GEN_MaxPlayerCountReached` = 0**. При полном отряде
   диалог сам уводит во вложенный `GLO_CompanionSwap_Recruitment` (см. разбор `Minsc_InParty`:
   узел «Follow me» при `!ORI_State_Recruited`, вложенный диалог при `GEN_MaxPlayerCountReached`,
   затем `OriginAddToParty`).

Путь «в лагерь, не в отряд» (`[H] …Origins.txt:1905-1983`): флаги
`GLO_ORI_Event_InvitedToCamp_Run/_Walk` → после диалога `PROC_ORI_SendToCampAfterDialog`:
`PROC_CheckFirstTimeRecruited` (уровень), **`RegisterAsCompanion(char, Player)`**, уход за экран →
`PROC_ORI_SetupCamp(char)`: `DB_PartOfTheTeam`, `SetOnStage 1`, снятие `DOWNED_DISABLED`, телепорт на
`QRY_Camp_GetCamperPos`, диалог = InParty.

Помимо флагов, скрипты зовут `PROC_GLO_Origins_SetRecruitmentDialog(char, dialog)`
(`[H] …Origins.txt:266-287`) — меняет диалог вербовки (Minsc после Бу: `[GD] GLO_Companion_Minsc.txt:178-182`).

### 1.4 Вход в отряд: тело `PROC_GLO_PartyMembers_Add`

`[SP] _GLO_Shared_PartyMembers.txt:500-528` (ветка «компаньон», не аватар). Условия:
`NOT DB_DismissedAvatar`, есть InParty-диалог (`QRY_GLO_PartyMembers_GetInPartyDialog` → `DB_OriginInPartyDialog`),
есть `DB_GLO_PartyMembers_DefaultFaction`. Действия по порядку:

```
PROC_GLO_PartyMembers_ClearCompanionHostilityForOriginalFaction(_Origin);
MakePlayer(_Origin,_Player);
RegisterAsCompanion(_Origin, _Player);
PROC_AssignCharacterToPlayer(_Origin,_Player);          // AssignToUser
PROC_GLO_PartyMembers_SetInpartyDialog(_Origin,_NewDialog); // DB_Dialogs
SetFaction(_Origin,_PlayerFaction);                     // DefaultFaction
ClearTag(_Origin, BLOCK_RESURRECTION);
DB_Players(_Origin); DB_PartOfTheTeam(_Origin);
NOT DB_GLO_PartyMembers_DefaultFaction(_Origin,_PlayerFaction);
PROC_CheckPartyFull();
PROC_CheckFirstTimeRecruited(_Origin);                  // RequestInitialLevel один раз
SetFlag(ORI_State_Recruited, _Origin);
SetNoFollowFlag(_Origin, 0);
PROC_GLO_PartyMembers_AddHook(_Origin,_Player);
```

`PROC_GLO_PartyMembers_AddHook` — точка расширения. Базовые обработчики: чистка
`DB_Origin_TemporaryLeaveReason`, установка `DB_OriginInPartyGlobal`-флага, снятие `DOWNED_DISABLED`
(`[SP] …:565-585`); `PROC_CheckDismissableAvatars` (`:1766`). Каждый поздний компаньон вешает сюда
«первый раз → `PROC_ORI_SetupCamp(char, 0)`» (Minsc `:53-58`, Halsin `:43-49`, Jaheira `:180`, Minthara `:133`).

Рядом: `DB_ApprovalRating(char, Avatar, 0)` создаётся автоматически для любого не-аватара в `DB_Players`
или `DB_InCamp` (`[H] …Origins.txt:895-919`); `DB_Avatars` → `DB_PartOfTheTeam` (`:861-864`);
`DB_PartOfTheTeam` → отключение self-healing (`:1997-2011`); `DB_PartyMembers` → регистрация
партийных триггеров (`[SP] …:1565-1569`).

### 1.5 Лимит отряда

`PROC_CheckPartyFull` (`[SP] _GLO_Shared_PartyMembers.txt:104-153`): `SysCount("DB_Players")` +
`DB_PlayerSlotReserved` против движкового `GetMaxPartySize` → глобальные `GEN_MaxPlayerCountReached`
и `GEN_SoloPlayer`. Резервирование слота — при подключении игрока и во время создания наёмника
(`:155-227`). Сам лимит (4) — движок, в Osiris не задаётся.

### 1.6 Отпустить в лагерь («подожди в лагере»)

- Диалог ставит object-флаг **`OriginRemoveFromPartyAfterDialog`** (`7a429beb-…`) →
  `DB_GLO_PartyMembers_DismissAfterDialog` → на `DialogEnded`
  `PROC_GLO_PartyMembers_Remove(char, Player, 0, 0)` (`[SP] …:419-465`; для компаньона сюжетные
  предметы **не** передаются — «они в лагере и в сети волшебных карманов»).
- Опция скрыта флагом `GLO_Origin_BlockWaitInCampOption` в опасных/блокированных зонах
  (`[H] …Origins.txt:2905-2990`).
- Также: движковое событие `ForceDismissCompanion` → `Remove(char,1)` (`[SP] :230-234`);
  кнопка «отправить в лагерь» — движок (`EnableSendToCamp`, `[H] GLO_Camp.txt:338-372`).

`Remove` → `RemoveIfUserHasOtherCharacter` → (передача золота/тел) → `DetachFromPartyGroup` →
`PROC_GLO_PartyMembers_MakeNPC` (`[SP] :619-699`). `MakeNPC` для компаньона (`[SP] :1296-1321`):
`PreMakeNPCHook`, `NOT DB_Players`, `MakeNPC`, снятие полиморфов, `DefaultFaction := текущая`,
`SetFaction(OriginalAlignment)`, `DB_NoLowAttitudeDialog`, стирание диалогов, `SetHasDialog 0`,
`PROC_GLO_PartyMembers_MakeNPCHook`, `ClearFlag(ORI_State_Recruited)`.

`MakeNPCHook` в Origins (`[H] …Origins.txt:394-457`): ставит диалог вербовки (= InParty, т.к. уже
`DB_PartOfTheTeam`), и **если `DB_OriginNPCAlignment` + `DB_PartOfTheTeam` и нет
`DB_GLO_PartyMembers_BlockReturnToRecruitmentPosition`** → `PROC_DismissToCamp`: идёт/исчезает к
`QRY_Camp_GetCamperPos`, по событию `Origin_RestoreDialog` телепорт на точку, `SetOnStage 1`,
`SetHasDialog 1` (`:459-553`).

Позиция в лагере — `QRY_Camp_GetCamperPos` (`[H] GLO_Camp.txt:3350-3455`), порядок:
`DB_Camp_CamperPosOverride` → позиция ночи `DB_CampNight_SetPosition` → `DB_ORI_OriginCampData(char,
активный лагерь)` → `QRY_Camp_GetCamperPos_Custom` (так делают наёмники) → вход в лагерь
`DB_Camp(_,_,_,Entrance)` → `DebugBreak`. Лагеря: `WLDMAIN, WLDBAS, WLDCAVGRN, WLDCAVSND, WLDDUNABB,
WLDDUNSHA, WLDUND` (`[G] Act1a_Camp.txt`), `CREMAIN, CREINSIDE` (`[GD] Act1b_Camp.txt`), `SCLMAIN,
SHARTEMPLE, HAVEN, MOONRISE` (`Act2_CAMP.txt`), `INTMAIN` (`Act2b_CAMP.txt`), `FARM` (`Act3_Camp.txt`),
`SLUMS, ELFSONG` (`Act3b_Camp.txt`). В лагере: `DB_InCamp`, тег `IN_CAMP`, флаг `CAMP_GLO_State_InCamp`
(`[H] GLO_Camp.txt:152-336`); для персонажей с `DB_OriginCampFlags` вне отряда — фракционные поправки
(`:2787-3001`).

Возврат из лагеря в отряд — тот же InParty-диалог с `OriginAddToParty`.

### 1.7 «Выгнать» при полном отряде (обмен)

`DB_OriginKickFromPartyFlags(char, KickEvent, CanBeKicked)`. В диалогах
`GLO_CompanionSwap_Camp/_Hirelings/_Recruitment` (`[GD] GLO_OriginKickFromParty_Gustav.txt:4-6`)
показываются опции по `CanBeKicked`-флагам на аватаре (`QRY_OriginKickFromPartyFlags`,
`[H] …Origins.txt:2765-2805`: тот же пользователь, не наёмник, не заблокирован);
выбранный `KickEvent` (глобальный) → `PROC_GLO_PartyMembers_Remove(char, Player, 1)` (`:2807-2820`).

**Находка:** во всех трёх ванильных swap-диалогах уже есть опция для Альфиры — флаги
`ORI_Alfira_State_CanBeKicked` (`a6499b8c-…`) и `ORI_Alfira_Event_KickCompanion` (`23496e30-…`), оба
определены в `Gustav/Public/GustavDev/Flags/`. Использует их DU-сценарий (§2.3).

### 1.8 Постоянный уход

`[H] _GLO_Shared_Origins.txt:884-1438`:
- `PROC_Origins_CompanionLeavePermanently(char, Reason)` → `PROC_Origins_RemoveFromTeam`
  (`:1156-1165`: `MakeNPC`, **`UnregisterAsCompanion`**, тег `BLOCK_RESURRECTION`, `NOT DB_PartOfTheTeam`)
  + удаление рейтинга (`RemoveApprovalRating`, `:887-893`), диалогов вербовки/InParty, романтических
  флагов, квестовое обновление `DB_QuestDef_State_CompanionLeft`, тег `DOWNED_DISABLED`, передача
  инвентаря (кроме причин `Killed/CompanionHostile/CompanionMurdered/Debug`, `:179-182`).
- `PROC_Origins_CompanionLeaveTemporarily(char, Reason)` — то же без «навсегда»,
  с `DB_Origin_TemporaryLeaveReason`.
- Исходы «диалога ухода» по флагам на персонаже (`:1226-1353`): `GLO_Companion_Leave` (уходит бегом),
  `GLO_Companion_LeaveNoDisappear`, `GLO_Companion_LeaveDisappearInstantly`, `GLO_Companion_Murder`
  (умирает), `GLO_Companion_Combat` (становится враждебным).

### 1.9 Смерть и воскрешение

- Вне отряда тег `BLOCK_RESURRECTION` снимается при входе (`Add`), ставится при `RemoveFromTeam` и
  заклинании `Target_AntiResurrection` (`[H] …Origins.txt:867-881`). Minsc и Minthara стартуют с этим тегом
  (`Minsc :6`, `Minthara :72`).
- `Resurrected` → переустановка диалогов: в отряде — InParty (`[SP] :1244-1259`), вне отряда —
  вербовочный (`[H] …Origins.txt:289-298`); флаг `GLO_State_ResurrectedOutOfParty` для `DB_GLO_Playable`
  (`[SP] :1677-1686`).
- **Withers** (`[G] GLO_Jergal.txt`): мёртвые **в отряде** — три универсальных слота
  `DB_GLO_Jergal_ResurrectionStringVariableAndFlags` (`:21-23`, логика `:520-540`) — работают для любого
  `DB_Players`. Мёртвые **в лагере** — только при `DB_Origins` + персональные флаги
  `DB_GLO_Jergal_CompanionResurrectionFlags` (`:27-36`, `:582-600`) с опцией в диалоге `CAMP_Jergal`.
  Для наёмников — свои три слота (`:38-40`).
- `DB_PermaDefeated` → квест `CompanionMurdered` для `DB_Origins` (`[H] …Origins.txt:1210-1223`).

### 1.10 Уровень при вступлении

- `PROC_CheckFirstTimeRecruited(char)` (`[SP] :492-498`): один раз на персонажа
  (`DB_OnlyOncePerPlayer(char,"Recruitment_Respec")`) → движковый **`RequestInitialLevel(char)`**.
  Вызывается из `Add` и из `PROC_ORI_SendToCampAfterDialog`. Тот же вызов делает туториальный
  временный спутник (`[G] TUT_Misc.txt:192-200`: `SetFaction(Hero)`, `MakePlayer`, `RequestInitialLevel`,
  `DB_Players`, `RegisterAsCompanion`). **[догадка]** `RequestInitialLevel` подтягивает уровень до уровня
  отряда; класс/подкласс берутся из данных шаблона (Osiris класс не задаёт).
- Фиксированные уровни в отдельных местах: Lae'zel `SetLevel 4` (`[G] Act1_PLA_GithChokepoint.txt:1265`),
  Wyll 2, Karlach 3; Jaheira/Minsc `SetLevel 12` в Храме Баала (`[GD] Act3b_LOW_BhaalTemple.txt:3566,3622`).
- Респек у Withers: `StartRespec` (`[SPD] Respec.txt`).
- **Для Альфиры:** патч сохранений `GUSX-11195` снимает с неё статус `BLOCK_LEVELUP` и теги
  `ILLITHID`/`BALDURIAN` (`[GD] BG3_Act1_SavegamePatches.txt:7550-7554`) — значит, в DU-сценарии она
  попадала в отряд с запретом повышения уровня. **[проверить]** есть ли `BLOCK_LEVELUP` в её шаблоне и
  есть ли у её статблока классовая прогрессия, иначе левел-ап сломается.

### 1.11 Инвентарь

- Уход в лагерь по диалогу: передаётся только золото и тела партийцев
  (`TransferItems=0` → `_OnlyGoldAndPartyMembers=1`, `[SP] :676-764`).
- Принудительный уход `Remove(...,1)` (кик): при общем пользователе `TransferItemsToCharacter`,
  иначе `TransferItemsToUser` (`[SP] :701-750`).
- Уход навсегда: `PROC_GLO_PartyMembers_TransferInventoryToPlayer` — всё в рюкзак
  `LOOT_GEN_Backpack_A_Posed_A` игроку + окно «Компаньон ушёл навсегда» (`[SP] :1439-1458`).
- Персонажи в лагере остаются частью «волшебных карманов» (комментарий `[SP] :452`).

---

## 2. Поздние компаньоны (Minsc, Halsin, Jaheira, Minthara) — наш случай

### 2.1 Чем они отличаются от семи ориджинов

| | Ориджины (Astarion…Karlach, DU) | Поздние компаньоны |
|---|---|---|
| Шаблон | `S_Player_*`, `Origins.lsx`, выбираемы в CC | Minsc/Jaheira — `S_Player_*`; Halsin — `S_GLO_Halsin`, Minthara — `S_GOB_DrowCommander` (обычные NPC) |
| `DB_Origins` | да (`Start.txt`, Karlach — `_StartPostEA.txt`) | да, добавлены в `_StartPostEA.txt:5-8` + `DB_Origins_UnavailableForRandom` |
| Фракция в отряде | размещены с игровой фракцией; `Initialize` меняет её на NPC-фракцию и запоминает игровую | **`DB_CompanionOnlyFaction(char, CompanionN)`** (Jaheira — нет, Halsin дополнительно чинит фракцию в AddHook `:81-84`) |
| Вербовка | ранний диалог вербовки | `DB_GLO_PartyMembers_BlockRecruitmentDialog` до сюжетного момента, потом `PROC_GLO_Origins_SetRecruitmentDialog` (Minsc `:178-182`) |
| Первый вход | — | AddHook + `QRY_OnlyOnce("RecruitedFirstTime_X")` → `PROC_ORI_SetupCamp(char,0)` |
| Одобрение | с нуля | стартовый бонус: Minsc +40 (`:210-228`), Jaheira +20 (`:194-207`, при первой загрузке `INT_Main_A`), через `ChangeApprovalRating(char, Avatar, 1, N, _)` |
| Теги | `PROC_GLO_DataGetOriginTags` берёт REALLY/God/Background из данных ориджина | Minsc зовёт тот же PROC (`:5`); Jaheira вручную `SetTag REALLY_JAHEIRA` (`:52`, комментарий «тег ставится кодом только когда она становится компаньоном»); Minthara — `DB_OriginTags` (`:7`) |
| Воскрешение | стартово свободно | Minsc, Minthara стартуют с `BLOCK_RESURRECTION` |

Jaheira ещё показывает запасной путь: если её оставили в лагере не завербованной, на входе в город её
«досоздают» компаньоном: `PROC_CheckFirstTimeRecruited`, `RegisterAsCompanion`, `PROC_ORI_SetupCamp`
(`[GD] GLO_Companion_Jaheira.txt:78-92`).

### 2.2 Чеклист «что нужно NPC, чтобы стать компаньоном»

Обязательное ядро (без него не работает вход/выход из отряда):

- [ ] **`DB_CompanionOnlyFaction(Alfira, CompanionN)`** — до вызова `Initialize`. Свободна, вероятно,
  Companion13/14/15 (в Osiris не используются; **[проверить]** фракции размещения ориджинов в данных уровней).
- [ ] **`DB_OriginNPCAlignment(Alfira, FACTION)`** — фракция в роли NPC (ванильная —
  `ACT1_DEN_TieflingBard_082ce2e1-…`).
- [ ] **`DB_OriginInPartyDialog(Alfira, <наш InParty>)`** — без неё `Add` не пройдёт условие
  `QRY_GLO_PartyMembers_GetInPartyDialog`; этот же диалог работает в лагере.
- [ ] **`PROC_GLO_PartyMembers_Initialize(Alfira)`** — один раз; даёт `DB_GLO_PartyMembers_DefaultFaction`.
- [ ] Диалог с узлами `OriginAddToParty` («пойдём со мной», вложенный `GLO_CompanionSwap_Recruitment`
  при `GEN_MaxPlayerCountReached`) и `OriginRemoveFromPartyAfterDialog` («жди в лагере», скрыть при
  `GLO_Origin_BlockWaitInCampOption`), условия на `ORI_State_Recruited`.
- [ ] `PROC_GLO_PartyMembers_AddHook(Alfira, _)` + `QRY_OnlyOnce` → `PROC_ORI_SetupCamp(Alfira, 0)`
  (ставит `DB_PartOfTheTeam` → при увольнении пойдёт в лагерь, а не «в мир»).
- [ ] Позиции в лагерях: `DB_ORI_OriginCampData(Alfira, camp, trigger)` — **у Альфиры уже есть** для 11
  лагерей (§2.3), нет для `CREMAIN, CREINSIDE, INTMAIN, FARM, SLUMS, ELFSONG` (там будет вход в лагерь).

Желательное (UI, обмен, одобрение):

- [ ] `DB_OriginKickFromPartyFlags(Alfira, ORI_Alfira_Event_KickCompanion, ORI_Alfira_State_CanBeKicked)` — ванильные флаги, опция уже в swap-диалогах.
- [ ] `DB_OriginPartOfTheTeamFlag(Alfira, GLO_Origin_PartOfTheTeam_Alfira, NULL, ORI_Alfira_ControlledByUser)` — ванильные флаги (`f5d7c888-…`, `e7f05e38-…`); `ORI_Alfira_ControlledByUser` проверяется в вербовочных диалогах Astarion/Gale/Minsc/Karlach.
- [ ] `DB_OriginInPartyGlobal(Alfira, <новый флаг IsInParty>)`.
- [ ] Стартовое одобрение (`ChangeApprovalRating(Alfira, Avatar, 1, N, _)` по образцу Minsc) и
  `DB_OriginWarning1Dialog/Warning2Dialog/LeavingDialog` (иначе при −50 просто ничего не случится).
- [ ] `DB_OriginCampFlags` с новыми флагами `ALFIRA/…CAMP/…PARTY` — для будущих лагерных ночей.

Опционально/позже: `DB_Origins` (плюсы: Withers в лагере, эпилог, `QRY_PartyMemberAttackedDialog`;
минусы — §7.4), `DB_Inclusion_Object`, `DB_CompanionCanPartner`, `DB_PermaDefeatedFlag`,
`DB_GLO_Jergal_CompanionResurrectionFlags` (+ правка `CAMP_Jergal`), личный уголок в лагере,
`PROC_GLO_DifficultyModes_AddHPBoostedEntity` (как Halsin/Jaheira).

Очистка ванильных «NPC-ролей» при вербовке (§6): `PROC_DEN_RemoveFromDenNPCs(Alfira)` (так Рощу
покидает Уилл, `[G] Act1_DEN_Misc.txt:1595-1627`), `NOT DB_GLO_LevelTraveler(Alfira, …)` и т.д.

### 2.3 Ванильная заготовка: Альфира уже бывает членом отряда (путь Темного Соблазна)

`[GD] Act1_ORI_DarkUrge.txt` (parent `Act1`, активен всю игру):
- `:6-16` + `:36-40` — `DB_ORI_OriginCampData` для Альфиры (и её дублёра `S_DEN_Bard_Backup`) в 11 лагерях.
  Правило безусловное → **эти факты есть в любой игре, не только DU.**
- `:529-541` (при постановке ночи `NIGHT_DarkUrge_MurderOfAlfira`, `:271-273`): `DB_OriginInPartyDialog(Alfira,
  DEN_Bard_InParty)`, `DB_OriginNPCAlignment(Alfira, ACT1_DEN_TieflingBard)`, `DB_OriginPartOfTheTeamFlag`,
  `DB_OriginKickFromPartyFlags`, `PROC_GLO_PartyMembers_Initialize`, `MakeNPC`.
  **`DB_CompanionOnlyFaction` не задаётся** → в отряде она остаётся в NPC-фракции.
- `:543-546` — `DB_Players(Alfira)` → `DB_GLO_Playable(Alfira)`.
- `:548-555` — при полном отряде вместо отряда `PROC_ORI_SetupCamp`.
- `:249-253` — **`PROC_GLO_PartyMembers_MakeNPCHook(Alfira)` → стирает диалоги и ставит
  `DEN_Bard_InParty`** — срабатывает в любой игре при каждом увольнении Альфиры.
- `:729-748` — Альфире не ставятся стартовые теги `ILLITHID`/`BALDURIAN`, запрещено волшебное зеркало.
- CFM `CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives` ставит `OriginAddToParty` на Альфиру
  (`reports/dialogs/CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives.md:51,56,297…`) — то есть
  **стандартный путь `OriginAddToParty` → `CheckAdd` → `Add` для Альфиры уже работает в ванилле.**
- `DEN_Bard_InParty` — 4 реплики «перед сном», без опций вступить/уйти (`reports/dialogs/DEN_Bard_InParty.md`).

---

## 3. Наёмники Withers

`[SPD] Hirelings.txt` (1287 строк):
- Наёмники — 12 фиксированных персонажей-шаблонов по классам `S_GLO_Hirelings_<Class>`
  (`DB_Hirelings_HACK_Classes`, `:75-86`). Внешность и статы задаются через движковый CC наёмников:
  `StartHenchmen(Player)` (`:1148-1154`) → событие `HenchmanSelected(Avatar, Hireling)` (`:741-747`),
  плюс «HACK»-путь с `Transform` на случайный игровой корень (`:805-885`).
- На найме (`:741-747`): `DB_OriginInPartyDialog(h, Hireling_418bd530-…)` (общий диалог наёмника),
  `DB_OriginNPCAlignment(h, Hirelings)`, `DB_GLO_PartyMembers_OriginalAlignment`, `PROC_Hirelings_Hire`.
- `PROC_Hirelings_AddToParty` (`:454-457`): `PROC_CheckPartyFull`, `PROC_Hirelings_AssignFaction`
  (одна из `Hireling1..3`, `:89-91`, через `DB_GLO_PartyMembers_DefaultFaction`),
  `PROC_GLO_PartyMembers_CheckAdd` — **тот же общий конвейер `Add`**.
- AddHook (`:503-510`): `DEV_EnableAnubis(h,"Hireling")`, слот лагеря 1–3, `DB_Hirelings_Hired`.
- В лагерь: общий флаг `OriginRemoveFromPartyAfterDialog` → `PROC_Hirelings_SendToCamp`; позиция через
  `QRY_Camp_GetCamperPos_Custom` + `DB_Hirelings_CampPositions(camp, 1..3, trigger)` (`:694-712`).
- Увольнение (`:535-665`): вещи аватару, сохранение экипировки, `Remove`, статус `HIRELING_DISAPPEAR`,
  **`SetOnStage 0`**.

Чего у наёмников нет: одобрения (`QRY_GetBestAvatarForCompanion` — «Hirelings have no Approval Rating»,
`[H] …Origins.txt:674-692`), романтики, лагерных ночей (`DB_OriginCampFlags`), личных диалогов
(общий `Hireling`), опций kick-флагов (исключены, `NOT DB_Hirelings_Hired`); не больше 3 слотов на всех;
воскрешение у Withers — через слоты наёмников.

**Годится ли для Альфиры как milestone 1?** Технически её можно пропустить через
`PROC_Hirelings_AddToParty` (нужны те же три факта, что ставит `HenchmanSelected`), но:
увольнение прячет её со сцены, общий «наёмничий» диалог, Anubis-конфиг наёмника, занятый слот
наёмника, общие счётчики `Hirelings_Hired_Count`. Выигрыша нет: путь «компаньона» (§2.2) по объёму
такой же и дальше расширяется до одобрения/романа. **Рекомендация: не использовать; разве что как
одноразовый smoke-тест.**

---

## 4. Разговор с компаньоном

Выбор диалога при клике (`[SP] __GLOBAL_Dialogs.txt:2113-2156`), по порядку:
`QRY_SelectCrimeBusyDialog` → **`QRY_SelectCustomDialog`** → `QRY_SelectADForRequest` →
`QRY_SelectReflectionDialog` → `QRY_SelectCompanionFallback` → **`QRY_SelectRelationShipDialog`** →
**`QRY_SelectCustomDialog_AfterGenerics`** → **`DB_Dialogs`** → default.

- **В отряде:** `DB_Dialogs(char, InParty)` ставит `PROC_GLO_PartyMembers_SetInpartyDialog`. Смена
  `DB_OriginInPartyDialog` сама переставляет `DB_Dialogs` (`[H] …Origins.txt:251-262`).
  `QRY_SelectCompanionFallback` (`:1727-1903`): компаньон другого игрока → `GLO_AD_CompanionCantTalk`;
  компаньон говорит с компаньоном → переключение на лучшего аватара того же пользователя или отказ;
  зона подавления партийных диалогов → свой/общий диалог.
- **В лагере (вне отряда):** диалог вербовки = InParty, т.к. `DB_PartOfTheTeam`
  (`QRY_Origin_GetRecruitmentDialog`, `:328-337`). Отдельных «лагерных» ресурсов у поздних компаньонов нет,
  кроме сюжетных (Halsin `CAMP_Halsin2`, Minthara `CAMP_Minthara`).
- **Relationship dialogs** (`[H] _GLOBAL_Shared_RelationshipDialogs.txt`):
  `PROC_RelationshipDialog(char, dialog, flag, anchor, partnerOnly, minApproval)` — «мировой» (WRD, в
  радиусе 30 м, `:87-200`); `PROC_CampRelationshipDialog(char, dialog, flag, …)` + `PROC_Try_CampRelationshipDialog`
  — лагерный (CRD, `:676-782`), восклицательный знак `PROC_ExclamationMark_Show`. Флаг передаётся в диалог
  как «тема» (IPRD/CRD-узлы внутри InParty-диалога, пример — `GLO_IPRD_RomanceConflict`).
  Завершённые — `DB_RelationshipDialogsFinished`.
- **Origin moments** (`[H] _GLO_Shared_OriginMoments.txt`): `DB_DoubleOriginMoment` / `PROC_DefineSingleOriginMoment`
  по **тегу** ориджина — перехват диалога с NPC; варианты AOM/COM/OOM/ACM.
  `_GLO_Shared_PartyOriginMoments.txt`: `PROC_StartPartyOriginMoment(char, dialog)` — сцена без внешнего NPC.
- **Inclusion** (`[H] GLO_InclusionNodes.txt:15-50`): любой не-аватар из `DB_Players` (или из лагеря)
  может быть случайно добавлен в чужой диалог как «включённый» спикер (`DB_Inclusion_SpeakerCandidate`);
  своё «включение» задаёт `DB_Inclusion_Object`. **[догадка]** Альфира без своих inclusion-узлов будет
  изредка занимать слот и молчать.
- Group discussions (`[H] _GLOBAL_Shared_GroupDiscussions.txt`): `PROC_GroupDiscussion_InstantStart` — IVB.
- Безопасная романтика: при старте диалога всем `DB_Players` ставится `GLO_SafeRomance_Enabled` по
  опции пользователя (`[GD] GLO_SafeRomance.txt:113-160`).

---

## 5. Одобрение, романтика, лагерные ночи, бантер, реакции

### 5.1 Одобрение

- Хранение — в движке (`GetApprovalRating`, `ChangeApprovalRating`, `RemoveApprovalRating`); Osiris
  зеркалит в `DB_ApprovalRating(Companion, Avatar, Value)` по событию `ApprovalRatingChangeAttempt`
  (`[H] …Origins.txt:921-948`). Начальное `0` создаётся автоматически (`:895-919`).
- Из диалогов одобрение меняется **данными**, не Osiris: у узлов есть `ApprovalRatingID`
  (21 шт. в `Halsin_InParty.lsj`), ссылающийся на ресурс одобрения. **[проверить]** где лежат эти ресурсы
  (предположительно `Public/*/ApprovalRatings/`) и как добавить реакцию Альфиры на чужие узлы — не распаковано.
- Из скриптов: `ChangeApprovalRating(C, A, 0, delta, _)`; `PROC_ChangeApprovalRatingForAllAvatars`
  (`:2825-2860`). Третий аргумент `1` использован для стартовых бонусов — **[догадка]** «без всплывающего
  уведомления/абсолютно».
- Пороговые флаги для диалогов: `DB_OriginRelationThresholdEventsPerSpeaker(SpeakerIdx, Approval_AtLeast_X_For_SpN, X)`
  для X ∈ {−40,−30,−20,−10,0,5,10,20,30,35,40,50,60,70,80,90,100} (`:5-142`); ставятся/снимаются на
  компаньоне, когда он и аватар в одном диалоге (`:1452-1490`).
- Предупреждения/уход: ≤ −20 → `DB_OriginWarning1Dialog`, ≤ −40 → `Warning2`, ≤ −50 (если флаг
  `GLO_Companion_LeaveBlocked` не стоит) → `DB_OriginLeavingDialog` (`:979-1101`).
- Автоматика: дружественный огонь 3 раза за 60 с → −10 (`:1551-1690`); убийство NPC «опекаемой» фракции
  `DB_CompanionCaredFaction(C, Faction, delta, includeChildren, onlyOnce)` (`:2825-2903`);
  `PROC_Origins_ForceLowApprovalLeavingDialog` (Minsc уходит, если ушла/умерла Jaheira, `Minsc :233-248`).
- Гейты: `DB_CampNight_Requirement_Approval(night, C, min)` (`[GD] Act1a_Camp_PostEA.txt:51`),
  `minApproval` у RD.

### 5.2 Романтика

`[H] _GLO_Shared_Origins.txt:2013-2532`:
- `DB_CompanionCanPartner(C, DatingFlag, PartnerFlag, ExFlag, HandledBreakupFlag, ChosePartnerOverFlag, "debugname")`
  — пример Minthara `[GD] GLO_Companion_Minthara.txt:67`.
- Установка `DatingFlag` на аватаре → `DB_ORI_Dating(A,C)` + `ORI_State_Dating`; `PartnerFlag` →
  `DB_ORI_Partnered(A,C)` + `ORI_State_Partnered`; снятие → `ExFlag`, `DB_ORI_WasDating`.
  Два «свидания» одновременно → `ORI_State_DoubleDating`, кроме `DB_ORI_FreeDating` (Minthara).
- Конфликт романов (`[GD] Act2_ORI_RomanceConflict.txt`): при появлении партнёра у аватара встреченному
  «datee» ставится RD `GLO_IPRD_RomanceConflict` на его InParty-диалог.
- Ночные романы: `DB_CampNight_RomanceNight`, `DB_CampNight_Requirement_Partner/_Dating`.
- Финал: `PROC_END_GameFinale_EndRelationship` работает только для `DB_Origins`
  (`[GD] Act3c_END_GameFinale.txt:1217-1230`).

### 5.3 Лагерные ночи, CFM, сны

`[H] GLO_CampNights.txt` (приоритеты в комментарии `:9-19`: Urgent 8000+, … Companion Regular 2000+):
- Объявление: `DB_CampNight(NIGHT_flag, priority[, char])`, `DB_CampNight_Camp(night,"CAMP")`,
  `DB_CampNight_Requirement(night, flag…)`, `…_CancelledBy`, `…_ExpiresAfter`, `…_ExclusiveMoment`.
  Пример — ночь после вербовки Уилла: `[GD] Act1_OriginMoments_Wyll.txt:9-22`.
- Содержимое: `DB_CampNight_CFM(night, dialog)` + `DB_CampfireMoment_FixedSpeakers/OptionalSpeakers`
  (`:1141-1226`, выбор спикеров — `[H] GLO_CampfireMoments.txt:128-366`); `DB_CampNight_IVB`;
  `DB_CampNight_CRD(night, char, dialog, flag)` (`:1350-1505`); `DB_CampNight_SoloDream(night, char, dialog)`,
  `DB_CampNight_AvatarDream`, `DB_CampNight_SCO`, `DB_CampNight_RomanceNight`, утренние `MorningCFM/MorningIVB`
  (`:1507-2400`).
- Флаги присутствия из `DB_OriginCampFlags`: `BASE` (в лагере), `AVATAR`, `COMPANION`, `PARTY`, `CAMP`
  (`:2757-2946`) — ими пишутся требования ночей. Флаги размера отряда `CAMP_PartySize_AtLeast2..4`.
- Вынужденные ночи при смене уровня: `DB_CampNight_ForceOnLevelSwap` (`[GD] GLO_FallbackCamp_Gustav.txt`).

### 5.4 Бантер

Отдельного Osiris-выбора бантера нет. Скрипты регистрируют триггеры `PROC_RegisterWorldGossipTrigger`
(напр. `S_PartyBanterTrigger_*`, `[G] Act1_CHA_Chapel.txt:2320-2330`); при входе игрока
(`[H] GLO_WorldGossip.txt:30-110`, кулдаун 60 с, блок 20 с после AD) движок сам выбирает диалог:
**`FindGossipWorld(Player, dialog, type)`** + `GetGossipSpeaker(dialog, idx, speaker)`. Список и условия
бантеров — в данных (`Dialogs/Companions/Party_Banter/PB_*.lsj`, 425+60 файлов; **[проверить]** ресурсы
Gossip в `Public/*`, не распакованы). Чтобы Альфира участвовала, нужны новые PB-диалоги и записи gossip —
это данные, не Osiris.

### 5.5 Реакции на события мира

- Реплики в сюжетных диалогах — узлы с проверкой тегов/флагов внутри самих диалогов (данные).
- Нападение на компаньона: `QRY_PartyMemberAttackedDialog` — для `DB_Origins` общий
  `GLO_Companion_PAD_Warning_Assault`, иначе `GEB_PartyMember_AD_Warning_Assault` (`[G] GLO_PartyDisturbanceReactions.txt`).
- Убийства фракций: `DB_CompanionCaredFaction` (§5.1). Пример: Уилл −10 за тифлингов, но
  `DB_CompanionCaredFaction_IgnoredNPC(Wyll, Alfira)` (`[GD] Act1_OriginMoments_Wyll.txt:4-6`).
- Topical greetings: `DB_TopicalGreeting(flag)` + `PROC_TopicalGreeting_UnlockTopic` (Minsc `:44-45,156-168`).

---

## 6. Что сломается, если Альфира в отряде

«Опасно» = двигает/телепортирует/меняет фракцию, диалог или убивает.

### Акт 1

| Файл | Что делает | Риск |
|---|---|---|
| `[G] Act1_DEN_TieflingBard.txt:4,21` | INIT: `DB_Dialogs(DEN_TieflingBard_Bard)`, `Use(BardSeat)`; реакции на пение, `DEN_ALFIRA_PROFICIENCY` | низкий; снять `DB_Dialogs`/привязку к сиденью при вербовке |
| `[G] Act1_DEN_Misc.txt:197,416` | `DB_DEN_NPC(Alfira,"Hideout",…)`, трупы при резне тифлингов | **высокий**: роль в штурме Рощи; снять `PROC_DEN_RemoveFromDenNPCs(Alfira)` |
| `[G] Act1_DEN_AttackOnDen.txt:310,877,3115-3132` | в списке уходящих NPC; условие старта; **`Die(Alfira)`** в `PROC_DEN_AttackOnDen_KillKids`; AD «защищает детей» | **высокий** |
| `[G] Act1_DEN_DruidAttack.txt:55` | роль «Cower» при нападении друидов | средний |
| `[G] Act1_CAMP_GoblinHuntCelebration.txt:48` | праздник: её сцена + дублёр `S_CAMP_TieflingBackup_001` | средний; **[догадка]** дублёр подменяет её, если недоступна |
| `[G] Act1_GLO_LevelTravelers.txt:37` | Anubis-конфиг `DEN_Bard` при входе в уровень | средний: NPC-поведение на партийце |
| `[GD] Act1_ORI_DarkUrge.txt` | весь DU-сценарий (§2.3): переписывает её origin-БД, `Initialize`+`MakeNPC`, телепорт в лагерь, смерть; **`MakeNPCHook` ставит `DEN_Bard_InParty` в любой игре** | **критический** для DU; в не-DU — порча диалога при увольнении |
| `[GD] BG3_Act1_SavegamePatches.txt:7505-7532` | при загрузке старых (< Patch 8) сейвов | низкий |
| **`[GD] BG3_Act3_SavegamePatches.txt:6060-6095` (GUSX-11941)** | **на каждой загрузке** (`[GD] BG3_SavegamePatchHelpers.txt:394-398`): если `DB_Players(Alfira)` и ночь убийства DU завершена → `CompanionLeavePermanently` + `Die` | **критический** для DU |
| `[GD] Act1a_Camp_PostEA.txt:404-410` | определение ночи `NIGHT_DarkUrge_MurderOfAlfira` | DU |
| `[G] Act1_GLO_Backgrounds_Goals.txt:1707` | цель фона при убийстве DU | DU |

### Акт 2 (Последний Свет, Лунные Башни, эпилог акта)

| Файл | Что делает | Риск |
|---|---|---|
| `[GD] Act2_HAV_TieflingSurvivors.txt:7,304-316` | `DB_HAV_TieflingSurvivors("Base", Alfira, …)` → **`SetFaction(Act2_HAV_TieflingSurvivors)`, стирание диалогов, `DB_Dialogs(HAV_AlfiraTale_Bard)`, `TeleportTo`, `SetLevel(4)`** | **критический** |
| `[GD] Act2_GLO_LevelTravelers.txt:16` | Anubis `HAV_Bard` | средний |
| `[GD] Act2_HAV_SavingPrisoners.txt:730-755` | `QRY_SelectCustomDialog_AfterGenerics(Alfira)` → встреча с Лакриссой **перехватывает её InParty** | высокий |
| `[GD] Act2_HAV_Journal.txt:395-413,533` | награды за спасённых | низкий |
| `[GD] Act2_HAV_General.txt:43`, `Act2_HAV_ShadowSiege.txt:61`, `…_Combat.txt:50`, `Act2_HAV_TakingIsobel_InnAttack.txt:17` | общие тифлинги, осада (роль в рое нежити), нокаут при похищении Изабель | высокий |
| `[GD] Act2_SCE_TieflingFollowUp.txt:7,13,19,28,143-218,292-297` + `Act2_SCE_EndBrief.txt:213-222,393-406` | «Дебриф» конца акта: участник-партиец **выводится из отряда** (`MakeNPC`) и уводится на точку `S_SCE_AlfiraPoint` с диалогом `SCE_Alfira`; назад в лагерь только в `INT_Main_A` (`[GD] Act2b_CAMP.txt:245-259`) | высокий, но есть готовый механизм возврата |

### Акт 3 и эпилог

| Файл | Что делает | Риск |
|---|---|---|
| `[GD] Act3b_LOW_ElfsongTavern.txt:116,492-516` | в INIT goal'а `PROC_LOW_AlfiraSetup`: **`TeleportTo` на крышу «Песни эльфов», `SetFaction(ACT3_LOW_ElfsongTavern)`, `PROC_RemoveDialog`, `DB_Dialogs(LOW_Elfsong_Alfira)`, выдаёт лютню** (при `DEN_TieflingRefugees_State_LeftDen`) | **критический**; PROC нельзя отменить — только исправлять после |
| `[GD] Act3b_LOW_ElfsongTavern.txt:519-593` | выступление, Anubis Лакриссы, `QRY_SelectCustomDialog(Alfira)` → перехват диалога | высокий |
| `[GD] Act3b_GLO_LevelTravelers.txt:28`, `BG3_Act3b_SavegamePatches.txt:11068-11070` | Anubis `LOW_Alfira` | средний |
| `[GD] Act3c_EPI_Letters.txt:444-472`, `[HGD] Act3c_EPI_Gazettes.txt:118,298` | письма/газета эпилога по `DB_PermaDefeated`/`DB_Dead` | низкий (текст противоречит «спутнице») |
| `[GD] Act3c_EPI_MainEpilogue.txt:560-570,1105-1115,1860-1870,2490-2500` | эпилог работает по `DB_Origins`/`DB_PartOfTheTeam` | только если внесём в `DB_Origins` |
| `[GD] GLO_Achievements_Gustav.txt:134` | достижение «спасти тифлингов» | низкий |

Общие: `DB_GLO_LevelTraveler` применяется на `EnteredLevel` любому персонажу из списка
(`[HG] GLO_LevelTravelers.txt`) — снимать `NOT DB_GLO_LevelTraveler(...)` после вербовки.

---

## 7. План milestone 1

Цель: Альфиру можно завербовать, она входит/выходит из отряда, уходит в лагерь и возвращается, растёт в
уровне, с ней можно поговорить.

### 7.1 Подход: Osiris-goals в моде, Script Extender — только для отладки

- Мод поставляет `Mods/_MOD_/Story/RawFiles/Goals/*.txt`; игра компилирует их вместе с
  ванильными (именно поэтому ванильные goals лежат в паках в виде txt). **[проверить]** что новый goal
  инициализируется (выполняется INITSECTION) при загрузке уже существующего сохранения.
- Почему Osiris, а не Lua: вся интеграция — это **расширение чужих PROC/QRY** (`PROC_GLO_PartyMembers_AddHook`,
  `PROC_GLO_PartyMembers_MakeNPCHook`, `QRY_Camp_GetCamperPos_Custom`, `QRY_SelectCustomDialog`) и реакции на
  вставку фактов в БД. В Osiris это просто ещё одно правило с тем же именем. SE умеет вызывать `Osi.*` и
  слушать события, но **не может добавить ветку QRY** и отменить чужое правило; плюс лишняя зависимость
  для игроков.
- SE (`Osi.PROC_GLO_PartyMembers_Add(...)`, `Osi.DB_Players:Get(nil)`) — удобная консоль для проверок.

### 7.2 Состав

1. `ALFSV_Companion.txt` (без `ParentTargetEdge` или под `__Start` — **[проверить]** что надёжнее).
   INIT (все факты идемпотентны):
   ```
   DB_CompanionOnlyFaction((CHARACTER)S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c, (FACTION)Companion15_9a7c52c8-ca88-4493-bca5-9b917494c94c); // [проверить] свободна
   DB_OriginNPCAlignment(S_DEN_Bard_…, (FACTION)ACT1_DEN_TieflingBard_082ce2e1-e636-4a56-817c-af798bdc59d8);
   DB_OriginPartOfTheTeamFlag(S_DEN_Bard_…, (FLAG)GLO_Origin_PartOfTheTeam_Alfira_f5d7c888-ccce-4a30-a0a8-6ac0c9f4c094, (FLAG)NULL_…, (FLAG)ORI_Alfira_ControlledByUser_e7f05e38-3c03-4e6d-9649-936d7fdfd8e9);
   DB_OriginKickFromPartyFlags(S_DEN_Bard_…, (FLAG)ORI_Alfira_Event_KickCompanion_23496e30-47fd-47a2-aa6d-8f2e71820e84, (FLAG)ORI_Alfira_State_CanBeKicked_a6499b8c-0908-463e-a9b7-ca0350820f1c);
   DB_ORI_OriginCampData(S_DEN_Bard_…, "CREMAIN"/"CREINSIDE"/"INTMAIN"/"FARM"/"SLUMS"/"ELFSONG", <триггер>); // временно — hireling-слот 3 из DB_Hirelings_CampPositions [догадка, конфликт при 3 наёмниках]
   ```
   `DB_OriginInPartyDialog` ставить **в момент вербовки**, а не в INIT: наличие InParty у NPC меняет
   ветки `QRY_Origin_GetRecruitmentDialog`/DU-логики.
2. Новый диалог `ALFSV_Alfira_InParty` (данные): «Пойдём со мной» (`!ORI_State_Recruited`; вложенный
   `GLO_CompanionSwap_Recruitment` при `GEN_MaxPlayerCountReached`; ставит `OriginAddToParty`),
   «Жди в лагере» (`ORI_State_Recruited`, `!GLO_Origin_BlockWaitInCampOption`; ставит
   `OriginRemoveFromPartyAfterDialog`), пара реплик. Образец — `Minsc_InParty` (узлы N638/N651).
3. Вход в вербовку без правки ванильного диалога Альфиры: `QRY_SelectCustomDialog(Alfira, Player)`
   при нашем условии (напр. после завершения её квеста песни/по флагу) → `DB_SelectedDialog(ALFSV_Alfira_Recruit, …)`.
   Плюс отладочный `TextEvent("alfc_recruit")`.
4. Правила KB:
   - `PROC_ALFSV_MakeCompanion()` (один раз, до первого `OriginAddToParty`): `DB_OriginInPartyDialog`,
     `PROC_GLO_PartyMembers_Initialize(Alfira)`, `PROC_DEN_RemoveFromDenNPCs(Alfira)`,
     `NOT DB_GLO_LevelTraveler(Alfira, …)` для трёх ванильных записей, `DB_ALFSV_IsCompanion(1)`.
   - `PROC_GLO_PartyMembers_AddHook(Alfira,_)` + `QRY_OnlyOnce("ALFSV_FirstRecruit")` →
     `PROC_ORI_SetupCamp(Alfira, 0)`; флаг «встречались».
   - Ремонт DU-хука: `IF DB_Dialogs(Alfira, DEN_Bard_InParty…) AND DB_ALFSV_IsCompanion(1) AND NOT DB_ORI_DarkUrge(_)
     THEN NOT DB_Dialogs(Alfira, DEN_Bard_InParty…); PROC_GLO_PartyMembers_SetInpartyDialog(Alfira, ALFSV_Alfira_InParty)`
     (реакция на вставку факта — не зависит от порядка правил `MakeNPCHook`).
   - Блокировка акт-2 ролей реактивно: `IF DB_HAV_TieflingSurvivors(_, Alfira, _, _, _) AND DB_PartOfTheTeam(Alfira)
     THEN NOT DB_HAV_TieflingSurvivors(...)`; аналогично `DB_HAV_General_Tieflings`, `DB_HAV_Siege_NPCs`,
     `DB_HAV_TakingIsobel_KOParticipants`, `DB_SCE_Debrief_Participant`, `DB_SCE_TieflingFollowUp_Tieflings`,
     `DB_GLO_LevelTraveler`. **[проверить]** что правило нашего goal срабатывает на факты из INIT
     вновь инициализируемого актового goal'а.
   - Акт 3: `PROC_LOW_AlfiraSetup` отменить нельзя → после `LevelGameplayStarted("CTY_Main_A",_)` при
     `DB_PartOfTheTeam(Alfira)` вернуть фракцию/диалог/позицию (в отряде — `DefaultFaction`), убрать
     `QRY_SelectCustomDialog`-перехват нельзя — только добавить свой более ранний ответ… **[проверить]**
     (для milestone 1 можно ограничиться актом 1).
   - Одобрение (опционально в M1): стартовый бонус по образцу Minsc `:210-228`.
5. Уровень: ничего писать не нужно — `Add` сам вызывает `RequestInitialLevel`. **[проверить]** шаблон
   Альфиры: класс/прогрессия, `BLOCK_LEVELUP`, иначе левел-ап/респек у Withers не сработают.

### 7.3 Порядок проверки

1. Не-DU игра, акт 1, после квеста с песней: вербовка → в отряде (портрет, управление, уровень = отряду).
2. «Жди в лагере» → идёт на `S_ORI_DarkUrge_AlfiraPosition_*` активного лагеря; разговор в лагере → снова в отряд.
3. Полный отряд → swap-диалог, опция «Альфира» (ванильный kick-флаг).
4. Смерть в отряде → Withers воскрешает через общий слот.
5. Перезагрузка сейва (проверка GUSX-патчей и идемпотентности INIT).

### 7.4 Риски

- **Темный Соблазн:** сценарий убийства переписывает её origin-БД и убивает; патч GUSX-11941 убивает её
  при загрузке. В M1 — запретить вербовку при `DB_ORI_DarkUrge(_)` (или до `ORI_DarkUrge_State_*`).
- **`DB_Origins`**: не добавлять в M1. Даст Withers-в-лагере и эпилог, но включит тадпол-исключения,
  эпилоговую выдачу/скрытие (`PROC_EPI_Epilogue_RemoveAndHideNPC` для незавербованных `DB_Origins`),
  случайный выбор спикера в DU-CFM, квест `CompanionMurdered`, `PROC_GLO_DataGetOriginTags` для не-ориджина
  (**[догадка]** `IterateOriginTags` для неё пуст).
- Фракция: без `DB_CompanionOnlyFaction` она в отряде остаётся в NPC-фракции (как в DU-заготовке) —
  возможны проблемы с преступлениями/враждебностью.
- Сюжетные перехваты диалогов (`QRY_SelectCustomDialog*`) в актах 2–3 и телепорты из §6.
- Удаление мода: в сейве останутся `DB_Players(Alfira)`, её факты; нужна процедура «отпустить навсегда»
  (`PROC_Origins_CompanionLeavePermanently` или возврат к ванильным ролям) до удаления.
- Одобрение/бантер/реакции в чужих диалогах — ресурсы данных (ApprovalRatings, Gossip), не Osiris.

---

## Приложение: движковые вызовы, встреченные в разборе

`MakePlayer`, `MakeNPC`, `RegisterAsCompanion`, `UnregisterAsCompanion`, `AssignToUser`, `DetachFromPartyGroup`,
`GetMaxPartySize`, `RequestInitialLevel`, `SetLevel`, `StartRespec`, `ChangeApprovalRating`, `GetApprovalRating`,
`RemoveApprovalRating`, `TransferItemsToCharacter`, `TransferItemsToUser`, `MoveAllItemsTo`, `MoveAllStoryItemsTo`,
`StartHenchmen`/`HenchmanSelected`, `DismissAvatar`, `FindGossipWorld`/`GetGossipSpeaker`, `SetHasDialog`,
`SetNoFollowFlag`, `SetBlockDismiss`, `EnableSendToCamp`. События: `ApprovalRatingChangeAttempt`,
`ApprovalRatingChanged`, `ForceDismissCompanion`, `CharacterMadePlayer`, `CharacterLeftParty`,
`TeleportedToCamp`/`TeleportedFromCamp`, `Resurrected`, `SavegameLoaded`.
