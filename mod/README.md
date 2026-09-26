# Исходники мода

Раскладка повторяет пак игры. `_MOD_` — папка модуля: `build_pak.py`
подставит `AlfiraSecondVerse_<uuid>` из `config/tools.json` и в путях, и внутри
`.lsx`/`.lsj`/`.xml`.

- `Mods/_MOD_/Story/RawFiles/Goals/` — сценарии Osiris (префикс `ALFSV_`). Перед сборкой
  `python scripts/check_story.py`; после любой правки поднять версию мода (docs/STAGE2.md §4)
- **Генерируются** `scripts/dialogs/build.py` из `scripts/dialogs/scenes/*.py` (руками не править,
  папки очищаются при каждой сборке; см. `docs/STAGING.md`):
  - `Mods/_MOD_/Story/DialogsBinary/**/*.lsx` — диалоги (в пак — `.lsf`);
  - `Public/_MOD_/Timeline/Generated/` — таймлайны и сцены (не в git);
  - `Public/_MOD_/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsx` — банк диалогов
    (ID ресурсов, на которые ссылается Osiris, задаются в сценах; не менять);
  - `Public/_MOD_/Content/Generated/[PAK]_GeneratedDialogTimelines/` — банк таймлайнов (не в git);
  - `Public/_MOD_/ApprovalRatings/Reactions/` — реакции одобрения (идут в пак как `.lsx`, как у игры);
  - `Public/_MOD_/Flags/` — новые флаги;
  - `Mods/_MOD_/Globals/WLD_Main_A/Characters/` — её персонаж с одобрением (не в git);
  - `Mods/_MOD_/Localization/English|Russian/AlfiraSecondVerse_*.xml` — тексты (без `<!-- -->`!),
    `…_ru_to_F.xml` — женские формы обращения к героине.
- `X.lsf.lsx` собирается в `X.lsf`; если рядом есть `X.lsf.lsx`, то `X.lsx` идёт в пак как есть
  (так игра хранит `_Scene.lsx`). Сборка проверяет, что у каждой реплики диалога есть текст во
  всех языках (озвученные реплики игры — по `build/dialogs/manifest.json`)
- `Public/_MOD_/Stats/Generated/Data/` — статы
- `Public/_MOD_/RootTemplates/`, `Public/_MOD_/Flags/`, `Public/_MOD_/Tags/` — шаблоны, флаги, теги (`.lsx`, собираются в `.lsf`)
