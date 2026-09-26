# Исходники мода

Раскладка повторяет пак игры. `_MOD_` — папка модуля: `build_pak.py`
подставит `AlfiraSecondVerse_<uuid>` из `config/tools.json`.

- `Mods/_MOD_/Story/RawFiles/Goals/` — сценарии Osiris
- `Mods/_MOD_/Story/DialogsBinary/`, `Public/_MOD_/Timeline/` — диалоги и постановка
- `Mods/_MOD_/Localization/English|Russian/AlfiraSecondVerse_*.xml` — тексты (без `<!-- -->`!)
- `Public/_MOD_/Stats/Generated/Data/` — статы
- `Public/_MOD_/RootTemplates/`, `Public/_MOD_/Flags/`, `Public/_MOD_/Tags/` — шаблоны, флаги, теги (`.lsx`, собираются в `.lsf`)
