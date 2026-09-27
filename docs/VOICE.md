# Голос

**Решение автора 2026-09-27: клон голоса, две сборки.**
- Автор сообщил, что у него есть разрешение актрисы Альфиры на реализацию и публикацию
  (письменное согласие хранит автор; в репозиторий не кладётся).
- **Личная сборка** — клон, обученный на её репликах из игры (548 реплик, 47 мин). Не публикуется.
- **Публичная сборка** — согласие актрисы снимает запрет §4.5 на имитацию голоса, но не запрет на
  извлечение аудио из файлов игры для машинного обучения. Поэтому для публикации модель учится
  на записях, которые даёт сама актриса (не из игры), или нужно письменное согласие Larian.
  До этого публичная сборка — без клона: текст и её реплики из игры.
- Её озвученные реплики игры (🔊) остаются в обеих сборках как есть.

## Ограничение: правила Larian

Fan Content Policy, §4.5 (31.07.2025), подробности в
[research/community-and-tools.md](research/community-and-tools.md), запрещает
в опубликованном фанатском контенте:
- имитировать голоса актёров озвучки Larian без их письменного согласия;
- извлекать аудио из файлов игры для машинного обучения.

Значит, мод с клонированным голосом Альфиры нельзя выкладывать. Варианты:

| Вариант | Публикация | Похожесть | Цена |
|---------|------------|-----------|------|
| Реплики без озвучки (только текст) | можно | — | 0 |
| Переиспользовать её существующие реплики, где они подходят по смыслу | можно | 100% | время на подбор |
| Заказать запись у актрисы Альфиры (письменное согласие) | можно | 100% | гонорар |
| Другая актриса / синтетический голос без клонирования | можно | «в духе» | от 0 |
| Клон по записям игры | **только для себя**, не выкладывать | высокая | GPU и время |

## Что уже известно про исходный материал

`scripts/voice/extract_voice.py` собирает датасет в `voice-work/dataset/`
(в git не попадает):

- VoiceMeta: `VoiceMeta.pak → Mods/Gustav/Localization/English/Soundbanks/4a405fba30004c6397e5a8001ebb883c.lsf`,
  то есть handle реплики → файл `.wem`, длительность и приоритет;
- аудио: `Voice.pak`, `v4a405fba30004c6397e5a8001ebb883c_<handle>.wem` (Vorbis);
- текст: английская loca по тому же handle.

Проверено 2026-09-26: **548 реплик, 47,4 минуты**, у каждой есть аудио и текст.
Этот же список пригодится, чтобы подбирать существующие реплики по смыслу:
metadata.csv — это каталог всего, что Альфира уже говорит голосом.

## Клон для личной сборки: этап 8, акт 1

Статус на 2026-09-27: референсы и слепое сравнение готовы; автор выбрал Breeze TTS 2 и IndexTTS-2.5 без
дообучения. Собран конвейер личной сборки (`build_pak --voice clone`) и поставлена на пробу одна
реплика — ниже, «Первая проба в игре». **В игре ещё не проверено.**

Всё аудио, модели, venv и кэши лежат в `voice-work/` (в git не попадает). В git — только
скрипты `scripts/voice/`, идентификаторы (handle) и эта документация.

### Порядок

```text
python scripts/voice/extract_voice.py          # .wem → .wav, metadata.csv (548 реплик, 47,4 мин)
python scripts/voice/label_emotions.py         # labels.csv, refs/<эмоция>/, dataset/finetune/
python scripts/voice/compare_models.py prepare # задания для сравнения
python scripts/voice/compare_models.py stress chatterbox --minutes 7   # стабильность GPU
python scripts/voice/compare_models.py run chatterbox breeze indextts voxcpm
python scripts/voice/compare_models.py score   # метрики (venv _metrics)
python scripts/voice/compare_models.py publish # compare/lineNN/, same_text/, LISTEN.md
python scripts/voice/game_voice.py --handle <h> --wav <48 кГц wav>   # прототип файлов для пака
python scripts/voice/voice_line.py all --handle <h> --emotion <эмоция> … # дубль → voice-work/game/
python scripts/build_pak.py --voice clone                            # личная сборка с голосом
```

Инструменты вне репозитория: vgmstream r2117 (`C:\Tools\vgmstream`, официальный релиз
github.com/vgmstream/vgmstream), uv 0.12.19 (`voice-work/tools/uv`, релиз astral-sh/uv).
Окружение моделей — `voice-work/env.sh`: кэши uv, pip, HuggingFace, torch и сам Python 3.11
лежат в `voice-work/`, в систему ничего не ставится.

### Разметка по эмоциям (`label_emotions.py`)

Для каждого handle скрипт находит узел диалога игры, где его говорит Альфира, и берёт:
- ремарки из editorData узла, по точности: `VOContext` (прямая ремарка актрисе, 63 реплики),
  `NodeContext` (258), `CinematicNodeContext`; поле `Emotion` узла (Sadness, Coyness…);
- эмоции её лица в таймлайне на этой реплике: `TLEmotionEvent` её актёра в окне её `TLVoice`
  (через bg3moddinglib, как `staging.voice_window`). Лицо — слабый признак: Larian ставит `fear`
  и на радостное «Really? Oh, this is wonderful!». В референсы идут только реплики с ремаркой;
- звук: пик, клиппинг, тишина по краям, уровень пауз между словами. Её записи студийные: паузы —
  цифровая тишина, музыки под голосом нет. Замечание «паузы громче −55 дБ» у 42 реплик —
  дыхание и хвосты (в том числе обработка «Разговора с мёртвыми»); они не берутся в референсы.

Исключены из референсов и датасета: пение 25 и пение с речью 3 (по тексту «Плача рассвета» и
по `DEN_TieflingBard_AD_FullSong`; декламация на празднике — речь, canon §8), «Разговор с
мёртвыми» 7, рыдание 1, короткие выкрики 58 (речь < 1,6 с или ≤ 2 слов), повторы текста 15,
отложенная выборка 5 (`holdout.json`, ниже).

Категории (всего / без исключений): грусть 143/124, воодушевление 66/58, страх 61/53,
злость 54/41, нейтраль 37/29, благодарность и тепло 33/30, навеселе на празднике 33/28,
удивление 29/25, подначка 19/19, сквозь слёзы 13/10, смех 10/9, флирт и нежность 9/9,
смущение 7/5, усталость 5/5, шёпот 1/1. **Похмелья в её банке нет**, ремарок «пьяная» тоже:
«навеселе» — весёлые реплики праздника (она пробует вино). Для похмелья в сравнении взят
референс «усталость».

`voice-work/refs/<категория>/` — до 8 лучших фрагментов 3–12 с на категорию (края тишины
подрезаны, текст в `.txt`, сводка в `index.csv`). `voice-work/dataset/finetune/` — ровная речь для
дообучения: 377 реплик, 33,4 мин, 48 кГц, без пения, выкриков, шёпота, смеха, слёз и «навеселе»;
списки `metadata.csv` (file|text), `gptsovits.list`, `train.jsonl` (формат VoxCPM/Qwen3-TTS:
audio, text, duration).

### Кандидаты (проверено по репозиториям и карточкам моделей 2026-09-27)

| Модель | Версия | Лицензия | Эмоции | Дообучение | Windows |
|---|---|---|---|---|---|
| IndexTTS-2.5 (bilibili) | тег v2.5.0, 2026-08-10 | bilibili Model Use License: некоммерческое — можно | отдельный эмоциональный референс, `emo_alpha`, вектор 8 эмоций, эмоция из текста | официального нет | официально, uv; без DeepSpeed |
| Breeze TTS 2 (BreezeBlue) | код 008f769, веса 2026-09-09 | код Apache-2.0; веса и результаты — только исследования и некоммерческое | «Voice Direction»: референс + свободная инструкция («flirty, embarrassed»), `(laugh)` `(sigh)` в тексте | официального нет | официально Linux; у нас работает нативно (eager, медленно) |
| VoxCPM2 (OpenBMB) | 2.0.3 | Apache-2.0 | стиль в скобках в начале текста, «ultimate cloning» по референсу с текстом | **официально**: LoRA и полное SFT, JSONL | pip; без triton |
| Chatterbox (Resemble AI) | 0.1.7 | MIT | референс + ручки `exaggeration` / `cfg_weight` | только сторонние скрипты | pip; нужен `setuptools<81` (perth) |

Отсеяны: Fish S2 Pro (24 ГБ, Linux, S1-mini закрыт логином), Higgs TTS 3 и Step-Audio-EditX (только
серверы vLLM/SGLang под Linux), Voxtral (управление голосом только в облаке Mistral), Qwen3-TTS
(у клона нет instruct; запасной вариант, если нужно дообучение), CosyVoice 3 (инструкции
по-китайски), GPT-SoVITS (последний релиз 2025-06, эмоция только референсом). Breeze, VoxCPM
и Higgs в лицензиях запрещают клонирование голоса без согласия: у автора есть согласие актрисы,
сборка личная.

Каждая модель — в своём venv под `voice-work/models/<имя>/`, обёртка — `scripts/voice/tts/run_<имя>.py`.

### Слепое сравнение (`compare_models.py`)

- 10 новых реплик ✍️ с разными эмоциями (`compare_lines.json`): смех, смущение, грусть,
  обида, флирт, тихо, навеселе, похмелье, страх, воодушевление;
- «тот же текст»: 5 её реплик из игры (`holdout.json`), которых нет ни в референсах, ни в
  датасете. Модели озвучивают их текст по референсу той же эмоции, рядом — оригинал;
- все модели получают один и тот же референс эмоции; 3 варианта на реплику и модель
  (у каждой свои настройки, см. обёртки), в сравнение идёт лучший по метрикам;
- выход: `voice-work/compare/lineNN/lineNN_A..D.wav` + `lineNN_ORIG_ref.wav`,
  `voice-work/compare/same_text/sNN_ORIG.wav` + `sNN_A..D.wav`, лист `LISTEN.md`; буквы
  перемешаны для каждой реплики, громкость и частота выровнены. Ключ и метрики —
  `voice-work/compare/_key/` (раскрывают модели, автору до выбора не показывать).

### Конвейер в игру (исследование; в сборке с 27.09 — ниже, в игре не проверено)

По данным игры (Patch 8 Hotfix 9) у озвученной реплики её голоса пять частей:

| Что | Где в игре | Что делаем мы |
|---|---|---|
| звук | `Localization/Voice.pak → Mods/Gustav/Localization/English/Soundbanks/v<id>_<handle>.wem`, Wwise Vorbis 48 кГц моно | `.wem` Wwise **PCM** (fmt 0xFFFE) — пишется без Wwise |
| VoiceMeta | `VoiceMeta.pak → …/Soundbanks/4a405fba30004c6397e5a8001ebb883c.lsf`: `VoiceSpeakerMetaData` (MapKey — её uuid) → `VoiceTextMetaData` (MapKey — handle) → `Codec`, `Length`, `Priority`, `Source` | свой банк с тем же именем в папке мода, только новые handle, `Codec=PCM` |
| липсинк | `English_Animations.pak → …/English/Animation/FX_v<id>_<handle>.ffxanim` (FaceFX) | заимствуется её `.ffxanim` реплики близкой длины |
| жесты | там же `MC_v<id>_<handle>.gr2` (мокап; у 7 её реплик нет — необязателен) | заимствуется там же |
| актёр FaceFX | `…/Animation/FaceFXActors/4a405fba-3000-4c63-97e5-a8001ebb883c.ffxactor/.ffxbones` | копия её файлов в папку мода |

`Length` в VoiceMeta = число сэмплов / 48000 (совпало у всех 545 её `.wem`). `TLVoice` в таймлайне
на файл не ссылается: узел диалога → handle → VoiceMeta.

Что мешает:
- **Wwise Vorbis без Wwise не сделать**: открытого кодировщика нет (ww2ogg и vgmstream только
  читают). Wwise скачивается через Audiokinetic Launcher, для него нужен аккаунт — не создаём.
  Обход — Wwise PCM: vgmstream читает наш `.wem` как «Audiokinetic Wwise RIFF, 16-bit PCM»,
  кодек `PCM` есть в списке кодеков `bg3_dx11.exe`. Примет ли его игра — **первая проверка в игре**.
  Файлы в 6 раз больше Vorbis (~94 КБ на секунду).
- **Липсинк**: `.ffxanim` — скомпилированные данные FaceFX (магия `__ffx`), открытых
  инструментов нет, сам FaceFX платный. Варианты: (а) заимствованный её `.ffxanim` — рот
  двигается, но не по словам (прототип так делает); (б) по руководству сообщества — Rhubarb Lip Sync
  + Blender + ригги BG3, экспорт GR2 через LSLib, в таймлайн `TLAdditiveAnimation` слот 1;
  (в) без липсинка рот не двигается.
- Голос звучит только в английской озвучке (русский текст — субтитрами, как у реплик игры).

Прототип: `scripts/voice/game_voice.py` собирает для одного handle в `voice-work/pipeline/proto/`
`.wem` + VoiceMeta (.lsx/.lsf через Divine) + заимствованные FX_/MC_ + FaceFXActors.
Для VoiceMeta в генераторе можно взять `soundbank_object` из bg3moddinglib (MIT; там Codec
жёстко VORBIS — поле нужно менять).

### Две сборки: флаг `--voice clone` (сделано 27.09)

```text
python scripts/voice/voice_line.py all --handle h… --emotion <refs/…> [--ref файл] --instruct "…" --vector …
python scripts/build_pak.py                   # публичная: dist/AlfiraSecondVerse.pak, реплики ✍️ — текстом
python scripts/build_pak.py --voice clone     # личная: build/personal/AlfiraSecondVerse_personal.pak
python scripts/install.py [--voice clone]     # ставит одну из двух: копию другой убирает из Mods
```

- `voice_line.py` озвучивает реплику Breeze и IndexTTS (по 3 варианта), считает метрики (venv `_metrics`)
  и выбирает дубль: из вариантов с WER ≤ 0,15 — самый похожий (ECAPA + WavLM к центру её голоса).
  Все варианты, приведённые к 48 кГц и одной громкости, — `voice-work/trial/<handle>/norm/`.
  Перед каждой моделью смотрит свободную видеопамять (`nvidia-smi`): если её меньше, чем нужно
  (IndexTTS 7 ГБ, Breeze 9,5 ГБ), модель считается на процессоре (`--device auto`; `gpu` — ждать памяти).
  Breeze на процессоре идёт через `model.generate` (потоковый рантайм — только CUDA) с тем же CFG.
- Выбранные дубли лежат в `voice-work/game/<handle>.wav` (48 кГц моно) и `voice-work/game/voice.json`
  (handle → файл, длина, модель, метрики). В `mod/` (git) клон не попадает никогда.
- `--voice clone`: генератор (`scripts/dialogs/build.py`, `generate(voice=…)`) заполняет
  `Stager.voice_durations[uuid узла]` длинами дублей; `Stager.phase_duration()` даёт фазу «длина звука +
  TAIL 0,6 с» вместо длины по тексту, `TLVoice` — на длину звука. `build/dialogs/manifest.json → voice_clone`
  — список озвученных handle; `build_pak --no-generate` проверяет, что таймлайны в `mod/` собраны для
  того же набора. После конвертации `build_pak` кладёт в `Mods/<папка>/Localization/English/` файлы
  `game_voice.write_takes()`: `Soundbanks/v<id>_<handle>.wem`, `Soundbanks/<id>.lsf`, `Animation/FX_/MC_`,
  `Animation/FaceFXActors/`.
- Путь проверен по пакам игры 27.09: все 184 978 `.wem` `Voice.pak` лежат в
  `Mods/Gustav/Localization/English/Soundbanks/`, её банк VoiceMeta — там же в `VoiceMeta.pak`, `Source`
  — только имя файла. В `bg3_dx11.exe` есть строка `Localization/English/Soundbanks` (путь внутри папки
  модуля), поэтому наш `.wem` лежит рядом с нашим банком в папке нашего модуля.
- Для AD-реплик (над головой) — приоритет `P4_RepeatingDialog_AD`, для сюжетных — `P1_StoryDialog`
  (пока все — `P1`, AD генератор с голосом клона ещё не связывает).

### Первая проба в игре: одна реплика (27.09, в игре ещё не проверено)

**Реплика** — первая, которую герой слышит в нашей вербовке: приветствие `A1_duet`
(`scenes/recruitment.py`), handle `habe18d85g7bf6g5207gbb65g98953eaaf91c`, узел
`6b469df3-426b-59ee-bc06-4a53edd164cb`, фаза 43 таймлайна `ALFSV_Alfira_Recruitment`.
EN: «There they are - my accompanist! I've been humming that bridge all morning. Lihala would've said
I'm *insufferable*.» RU: «А вот и мой аккомпаниатор! Всё утро напеваю тот переход. Лихейла сказала бы,
что я *невыносима*.»

Почему она: в сохранении **«Леший — Лес — 5ч 02м» (25.09, 13:57)** песня закончена
(`DEN_TieflingBard_State_FinishedSong`), лютню не крали (`ReturnedInstrument` нет), тифлинги в Роще,
а на аватаре (Леший, варвар-человек) стоит `DEN_TieflingBard_Event_GiveProficiency` (дуэт на лютне;
статус `DEN_ALFIRA_PROFICIENCY` тоже на нём, проверено по `Globals.lsf` сохранения). Значит, из
приветствий A1 срабатывает `A1_duet`. Альфира в сохранении — в Роще у тифлингов (≈ 284, 22, 494),
герой — в лесу (≈ −13, 37, 434).

**Голос:** референс «воодушевление» `refs/excited/h3acb7afc…wav` («sincere and excited»: концерт для
детей), подача Breeze — «warm and delighted, beaming, a cheerful teasing greeting to a friend», вектор
IndexTTS — радость 0,7, удивление 0,2, спокойствие 0,1. Видеокарта была занята озвучкой акта 1
(свободно 5,5–8,7 ГБ), поэтому IndexTTS считался на процессоре (~50 с на вариант).
Breeze не считался: его потоковый рантайм работает только на CUDA (`fast streaming requires a CUDA
device`; обычный `model.generate` на процессоре с этими входами падает), а видеокарту целиком занимала
озвучка акта 1 (Breeze + метрики, свободно до 0,2 ГБ). Когда видеокарта освободится:
`voice_line.py gen --models breeze … --device gpu`, затем `score` и `pick` (параметры — в `trial/<handle>/jobs.json`).

| Вариант | ECAPA | WavLM | WER | Whisper |
|---|---|---|---|---|
| **IndexTTS v1** (эмоция из референса, α 0,8) — выбран | 0,546 | 0,807 | 0,12 | «…Lihala would have said I'm insufferable.» |
| IndexTTS v3 (только референс) | 0,475 | 0,799 | 0,24 | «…Lehala would have said I'm inseparable.» |
| IndexTTS v2 (вектор эмоций) | 0,188 | 0,743 | 0,12 | текст верный |
| её собственные реплики к центру голоса | 0,695 | 0,950 | — | — |

WER 0,12 у v1 — только «would've» → «would have». Дубль: `voice-work/game/habe18d85g7bf6g5207gbb65g98953eaaf91c.wav`
(6,34 с), все варианты — `voice-work/trial/habe18d85g7bf6g5207gbb65g98953eaaf91c/norm/`.

**Сборка:** `build_pak --voice clone` → `build/personal/AlfiraSecondVerse_personal.pak` (450 файлов,
публичный — 444): `.wem` Wwise PCM 48 кГц моно 6,339 с (vgmstream читает его из пака как «Audiokinetic
Wwise RIFF, 16-bit PCM»), банк VoiceMeta (`Codec=PCM`, `Length=6.339062`, `Priority=P1_StoryDialog`),
FX_/MC_ от её реплики `h35f52e08gba2bg44cag94edg8b6f0318084a` (6,34 с, «Heh. She'd yell at me for that
metre…»), FaceFXActors. Фаза 43 — 6,939 с (6,339 + 0,6), `TLVoice` — 6,339 с. `check_story`,
`validate` — без ошибок.

**Установка** (27.09 не выполнена: был открыт BG3 Mod Manager Redux). При закрытых BG3 и менеджере:
`python scripts/test_mode.py on` (ставит публичный пак и выключает AJTP с переводом и патчем), затем
`python scripts/install.py --voice clone` — личный пак вместо публичного, мод последним, после Alfira Redone.

**Что проверить в игре** (личный пак, `test_mode.py on`; запуск — только `bg3_dx11.exe`):
1. Загрузить «Леший — Лес — 5ч 02м» (25.09). Сохранения «Лешего» позже 26.09 14:40 без AJTP не открывать.
2. Путевая точка «Изумрудная роща» → тифлинги, Альфира. Заговорить с ней **самим Лешим** (не спутником:
   вербовку открывает только аватар).
3. Первая реплика — «There they are - my accompanist!…» с голосом. Смотреть:
   - звучит ли голос вообще (если тишина и субтитр 6,9 с — игра не приняла Wwise PCM);
   - двигается ли рот (липсинк чужой реплики: рот не по словам, но должен двигаться);
   - не обрывается ли звук до конца фазы и нет ли долгой немой паузы после (фаза = звук + 0,6 с);
   - нет ли лишних жестов от MC_ донора;
   - после реплики — меню A2 как обычно, остальные реплики ✍️ — без голоса, реплики игры — с её голосом.
4. Выйти без сохранения, закрыть игру, `python scripts/test_mode.py off`.

### Видеокарта

RTX 4080 SUPER 16 ГБ, драйвер 617.14 (с 27.09; до этого 616.92). Сбросы `nvlddmkm` 153 в журнале
System: 38 за май–сентябрь (3.05 — 3, 6.06 — 3, 15.08 и 22.08 — по 1, 6–10.09 — 21, 21.09 — 9),
после установки 617.14 — ни одного. Проверка 27.09: 7 минут генерации Chatterbox — без сбросов,
до 168 Вт и 59 °C. Power limit 320 Вт (допустимо 150–320) меняет только администратор:
`nvidia-smi -pl 250` перед дообучением.
