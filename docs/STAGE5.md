# Этап 5 (начало). Глава 2 «Лютня», реплики на местах и в пути

Статус: **собрано, в игре не проверено.** Этап закрывается только после проверки по §6
(CLAUDE.md §2).

**Версия 0.5.0.** Новый goal Osiris `ALFSV_World` (генерируется), изменился goal глав. Новой игры не
нужно: на сохранении 0.4.0 goal добавится при story patching, его данные (`PROC_ALFSV_World_Data`)
вставятся в INIT и при каждой загрузке уровня.

## 1. Что сделано

- **Глава 2 «Лютня»** — точно по `design/dialogs/03_act1_ch2_lute.md` (согласовано 2026-09-26),
  `scripts/dialogs/scenes/ch02_lute.py`. Дерево: `build/dialogs/ALFSV_Alfira_Ch02_Lute.md`. 53 узла,
  34 фазы: 10 её озвученных реплик игры (handle из сценария) с их постановкой, новые реплики — только
  текст, действия — ремарки рассказчика.
- **Реплики на местах, акты 1–3** — `design/banter/02_places.md`, `scripts/dialogs/scenes/places.py`:
  36 AD (фуникулёр Яслей — три реплики по ходу рейса). 5 мест без надёжного запуска — §5.
- **Фразы в пути, акт 1** — `design/banter/01_act1_world.md` §2, `scripts/dialogs/scenes/travel.py`:
  10 фраз, 3 из них — её озвученные из `CAMP_Bard_AD`.
- **Конвейер AD** (`scripts/dialogs/ads.py`): описание мест и фраз → AD (текст над головой) + goal
  `ALFSV_World.txt`. Схема — [STAGING.md §5b](STAGING.md#5b-реплики-над-головой-ad-этап-5), формат —
  [scripts/dialogs/README.md](../scripts/dialogs/README.md#реплики-над-головой-места-и-путь-этап-5).
- **Озвученная реплика из AD внутри главы:** фаза по длине голоса (у AD нет сцены) — `staging.py`.

Идентификаторы (на них ссылаются Osiris и сохранения — **не менять**):

| Что | ID |
|-----|----|
| ресурс `ALFSV_Alfira_Ch02_Lute` | `7f3c1e52-9a6b-4c1d-8e2f-5b0a4d6c9e13` |
| `ALFSV_Chapter02_Available` / `_Done` (глобальные) | `b8ac2941-38e0-5c94-8fc1-4dec55aa4d2d` / `4cd365b4-313e-536b-969f-84319fa4cbb6` |
| AD мест и фраз в пути | uuid5(UUID мода, `ad/<имя>`): выводятся из ключа места — ключи не переименовывать |
| «сказано» фраз в пути | `ALFSV_Travel_NN_Played`: номер = место в списке, новые фразы — только в конец |

## 2. Глава 2: как устроена

- **Открытие:** после долгого отдыха, когда сыграна глава 1 (`after_rest=True`). Вход — в любом
  разговоре в отряде или в лагере, днём и вечером (сценарий: «лагерь или отряд»). При одобрении
  ниже 0 — холодная реплика разговора в отряде, глава ждёт.
- **Где лютня Лихейлы** (ответ на вопрос сценария). `DEN_TieflingBard_Event_TransferInstrument` — не
  состояние, а событие «передать лютню от Альфиры тому, на ком флаг» (`Act1_DEN_TieflingBard.txt:45-49`);
  его ставят и дуэт, и возврат украденной лютни, и отказ от помощи. `DEN_TieflingBard_Event_PlayWithInstrument`
  ставится на героя, когда он взял её лютню для дуэта (`DEN_TieflingBard_Bard` N4659), и после этого все
  ветки оставляют лютню у него («Keep the lute» N2541, N4534). Вариант «лютня у героя» = этот флаг на герое.
- **L1:** лютня у героя — «Can I ask you something odd?»; иначе — ремарка «прижав лютню к груди» и
  «Oh — hi… counting».
- **L2** (любой ответ ставит `ALFSV_Chapter02_Done`): тёплый +2 (две её озвученные), любопытный +1
  (только при лютне у неё — это ответ на её «считаю»), шутливый +1, 🏷️ «Возьми её обратно» +2 (только
  при лютне у героя; озвученная «Keep the lute…» + новая), циничный −2. Все ведут в L3.
- **L3:** ремарка и две реплики о зарубках → «вместе в городе» +2 (`ALFSV_Notch_City`), «Роща
  считается» +1 (`ALFSV_Notch_Grove`), «оставить как есть» 0.
- **L4:** озвученная «Oh, oh! I have an idea…»; герою-барду (тег `BARD`) — «Ah! A fellow bard…».
  🎲 Исполнение `Act1_Medium` (10, как в главе 1): успех +3 (две озвученные), провал +1 (новая); обе
  ставят `ALFSV_PlayedTogether`. «Я не умею» +2 (`ALFSV_LuteLesson`): озвученная + новая, затем
  ✨ «Поправь мне пальцы сама» +2 (`ALFSV_Romance_LuteHands`) или нейтральное *Взять аккорд*.
  «Лучше я послушаю тебя» +1: ремарка «играет что-то простое, светлое»; 🏷️ Темный Соблазн (тег
  `REALLY_DARK_URGE`) — ремарка-шёпот Побуждения и выбор «Сопротивляться» (`ALFSV_Durge_Resisted`, её
  «You all right?») / «Сжать кулак» (`ALFSV_Durge_UrgeNear`, ремарка «ничего не замечает»); потом
  ✨ *Смотреть на неё* +2 (`ALFSV_Romance_MissedNote`) или нейтральное *Слушать* (ремарка «улыбается
  сама себе»).
- **L5:** две её озвученные («Thanks. Lihala made me love music…», «Until now…») → конец.
- Романтические варианты — только с `ALFSV_Romance_Spark` на герое. Флаги-воспоминания — на герое.

## 3. Места: откуда запуск

Триггеры — только те, что игра сама держит зарегистрированными для отряда (подрегионы и триггеры
бесед отряда, [STAGING.md §5b](STAGING.md#5b-реплики-над-головой-ad-этап-5)). Каждое место — один
раз за игру, когда Альфира в активном отряде. Пути к goals — `Gustav/Mods/Gustav(Dev)/Story/RawFiles/Goals/`.

| Акт | Место | Ключ | Запуск | Откуда (данные игры) |
|---|---|---|---|---|
| 1 | Ясли Иллек: фуникулёр, начало подъёма | `CRE_LiftStart` | рейс фуникулёра (§4) | Act1b_CRE_Exterior.txt:103-130,194-198 (PROC_CRE_Dungeon_ElevatorMove) |
| 1 | Ясли Иллек: фуникулёр, середина пути | `CRE_LiftMid` | рейс фуникулёра (§4) | Act1b_CRE_Exterior.txt (опрос расстояния до точки назначения) |
| 1 | Ясли Иллек: фуникулёр, наверху | `CRE_LiftTop` | рейс фуникулёра (§4) | Act1b_CRE_Exterior.txt:200-207 (PlatformMovementFinished) |
| 1 | Горный перевал, вид на долину | `MountainPass` | `S_PLA_MountainPass_SUB_e0daf9ba-4b75-4482-b73a-b46fc8f62a44` | Act1_Subregions.txt (PLA_MountainPass_SUB) |
| 1 | Обитель Розиморн | `Monastery` | `S_CRE_Monastery_SUB_94be6628-ed02-4bdc-9173-5d1b06f26daa` | Act1b_Subregions.txt (CRE_Monastery_SUB) |
| 1 | Подземье, первый шаг | `UnderdarkFirst` | `S_UND_Underdark_SUB_b379a862-a59f-4e52-9166-23fbe0e8976e` | Act1_Subregions.txt (UND_Underdark_SUB) |
| 1 | Подземье, колония миконидов | `Myconids` | `S_UND_MyconidCircle_SUB_4b5cc8fc-88f4-465e-bf82-4c20b055c019` | Act1_Subregions.txt:54 |
| 1 | Адамантиновая кузня | `AdamantineForge` | `S_UND_AdamantineForge_SUB_5fd81ed1-b91b-413e-91de-360715aba962` | Act1_Subregions.txt (UND_AdamantineForge_SUB) |
| 1 | Изумрудная роща, Священный пруд | `SacredPool` | `S_DEN_SacredPond_SUB_2303e19f-549f-434f-bee0-b886fb34c46a` | Act1_Subregions.txt:18 |
| 1 | Всхожая дорога | `RisenRoad` | `S_PLA_Plains_SUB_bcc3efa5-bfe1-4224-9df1-6758cac764cd` | Act1_Subregions.txt:45 — **проверить в игре**: подрегион «равнин» = Всхожая дорога |
| 1 | Вымершая деревня | `BlightedVillage` | `S_FOR_ForestVillage_SUB_21e6bfbf-c5c9-4e99-97f8-2df7143967c4` | Act1_Subregions.txt:30 |
| 1 | Место крушения наутилоида | `CrashSite` | `S_CRA_Beach_SUB_a78bd6f2-9c61-4866-a6d7-74a46ebd82b0` | Act1_Subregions.txt:85 |
| 1 | Чайный домик у реки | `Teahouse` | `S_HAG_House_SUB_a54033ab-fc50-476b-99c6-5d6ad01bcf18` | Act1_HAG_Hag.txt:74 (DB_SubregionMarker) |
| 1 | Лагерь гоблинов | `GoblinCamp` | `S_GOB_Festivities_SUB_217424e5-f9b7-4441-ab09-715076696a12` | Act1_Subregions.txt — **проверить в игре**: двор лагеря |
| 1 | Темный склеп | `DankCrypt` | `S_CHA_Crypt_SUB_001_f8bc812e-1cb3-46bd-942a-9f572f66ef16` | Act1_Subregions.txt (CHA_Crypt_SUB_001) |
| 1 | Гнездо медвесыча (детёныш) | `OwlbearNest` | `S_FOR_OwlBear_SUB_1fa871e1-4979-4259-9e5e-5017b06d077f` | Act1_Subregions.txt (FOR_OwlBear_SUB) |
| 2 | Рассвет над Оскверненными тенью землями | `Sunrise` | флаг `GLO_LiftingTheCurse_State_BreathHasBeenRestored_2113b54e-…` или `SCL_ShadowCurse_State_CurseLifted_af78af4a-…`, что раньше | Act2_SCL_LiftingTheCurse_Confrontation.txt:781; Act2_SCE_LiftingTheCurse_HalsinFollowUp.txt:52-68 |
| 2 | Оскверненные тенью земли, первый шаг | `SCLFirst` | начало уровня `SCL_Main_A` | LevelGameplayStarted |
| 2 | Таверна «Последний свет» | `LastLight` | `S_HAV_Haven_SUB_6ac001f4-9c56-4a1b-963d-a509e158ffab` | Act2_Subregions.txt (HAV_Haven_SUB) |
| 2 | Вызов Шар | `Gauntlet` | `S_SHA_Temple_SUB_348b76ee-33d8-471b-a95d-7ded0d6cdfd5` | Act2_Subregions.txt (SHA_Temple_SUB) |
| 2 | Вызов Шар, подъёмник | `GauntletLift` | `S_SHA_Disc_Bounds_ed943df3-d3ca-43e4-890f-4ef9bd30faa1` (диск) | Act2_SHA_Disc.txt:4 (регистрация), :69 |
| 2 | Песня Ночи | `Nightsong` | `S_SHA_NightsongPrison_SUB_0a302268-dd92-4462-99e5-ca7491815ec0` | Act2_Subregions.txt |
| 2 | Лунные Башни | `Moonrise` | `S_MOO_MoonriseTower_SUB_14187ad9-cf83-44f9-81bf-bb46cb4cd8e6` | Act2_Subregions.txt |
| 2 | Величественная усыпальница | `Mausoleum` | `S_SHA_Mausoleum_SUB_66b74527-67c9-47bf-92a4-b90e1b189739` | Act2_Subregions.txt |
| 2 | Дом исцеления | `HouseOfHealing` | `S_TWN_Hospital_SUB_2ec2cc09-94ab-4479-bacd-cd5ca6911833` | Act2_Subregions.txt |
| 3 | Первый вид на Врата Балдура | `BaldursGateView` | `S_WYR_Rivington_SUB_40c3661e-99a1-4189-aa69-c006e77e3db8` или `S_WYR_Bridge_SUB_ed5b53be-de5f-46e9-ab78-2707c0bfe61e`, что раньше | Act3_Subregions.txt |
| 3 | Змеиная скала, мост | `WyrmsRockBridge` | `S_WYR_PartyBanter_WyrmsRock_88780113-c3be-43ab-b718-44f72fd16c70` | Act3_WYR_General.txt:220 (беседа отряда) |
| 3 | Серая бухта, море | `GreyHarbour` | `S_PartyBanterTrigger_NorthDocks_a6b6c79c-…` или `…SouthDocks_6f047c6b-…` | Act3b_LOW_Misc.txt:332,337 — **проверить в игре**: это Серая бухта |
| 3 | Парк Блумридж | `BloomridgePark` | `S_PartyBanterTrigger_BloomridgePark_d1289cdd-547d-49da-a538-1ffb117bb5f6` | Act3b_LOW_Misc.txt:312 |
| 3 | Киот Штормового берега | `Tabernacle` | `S_LOW_StormshoreTabernacle_SUB_8ef5fd83-3fa2-48c1-b103-0846ee138206` | Act3b_Subregions.txt |
| 3 | Цирк Конца Дней | `Circus` | `S_WYR_Circus_SUB_22d3f3ff-3cbb-4240-a3ab-051889832375` | Act3_Subregions.txt |
| 3 | «Волшебные принадлежности» | `SorcerousSundries` | `S_LOW_SorcerousSundries_Shop_SUB_da22d284-7b3a-4c6a-884c-685c07d26068` | Act3b_Subregions.txt |
| 3 | «Ласка Шаресс» | `SharessCaress` | `S_WYR_SharessCaress_SUB_07597ced-f3fe-45f8-bab6-13f0064b75bb` | Act3_Subregions.txt |
| 3 | Дом Надежды | `HouseOfHope` | `S_LOW_HouseOfHope_SUB_49462249-7f39-4b91-af1d-ba121c711213` | Act3b_Subregions.txt |
| 3 | Водоем Изменений | `MorphicPool` | `S_END_MorphicPool_SUB_5a646d13-e9bb-42f0-84e6-1f8fad2bef81` | Act3c_Subregions.txt |
| 3 | Астральный план | `AstralPlane` | `S_END_AstralPrism_SUB_adf44e33-…` или `S_INT_AstralPlane_SUB_98791ae8-…` | Act3c_Subregions.txt, Act2b_Subregions.txt |

Варианты мест, где ✨/💞/🔁 в сценарии — добавка к основной реплике («Ласка Шаресс», рассвет,
Врата Балдура), собраны как «основная реплика + добавка». Ремарки («берёт за руку», «шёпотом») над
головой не показываются — их роль играют эмоции.

## 4. Фуникулёр Яслей Иллек (сцена из трёх реплик)

Платформа `S_LTN_PLT_CRE_RailLift_000` ходит между триггерами-станциями `S_CRE_RailLift000_Down/_Up`
(`Act1b_CRE_Exterior.txt`): рейс начинает `PROC_CRE_Dungeon_ElevatorMove` (`PlatformMoveTo`, скорость 5),
кончает `PlatformMovementFinished(…, "CRE_Dungeon_ElevatorMoved")`. Мод добавляет свои правила
(ванильные не меняются, `ads.LIFT_BLOCK`):

1. **Начало** — своё правило к `PROC_CRE_Dungeon_ElevatorMove`, если Альфира в отряде и в 10 м от
   рычага кабины `S_CRE_ElevatorLever_000` (она на платформе). Пустая платформа, вызванная со станции,
   не считается.
2. **Середина** — опрос раз в секунду: до точки назначения меньше половины начального расстояния.
3. **Наверху** — `PlatformMovementFinished`, если середина уже была.

Рейсы отслеживаются, пока не сказана верхняя реплика; каждая из трёх — один раз. Если предыдущая ещё
звучит, следующая ждёт очереди (до 60 с). «Наверху» — конец рейса в любую сторону: какая станция
выше, по данным не видно (станции названы Down/Up).

## 5. Места без надёжного запуска (в игру не идут)

| Место | Ключ | Почему |
|---|---|---|
| Селунитский аванпост (Подземье) | `SeluneOutpost` | нет подрегиона и триггера бесед с этим местом; точечные триггеры путевых камней Подземья (`_Gustav_Waypoints_Act1.txt`) не подписаны местом — не угадываем |
| Лифт Гримфорджа | `GrymforgeLift` | лифт — предмет `S_UND_Elevator_Fort_ToShadowlands` (`Act1_UND_DuergarCamp_Elevator.txt:188`, флаг `UND_ElevatorToScl_Used`): по имени и флагу это переход к Оскверненным землям, а не поездка; своего триггера у кабины нет — проверить в игре, есть ли поездка, на которой успеет реплика |
| Ясная ночь в пути | `ClearNight` | в данных нет события «ясная ночь»: день и ночь меняются только в лагере (`GLO_CAMP_State_NightMode`) |
| Приют Вокин (горит) | `WaukeensRest` | триггер горящего трактира `S_PLA_TavernInvestigation_BurnDownTrigger_Inner` игра снимает с отряда (`Act1_PLA_TavernInvestigation.txt:711`), подрегиона у трактира нет |
| Рейтвин | `Reithwin` | у города нет подрегиона; триггеры бесед Рейтвина — только «…Cleared» (после зачистки, `Act2_Gossip.txt:15-21`) |

## 6. Как проверить в игре

Подготовка — как в [STAGE2.md §3.0](STAGE2.md#30-режим-проверки) (`test_mode.py on`, `bg3_dx11.exe`):

```
python scripts/check_story.py        # 3 goal(s) мода: ошибок 0
python scripts/build_pak.py          # версия 0.5.0
python scripts/dialogs/validate.py   # «Проверка пройдена.»
python scripts/dialogs/tree.py       # build/dialogs/ALFSV_Alfira_Ch02_Lute.md, ALFSV_AD_*.md
```

Консоль SE (сервер): `Osi.PROC_ALFSV_Debug_Recruit()`, `Osi.PROC_ALFSV_Debug_UnlockChapter()` (как
после отдыха), `Osi.PROC_ALFSV_Debug_Place("CRE_LiftMid")` (сыграть реплику места сейчас, повторно),
`Osi.PROC_ALFSV_Debug_Travel()` (следующая фраза в пути через 5 с).

**Глава 2**

1. **Открытие.** Сыграть главу 1 → долгий отдых → заговорить с Альфирой днём: глава 2 (без отдыха —
   ротация приветствий). Отладка: `PROC_ALFSV_Debug_UnlockChapter()` после главы 1.
2. **Лютня у неё** (дуэта в Роще не было): ремарка «прижав лютню», «Oh — hi… counting»; в L2 есть
   «Что ты там считаешь?», нет «Возьми её обратно».
3. **Лютня у героя** (дуэт на её лютне в Роще): «Can I ask you something odd?»; в L2 есть «Возьми её
   обратно» с озвученной «Keep the lute…», нет «Что ты считаешь». Лютня в инвентаре героя.
4. **Озвученные реплики** — её голос, лицо по постановке Larian; «I can't remember the last time I
   played like that» (из AD акта 2) — голос есть, постановка стандартная.
5. **L4:** герой-бард — «Ah! A fellow bard…», иначе «Oh, oh! I have an idea…». Исполнение — успех и
   провал.
6. **Искра** (из вербовки): «Поправь мне пальцы сама», «Смотреть на неё» — есть; без искры — вместо них
   нейтральные *Взять аккорд* / *Слушать*.
7. **Темный Соблазн:** в ветке «Лучше я послушаю тебя» — шёпот Побуждения, два варианта; «You all
   right? …призрака увидел/увидела» — в роде героя.
8. **Одобрение:** всплывающие реакции по §2. **Сыгранная глава:** после ответа в L2 — ротация.

**Места** (Альфира в активном отряде; каждое — один раз)

9. **Фуникулёр Яслей** (главное): подняться с Альфирой на платформе. Начало — «Gith architecture…»,
   середина — один вариант (обычный / ✨ «I'm going to remember this» / ❄️ «…It's pretty»), конец —
   «There's a verse in this…». Реплики не накладываются, текст держится над её головой. Повторный
   рейс — тишина.
10. **Горный перевал** — «Is that the whole Sword Coast?» на входе в подрегион.
11. **Темный склеп** — её озвученная «And the dead deserve to be remembered…».
12. **Лагерь гоблинов**, **Всхожая дорога**, **Серая бухта** — реплика в правильном ли месте.
13. **Вход в бою / в разговоре:** реплика ждёт и звучит после (до 60 с) или сработает при следующем входе.
14. **Альфира в лагере** (не в отряде): реплик нет.

**Фразы в пути**

15. Идти с отрядом 10–15 минут: фраза раз в 3–6 минут над её головой; в лагере, в бою, в разговоре —
    нет; без повторов; три озвученные — её голосом. Одобрение ниже 0 — только «…Just keep walking.».
16. Сохранение 0.4.0 с завербованной Альфирой → загрузить с 0.5.0 → через несколько минут пути —
    фраза; у входа в подрегион из таблицы — реплика места.

## 7. Известные ограничения и риски

1. **Текст AD без голоса.** Длина фазы — по объёму текста (до 10 с). Покажет ли игра текстовую
   реплику AD без звука так же, как в диалоге, — главный вопрос проверки (п. 9).
2. **Категория AD.** Места — «Voice bark» (как реакции спутников Larian), фразы в пути — «Repeated
   automated NPC Dialog» (как её `CAMP_Bard_AD`). Если игра не играет одну из них — константы в `ads.py`.
3. **Выбор варианта — флагами на Альфире**, по всем героям сразу: в мультиплеере ✨/💞 сработает,
   если искра/роман есть у любого героя.
4. **💞 роман** (`ALFSV_Romance_Started`) пока никто не ставит — его поставит глава, где роман
   открывается (R3/R4). До тех пор 💞-варианты не звучат.
5. **Порог «тёплой» фразы** — 40 (решение сборки: в сценарии «одобрение высокое» без числа).
6. **«Случайные» фразы** случайны по времени, порядок — первый подходящий по списку.
7. **Подрегионы большие:** реплика звучит на входе в подрегион, а не у конкретного вида.
8. **Порядок Osiris** при нескольких местах сразу: запускается одно, остальные ждут (выбор «первого»
   держится на проверке `NOT DB_ALFSV_AD_Requested` внутри одного правила — проверить п. 13).
