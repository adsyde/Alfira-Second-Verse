# Сообщество, инструменты, правила (исследование 2026-09-26)

Сводка веб-исследования. Непроверенное помечено. Ссылки — первоисточники.

## Готовые спутники-моды: образцы устройства

Моды, где новый персонаж сделан спутником, существуют. Их устройство изучаем,
контент **не заимствуем**: у всех трёх разрешения запрещают переиспользование.

- **A Candle In The Dark — Jason Altea** (Magnetuning, v1.3.0.0, 2026-09-11) —
  https://www.nexusmods.com/baldursgate3/mods/10000
  - Спутник не-ориджин, около 200 озвученных реплик, свой липсинк.
  - Одобрение на всю игру, в основном через скрипты Osiris. Места в лагере, участие в беседах отряда (`PB_*`).
  - Собран в основном ручной правкой XML, Toolkit использовался только для отладки Osiris.
  - Переопределяет `GLO_CompanionSwap_Camp` (для «занять место»), `CAMP_Jergal` (чтобы Иссохший его воскрешал) и `Gossips.lsx` в беседах.
  - Романтика у автора только «в планах»: по его словам, для не-ориджина она требует «немало обходных путей».
  - Вербуется в уже начатой игре. Если удалить мод посреди прохождения, сохранение не загрузится.
- **The Bloodletter (Veilyn)** — https://www.nexusmods.com/baldursgate3/mods/13529.
  Прототип: вербовка, палатки по актам, уровни. Работает только в новой игре.
- **Alfira Joins The Party** (adriant1978) — https://www.nexusmods.com/baldursgate3/mods/12257
  - Альфира вербуется на долгом отдыхе после песни в акте 1. Основной файл обходится без Script Extender.
  - Для прохождения за Темного Соблазна есть отдельный файл, ему SE нужен.
  - Бесед отряда и реплик по клику нет. Разрешения: без переделок и без заимствования ассетов. **Не используем.**

## Официальные вызовы Osiris

- `RegisterAsCompanion(char, recruiter)`, `UnregisterAsCompanion`,
  `ForceDismissCompanion`, `SetBlockDismiss` — https://docs.baldursgate3.game/index.php?title=RegisterAsCompanion
- `ChangeApprovalRating(owner, rated, type, delta)`, `GetApprovalRating`,
  событие `ApprovalRatingChanged` — https://docs.baldursgate3.game/index.php?title=ChangeApprovalRating
- Базы: `DB_Players`, `DB_PartyMembers`, `DB_PartyFollowers`, `DB_IsOrWasInParty`,
  `DB_InCamp`, `DB_Origins`, `DB_CampNight(flag, priority, char)` —
  https://wiki.bg3.community/Information/Osiris/db-reference/character-dbs
- Пример вербовки через Script Extender (Hippo0o, `Server/Player.lua`,
  https://github.com/Hippo0o/bg3-mods):
  1. `PROC_ORI_SetupCamp(char,1)`
  2. `SetOnStage`
  3. `RegisterAsCompanion`
  4. `PROC_GLO_InfernalBox_*`
  5. `SetFaction`
  6. `SetLevel`
  7. `RequestRespec`

  Диалог в отряде задаётся через `DB_Dialogs(char, <X>_InParty)`.

Проверять всё это нужно по нашим распакованным целям (goals) — см. [vanilla-companions.md](vanilla-companions.md).

## Инструменты

- **Официальный Toolkit** не умеет редактировать диалоги и звук —
  https://wiki.bg3.community/Tutorials/Toolkit/Toolkit-FAQ. Разблокированные сборки
  (MoonGlasses, https://www.nexusmods.com/baldursgate3/mods/12308) дают редактор узлов
  диалога и Timeline, но это неофициальный путь.
- **bg3moddinglib** (MIT) — Python-библиотека для диалогов, таймлайнов,
  реакций, саундбанков и loca: https://github.com/0x1amy0urdad/Guidance.
  **Кандидат на основу нашего компилятора сценариев.** Копию из ReallyShadowheart
  (CC BY-NC-ND) не брать.
- Новый диалог — это шесть частей: loca, DialogsBinary, Timeline, Scene,
  запись в `GeneratedDialogTimelines` и Dialog Resource —
  https://wiki.bg3.community/en/Tutorials/dialogue-files-tutorial
- Новые реплики с озвучкой — https://wiki.bg3.community/Tutorials/new-voice-lines:
  - VoiceMeta называется UUID персонажа без дефисов;
  - аудио — `v<id>_<handle>.wem` в `Mods/<мод>/Localization/English/Soundbanks/`;
  - липсинк — `.ffxanim` в `Localization/English/Animation/`.

  Руководство использует FaceFX-актёра самой Альфиры, значит её файлы лицевой анимации годятся напрямую.

## Правила Larian об ИИ и голосе (проверено по первоисточнику)

Larian Fan Content Policy, 31.07.2025, §4.5 — https://larian.com/fan-content-policy:
- нельзя обучать генеративный ИИ на IP Larian для фанатского контента;
- нельзя имитировать голоса актёров озвучки из игр Larian без их явного
  письменного согласия (voice swapping, deepfake и любая репликация голоса);
- нельзя извлекать аудио из файлов игры для машинного обучения и синтезировать
  новые реплики, обучаясь на голосах актёров.

Политика касается опубликованного фанатского контента. Частное использование
она прямо не регулирует. Следствия — в [../VOICE.md](../VOICE.md).

Nexus допускает ИИ-контент с обязательной пометкой и снимает его по жалобе
правообладателя: https://www.nexusmods.com/news/14850 (дату не проверяли).

## Подводные камни

- В отряде 4 места. «Занять место» требует переопределить `GLO_CompanionSwap_Camp`,
  который трогают и другие моды.
- Лучше заводить новые ресурсы, чем переопределять чужие файлы: два мода,
  правящие один диалог, требуют патча совместимости.
- Удаление мода посреди прохождения ломает сохранение. Об этом нужно предупредить в описании мода.
- Ориджин-механики (ночные события в лагере, сны) придётся делать своими
  `DB_CampNight` и диалогами.
