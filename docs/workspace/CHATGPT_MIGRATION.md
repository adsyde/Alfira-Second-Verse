# BG3: переход с Claude Code на ChatGPT / Codex

Дата: 01.10.2026. Область обзора — все проекты в C:/Users/AdSyDe/Repo/Games/BG3.
Проверены структура папок, Git-репозитории и рабочие деревья, все варианты
CLAUDE.md, имеющиеся README, документы передачи сессии и точки входа сборки.
Это обзор и перенос инструкций, а не полный аудит каждого файла реализации
или проверка модов в игре. Репозитории вне этой рабочей области не исследовались.

## Что подготовлено
- Общий AGENTS.md для рабочей области и самостоятельный AGENTS.md в каждом
  непустом каталоге проекта. Их можно читать отдельно при открытии проекта.
- Из 17 CLAUDE.md перенесены предметные правила, источники истины, ограничения
  публикации и требования проверки. Оригиналы сохранены для Claude Code.
- Для DialogKit, SuccubusPlus, SSF, MintharaVarC и локальных модов без CLAUDE.md
  написаны инструкции по README, документам передачи и существующим скриптам.
- В документах NEXT_SESSION.md заменены привязки к Claude Code и стартовому
  CLAUDE.md на ChatGPT / Codex и AGENTS.md. История и задачи сохранены.
- SendUserFile заменён сохранением локальных файлов и абсолютными ссылками.
  .claude/settings.local.json и scheduled_tasks.lock оставлены без изменений:
  это не настройки и не расписания Codex. Автоматики не создавались.

## Карта основных проектов
| Проект | Назначение | Начало работы |
|---|---|---|
| AlfiraCompanion | Alfira: Second Verse, спутница Альфира | AGENTS.md, docs/ROADMAP.md, docs/NEXT_SESSION.md, docs/VOICE.md |
| AlfiraSV-* | 13 Git worktree Альфиры на отдельных ветках | Инструкции и документы именно текущей ветки; список ниже |
| ATECCRus | Перевод Act Two Expansion | AGENTS.md, docs/WORKFLOW.md, glossary/style-guide.md |
| WyllPactPointsRU | Перевод If Fate Chose Differently | AGENTS.md, docs/WORKFLOW.md, glossary/style-guide.md |
| TeamEffort | Навыки и реплики спутников | AGENTS.md, docs/NEXT_SESSION.md, docs/TESTING.md |
| DialogKit | Общий конвейер патчей диалогов | AGENTS.md, README.md, tests/ |
| SuccubusPlus | Личная сборка класса суккуба | AGENTS.md, docs/NEXT_SESSION.md, README_RU.md |
| SSF | Голова и текстуры Шэдоухарт | AGENTS.md, README.md, docs/TEXTURES.md, docs/RESTORE.md |
| MintharaVarC | Перепаковка реплейсера Минтары | AGENTS.md, README.md, scripts/build.py |
| AutoStackMerge, CarryWeightMCM, PartyOfEight | Локальные MCM-моды | AGENTS.md, make_data.py, handles.json; Lua в build/ |
| CampEventsInCamp | Личный вариант лагерных событий | AGENTS.md, build.py; --install меняет установку |
| SuccubusFix | Патч исходного Succubus, входные данные SuccubusPlus | AGENTS.md, make_data.py, ru_text.py |
| FemaleBodiesLOD | Перенос формы тел на LOD и одежду | AGENTS.md, make.py, conform_clothing.py |
| *RU и ExpansionRUAddon | Локальные русификаторы разной структуры | Локальный AGENTS.md; выяснить источник строк и сборщик |
| LaezelFace | Только распакованные ресурсы | AGENTS.md; конвейер сборки не найден |
| _disabled_mods | Сохранённые отключённые паки | Не рабочий проект; не удалять автоматически |
| AlfiraSV-ch2 | Пустой каталог | Инструкции не создавались |

## Особенности, которые нельзя потерять при переходе
1. BG3 не является единым репозиторием: найдено 6 самостоятельных Git-репозиториев
   и 13 дополнительных рабочих деревьев AlfiraCompanion. Их ветки не объединялись.
2. В восьми копиях CLAUDE.md Альфиры публичный клон допускается при отдельных
   записях актрисы; в шести более новых вариантах публичные клоны исключены даже
   с согласием. Сохранены оба варианта как контекст веток; AGENTS.md требует
   сверки актуального docs/VOICE.md и запрещает добавлять клон в публичную сборку
   до разрешения расхождения. Это перенос решений проекта, не новая проверка
   юридических условий Larian.
3. Старые NEXT_SESSION.md описывают будущие задачи и местами отстают от кода.
   Они не служат командой автоматически начать озвучку, установку или публикацию.
4. Разрешения на push/PR/merge отличаются по проектам. У ATECCRus и Wyll
   сохраняются ограничения из исходных правил; у Альфиры сохранена записанная
   авторизация. Allow-list Claude сам по себе не даёт авторизации Codex.
5. build/ содержит исходные файлы в маленьких модах; слепая очистка опасна.
   В CampEventsInCamp пакуются готовые loca оригинала, тогда как собственные
   локализации ряда других проектов идут XML внутри модуля.
6. Корневой install_ru.py устанавливает сразу много русификаторов, проверяет
   запущенную игру и меняет modsettings.lsx. В прочитанном коде нет синхронизации
   всех файлов BG3MM, поэтому его нельзя считать универсальным установщиком.
7. На начало миграции есть изменения пользователя: AlfiraCompanion/voice_line.py
   (неотслеживаемый) и SuccubusPlus/make_mod.py (изменённый). Они сохранены.

## Как пользоваться
Открой чат в папке нужного проекта и дай конкретную задачу. Если чат открыт
в BG3, укажи имя проекта: агент сначала прочитает его локальный AGENTS.md.
Для обычного веб-чата ChatGPT без доступа к диску прикрепи AGENTS.md и нужные
документы: локальные инструкции не предоставляют ему доступ к репозиториям.
Будущие изменения правил Codex вноси в AGENTS.md. CLAUDE.md не синхронизируются
автоматически. Локальные файлы новых инструкций ещё не закоммичены и не отправлены.

Формат инструкций сверен с официальной документацией OpenAI:
https://learn.chatgpt.com/docs/agent-configuration/agents-md

## Полная инвентаризация
Состояние веток на момент миграции; для работы проверять заново.

| Каталог | Тип | Ветка | Инструкции |
|---|---|---|---|
| _disabled_mods | Архив отключённых паков | — | — |
| AlfiraCompanion | Git-репозиторий | main | AGENTS.md |
| AlfiraJoinsThePartyRU | Локальный проект | — | AGENTS.md |
| AlfiraRedoneRU | Локальный проект | — | AGENTS.md |
| AlfiraSV-build | Worktree Альфиры | feat/build-lv1 | AGENTS.md |
| AlfiraSV-ch2 | Пустая папка | — | — |
| AlfiraSV-checks | Worktree Альфиры | docs/check-class | AGENTS.md |
| AlfiraSV-events | Worktree Альфиры | design/act1-events-marker | AGENTS.md |
| AlfiraSV-local | Worktree Альфиры | design/act1-local | AGENTS.md |
| AlfiraSV-newgame | Worktree Альфиры | docs/new-game | AGENTS.md |
| AlfiraSV-portraits | Worktree Альфиры | feat/portraits | AGENTS.md |
| AlfiraSV-pubvoice | Worktree Альфиры | docs/public-no-clone | AGENTS.md |
| AlfiraSV-respec | Worktree Альфиры | feat/respec | AGENTS.md |
| AlfiraSV-staging | Worktree Альфиры | feat/staging-act1 | AGENTS.md |
| AlfiraSV-talks | Worktree Альфиры | feat/act1-talks | AGENTS.md |
| AlfiraSV-voice | Worktree Альфиры | feat/voice-act1 | AGENTS.md |
| AlfiraSV-voiceint | Worktree Альфиры | docs/readme-disclaimer | AGENTS.md |
| AlfiraSV-voicetrial | Worktree Альфиры | feat/voice-trial | AGENTS.md |
| AntifaLafelRU | Локальный проект | — | AGENTS.md |
| ATECCRus | Git-репозиторий | main | AGENTS.md |
| AutoStackMerge | Локальный проект | — | AGENTS.md |
| BG3SXRU | Локальный проект | — | AGENTS.md |
| BhaalsForgottenSonRU | Локальный проект | — | AGENTS.md |
| CampEventsInCamp | Локальный проект | — | AGENTS.md |
| CarryWeightMCM | Локальный проект | — | AGENTS.md |
| CCPresetsRU | Локальный проект | — | AGENTS.md |
| CYSRU | Локальный проект | — | AGENTS.md |
| DialogKit | Git-репозиторий | main | AGENTS.md |
| DreadOverlordRU | Локальный проект | — | AGENTS.md |
| ElegantDressRU | Локальный проект | — | AGENTS.md |
| ExpansionRUAddon | Локальный проект | — | AGENTS.md |
| EyesOfTheHoarderRU | Локальный проект | — | AGENTS.md |
| FemaleBodiesLOD | Локальный проект | — | AGENTS.md |
| GoonsLibRU | Локальный проект | — | AGENTS.md |
| ImpartUndeathRU | Локальный проект | — | AGENTS.md |
| ItemTagsExtraRU | Локальный проект | — | AGENTS.md |
| LaezelFace | Локальный проект | — | AGENTS.md |
| LootAuraRU | Локальный проект | — | AGENTS.md |
| MCMRU | Локальный проект | — | AGENTS.md |
| MintharaVarC | Локальный проект | — | AGENTS.md |
| MykyHairstylesRU | Локальный проект | — | AGENTS.md |
| PartyOfEight | Локальный проект | — | AGENTS.md |
| ScantilyCampOutfitRU | Локальный проект | — | AGENTS.md |
| ShadowheartHairdoRU | Локальный проект | — | AGENTS.md |
| SmallModsRU | Локальный проект | — | AGENTS.md |
| SmartContainersRU | Локальный проект | — | AGENTS.md |
| SSF | Локальный проект | — | AGENTS.md |
| SuccubusFix | Локальный проект | — | AGENTS.md |
| SuccubusPlus | Git-репозиторий | main | AGENTS.md |
| TavHairpackRU | Локальный проект | — | AGENTS.md |
| TeamEffort | Git-репозиторий | main | AGENTS.md |
| ValkranaSpellbookRU | Локальный проект | — | AGENTS.md |
| WaypointsRU | Локальный проект | — | AGENTS.md |
| WyllPactPointsRU | Git-репозиторий | main | AGENTS.md |
| zAxCCEyesRU | Локальный проект | — | AGENTS.md |
| ZivaBootsRU | Локальный проект | — | AGENTS.md |

Изменены ссылки начала сессии в NEXT_SESSION.md: AlfiraCompanion, AlfiraSV-build, AlfiraSV-checks, AlfiraSV-events, AlfiraSV-local, AlfiraSV-newgame, AlfiraSV-portraits, AlfiraSV-pubvoice, AlfiraSV-respec, AlfiraSV-staging, AlfiraSV-talks, AlfiraSV-voice, AlfiraSV-voiceint, AlfiraSV-voicetrial, TeamEffort.

## Проверка результата
Создано 55 AGENTS.md (общий и 54 локальных), обновлено 15 NEXT_SESSION.md.
Проверены UTF-8 без BOM, отсутствие активных команд SendUserFile и заголовков
Claude Code в новых инструкциях, наличие указанных скриптов Альфиры.
Git diff --check прошёл во всех 19 рабочих копиях; исходные CLAUDE.md
не изменены. Моды не пересобирались и игра не запускалась: изменена документация.
