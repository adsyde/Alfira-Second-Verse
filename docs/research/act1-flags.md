# Акт 1: флаги и события для реакций Альфиры и глав разговоров

Исследование по распакованным данным игры (Patch 8 Hotfix 9), `game-data/`. Проводилось только чтение, ничего не коммитилось.
Сокращения путей:
- `[G]` — `Gustav/Mods/Gustav/Story/RawFiles/Goals/`
- `[GD]` — `Gustav/Mods/GustavDev/Story/RawFiles/Goals/`
- `[H]` — `Patch8_HotFix9/Mods/Shared/Story/RawFiles/Goals/`
- `[S]` — `Shared/Mods/Shared/Story/RawFiles/Goals/`
- `Dlg:` — диалог `Gustav/Mods/*/Story/Dialogs/**/<имя>.lsj`

Столбец «Usage» — поле `Usage` в `Public/*/Flags/<uuid>.lsx`. Это битовая маска: 1 = Global, 2 = User, 4 = Object. Например, 5 = Global+Object. Чем флаг ставится на самом деле (глобально или на персонажа), видно по вызову `SetFlag(X, NULL_…)` или `SetFlag(X, _Player)` в goal либо по типу flaggroup в диалоге. Это указано отдельно.

Уверенность:
- ✅ — проверено в данных (правило в goal или узел в диалоге);
- 🟡 — частично: флаг найден, но есть оговорки;
- ❔ — предположение;
- ❌ — в игре нет ничего пригодного.

---

## 0. Как ванильные спутники реагируют и как проверить «Альфира рядом»

**Одобрение ванильных спутников почти всегда записано в данных диалога, а не в Osiris.** У узла диалога есть поле `ApprovalRatingID`. Оно указывает на ресурс `Gustav/Public/GustavDev/ApprovalRatings/Reactions/<uuid>.lsx` со списком «id спутника → величина». Движок применяет эту величину к спутникам, которые участвуют в диалоге. Вызовы `ChangeApprovalRating` из Osiris в акте 1 редки. Всего их три:
- `[G] Act1_ORI_Gale.txt:325-355` (Гейл, «моменты доверия»);
- `[G] Act1_PLA_GithChokepoint.txt:1356-1365` (Лаэ'зель);
- `[G] Act1_FOR_Boosters.txt:451-464, 622-635` (Шэдоухарт).

Id спутников в Reactions я вывел частотным анализом `*_InParty*.lsj`:

| Спутник | Id |
|---|---|
| Астарион | `3780c689-d903-41c2-bf64-1e6ec6a8e1e5` |
| Гейл | `35c3caad-5543-4593-be75-e7deba30f062` |
| Лаэ'зель | `fb3bc4c3-49eb-4944-b714-d0cb357bb635` |
| Шэдоухарт | `2bb39cf2-4649-4238-8d0c-44f62b5a3dfd` |
| Уилл | `efc9d114-0296-4a30-b701-365fc07d44fb` |
| Карлах | `b8b4a974-b045-45f6-9516-b457b8773abd` |
| Хальсин | `a36281c5-adcd-4d6e-8e5a-b5650b8f17eb` |
| Джахейра | `c1f137c7-a17c-47b0-826a-12e44a8ec45c` |
| Минск | `e1b629bc-7340-4fe6-81a4-834a838ff5c5` |
| Минтара | `eae09670-869d-4b70-b605-33af4ee80b34` |

❔ **Id одобрения Альфиры в диалогах:** `38357c93-b437-4f03-88d0-a67bd4c0e3e9`. Он встречается в Reactions ванильного `DEN_Bard_InParty.lsj` (ветка Тёмного соблазна, +5), всего в 4 ресурсах. Где определено, что этот id означает Альфиру, я не нашёл: вероятно, в непрочитанном `.lsf`. Если подтвердится, наши диалоги смогут давать одобрение через `ApprovalRatingID` так же, как ванильные. Дописывать Альфиру в чужие Reactions не советую: это переопределение ванильных файлов.

**Три способа проверить в Osiris, была ли Альфира рядом.** Все три взяты из ванили:

| Способ | Когда подходит | Образец в игре |
|---|---|---|
| A. `FlagSet(F, _Char, _Inst)` + `DB_DialogSpeakers(_Inst, S_DEN_Bard_…, _)` | флаг ставит узел диалога; Альфира — участник диалога | `[G] Act1_ORI_Gale.txt:326-341`. Если Гейла в диалоге нет, одобрение идёт отложенно на `DialogEnded` (`:343-355`). `DB_DialogSpeakers` ведёт `[S] ZZZ_LastGoal.txt:60-65` |
| B. `DB_Players(Альфира)` + `QRY_SpeakerIsInDialogRange(_Avatar, Альфира)` или `DB_InRegion(Альфира, <триггер>)` / `QRY_DEN_IsInDen(Альфира)` | глобальный флаг состояния мира (бой, итог квеста) | `[H] _GLO_Shared_Origins.txt:700-704` (`QRY_GetBestAvatarForCompanion_CheckNearby`); `[G] Act1_DEN_Misc.txt:477-499` (`QRY_DEN_IsInDen`) |
| C. Только `DB_PartOfTheTeam(Альфира)`, без проверки «рядом» | «убийство тех, кто ей дорог» | `[H] _GLO_Shared_Origins.txt:2826-2847`: `DB_CompanionCaredFaction` → `PROC_ChangeApprovalRatingForAllAvatars`. У Уилла −10 за убийство тифлингов: `[GD] Act1_OriginMoments_Wyll.txt:4-6`, Альфира там исключена через `_IgnoredNPC` |

Одобрение даётся функцией `ChangeApprovalRating(Альфира, _Avatar, 0|1, N, _)`. Мод уже так делает: `mod/.../ALFSV_Companion.txt`, по образцу Джахейры. Для всех аватаров есть готовая процедура `PROC_ChangeApprovalRatingForAllAvatars(char, N)` (`[H] _GLO_Shared_Origins.txt:2849-2855`).

**Состояния Рощи хранятся без флагов.** Состояние лежит в `DB_State_Current(S_DEN_RangerDen_SUB_50062397-bf9c-4765-9cbc-e40b5148f211, "DEN", <state>)`. Переходы отдаются хуком `PROC_State_Changed(S_DEN_RangerDen_SUB_…, "DEN", "<state>")`, и наш goal может его перехватить. Список состояний и приоритеты: `[G] Act1_DEN_Misc.txt:43-59`.

---

## Задача A — реакции на поступки (design/APPROVAL.md §5)

### A1. Защитить тифлингов при налёте гоблинов

Сначала разберёмся, о каком налёте речь. Налётов два.
- **Налёт у ворот при первом приходе к Роще** (`[G] Act1_DEN_RaidingParty.txt`): флаг `DEN_RaidingParty_Quest_GoblinRaidOver` `98712d90-c46b-20c4-c4df-02c0117e85a5` (Global), ставится в `:733-737`. Этот бой идёт до встречи с Альфирой, спутницей она тогда быть не может. Для реакции он не годится.
- **Нападение Минтары на Рощу («Attack on Den»)** начинается, если игрок выдал гоблинам Рощу. Это и есть нужный случай.

| Флаг / событие | UUID | Usage / как ставится | Где и когда | Уверенность |
|---|---|---|---|---|
| `DEN_AttackOnDen_Event_Start` | `c641da6a-b3f5-4873-bd34-c53768d30d6f` | 5 / Global | начало нападения, `[G] Act1_DEN_AttackOnDen.txt:850` | ✅ |
| `DEN_AttackOnDen_State_DenVictory` | `71c7f23e-3ff1-c9b8-3ef5-d75fa1b42c8d` | 5 / Global | все рейдеры побеждены при `UnderAttack` и без `HostileTieflings`, `[G] Act1_DEN_AttackOnDen.txt:2487-2502` | ✅ |
| ⚠️ Тот же `DenVictory` | | | **ставится и после «Охоты на гоблинов»** (убиты три лидера лагеря), см. комментарий Larian в `[G] Act1_DEN_TieflingRefugees.txt:400` | ✅ |
| Правильная проверка «отбили налёт» | | | `DB_GlobalFlag(DEN_AttackOnDen_Event_Start)` **И** `DenVictory`. Так проверяет и сама игра: `[G] Act1_DEN_AttackOnDen.txt:456-465` (цель предыстории `Act1_HauntedOne_SidedAgainstGoblins`) | ✅ |
| Противоположный исход: `DEN_AttackOnDen_State_RaiderVictory` | `abe1bce8-c234-4afe-a490-76210d98a078` | 5 / Global | Роща пала, `[G] Act1_DEN_AttackOnDen.txt:3036, 3588` | ✅ |
| Игрок открыл ворота: `DEN_AttackOnDen_State_HostileTieflings` | `c5641caa-4409-4739-a1fe-8263b8271f4e` | 5 / Global | `:1324, 2324` | ✅ |

- **Рядом ли Альфира.** Бой идёт в Роще, поэтому подходит `QRY_DEN_IsInDen(S_DEN_Bard_…)` (способ B). Игра так же проверяет игроков в `:448-454`.
- **Ваниль для ориентира.**
  - `Dlg: DEN_AttackOnDen_RaidersArriveBeforeFight`: отказ Минтаре — Гейл/Уилл/Карлах +5; «открыть ворота» — Гейл −5, Уилл/Карлах −10.
  - `DEN_AttackOnDen_TieflingVictory`, приветствие Зевлора после боя: Гейл +10, Уилл +15, Карлах +10, Шэдоухарт +1.
  - `DEN_AttackOnDen_TieflingLeader` / `_Trainer`, ответ «я с ними»: Астарион +5, Гейл/Уилл/Карлах −10.

### A2. Остановить ритуал Каги (тифлингов не выгоняют)

| Флаг / событие | UUID | Usage / как | Где и когда | Уверенность |
|---|---|---|---|---|
| `PROC_State_Changed(S_DEN_RangerDen_SUB_…, "DEN", "DEN_State_RitualStopped")` | — | хук | Кагу разоблачили письмом: `FlagSet(DEN_ShadowDruid_Event_StartDenouncingScene)` → `[G] Act1_DEN_ShadowDruid.txt:958-965` | ✅ |
| `DEN_ShadowDruid_State_DenouncingInProgress` | `3143a5ba-c508-4a32-a2f1-8091731d83e0` | 5 / Global | ставится на этот хук, `[G] Act1_DEN_ShadowDruid.txt:967-970` | ✅ |
| `DEN_ShadowDruid_Event_StartDenouncingScene` | `e01769d4-9ac4-17a0-584e-ceb26e4bc384` | 5 / Global, из диалога | начало сцены разоблачения. Инстанс диалога есть, поэтому работает способ A | ✅ |
| `DEN_ShadowDruid_Event_KaghaTurnedGood` | `f2de839d-b971-86ee-f02c-5e09174ce919` | 5 / Global | Кагу убедили (`:172-177`) | ✅ |
| `DEN_ShadowDruid_State_KaghaKilled` | `fbf50ed0-6ebb-4306-bc5a-0a94e0a1c593` | 5 | Кага убита | 🟡 где ставится, не прослежено |
| Другой путь к той же цели — «Охота на гоблинов»: `GOB_State_LeadersAreDead` | `a1c5b01f-4b7f-47ab-82b0-d24d9c6d8bc6` | 5 / Global | → `DEN_State_GoblinHuntVictory` (`[G] Act1_DEN_TieflingRefugees.txt:331-347`) → `DEN_Refugees_State_LeadersAreDead` `1e6a42ed-8313-4f46-57e2-20dbdb2df923` (`:352-354`). Это тоже конец ритуала, и тифлинги уходят с миром | ✅ |

- **Рядом ли Альфира.** Для разоблачения — способ A по инстансу `StartDenouncingScene`. Для хука состояния — `QRY_DEN_IsInDen(Альфира)`.
- **Ваниль.**
  - `Dlg: DEN_ShadowDruid_Denouncing`: ответы на угрозу Каги — Карлах +5, Уилл/Гейл +1.
  - `DEN_TieflingLeader(_DenIntro)`, «поговорю с друидами» / «помогу»: Уилл +5, Карлах +3…+5, Гейл +1, Астарион −1.

### A3. Ритуал свершился, тифлингов выгнали

| Флаг / событие | UUID | Usage / как | Где и когда | Уверенность |
|---|---|---|---|---|
| `DEN_Lockdown_State_Active` | `0b54c7d2-b7b1-4d0f-b8e4-0cf1ee32b1eb` | 5 / Global | лозы закрывают Рощу, `[G] Act1_DEN_Lockdown.txt:120-140` (`PROC_DEN_Lockdown`) | ✅ |
| `PROC_State_Changed(…,"DEN","DEN_State_Lockdown")` → `LockdownComplete` | — | хук | `[G] Act1_DEN_Lockdown.txt:108-113` | ✅ |
| Когда наступает | | | (1) после кражи идола друиды побеждают: `DEN_State_DruidAttack` → уход игрока или долгий отдых → `DruidsHostileNoTieflings` → `Lockdown` (`[G] Act1_DEN_DruidAttack.txt:1851-1879`); (2) в Роще осталось слишком мало тифлингов: `DEN_GroveConflict_State_TooLowTieflings` `ed9fe6c4-5037-4f74-968c-a166aeb29d9c` (`[G] Act1_DEN_Misc.txt:1442-1470`) | ✅ |
| Смежный исход: `DEN_General_State_RitualStoppedNoTieflings` | `f4712c06-ae76-4ba3-87e8-a3f71d9b621c` | 5 / Global | ритуал остановлен, но тифлингов почти нет, `[G] Act1_DEN_Misc.txt:1489-1492` | ✅ |

- **Рядом ли Альфира.** Lockdown срабатывает, когда игроков в Роще нет (`NOT DB_DEN_PlayerInDen`). Поэтому проверка «рядом» здесь бессмысленна: реакция должна идти по способу C, то есть просто «она в команде».
- **Ваниль.** На сам Lockdown реакций в диалогах я не нашёл.

### A4. Спасти Арабеллу

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| `DEN_ShadowDruid_State_KidFreed` | `8d9e9065-7bb5-a516-15c3-c9d8c1f4f5e2` | 5 / Global | узел `DEN_ShadowDruid_SnakesCourt` («Out, thief…»), а также `[G] Act1_DEN_ShadowDruid.txt:118,139,292` (сцену прервали насилием и т. п.) | ✅ |
| `DEN_ShadowDruid_State_FreedChild` | `e0db3e8d-497d-33bb-ce67-91dff9fb1c67` | 4 / Object, ставится из диалога на игрока | тот же узел | ✅ |
| Противоположный исход: `DEN_ShadowDruid_State_KidDied` | `5b5de896-e733-47ae-81df-85a4b25ebfd1` | 5 / Global | `[G] Act1_DEN_ShadowDruid.txt:467` | ✅ |

- **Рядом ли Альфира.** `FreedChild` ставится из диалога, поэтому подходит способ A. Такую же пару флагов использует «момент доверия» Гейла: `[G] Act1_ORI_Gale.txt:15,21`, Гейл +8 в диалоге / +6 после.
- ⚠️ Суд змеи обычно проходит при первом входе во внутреннюю Рощу. Альфира к этому времени часто ещё не завербована, и реакция может не выпасть ни разу.
- **Ваниль (`SnakesCourt`):** «докажи милосердие» — Шэдоухарт/Уилл/Карлах +5, Лаэ'зель −1; «ничего не делать» — Уилл/Карлах −1.

### A5. Спасти Миркона от гарпий

Миркон — это `S_DEN_CharmedKid_3b92c689-6024-4446-a6c9-584e9e8d77ca`. Имя проверено по DisplayName в `Globals/WLD_Main_A`.

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| `DEN_HarpyMeal_State_HarpyEncounterOver` | `48fd55cd-a79a-8b4a-8dd6-901910b5d739` | 5 / Global | бой с гарпиями закончен, `[G] Act1_DEN_HarpyMeal.txt:684, 985` | ✅ |
| `DEN_HarpyMeal_State_HelpedSaveVictim` | `13491e5a-6381-2d8d-e015-5aae3948b794` | 4 / Object: **на каждого игрока в регионе Cove** | `[G] Act1_DEN_HarpyMeal.txt:770-776` | ✅ |
| `DEN_HarpyMeal_State_RescuedChild` | `7a90f576-f762-4710-aa4d-9a81905bd971` | 4 / Object из диалога | Миркон благодарит (`DEN_HarpyMeal_AfterHarpyEncounter`); триггер журнала `:1076` | ✅ |
| Противоположный исход: `DEN_HarpyMeal_State_VictimDead` | `50cfd9b3-bf92-e441-e166-1466dcf1e185` | 5 | Миркон погиб; дополнительно можно проверить `DB_PermaDefeated(S_DEN_CharmedKid_…)` | 🟡 |

- **Рядом ли Альфира.** Самый удобный вариант — `GetFlag(DEN_HarpyMeal_State_HelpedSaveVictim, S_DEN_Bard_…, 1)`. Игра сама ставит этот флаг всем `DB_Players` на пляже, то есть «она была там» получаем даром.
- **Ваниль:** Гейл через «момент доверия» `[G] Act1_ORI_Gale.txt:22` (+8/+6); грубость к Миркону — Уилл/Карлах/Гейл −1. Эпизод тоже часто бывает до вербовки.

### A6. Майрина и Тетушка Этель

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| **Сделка (плохо).** `HAG_Hag_State_HagTookMother` | `38dc6752-5ab3-e108-64ed-fe63971d69fd` | 5 / Global из диалога | `Dlg: HAG_HagLair_HagBegsForMercy`: «Оставь девушку, дай силу»; `[G] Act1_HAG_HagLair_Combat.txt:976, 1169` | ✅ |
| `HAG_Hag_State_HagGaveReward` | `72881644-628d-0a3f-4de1-3f6dce1078b7` | 5 / Global | тот же диалог; при варианте «сила + отпустить Майрину» стоит вместе с `SurrogateReleased` | ✅ |
| **Спасение.** `HAG_HagSpawn_Quest_SurrogateReleased` | `dafa0dd7-c2bb-be04-6881-ed81a87373fd` | 5 / Global из диалога | «Отпусти Майрину» в `HagBegsForMercy` | ✅ |
| Спасение через смерть Этель: `HAG_Hag_State_IsDead` | `781391e2-7d33-642d-28c0-e9b06cde32bb` | 5 / Global | `DB_DeadOnceFlag`, `[G] Act1_HAG_Hag.txt:9`. Дополнительно проверить `NOT DB_Dead(S_HAG_Hagspawn_SurrogateMother_08c970d7-3138-45e8-8965-68eadf4b07cd)` | 🟡 |
| Смерть Майрины: `HAG_Hagspawn_Quest_SurrogateMotherDead` | `746ee170-d126-42bd-bf44-ba27c6a8d718` | 5 | | 🟡 |

- **Рядом ли Альфира.** Флаги ставятся из диалога, поэтому подходит способ A (`FlagSet(..., _, _Inst)` + `DB_DialogSpeakers`).
- **Ваниль (`HagBegsForMercy`):**
  - «оставь девушку, дай силу»: Астарион +5; Гейл −5, Уилл −5; Шэдоухарт −1, Карлах −1;
  - «отпусти Майрину»: Гейл +1, Карлах +1; Астарион −5;
  - «убить ведьму»: Шэдоухарт +5; Гейл/Лаэ'зель/Уилл/Карлах +1; Астарион −5.
- Ещё одна «сделка» — «You have a deal» в `HAG_Hagspawn_StartScene`: Лаэ'зель −5, Шэдоухарт −5. Она ставит только квестовый флаг `edc0fec1-acae-46c9-a7ea-4871a4a80ea2` [Q] и в Osiris не ловится ❔.

### A7. Пощадить Карлах, выслушать её

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| Первая встреча: `ORI_Karlach_HasMet` | `50a43cde-0702-4c2a-a490-e9ee5f061f45` | 5 / Global | ставит диалог `PLA_KarlachRecruitment_Karlach_PostEA`; ещё раз при первой вербовке, `[G] GLO_Origin_Karlach.txt:48-55` | ✅ |
| Согласился помочь: `PLA_KarlachRecruitment_State_HelpingKarlach` | `b7cd48bc-b9e3-419e-8ad0-c4837bc0cec0` | Global из диалога | тот же диалог | ✅ |
| Обещал помочь без вербовки: `ORI_Karlach_Quest_AgreedToHelpNotRecruited` | `f08dc12e-cb2e-e373-e2eb-b0d2c7b0d7dc` | Global из диалога | тот же | ✅ |
| Вербовка | — | `FlagSet(OriginAddToParty, S_Player_Karlach_2c76687d-…, _)` или `PROC_GLO_PartyMembers_AddHook(S_Player_Karlach…, _)` | `[G] GLO_Origin_Karlach.txt:48` | ✅ |
| Нападение (плохо): `PLA_KarlachRecruitment_Event_KarlachHostile` | `cb16919b-08da-485c-a9df-7911ba1572d1` | Global из диалога | | ✅ |
| Убийство: `PLA_KarlachRecruitment_State_KilledKarlach` | `ee2f4a40-6290-4a2b-ba3a-54da7dc3f69f` | `DB_KilledEvent` | `[G] Act1_PLA_KarlachRecruitment.txt:6`; окончательно — `GLO_Karlach_State_Dead` `26f3c3b0-a9c8-40d6-8950-67c9b8e134e2` (`:345`) | ✅ |
| Сдал голову паладинам: `PLA_KarlachRecruitmentTollhouse_Event_GiveHead` | `d4e8a331-084c-42b7-a2b3-99e587f8679e` | | `[G] Act1_PLA_KarlachRecruitment.txt` | 🟡 |

- **Рядом ли Альфира.** Диалог собирает всех из триггера: `DB_AddCharactersInTriggerToDialog(PLA_KarlachRecruitment_Karlach_PostEA_0f598b1a-b8b9-10cf-4d0d-0cd958586f61, S_PLA_KarlachRiverSpot_IncludePlayers…, 1, 0)`, `[G] Act1_PLA_KarlachRecruitment.txt:26`. Значит, `DialogEnded(PLA_KarlachRecruitment_Karlach_PostEA_0f598b1a…, _Inst)` + `DB_DialogSpeakers` работают (способ A).
- **Ваниль.** В PostEA-версии диалога реакций нет. В старом `PLA_KarlachRecruitment_Karlach.lsj` доверие Карлах даёт Гейлу/Шэдоухарт/Уиллу +1, «Attack» — Лаэ'зель +1.
- Слова «выслушать её (Аверно)» относятся к нашим диалогам. Отдельного флага «выслушал историю» в акте 1 нет.

### A8. Вызволить Воло из лагеря гоблинов

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| `GOB_VoloBallad_State_VoloEscaped` | `13ae819f-b0b7-434d-9ebb-cee412b1a407` | 5 / Global | `PROC_GOB_VoloBallad_MoveVoloToCamp`, `[G] Act1_GOB_VoloBallad.txt:810-814` | ✅ |
| `GLO_Volo_State_AtCamp` | `de1cadca-2eca-4cee-a3dc-e262bbb92277` | 5 / Global | тот же PROC, `[G] _Gustav_CampFollowers.txt:67-73` | ✅ |
| Защита от ложного срабатывания: `GOB_VoloBallad_State_PlayersMetVolo` | `0c341094-ae74-4a72-b2b6-3cd98a43ae11` | 5 / Global | `[G] Act1_GOB_VoloBallad.txt:838`. MoveVoloToCamp вызывается и отладкой (`DebugTeleportedToCamp`) | 🟡 |

- **Рядом ли Альфира.** Воло попадает в лагерь после долгого отдыха (`:795-801`), поэтому достаточно способа C. Если нужен именно момент спасения, возьмите диалог охранника `GOB_VoloBallad_Guard…` по способу A (не прослеживал).
- **Ваниль.** На спасение реакций нет. «Boo! Get off the stage!» Воло даёт Астариону/Лаэ'зель +1, Карлах −1.

### A9. Освободить пленников в Гримфордже (глубинные гномы у дуэргаров Нере)

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| `UND_State_LeaderFreedGnomes` | `49acb531-d0c4-d3d1-6af4-c79e246e4327` | 5 / Global | после боя Нере, все дуэргары побеждены, рабочие живы: `[G] Act1_UND_DuergarCamp_Excavation.txt:1343-1354`; квест `UND_GnomeRescue` → `DealtWithSlavers` (`:132`) | ✅ (прослежена одна ветка PROC) |
| `UND_GnomeWorkers_Event_Leave` | `ad897c6f-87d5-4a30-88f0-41c92b965bc8` | 5 / Global | гномы уходят свободными (`Left_Freed`), `:1377-1381` | ✅ |
| Встал на сторону мятежников: `UND_DuergarCamp_State_SidedMutineers` | `581443f0-b4bd-d3c2-7122-a4d2aa7fb5f9` | 5 / Global из диалога | `Dlg: UND_TheDrowNere_Mutiny` | ✅ |
| Плохо: `UND_TheDrowNere_State_GnomesExecuted` | `7f3f882c-40fb-430e-8df6-c1d6e450aebd` | 5 / Global | `:1001-1008`; «Attack the deep gnomes» → `UND_DuergarCamp_State_GnomesHostile` `53aab2ec-c119-b4ed-c3b2-7181e4ecbaf7` | ✅ |

- **Рядом ли Альфира.** Для флагов из диалога Нере — способ A. Для глобальных итогов — `DB_InRegion(Альфира, S_UND_DuergarCamp_SUB_05c3bf1f-29a6-437c-9a98-c1ff0ec53a53)`.
- **Ваниль (`UND_TheDrowNere_Mutiny`):**
  - «Stop! No more innocents»: Уилл +5, Карлах +5;
  - «Finish the slaves» / «Say nothing»: Уилл −5, Карлах −5;
  - «Attack the deep gnomes»: Уилл −5, Карлах −5.

### A10. Жестокость к пленным, пытки

| Эпизод | Флаг / событие | UUID | Как | Где | Уверенность |
|---|---|---|---|---|---|
| Пытка пленника в лагере гоблинов | `GOB_Torturers_Assisted` | `aee96e28-e049-0e55-b5d8-c001580de642` | Usage 6; `FlagSet(…, _Player, _Instance)` | `Dlg: GOB_Torturers_Torture` (ответы «Trim toenails / Crack kneecaps / poker / spear-butt»); `[G] Act1_GOB_HappyTorturers.txt:178-185` | ✅ |
| то же | `GOB_TorturedAdventurer_Event_SoftOption` / `_HardOption` | `351539cc-1601-f5ba-d55d-515b8bd79993` / `26cf8dbf-0110-0681-bfff-f874c5b2dc07` | на пленника `S_GOB_TorturedAdventurer_0dd6e9f1…` | `:437` | ✅ |
| то же (побочный признак) | `GLO_PaladinOathbreaker_Event_BrokeOath` | `0246da96-5ef8-4c65-9f0d-c2856bd17674` | Object, на игрока | ставится теми же узлами пытки | ✅ |
| Бросать камни в медведя-Хальсина (загоны) | `GOB_WolfPens_Event_ThrewRock` | `9af39233-b6e9-4279-b3ca-d68163b240bc` | 5 / Global из диалога | `Dlg: GOB_WolfPens_GroupDialogWithBear` | ✅ |
| то же | `GOB_WolfPens_Event_SidedWithGoblins` | `8887d64d-f76a-4410-b5a5-9f33f0362a64` | Global | | ✅ |
| Бросил пленника в цепях | `GOB_TorturedAdventurer_LeftInChains` | `94987d71-bd64-df88-25b8-12ddf2d50d82` | Dialog-флаг | `Dlg: GOB_TortureredAdventurer` | 🟡 dialog-флаги локальны для диалога |
| Саза (пленная гоблинша в Роще): дал тифлингам её казнить | `DEN_CapturedGoblin_State_PlayerWatchedGoblinExecution` | `cccd8084-dc8f-88c2-c145-482c34ab094f` | 5 | `Dlg: DEN_CapturedGoblin_GuardsAvenge` («admire the guard's hate») | 🟡 место установки не прослежено |
| Убийство тифлингов | `DB_CompanionCaredFaction(Альфира, ACT1_DEN_Tieflings_ca9de2d9-9022-9215-6d9b-676d916dcb5a, −N, 1, 0)` | — | способ C | как у Уилла: `[GD] Act1_OriginMoments_Wyll.txt:4-5` | ✅ |

- **Рядом ли Альфира.** Для диалогов — способ A по `_Instance`.
- **Ваниль (`GOB_Torturers_Torture`):** за каждый ответ-пытку Астарион/Лаэ'зель +1, Уилл/Карлах −1, Гейл −1 (часть). Камни в медведя — Астарион +1, Уилл/Карлах −1. Уилл за убийство тифлинга −10 (способ C).
- В Роще пытки Сазы как таковой нет. Есть только «позволить казнить» и «защитить» (Гейл +8/+6: `DEN_CapturedGoblin_State_SteppedInfrontOfCrossbow` `dff39def-ac63-8851-1330-239b310f090f`).

### A11. Насмешка над её песней или искусством

❌ Пока она спутница, в игре этого нет. Похожие ванильные реплики звучат до вербовки:
- `Dlg: DEN_TieflingBard_Bard`: «Give up — you don't have the makings of a bard» (Астарион +1, Уилл/Карлах −1) → `DEN_TieflingBard_State_ConvincedToQuit` `43352c49-25c4-1e6c-4531-e6469a9e71c3`;
- там же «разбить лютню» → `DEN_TieflingBard_State_SmashedLute` `d9778e98-9f2e-e522-ba99-116b00fa3454`.

Это исход до вербовки: мод уже блокирует по нему вербовку. Во время спутничества насмешки придётся писать в **наших диалогах**.

### A12. Сделка с Рафаилом

❌ **В акте 1 договора нет.** В ужине с Рафаилом (`Dlg: FOR_Monitor_Dinner`) ответ «I'll do anything to get rid of the tadpole» не ставит **ни одного флага**. Он даёт только ванильное одобрение: Астарион −5, Уилл −1, Карлах −1. Рафаил в ответ предлагает «прийти, когда отчаешься». Ловится только сам факт предложения:

| Флаг | UUID | Usage / как | Где | Уверенность |
|---|---|---|---|---|
| `GLO_Monitor_State_FirstDealOffered` | `ef829706-978e-4741-4610-bfb93006e886` | Global из диалога | узел «I could fix it all like that» (`FOR_Monitor_Dinner`) | ✅ |
| Отказ «You're mad if you think I'll make a deal with another devil» | — | флага нет | ваниль: Шэдоухарт/Уилл/Карлах +5 | ✅ |

`GLO_DevilDeal_State_PlayerSigned` / `…PlayerPacted` есть в Flags, но ни один goal или диалог актов 1–2 их не использует. Похоже, это остаток ранней версии ❔. Настоящий договор с Рафаилом — акт 3 (`WYR_RaphaelTango_*`). Реакцию −5 из таблицы стоит перенести в акт 3 или вешать на `FirstDealOffered` + выбор в нашем разговоре.

### A13. Разговор с мёртвым

- ✅ Каст ловится: `StatusApplied(_Target, "SPEAK_WITH_DEAD", _Player, _)` + `IsDead(_Target, 1)`, `[H] GLO_SpeakWithDead.txt:24, 55`. Труп получает тег `CORPSE_SPOKEN` `249ba319-6652-47ec-9f31-ef5be55429c3`. Каждый вопрос ставит `GLO_SpeakWithDead_Event_QuestionAsked` `9984cd59-2fad-46cb-bf61-96af6034fbea` на труп (`:117`).
- ❌ **«С уважением» и «глумление» в игре не различаются.** Нет ни общего флага, ни общего ответа. Реплики у каждого трупа свои. Реалистично можно сделать только нейтральное +1 «за интерес к мёртвым» или отказаться от пункта.

### A14. Проверки Исполнения, игра на инструменте при ней

- ✅ **Игра на инструменте** ловится. Действие «Выступить» даёт статус по итогу броска:
  - `PERFORM_POSITIVE` — удачно;
  - `PERFORM_NEGATIVE` — неудачно.

  Правило: `StatusApplied(_Performer, _Status, _, _)` + `DB_PartyMembers(_Performer)` вне боя, `[S] _CRIME_BardReactions.txt:6-30, 53-66`. Рядом ли Альфира, проверяется через `QRY_SpeakerIsInDialogRange(_Performer, Альфира)` или расстояние (способ B). Если играет сама Альфира, `_Performer` равен Альфире.
- ❌ **Проверки Исполнения в чужих диалогах** в Osiris не видны. Бросок узла диалога не даёт события, есть только флаги, которые ставит конкретный узел.

---

## Задача B — сюжетные условия глав акта 1

### Глава 6 «Элтуриэль» (после встречи с чем-то адским)

| Условие | Флаг / событие | UUID | Где | Уверенность |
|---|---|---|---|---|
| Первая встреча с Карлах | `ORI_Karlach_HasMet` | `50a43cde-0702-4c2a-a490-e9ee5f061f45` (Global) | диалог `PLA_KarlachRecruitment_Karlach_PostEA`; также `[G] GLO_Origin_Karlach.txt:55` | ✅ |
| то же (момент) | `DialogEnded(PLA_KarlachRecruitment_Karlach_PostEA_0f598b1a-b8b9-10cf-4d0d-0cd958586f61, _Inst)` | | `[GD] Act1_PLA_KarlachRecruitment_PostEA.txt:109-125` | ✅ |
| Первая встреча с Рафаилом | `GLO_TheMonitor_HasMet_TheMonitor` | `43aea040-f9d3-4f73-bdaa-b3512a3c92db` (Global из диалога) | `CAMP_MonitorIntro_CFM` | ✅ |
| то же, сцена ужина состоялась | `NIGHT_MonitorIntro` | `a9297517-ab4d-482d-b287-fc6e7001d93e` (Global) | `[GD] Act1_FOR_Monitor_PostEA.txt:177-184` (`InstanceDialogChanged` → ужин); также `FOR_Monitor_HasMet_Dinner` `fc3c9c86-b3c6-3e05-056e-4d6d01bf7073` | ✅ |

⚠️ Рафаил появляется **не только у Вымершей деревни**. После одного из флагов-условий он подходит у любого из пяти триггеров: CRA, DEN, GOB, PLA, UND (`[GD] Act1_FOR_Monitor_PostEA.txt:4-17`). Условия:
- `DEN_Apprentice_State_MonitorIntroRequirementMet`;
- `GLO_Hag_State_FailedTadpole`;
- `GOB_GoblinPriest_Quest_CureIsHoax`;
- `UND_…ConnectionPerformed`;
- `PLA_GithChokepoint_…`;
- `GLO_Halsin_State_Returned` / `…AskedKilledLeaders` / `…ToldAboutMoonrise`;
- `SCL_State_RegionVisited`.

Диалог добавляет всех ближних игроков (`DB_Dialog_AddAllNearbyPlayersAtStart`, `:4-5`). Поэтому «Альфира видела» проверяется через `DB_DialogSpeakers`.

Дополнительные «адские» кандидаты:
- ночь `NIGHT_Wyll_MizoraFirstContact` `aca43cd3-ce1d-4042-b7d2-b7813f923daf`: первая встреча с Мизорой, флаг ставится по завершении ночи;
- дьявольский бык Рощи: `GLO_DevilishOx_State_Defeated` `4061b72f-ce89-4b86-b18b-ed9c5fbc7cc8`, `[GD] Act1_DEN_DevilishOx.txt`, ❔.

### Глава 7 «Страх» (Подземье, Горный перевал, Гримфордж)

| Условие | Флаг / событие | UUID | Где | Уверенность |
|---|---|---|---|---|
| Вход в Подземье | `GLO_Underdark_EverEnteredBefore` | `dd5cd5b4-2ad5-4dbd-4972-2afaa7538994` (Global) | игрок в `S_UND_Underdark_SUB_b379a862-a59f-4e52-9166-23fbe0e8976e`, `[G] Act1_UND_General.txt:183-188`. Подземье — часть уровня `WLD_Main_A` | ✅ |
| Вход в Гримфордж | `GLO_DuergarCamp_EverEnteredBefore` | `ac0bae57-7006-4676-88b8-7498dde79c41` (Global) | игрок в `S_UND_DuergarCamp_SUB_05c3bf1f-…`, `[G] Act1_UND_DuergarCamp_Misc.txt:236-245` | ✅ |
| Горный перевал | уровень `CRE_Main_A` (Act1b). Событие `LevelLoaded("CRE_Main_A")` (`[GD] Act1b.txt:9`); субрегион `S_CRE_Mountains_SUB_6baef4b2-c773-440e-b3bd-4a4e885ace28` (`[GD] Act1b_Subregions.txt:4`) | — | ✅ |
| то же флагом | `VISITEDREGION_CRE_Main_A` | `c22062f9-2a42-4e19-8c72-34a2d9ff9c0a` (Global) | в goals нет `SetFlag`, диалоги его проверяют. Ставит движок ❔ | 🟡 |

Для «при ней» нужно, чтобы Альфира была в отряде в момент входа. Лучше ловить `DB_InRegion(S_DEN_Bard_…, <SUB>)` или `EnteredTrigger(S_DEN_Bard_…, <SUB>)` самостоятельно, чем полагаться на флаги «когда-либо входил», которые могли стоять ещё до вербовки.

### Глава 8 «Первый поцелуй» (перед уходом из Рощи или на первом привале в пути)

Цепочка событий после «Охоты на гоблинов», всё ✅:
1. `GOB_State_LeadersAreDead` → `DEN_State_GoblinHuntVictory` → `DEN_Refugees_State_LeadersAreDead` `1e6a42ed-8313-4f46-57e2-20dbdb2df923` и `DenVictory`. Источник: `[G] Act1_DEN_TieflingRefugees.txt:331-359`.
2. Условия ухода: игрок поговорил с лидером и побывал в Роще → `DEN_TieflingRefugees_State_PrepToLeave` `a3454969-aff1-4e0c-2d1a-f61fddea69d4` (Global), `:445-449`.
3. Приглашение на праздник: `DEN_AttackOnDen_Event_TieflingPartyInvitation` `545593fd-42e6-15c1-1e96-18e0e0be0443` (Global), `[G] Act1_CAMP_GoblinHuntCelebration.txt:1354`. Это обязательное условие праздничной ночи (`:14`).
4. Праздник: ночь `NIGHT_GoblinHunt_TieflingCelebration` `1ad8c357-2695-4d5c-b5f9-8b8c07803121`. Альфира там со своим диалогом `CAMP_GoblinHuntCelebration_Bard` (`:48`), Лакрисса — со своим (`:49`).
5. **Уход тифлингов** на ближайшем `PROC_LongRest()` после завершённой праздничной ночи при `PrepToLeave` (`:454-462`). Ставится `DEN_TieflingRefugees_State_LeftDen` `003b304b-f058-4f8a-b9fa-a097e1b6b395` (Global, `:514-518`) → `DEN_State_TieflingsGone` (`:522-528`).

Запасные пути:
- праздник отменён (`DB_CAMP_GoblinHuntCelebration_Cancelled(1)`) → уход на следующем отдыхе (`:465-473`);
- выгрузка `WLD_Main_A` при `DenVictory` (`:563-568`).

**Для главы 8.** Точка «перед уходом из Рощи» — это окно `PrepToLeave` = 1 и `LeftDen` = 0: праздник впереди или идёт. «Первый привал в пути» — первый `PROC_LongRest` при `LeftDen` = 1. Флаг «праздник прошёл» — `NIGHT_GoblinHunt_TieflingCelebration`: он ставится в конце вечера праздника (`[H] GLO_CampNights.txt:1700-1713`, `PROC_Camp_EndEvening` → `PROC_GlobalSetFlagAndCache(_NightFlag)`).

⚠️ Мод уже блокирует вербовку при `LeftDen`. После праздника Альфира-NPC уходит вместе с тифлингами. Если она спутница, мод убирает её из `DB_DEN_NPC` через `PROC_DEN_RemoveFromDenNPCs`, так что уход её не должен касаться (проверить в игре).

### Глава 5 «Утро после»

| Условие | Флаг / событие | UUID | Где | Уверенность |
|---|---|---|---|---|
| Праздник тифлингов в лагере прошёл | `NIGHT_GoblinHunt_TieflingCelebration` | `1ad8c357-2695-4d5c-b5f9-8b8c07803121` (Global) | ставится в конце вечера (`[H] GLO_CampNights.txt:1713`). Утро — ближайший `PROC_LongRest()` при этом флаге. Мод уже ловит `PROC_LongRest` (`ALFSV_Chapters.txt`) | ✅ |
| (альтернатива) праздник рейдеров | `NIGHT_GoblinHunt_RaiderCelebration` | `86fee25f-1069-4f17-89fa-4c5b69f82e0b` | тифлинги мертвы, отдельная ветка | ✅ |
| Лакрисса мертва | **флага нет.** Проверять `DB_PermaDefeated(S_DEN_Tiefling_010_23129d6c-8d39-4a4c-a4f6-cfc6637b597c)` или `DB_Dead(...)`. Так проверяет сама игра в `[GD] Act3b_LOW_ElfsongTavern.txt:361, 384, 396`. Лакрисса = `S_DEN_Tiefling_010`: DisplayName «Lakrissa» в `Globals/WLD_Main_A/Characters/_merged.lsx` | — | ✅ |
| (дебаг) | `Debug_Act2Setup_State_LakrissaDead` `51487a98-ea74-4278-6725-304de01ca18f` — только отладка (`DB_GLO_DieFlag`) | | `[GD] DebugItem_Dev.txt:206` | не использовать |

### «Акт 1 закончился»

| Вариант | Флаг / событие | UUID | Где | Уверенность |
|---|---|---|---|---|
| Точка невозврата (акт 1 больше недоступен) | `Act2_PointOfNoReturnReached` | `a3155f30-b8f3-4db5-ac21-d3036f4426e3` (Global) | по нему `WLD_Main_A` и `CRE_Main_A` становятся недоступны: `[GD] GLO_LevelCaches.txt:12-13`; блок возврата — `[GD] Act2_General.txt:74-90` (готовность «войти в тюрьму Ночной Песни» / `FlagSet`). Где именно ставится флаг, не нашёл (вероятно, диалог-предупреждение или движок) | ✅ смысл / 🟡 источник |
| Первый вход в Земли тени (акт 2 начался, но в акт 1 можно вернуться) | `LevelLoaded("SCL_Main_A")` (`[GD] Act2.txt`), `VISITEDREGION_SCL_Main_A` `f6e72539-9bc6-42e1-a20f-390f3a17ad8d` | | ✅ / 🟡 |
| Текущий уровень | `DB_CurrentLevel("WLD_Main_A")` или `("CRE_Main_A")` — мод уже так делает | | ✅ |

**Рекомендация.** Необязательные главы акта 1 открывать при `NOT DB_GlobalFlag(VISITEDREGION_SCL_Main_A)`. Это строгий вариант: после первого входа в акт 2 главы больше не открываются. Если нужно, чтобы главы жили до конца акта даже после вылазки в Земли тени, используйте `NOT DB_GlobalFlag(Act2_PointOfNoReturnReached)`. Проверку `DB_CurrentLevel` добавлять не нужно: разговор в лагере акта 2 тоже идёт на другом уровне.

---

## Сводно: что пригодно для реакций

| № | Пункт | Надёжно ловится | Способ «рядом» |
|---|---|---|---|
| 1 | Защита Рощи | `Event_Start` + `DenVictory` | B (`QRY_DEN_IsInDen`) |
| 2 | Ритуал остановлен | хук `DEN_State_RitualStopped`, `DenouncingInProgress`; или `GoblinHuntVictory` | A / B |
| 3 | Ритуал свершился | `DEN_Lockdown_State_Active` | C (игроков в Роще нет) |
| 4 | Арабелла | `KidFreed` / `FreedChild` | A (часто до вербовки) |
| 5 | Миркон | `HelpedSaveVictim` на самой Альфире | готово в игре |
| 6 | Майрина / сделка | `SurrogateReleased` / `HagTookMother` | A |
| 7 | Карлах | `HelpingKarlach`, `AgreedToHelpNotRecruited`, `KarlachHostile`, `KilledKarlach` | A |
| 8 | Воло | `VoloEscaped` (+ `PlayersMetVolo`) | C |
| 9 | Гримфордж | `UND_State_LeaderFreedGnomes`, `UND_GnomeWorkers_Event_Leave`, `GnomesExecuted` | A / B |
| 10 | Пытки | `GOB_Torturers_Assisted`, `WolfPens_ThrewRock`, `CompanionCaredFaction` | A / C |
| 11 | Насмешка над песней | ❌ только наши диалоги | — |
| 12 | Рафаил | ❌ договора в акте 1 нет; `FirstDealOffered` | A |
| 13 | Разговор с мёртвым | только факт каста; уважение и глумление ❌ | B |
| 14 | Исполнение | `PERFORM_POSITIVE` / `PERFORM_NEGATIVE`; броски в диалогах ❌ | B |
