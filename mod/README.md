# Исходники мода

Раскладка повторяет пак игры. `_MOD_` — папка модуля: `build_pak.py`
подставит `AlfiraSecondVerse_<uuid>` из `config/tools.json` и в путях, и внутри
`.lsx`/`.lsj`/`.xml`.

- `Mods/_MOD_/Story/RawFiles/Goals/` — сценарии Osiris (префикс `ALFSV_`). Перед сборкой
  `python scripts/check_story.py`; после любой правки поднять версию мода (docs/STAGE2.md §4)
- `Mods/_MOD_/Story/DialogsBinary/**/*.lsx` — диалоги (собираются в `.lsf`); `.lsj` из
  редактора можно класть в `Mods/_MOD_/Story/Dialogs/` — сборка переведёт их в `DialogsBinary`
- `Public/_MOD_/Content/Assets/Dialogs/[PAK]_ALFSV_Dialogs/_merged.lsx` — банк диалогов
  (ID ресурсов, на которые ссылается Osiris; не менять)
- `Public/_MOD_/Timeline/` — постановка (пока нет)
- `Mods/_MOD_/Localization/English|Russian/AlfiraSecondVerse_*.xml` — тексты (без `<!-- -->`!).
  Сборка проверяет, что у каждой реплики диалога есть текст во всех языках
- `Public/_MOD_/Stats/Generated/Data/` — статы
- `Public/_MOD_/RootTemplates/`, `Public/_MOD_/Flags/`, `Public/_MOD_/Tags/` — шаблоны, флаги, теги (`.lsx`, собираются в `.lsf`)
