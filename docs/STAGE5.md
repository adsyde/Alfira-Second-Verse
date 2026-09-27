# Этап 5. Глава 2 «Лютня», реплики на местах и в пути, беседы отряда, разговоры акта 1 (§9)

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
  41 AD (фуникулёр Яслей — три реплики по ходу рейса). Все места сценария собраны; пять из них
  (аванпост, лифт Гримфорджа, ясная ночь, Приют Вокин, Рейтвин) — с особым запуском, §5.
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
| 1 | Селунитский аванпост | `SeluneOutpost` | `S_UND_SharFortBox_3419cfbf-5ad0-473b-bfa6-f10cb1e4a415` | Act1_UND_SharFort.txt:4 (регистрация для отряда, не снимается) — §5 |
| 1 | Адамантиновая кузня | `AdamantineForge` | `S_UND_AdamantineForge_SUB_5fd81ed1-b91b-413e-91de-360715aba962` | Act1_Subregions.txt (UND_AdamantineForge_SUB) |
| 1 | Лифт Гримфорджа | `GrymforgeLift` | по прибытии после поездки на лифте (§5) | GLO_LevelSwap_PostEA.txt:9,13; GLO_LevelSwap.txt (PROC_GLO_LevelSwap_LeavingFromTo) |
| 1 | Изумрудная роща, Священный пруд | `SacredPool` | `S_DEN_SacredPond_SUB_2303e19f-549f-434f-bee0-b886fb34c46a` | Act1_Subregions.txt:18 |
| 1 | Ясная ночь | `ClearNight` | первый свободный вечер в лесном лагере `WLDMAIN` (§5) | Shared GLO_Camp.txt (PROC_Camp_SetModeToNight), Act1a_Camp.txt:7 |
| 1 | Всхожая дорога | `RisenRoad` | `S_PLA_Plains_SUB_bcc3efa5-bfe1-4224-9df1-6758cac764cd` | Act1_Subregions.txt:45 — **проверить в игре**: подрегион «равнин» = Всхожая дорога |
| 1 | Вымершая деревня | `BlightedVillage` | `S_FOR_ForestVillage_SUB_21e6bfbf-c5c9-4e99-97f8-2df7143967c4` | Act1_Subregions.txt:30 |
| 1 | Место крушения наутилоида | `CrashSite` | `S_CRA_Beach_SUB_a78bd6f2-9c61-4866-a6d7-74a46ebd82b0` | Act1_Subregions.txt:85 |
| 1 | Приют Вокин (горит) | `WaukeensRest` | флаг `PLA_Tavern_Knows_Burning_f1d6e5cf-e8d4-4095-a6ef-17dfcd4521b0` | Act1_PLA_TavernInvestigation_Surroundings.txt:19,912-916 — §5 |
| 1 | Чайный домик у реки | `Teahouse` | `S_HAG_House_SUB_a54033ab-fc50-476b-99c6-5d6ad01bcf18` | Act1_HAG_Hag.txt:74 (DB_SubregionMarker) |
| 1 | Лагерь гоблинов | `GoblinCamp` | `S_GOB_Festivities_SUB_217424e5-f9b7-4441-ab09-715076696a12` | Act1_Subregions.txt — **проверить в игре**: двор лагеря |
| 1 | Темный склеп | `DankCrypt` | `S_CHA_Crypt_SUB_001_f8bc812e-1cb3-46bd-942a-9f572f66ef16` | Act1_Subregions.txt (CHA_Crypt_SUB_001) |
| 1 | Гнездо медвесыча (детёныш) | `OwlbearNest` | `S_FOR_OwlBear_SUB_1fa871e1-4979-4259-9e5e-5017b06d077f` | Act1_Subregions.txt (FOR_OwlBear_SUB) |
| 2 | Рассвет над Оскверненными тенью землями | `Sunrise` | флаг `GLO_LiftingTheCurse_State_BreathHasBeenRestored_2113b54e-…` или `SCL_ShadowCurse_State_CurseLifted_af78af4a-…`, что раньше | Act2_SCL_LiftingTheCurse_Confrontation.txt:781; Act2_SCE_LiftingTheCurse_HalsinFollowUp.txt:52-68 |
| 2 | Оскверненные тенью земли, первый шаг | `SCLFirst` | начало уровня `SCL_Main_A` | LevelGameplayStarted |
| 2 | Таверна «Последний свет» | `LastLight` | `S_HAV_Haven_SUB_6ac001f4-9c56-4a1b-963d-a509e158ffab` | Act2_Subregions.txt (HAV_Haven_SUB) |
| 2 | Рейтвин | `Reithwin` | `S_TWN_MainSub_169edf4a-bd51-4964-adb0-4d47956d5fae` | Act2_TWN_General.txt:49, Act2_TWN_Misc.txt:80 — §5 |
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

## 5. Особые запуски: аванпост, лифт Гримфорджа, ясная ночь, Приют Вокин, Рейтвин

Раньше эти пять мест не собирались: не было надёжного запуска. Теперь запуск найден для всех пяти, в
`GAPS` (`places.py`) ничего не осталось. Goals — `Gustav/Mods/Gustav(Dev)/Story/RawFiles/Goals/`, лагерь —
`Shared/Mods/Shared/…/GLO_Camp.txt` (из хотфикса).

| Место | Запуск | Почему это надёжно (данные игры) |
|---|---|---|
| **Селунитский аванпост** (Подземье) | `EnteredTrigger(Альфира, S_UND_SharFortBox_3419cfbf-…)` | В игре аванпост — `UND_SharFort` (статуи Селуны с «глазами»-турелями, самоцвет Селуны). Коробка-триггер вокруг него регистрируется для отряда в INIT `Act1_UND_SharFort.txt:4` и нигде не снимается. Что это аванпост, видно по данным: при уничтожении самоцвета `S_UND_Gem` цель предыстории «Act1_Acolyte_SeluneGem» засчитывается тому, кто стоит в этой коробке (`Act1_GLO_Backgrounds_Goals.txt:646`). Ещё в `Act1_DEN_AdventurersQuest.txt:56` эту коробку описывают как часть Подземья с лифтом наверх. |
| **Лифт Гримфорджа** | по прибытии: `PROC_GLO_LevelSwap_LeavingFromTo(_, "ReadyCheck_ToSCLFromUnderdark")` → `LevelGameplayStarted("SCL_Main_A")`, обратно — `"ReadyCheck_ToWLDFromSCL"` → `"WLD_Main_A"` (`ads.GRYMFORGE_LIFT_BLOCK`) | Лифт `S_UND_Elevator_Fort_ToShadowlands` — телепорт смены уровня (`GLO_LevelSwap_PostEA.txt:9`, прибытие — `StartPoint_000` в `SCL_Main_A`, :21; обратно — `S_SCL_Elevator_Fort_ToUnderdark`, :13). Сама поездка идёт за экраном загрузки, поэтому реплика звучит по прибытии. `PROC_GLO_LevelSwap_LeavingFromTo` игра вызывает только тогда, когда переход действительно начался: проверка готовности пройдена, лагерь перехода (`GLO_CampNights.txt`, fallback camp) закончился (`GLO_LevelSwap.txt`, `PROC_GLO_LevelSwap_CheckSwap`). Если на лифт нажали и отказались, реплики нет. Звучит один раз, в какую бы сторону ни ехали впервые с ней. ✨ — основная реплика + «…Loose strap.» |
| **Ясная ночь** | первый свободный вечер в лагере `WLDMAIN` (`ads.CLEAR_NIGHT_BLOCK`) | В пути ночи нет: день и ночь меняются только в лагере. «Закончить день» включает вечер: `PROC_Camp_SetModeToNight` ставит флаг `GLO_CAMP_State_NightMode_fb53edc2-…` и `DB_Camp_NightMode(1)` (`GLO_Camp.txt:2733-2735`). Честный вариант — лесной главный лагерь акта 1 `WLDMAIN` (Main Camp (Forest), `Act1a_Camp.txt:7`): там открытое небо. Мини-лагеря (подвал, пещеры, подземелья) и Подземье (`WLDUND`) не подходят, акты 2–3 тоже, у них свои лагеря. Флаг ставится в затемнении, потом идут сцены лагеря, поэтому реплика ждёт: раз в 5 с, пока вечер не кончился, проверяется, что лагерь — `WLDMAIN`, Альфира в лагере (`DB_InCamp`), экран не затемнён (`DB_Camp_Faded`) и никто из героев не в разговоре (`DB_InteractiveDialogSpeaker`). Потом — обычная очередь реплик места. Если в этот вечер не сработало, реплика ждёт следующего. |
| **Приют Вокин (горит)** | флаг `PLA_Tavern_Knows_Burning_f1d6e5cf-…` | Это акт 1 (в `02_places.md` — «Тяжёлые места» акта 1): трактир горит, когда отряд приходит впервые. Триггер `S_PLA_TavernInvestigation_BurnDownTrigger_Inner` регистрируется для отряда в INIT (`Act1_PLA_TavernInvestigation_Surroundings.txt:19`). Когда в него впервые входит кто-то из отряда, игра снимает триггер и ставит глобальный флаг «знаем, что горит» (:912-916). Снятие, из-за которого место раньше не собирали, происходит ровно в момент прихода, поэтому берём флаг, а не `EnteredTrigger` Альфиры. Если трактир сгорел без отряда (уход с уровня, `PROC_LevelUnloading("WLD_Main_A")`), `PROC_PLA_BurnDownTavern` снимает триггер (`Act1_PLA_TavernInvestigation.txt:711`), флага нет — и реплики нет, что правильно. |
| **Рейтвин** | `EnteredTrigger(Альфира, S_TWN_MainSub_169edf4a-…)` | У города нет `DB_Subregion`, но есть главный триггер города `S_TWN_MainSub`. Он регистрируется для героев отряда (`PROC_TriggerRegisterForPlayers`, `Act2_TWN_General.txt:49`) и не снимается. Этим же триггером игра отмечает «впервые в городе» (`DB_PartyProgress_Trigger` → `TWN_State_EverEnteredBefore`, `Act2_TWN_Misc.txt:80`). Карлах по нему перестаёт жаловаться на проклятие (`Act2_OriginMoments_Karlach.txt:35`, вместе с подрегионами «Последнего света» и Лунных Башен). «PlayerTriggers» регистрируются на всех из `DB_Players`, то есть и на Альфиру в активном отряде (`_GLO_Shared_PartyMembers.txt`, `PROC_RegisterPartyTrigger`). |

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
14a. **Селунитский аванпост:** войти в аванпост со статуями Селуны пешком из Подземья и (отдельно)
    приехать лифтом из Оскверненного храма — «Someone built a lighthouse down here…». Если прийти в
    Подземье впервые через этот лифт, то сначала звучит аванпост, «No sky, no stars…» — при выходе в пещеры.
14b. **Лифт Гримфорджа:** поехать на лифте в Оскверненные земли. После загрузки — «If this rope snaps…»
    (с искрой — и «…Loose strap.»), затем «Oh, gods. It's like the whole world is holding its breath…»
    (первый шаг): порядок именно такой. Нажать на лифт и отказаться в окне готовности — реплики нет.
14c. **Ясная ночь:** в лесном лагере акта 1 нажать «Закончить день». После сцен лагеря, когда экран
    открыт и никто не разговаривает, — «Stars are out. She'd be dancing.». В лагере Подземья — тишина,
    реплика ждёт вечера в лесу.
14d. **Приют Вокин:** подойти к горящему трактиру — «An inn! A real inn! …Oh. It's on fire.».
14e. **Рейтвин:** войти в город — «Empty streets and doors left open…». Проверить, что реплика звучит на
    въезде в город, а не только у отдельных зданий.

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
9. **Порядок «лифт → первый шаг»** в Оскверненных землях держится на порядке правил в `ALFSV_World.txt`:
   правило прибытия (`GRYMFORGE_LIFT_BLOCK`) стоит раньше общего `LevelGameplayStarted` мест, и очередь
   берёт первую заявку. Проверить п. 14b.
10. **Ясная ночь и праздник.** В ночь праздника тифлингов с ней (`ALFSV_Celebration_Tonight`, глава 4)
   реплика не звучит и ждёт следующего свободного вечера в лесном лагере.
11. **Лифт Гримфорджа по прибытии**, а не в поездке: поездки на экране нет (переход уровня без ролика,
   `GLO_LevelSwap_PostEA.txt:21`). Строка «If this rope snaps…» звучит как отклик на только что
   закончившийся спуск/подъём.

## 8. Беседы отряда, акт 1

По `design/banter/03_act1_party.md` (согласовано 2026-09-27). Описание — `scripts/dialogs/scenes/banter.py`
(`banter(...)`), механизм — `ads.banter` и регион «Party banters» в `ALFSV_World.txt` (генерируется).

**Как в игре.** Её беседы со спутниками в лагере — AD на двоих `CAMP_Bard_AD_Astarion`, `_GaleTressym`, `_Wyll`,
`_Volo` («Repeated automated NPC Dialog», корни по кругу локальными флагами). Своих условий у них нет — условие
`CAMP_DarkUrge_Event_RecruitAlfira` стоит только у её одиночного `CAMP_Bard_AD`; Osiris их не запускает (ни в
goals, ни в `Gossips.lsx`, ни в триггерах уровня) — судя по всему, их запускает поведение Anubis лагеря,
которое в `game-data` не распаковано. Поэтому запуск — наш, через `PROC_TryStartAD(диалог, Альфира,
собеседник)` (как `__GLOBAL_Dialogs.txt`). Беседы отряда Larian в пути (`GLO_WorldGossip`, `Gossips.lsx`) —
по триггерам мест; для «разговора двоих в пути» свой таймер надёжнее.

**Как у нас.** Раз в 20 с ищется одна беседа: она спутница, свободна (`QRY_SpeakerIsAvailable`, не в бою), нет
другой AD и ожидающих реплик мест, прошло 5 минут с прошлой беседы; беседа не исчерпана и её условия
выполнены; «в пути» — оба в активном отряде, она не в лагере, собеседник в 10 м; «в лагере» — она в лагере,
собеседник в 20 м от неё, кто-то из героев в 10 м от неё. Запуск — первая подходящая по списку.

| # | Собеседник | Где | Что | Условие |
|---|---|---|---|---|
| Б1–Б2 | Астарион | лагерь | ванильный `CAMP_Bard_AD_Astarion`, 2 раза (корень N1, затем N9) | Астарион в команде |
| Б3 | Астарион | путь | наш AD | после Б1–Б2 |
| Б4 | Астарион | путь | наш AD | у кого-то `ALFSV_Romance_Started` |
| Б5 | Тара | лагерь | ванильный `CAMP_Bard_AD_GaleTressym`, 2 раза | Тара рядом |
| Б6 | Гейл | путь | наш AD | — |
| Б7 | Уилл | лагерь | ванильный `CAMP_Bard_AD_Wyll`, 1 раз (корень N1; «непристойная» часть в данных игры и так звучит в обеих ветках — с рогами `WYLL_DEVIL` и без) | Уилл в команде |
| Б8 | Уилл | путь | наш AD; первая реплика — «Лакрисса…» или «Один тифлинг…» (`ALFSV_LakrissaDead` из `DB_Dead`) | после Б7 |
| Б9 | Шэдоухарт | путь | наш AD, её реплика 🔊 (`DEN_TieflingBard_Bard`) | — |
| Б10 | Лаэзель | путь | наш AD, её реплика 🔊 | — |
| Б11 | Карлах | лагерь | наш AD, первая реплика — голос Карлах 🔊 (`CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives`) | Карлах в команде |
| Б12 | Карлах | путь | наш AD | у кого-то `ALFSV_Elturel_AngrySong` (глава 6, «злая песня» — новый флаг) |
| Б13 | Хальсин | лагерь | наш AD | Хальсин в команде |
| Б14 | Воло | лагерь | ванильный `CAMP_Bard_AD_Volo`, 2 раза (N2, затем N12) | Воло рядом |

- **Наши AD бесед** — основа `CAMP_Bard_AD_Astarion` (её беседа на двоих), в копии на место Астариона встаёт
  собеседник (`Scene.other_base`: у спикера в `speakerlist` только uuid персонажа, актёры таймлайна — по номеру
  спикера). Реплики собеседника — `say(..., speaker=OTHER)` текстом или `voice(handle, speaker=OTHER)` с его
  голосом (озвучка проверяется по VoiceMeta говорящего). Ресурсы `ALFSV_Banter_B3…B13`, ID — от ключа
  (`uuid5(мод, "banter/<ключ>")`), ключи не менять.
- **Счётчик** — `DB_ALFSV_BanterPlayed(ключ, n)`; отладка из консоли SE: `Osi.PROC_ALFSV_Debug_Banter("B11")`.

Проверить в игре:
1. Б1 → через 5+ минут у костра Б2 (второй корень). Если второй раз снова Б1 — локальные флаги корней ванильного
   AD не сохраняются между запусками (тогда делать свои копии ванильных бесед).
2. Беседы в лагере звучат, когда герой проходит мимо неё, а собеседник стоит на своём месте (20 м — хватает ли?).
3. В пути — одна беседа за 5 минут, не в бою, не поверх реплик мест и фраз в пути.
4. Голос Карлах в Б11, её голоса в Б9 и Б10; текст спутников — над их головами.
5. Б4 — только после первого поцелуя; Б12 — только после «злой песни» в главе 6; Б8 — после Б7, вариант при мёртвой
   Лакриссе.

## 9. Разговоры акта 1 по событиям и по месту (0.8.0)

Статус: **собрано, в игре не проверено.** Сценарии — `design/dialogs/11_act1_events.md` (С1–С7) и
`design/dialogs/12_act1_local.md` (Л1–Л8, К1–К15), оба согласованы 2026-09-27. Разбор механики Larian —
[research/local-dialogs.md](research/local-dialogs.md). Новый goal `ALFSV_Talks.txt` (генерирует
`scripts/dialogs/talks.py`) и правка `ALFSV_Companion.txt` (после ухода в акте 1 вербовка закрыта) — поэтому 0.8.0.
Новой игры не нужно: на сохранении 0.7.0 goal новый, его INIT ставит тег и OM; данные вставляются и при каждой
загрузке уровня.

### 9.1 Как устроено

| Что | Сцены | Запуск |
|---|---|---|
| «!» по событию С1–С7 | `scenes/events.py`: `ALFSV_WRD_Event_*`, основа `DEN_Bard_InParty`, стоя | ванильная `PROC_RelationshipDialog(Альфира, диалог, NULL, Альфира)`; `DB_RelationshipDialog_WRD_TriggerInCamp` — знак в мире и в лагере (не ночью), `DB_ExclamationDialog_NeverStop` — не гаснет |
| «!» по месту Л1, Л5–Л8 | `scenes/local.py`: `ALFSV_WRD_Local_*` | та же процедура, категория `WORLD`: знак гаснет дальше 30 м (как у WRD Larian) |
| Сцена перед диалогом NPC Л2–Л4 | `ALFSV_OM_Local_Asharak/_Lakrissa/_Dammon`, основа `HAV_AlfiraTale_ReunionWithFlirty` (0 — NPC, 1 — Альфира, 2 — герой: так COM раздаёт спикеров); у Ашарака и Даммона их uuid на месте Лакриссы (`Scene.other_base`) | `PROC_DefineSingleOriginMoment(диалог NPC, ALFIRA, NULL, наша сцена, NULL)` — только COM; после сцены игра сама снимает OM и перезапускает диалог NPC |
| Реплики над головой К1–К15 | места `Talk_K01…K15` в `scenes/local.py` (конвейер этапа 5, `ads.place`) | К1, К3, К9 — глобальные флаги игры (`ALFSV_World.txt`); остальные — `PROC_ALFSV_Place_Request` из `ALFSV_Talks.txt` |

- **Начало разговора по событию** — общая реплика по тону и выбор героя: «Я слушаю, продолжай.» (реплика героя
  игры `h13b674ac…`; [решение сборки]: отказ должен быть до разговора) или «Не сейчас.» (`h13b3ab30…`). «Не сейчас»
  ставит на неё `ALFSV_Talk_Postponed`; когда игра записывает разговор в `DB_RelationshipDialogsFinished`, наше правило
  снимает запись и ставит знак снова — текст тот же. С2б — прощание без выбора и без отказа.
- **Условия.** Каждый разговор — один раз (`DB_ALFSV_TalkQueued(ключ)`). По событию — если она спутница в отряде или
  в лагере (`QRY_ALFSV_Talk_WithUs`); «была рядом» (С3–С6) — спикер того диалога или в отряде в 15 м от его героя
  (`QRY_ALFSV_Talk_Near`). По месту — она в активном отряде (Л1, Л7 — в 15 м от карты / ящика).
- **Одобрение за ответ** — реакции диалога (`ApprovalRatingID`), как в главах; −3 — новая реакция.
- **Эмоции** — по ремаркам сценария (`note=`) через её словарь постановки (`style.py`), как в главах.

### 9.2 Выбранные триггеры

| # | Триггер (данные игры) |
|---|---|
| С1 | `DEN_AttackOnDen_State_DenVictory` после `Event_Start` (реакция 1) или `GOB_State_LeadersAreDead` без `Lockdown` и `HostileTieflings` (3б) |
| С2а | `DEN_Lockdown_State_Active` (реакция 4). Итог — флаг игры `Approval_AtLeast_20_For_Sp1` на ней в конце разговора: одобрение уже с реакцией −10; ±1…2 за ответ в порог не входят ([решение сборки]: флаги порогов Osiris обновляет после узла). Ниже 20 — глобальный флаг `ALFSV_LeftWithRefugees`, `PROC_Origins_CompanionLeaveTemporarily(…, "ALFSV_LeftWithRefugees")` (одобрение и диалог в отряде остаются — для акта 2), уходит пешком (`PROC_DisappearOutOfSight … "Walk"`). `DB_ALFSV_IsCompanion` снимается — ванильные базы акта 2 (выжившие в «Последнем свете») её больше не теряют |
| С2б | `DEN_AttackOnDen_State_HostileTieflings` (реакция 2), она в отряде или в лагере. `DB_RelationshipDialog_AutostartTryOnce` — прощание начинается само, если может, иначе «!». После прощания (флаг `ALFSV_Talk_GatesFarewell`): `PROC_Origins_CompanionLeavePermanently`, флаг `ALFSV_LeftForGrove`, убегает (`… "Run"`), затем стоит в убежище детей (`S_DEN_AttackKidPos_011`, фракция роли «Hideout» `ACT1_DEN_AttackOnDen_Defenseless`). Резни в убежище ещё не было — её убивает сама игра (`PROC_DEN_AttackOnDen_KillKids`: безусловный `Die(S_DEN_Bard)`, `Act1_DEN_AttackOnDen.txt:3128-3133`), как без вербовки; уже была или налёт кончился (`RaiderVictory`) — `Die(…, DoT)` и лужа крови, как в `KillKids`. Страховка: прощание так и не нажато — при `RaiderVictory` или долгом отдыхе она уходит без него |
| С3 | `DEN_ShadowDruid_Event_StartDenouncingScene` при ней или `DEN_State_RitualStopped`, она в Роще |
| С4 | `DEN_ShadowDruid_State_FreedChild` при ней (Арабелла) или `DEN_HarpyMeal_State_HelpedSaveVictim` на ней (Миркон) — кто первый; для Миркона Osiris ставит на неё `ALFSV_Talk_Children_Mirkon` |
| С5 | `PLA_KarlachRecruitment_State_HelpingKarlach` / `ORI_Karlach_Quest_AgreedToHelpNotRecruited` при ней |
| С6 | **разговор с Нетти о личинке:** `DEN_Apprentice_Event_RevealedTadpole` на герое при ней (`Act1_DEN_Apprentice.txt:114-120`) — там объясняют цереморфоз. `GLO_Tadpole_TrueSoulCorpse` отвергнут: это диалог с трупом Истинной души, часто без неё и не о цереморфозе. У неё самой личинки нет: `ILLITHID` игра ставит только стартовым героям (`GLO_Tadpole.txt:17-21`), мод — тоже нет |
| С7 | `DB_CompanionReactedToFactionMemberDeath(Альфира, _)`, первый раз (реакция 18) |
| Л1 | `UseStarted(_, S_DEN_TieflingLeaderMap)` (`Act1_DEN_TieflingRefugees.txt:190-204`) |
| Л5 | `PLA_ConflictedFlind_State_RegularGnollsDead` |
| Л6 | `PLA_KarlachRecruitmentTollhouse_Knows_RefugeesAreCultists` |
| Л7 | `VoiceBarkEnded/Failed(HAG_Campsite_VB)` (`Act1_HAG_Boosters.txt:14`) |
| Л8 | конец AD К10 (`AutomatedDialogEnded`) |
| Л2–Л4 | OM на `DEN_Thieflings_Trainer`, `DEN_General_TieflingGuard10` (до праздника: снимается в `PROC_CAMP_GoblinHuntCelebration_SetupTieflings`), `DEN_Weaponsmith_PostEA`. Даммон: OM стоит, только пока Карлах не в `DB_Players` (у неё свой OM на этом диалоге, `Act1_OriginMoments_Karlach.txt:64`); с Карлах — «!» после `DialogEnded(DEN_Weaponsmith_PostEA)`, клик — наш `QRY_SelectCustomDialog` ставит ту же сцену на троих (Даммон, Альфира, герой); Даммон не рядом — её обычный разговор, знак остаётся |
| К2 | `VoiceBarkStarted(PLA_DyingHyena_VB_HyenaRunning)` — сразу, в бою, мимо ожидания свободной минуты |
| К4 | `PROC_FlagReactionAfterDialog(_, DEN_Thieflings_Event_TookGruel/2)`, она в диапазоне диалога с Октой |
| К5 | `DialogEnded` диалога ритуального друида (`DB_DEN_RitualDialogs`, хотфикс `Act1_DEN_SacredPond.txt`) |
| К6, К7, К8 | `VoiceBarkEnded(FOR_KidsGame_VB)`; `UseStarted(_, S_FOR_HoleBook)`; `DestroyedBy(S_FOR_DangerousBook_Tome)` — она в 15 м |
| К9 | `GLO_GoblinHunt_Quest_CampEntered` (пост у ворот, `Act1_GOB_Checkpoint.txt:118-128`) |
| К10 | `EnteredTrigger(Альфира, S_GOB_VoloBallad_FirstHeardArea)` + `GOB_VoloBallad_State_OnStage` |
| К11 | `PROC_FlagReactionAfterDialog(_, GOB_Checkpoint_Event_ReactOnPlayerPerformingSong)` |
| К12 | `GameBookInterfaceClosed` + `DB_UND_ArcaneTower_Poems` |
| К13 | `PROC_GLO_KnowledgeCheckSuccess(_, "CRE_Exterior_ArrivalStatuePlaque_Religion" / "…CourtyardStatue_Religion", _)` |
| К14 | `VoiceBarkStarted` реплик учебного зала (`CRE_YouthTraining_VB_TrainingDummyComment` / `…AnatomicalSketchesComment`) |
| К15 | сразу после её реплики места `UnderdarkFirst` (тот же вход в Подземье) |

**Тег `ALFIRA`.** На её персонаже его нет: шаблон `Tieflings_Female_Asmodeus_Civilian` без тегов Origin, в `Origins.lsx`
у Origin «Alfira» только `ReallyTags` (`REALLY_ALFIRA`), в goals игры тег не ставится нигде. `SetTag` — в
`PROC_ALFSV_Talks_Init` (при вербовке, в INIT goal и при загрузке уровня).

**Совпадения, о которых надо знать автору.** К15 и реплика места «Подземье, первый шаг» (`UnderdarkFirst`, «No sky,
no stars…») звучат одна за другой на одном входе; К9 (ворота лагеря гоблинов) идёт незадолго до места `GoblinCamp`
(двор) — две реплики подряд при входе в лагерь.

### 9.3 Идентификаторы (не менять)

| Что | ID / ключ |
|---|---|
| С1…С7: `ALFSV_WRD_Event_GroveHeld/RoadExpelled/GatesOpened/Kagha/Children/Karlach/Tadpole/Blood` | `1cc0cfa0-…`, `198867ca-…`, `101ef669-…`, `5aa81e7a-…`, `c4d68914-…`, `aa3e67b0-…`, `b2d25c91-…`, `09f9a65a-…` |
| Л1, Л5–Л8: `ALFSV_WRD_Local_ZevlorMap/Gnolls/Tollhouse/Campsite/Volo` | `92ebdc2b-…`, `500b4d1f-…`, `19b3079b-…`, `d14d576b-…`, `f3914786-…` |
| Л2–Л4: `ALFSV_OM_Local_Asharak/Lakrissa/Dammon` | `154c85d2-…`, `5858cd09-…`, `f5c9b87d-…` |
| ключи разговоров (`DB_ALFSV_Talk`, отладка) | `GroveHeld, RoadExpelled, GatesOpened, Kagha, Children, Karlach, Tadpole, Blood, ZevlorMap, Gnolls, Tollhouse, Campsite, Volo, Dammon`; OM — `Asharak, Lakrissa, Dammon` |
| места К | `Talk_K01_Gnolls … Talk_K15_Underdark` |

### 9.4 Отладка (консоль Script Extender)

| Команда | Что делает |
|---|---|
| `Osi.PROC_ALFSV_Debug_Talk("GroveHeld")` | снова поставить «!» разговора (не смотрит на «один раз»; она должна быть спутницей, для разговоров по месту — в отряде) |
| `Osi.PROC_ALFSV_Debug_TalkNow("Kagha")` | начать разговор сразу, без знака (с героем-хостом); `"Dammon"` — сцена на троих, Даммон рядом |
| `Osi.PROC_ALFSV_Debug_TalkMirkon()` | С4 начнётся с Миркона (по умолчанию — Арабелла) |
| `Osi.PROC_ALFSV_Debug_OM("Asharak")` | снова поставить сцену перед диалогом NPC, потом заговорить с ним (Лакрисса — только до праздника, Даммон — без Карлах) |
| `Osi.PROC_ALFSV_Debug_OMNow("Lakrissa")` | сцена на троих сразу (NPC рядом) |
| `Osi.PROC_ALFSV_Debug_Place("Talk_K05_Ritual")` | реплика над головой К сразу (общая отладка мест) |
| порог С2а | одобрение ниже 20: `Osi.ChangeApprovalRating("S_DEN_Bard_4a405fba-3000-4c63-97e5-a8001ebb883c", Osi.GetHostCharacter(), 0, -40)` **[проверить синтаксис]**, затем `Debug_TalkNow("RoadExpelled")` |

### 9.5 Что проверить в игре

1. **Знак «!» на её модели** (VFX `VFX_UI_ExclamationMark_01` на кости `Dummy_OverheadFX`): `Debug_Talk("GroveHeld")` в мире,
   потом в лагере днём; ночью в лагере знака нет. Клик — наш диалог; после него знак гаснет и больше не встаёт.
2. «Не сейчас» — знак возвращается, разговор тот же. Отойти на 50 м от места локального «!» (Л5) — знак гаснет.
3. Тег `ALFIRA` на ней (`Osi.IsTagged`); сцены Л2–Л4: заговорить с Ашараком, Лакриссой, Даммоном — сначала сцена на
   троих, потом их обычный диалог; во второй раз — только их диалог. Постановка: камеры `bnz_standing_Px2`, свет основы
   (сцена из «Последнего света» — не темно ли днём в Роще), реплики NPC пока без голоса.
4. Даммон при Карлах в отряде: её OM Larian; после разговора с Даммоном — «!» над Альфирой, клик — сцена на троих.
5. С2а: одобрение ниже 20 → «Не могу…», она уходит пешком, её нет ни в отряде, ни в лагере, стоит `ALFSV_LeftWithRefugees`;
   20+ → остаётся. С2б на стороне гоблинов: прощание (само или «!»), уход, её тело в убежище детей после налёта.
6. С6 у Нетти с ней в отряде; С3–С5 — только если она была рядом.
7. К2 звучит в бою; К10 → Л8; К15 — после «No sky, no stars…».

### 9.6 Ограничения

- **Выход из отряда в С2а/С2б** — ванильные процедуры ухода (`PROC_Origins_CompanionLeave*`), в игре не проверены.
  Возвращение в акте 2 (С2а) — сценарий акта 2; до него вербовку закрывает `DB_ALFSV_Left(_)` (`ALFSV_Companion.txt`).
- **С7 «уходит по общим правилам ухода»:** у неё нет `DB_OriginLeavingDialog`, поэтому ванильный уход при −50 ничего не
  сделает — это отдельная задача.
- **С2б:** если в момент открытия ворот она в отряде, бой начинается раньше прощания — она может оказаться в бою на
  стороне героя; прощание придёт после боя («!» после неудачного автостарта).
- Реплики NPC и новые реплики Альфиры — текст; список для озвучки — `voice-work/act1/lines_talks.json` (вне git),
  его источник — `build/dialogs/voice_lines.json` (build.py пишет все новые реплики с говорящим, лицом и ремаркой).
