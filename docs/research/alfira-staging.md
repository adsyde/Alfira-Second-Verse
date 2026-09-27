# Альфира у Larian: как поставлены её реплики

Сводка каталога её постановки (этап 9). Источник — `scripts/dialogs/alfira_catalog.py`: он проходит по всем
диалогам игры, где говорит Альфира (34 диалога, те же, что в `reports/dialogs/`), и по каждой её реплике
собирает ремарку редактора, эмоции лица, позы, взгляды, анимации и планы камеры. Сырой результат с текстами и
ремарками Larian — `reports/staging/alfira_catalog.json` и `.md` (локально, в git не идёт). Словарь для
генератора — `scripts/dialogs/alfira_style.json` (только идентификаторы и частоты), как он встроен — §6.

```
python scripts/dialogs/alfira_catalog.py            # ~45 с; список её диалогов кэшируется в reports/staging/
python scripts/dialogs/alfira_catalog.py --rescan   # заново найти её диалоги в game-data
```

## 1. Что в каталоге

- **548 её реплик** (2901 с голоса, медиана 4,9 с) и 19 фаз без голоса, где у неё есть `TLAnimation`
  (кат-сцены: смерть, Разговор с мертвым, воссоединение с Лакриссой).
- Окно реплики — от начала её `TLVoice` до следующего голоса в фазе (или конца фазы, но не дальше 3 с после
  голоса). В окне — только компоненты её актёра, кроме планов камеры.
- Ремарки редактора из `.lsj`: `NodeContext`, `CinematicNodeContext`, `AnimationTags`, метки `Emotion` и
  `Attitude`. Имена поз и анимаций — из `Public/Shared/Animation/ShortNames.lsx`, камер — из `TLCameras` сцен.

## 2. Лицо и тело: эмоции

Доля времени на её лице: sad 20 %, happy 18 %, fear 14 %, thinking 13 %, surprise 11 %, confusion 10 %,
angry 5 %, neutral 5 %, остальное (disgust, pain, sleeping, dead) — 5 %.

- **Ключи часто.** В среднем 2,7 ключа `TLEmotionEvent` на реплику — ключ каждые ~2 с. Внутри реплики меняется
  вариация той же эмоции или эмоция целиком (`sad/0 → happy/0` — 10 реплик из 130 грустных).
- **Нейтрально она почти не начинает**: первый ключ — sad (115), fear (92), happy (78), surprise (72).
- **Вариация — это жест.** В `Emotions.lsf` (`AnimSetToShortNames`) у каждой эмоции 6 анимаций-вариантов; номер
  вариации ключа выбирает, какая играет. Отдельных `TLAnimation` в её репликах почти нет (§3), поэтому её
  «жесты» — это вариации эмоций. Вариации 23, 24, 25 — особые (не из шести вариантов), их генератор не берёт.
- **Метки редактора** (`Emotion`) почти всегда `Default` (410 из 548); из заданных: `Sadness` (56) → лицо
  sad/0, fear/0, sad/2; `Happiness` (18) → happy/0; `Surprise` (16) → confusion/1, thinking/1, surprise/2;
  `Determination` (19) → happy/1, thinking/1, fear/1; `Anger` (11) → angry/2, sad/2.

Где что (главная эмоция реплик, первые три): `DEN_TieflingBard_Bard` — sad, happy, thinking;
`CAMP_DarkUrge_MurderOfAlfira_CFM_AlfiraArrives` — surprise, fear, happy; `HAV_AlfiraTale_Bard` — fear, sad,
angry; `CAMP_GoblinHuntCelebration_Bard` — confusion, thinking, happy; `LOW_Elfsong_Alfira` — happy, sad,
confusion; все AD в лагере Тёмного соблазна (`CAMP_Bard_AD*`) — sad.

### Таблица 1. Эмоция сценария → её эмоция у Larian

`emo=` в сценах (`dsl.EMOTIONS`) → её реплики с этой главной эмоцией. «Вариации» — сколько её ключей этой
эмоции с таким номером; жирным — те, что берёт генератор (до трёх, номера 0–5).

| emo сценария | реплик | вариации (ключей) | ключ раз в | частый ход лица |
|---|---|---|---|---|
| happy | 96 | **0** (68), **2** (37), **1** (33), 23 (12) | 2,1 с | happy/0; sad/0 → happy/0 |
| sad | 130 | **0** (102), **1** (42), **2** (28), 24 (10) | 2,1 с | sad/0; sad/0 → happy/0 |
| fear | 76 | **1** (35), **0** (26), **2** (25), 23 (4) | 2,0 с | fear/0; fear/1 → sad/0 |
| thinking | 63 | **0** (44), **1** (29), **2** (23), 3 (2) | 1,7 с | thinking/0 → happy/0 |
| surprise | 63 | **1** (28), **2** (25), **0** (17) | 2,0 с | surprise/2; surprise/2 → happy/2 |
| confusion | 55 | **2** (37), **1** (27), **0** (15) | 1,8 с | confusion/2 → neutral |
| angry | 32 | **2** (17), **0** (11), **1** (11), 23 (4) | 1,9 с | angry/2 |
| disgust | 11 | **1** (4), **0** (4), **2** (3) | 1,9 с | disgust → angry/fear |
| pain | 6 | **0** (3), **2** (3), **1** (1) | 1,8 с | fear/1 → pain/0 |
| neutral | 13 | 0 | ключей почти нет | — |

### Таблица 2. Ремарка сценария → её лицо и анимация у Larian

Ремарка сценария (`note=`, ремарка рассказчика) → её реплики, где редактор Larian пишет то же самое
(`NodeContext`/`AnimationTags`, английские слова — `alfira_catalog.REMARKS`). «Лицо» — эмоция/вариация и
секунды на лице во всех таких репликах; анимации — `TLAnimation` в этих репликах (uuid ресурса).

| ремарка | реплик | главная эмоция (реплик) | лицо, с | TLAnimation |
|---|---|---|---|---|
| краснеет | 4 | happy (4) | happy/0 4.3, happy/2 2.8, sad/0 2.2, happy/1 1.9 | — |
| смеётся | 9 | happy (4), confusion (3), thinking (2) | thinking/0 11.2, happy/1 6.7, confusion/1 5.6, happy/2 5.2 | — |
| улыбается | 36 | happy (16), sad (6), confusion (5) | happy/2 34.8, happy/0 30.0, sad/0 17.3, thinking/0 11.7 | `13405ac3` ×1 |
| грустно | 92 | sad (47), fear (13), happy (10) | sad/0 105.1, sad/1 49.5, sad/2 39.9, fear/0 38.6 | — |
| тихо | 13 | happy (6), sad (2), thinking (2) | happy/0 26.4, happy/1 11.6, thinking/0 8.8 | — |
| плачет | 17 | sad (8), confusion (4), angry (3) | sad/2 14.8, sad/0 6.5, angry/2 5.7, sad/24 5.6 | — |
| испуг | 44 | sad (14), fear (11), surprise (8) | sad/0 45.3, fear/1 32.8, surprise/2 26.8, fear/2 19.8 | `89019982` ×1 |
| злится | 41 | sad (12), angry (9), fear (6) | sad/0 16.9, angry/2 15.5, angry/0 14.9, sad/1 14.2 | `34d69caf`, `d47d576f` |
| думает | 20 | sad (5), happy (4), fear (4) | happy/0 11.0, sad/1 10.6, happy/1 9.4, surprise/2 9.1 | — |
| удивлена | 28 | fear (8), thinking (7), confusion (5) | fear/2 13.4, thinking/1 13.0, confusion/1 12.8 | `e9ca7a17`, `13405ac3` |
| нежно | 30 | happy (12), surprise (6), confusion (4) | happy/2 30.1, happy/1 24.3, surprise/1 20.8, happy/0 14.3 | `8b35c8aa` ×1 |
| дразнит | 17 | happy (8), confusion (5), thinking (2) | happy/2 16.8, confusion/2 12.5, surprise/1 12.1, happy/1 11.8 | — |
| восторг | 26 | happy (11), surprise (8), sad (2) | surprise/1 21.8, happy/0 20.7, happy/2 20.3 | — |
| устала | 6 | sad (2), confusion (2), happy (1) | sad/0 9.3, sad/1 5.8, happy/0 5.1 | — |
| поёт | 27 | happy (7), sad (7), fear (5) | happy/0 22.5, sad/0 17.4, sleeping/0 15.7, fear/0 15.4 | — |
| играет на лютне | 68 | happy (13), thinking (12), sad (9) | happy/1 32.5, thinking/0 26.3, neutral/0 24.9 | `d47d576f` ×3, `e9ca7a17` ×2 |
| гордо, вздыхает | 1, 2 | — | мало данных | — |

«Пожимает плечами» и «пьяная» у неё в ремарках Larian не встречаются (на празднике она пьёт, но редактор это
не пишет).

## 3. Анимации (TLAnimation)

- **В репликах — 12 на 548**, все в `DEN_TieflingBard_Bard` (песня в Роще, лютня) и одна —
  `CINE_WeightShift_StandL_01` в `HAV_AlfiraTale_ReunionWithFlirty`. Ресурсы `d47d576f` (×3, 4,2 с, с гневом —
  лютня сломана), `e9ca7a17` (×2, с root motion), `34d69caf`, `8b35c8aa`, `89019982` — имён в `ShortNames.lsx`
  нет; привязаны к её камню и лютне в Роще. Переносить их в чужую сцену генератор не стал.
- **В кат-фазах** (19): `CINE_Dead_Pose_03` (×6, `CAMP_DarkUrge_MurderOfAlfira_SD_BloodOnHands`),
  `CINE_Dead_Pose_01`, `CINE_SpeakWithDead_Corpse_02_Start/Loop/End` (`DEN_TieflingBard_Dead`),
  `CINE_Still_Breathing_Idle_StandL_01`, `CINE_Approve_React_01`, `CINE_NodHead_Yes_StandL_02` (воссоединение).

## 4. Позы, взгляды, камеры

- **Поза** — `DIAG_Pose_Stand_R_Forward_01` (88 ключей в 87 репликах; в остальных ключа позы в окне нет — поза
  держится с начала сцены). Та же поза у неё в шаблонной фазе `DEN_Bard_InParty` — менять не нужно.
  Сидит она у Larian только на своём камне в Роще (`Cam_Custom_SeatedGreeting_01`, своя камера сцены).
- **Взгляд** — на героя (272 ключа из 305), кость `Head_M`; на Лакриссу и других NPC — 15.
- **Камеры** — 1,2 плана на реплику: `cam_subject1_OTS_player` (105 + 14 своих вариантов сцены),
  `cam_subject1_MCU` (105 + 41), `cam_subject1_OTSCLOSE_player` (56 + 48), `cam_subject1_CU` (45 + 26),
  `Q_cam_player_WIDEOTS_subject1` (35 + 31), на героя — `cam_player_MCU`, `cam_player_OTS_subject1`. У нас
  `alfira` = OTS из-за плеча героя, `alfira_close` = CU, `player` = MCU героя — те же планы.

**Сидя у костра у Larian** (для глав, §6). Спутник и герой в лагерных сценах сидят позами диалога
`DIAG_Pose_SitGround_*` поверх обычной сцены `bnz_standing_Px1`, переход — `DIAG_T_Pose`, поза держится всю
фазу: `CAMP_GalesLastNightAlive_SD_ROM` — Гейл `SitGround_HandsDn_01`, герой `SitGround_CrossLegs_01`;
`CAMP_DaisyCourseCorrection_AvD` — `RKneeUp_01` / `LKneeUp_01`; `CAMP_DarkUrge_SparedIsobel_SD` — `LKneeUp_01`,
`HandsDn_01`. Сцены с реквизитом (`CAMP_GoblinHuntRaiderCelebration_CRD_Shadowheart` — «Sit_byFire»,
`CAMP_BurningUpForYou_CFM_ROM` — «SitOpposite») ставят героя своими `TLAnimation` и своими камерами
(`cam_subject1_2SHOT_player_Sitting`) — к нашей сцене они не подходят.

## 5. Сцена на троих: она и Лакрисса

`HAV_AlfiraTale_ReunionWithFlirty` (спикеры: 0 Лакрисса, 1 Альфира, 2 герой; сцена `bnz_standing_Px2`, свет
EXT_NIGHT) и `LOW_Elfsong_Alfira_Lakrisssa`. На празднике у них только AD (`…_AD_Bard_Flirty`, без сцены и
камер), поэтому образец — воссоединение:
- реплика Лакриссы: `cam_subject1_OTS_player` → `cam_subject1_CU`; Альфира смотрит на Лакриссу, герой — на неё;
- реплика Альфиры: `cam_subject2_MCU` (или `cam_subject2_OTS_player`); она смотрит на героя, Лакрисса — на неё;
- обмен между ними: `cam_subject1_OTS_subject2` ↔ `cam_subject2_OTS_subject1`, взгляды друг на друга;
- первая фаза — вход в сцену (`CINE_StepForward_to_StandL`, `CINE_Slow_Walk_to_Stop`, `CINE_TurnRight105`):
  её как шаблон брать нельзя — шаги повторялись бы на каждой реплике.

## 6. Как это встроено в генератор

- **Лицо Альфиры** в текстовых репликах и ремарках (`staging.text_phase`, AD — `ads.ADStager`) строит
  `scripts/dialogs/style.py` по `alfira_style.json`: эмоция без вариации (`emo="happy"`) — её три частые
  вариации, по ключу на 2–4 с (её частота ключей), первая выбирается по uuid узла; ремарка (`note=` по-русски
  или текст `narrate` по-английски) — вариации из её реплик с той же ремаркой; `emo` не задана, а ремарка есть —
  её главное лицо для этой ремарки. `emo="happy/2"` и списки ключей — как написал автор. `style.ENABLED = False`
  возвращает прежний шаблон.
- **Сидя** — `Scene(seated=…)` / `block(seated=…)` (`staging.SEATED`), §4.
- **Сцена на троих** — шаблонная фаза своя у каждого говорящего (первая фаза основы с одним его голосом, где
  никто не ходит), взгляды и планы — из неё (§5).
- Пересобрать словарь: `alfira_catalog.py`, затем `build_pak.py`. Формат сцен не меняется.
