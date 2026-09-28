# Портрет Альфиры в интерфейсе

Итог: **своего портрета мод не поставляет, и он не нужен.** У ванильной Альфиры портрет есть,
Alfira Redux подменяет его своим сам. Разбор по данным Patch 8 Hotfix 9 (набор `portraits` в
`config/tools.json`, `python scripts/unpack_game.py portraits`). В живой игре не проверено: см.
«Что проверить в игре».

## Как игра находит портрет

1. У персонажа (глобальный объект или RootTemplate, если у объекта поле пустое) есть атрибут
   `Icon`. Его имя — `<CharacterVisual>-<Equipment>_(<базовая иконка>)`, например у Альфиры
   (`Mods/Gustav/Globals/WLD_Main_A/Characters/_merged.lsf`, `S_DEN_Bard`):
   `1ab11041-a5b8-7f62-ced5-a6bc1179c0e3-EQP_Unarmed_Lute_(Icon_Tiefling_Female)`.
   UUID в имени совпадает с её `CharacterVisualResourceID`, но игра ищет по строке `Icon`, а не по
   визуалу или тегу: у `S_DEN_Bard_Backup` (двойник для Тёмного Соблазна) свой `Icon`.
2. По этому имени интерфейс берёт текстуру `Mods/<модуль>/GUI/Assets/Portraits/<Icon>.DDS`.
   Размеры записаны в `Mods/<модуль>/GUI/metadata.lsf`: ключ `Assets/Portraits/<Icon>.png`,
   `w`, `h`, `mipcount`.
3. Одинаковый ключ в нескольких модулях: действует модуль, загруженный позже. Так у Larian
   `GustavDev` перекрывает `Gustav`: у Альфиры два файла с одним именем и разными байтами.
4. Панель отряда (`Mods/MainUI/GUI/Pages/PlayerPortraits.xaml` → `CharacterPortraitTemplate` в
   `Public/Game/GUI/Library/DataTemplates.xaml`), инвентарь, лист персонажа, журнал, очерёдность хода,
   уведомления берут картинку из свойства `Icon` персонажа (`Background="{Binding Icon}"`).
   Отдельного «большого» портрета для отряда, жетона или диалога у персонажей нет.

## Формат

Все портреты персонажей в игре (5646 файлов) одного формата: **152×152, BC1 (DXT1), 8 мипмапов**,
15 664 байта, один вариант на `Icon`. Портреты спутников Larian тоже такие:

| Кто | `Icon` (сокращённо) |
|-----|---------------------|
| Минск (`S_Player_Minsc`) | `b933b9ae-…-EQP_Minsc_(Icon_Minsc)` |
| Джахейра (`S_Player_Jaheira`) | `966e8a68-…-EQP_Jaheira_(Icon_Jaheira)` |
| Хальсин (`S_GLO_Halsin`) | `b7830265-…-EQ_Halsin_(Icon_Halsin)` |
| Минтара (шаблон `Elves_Female_Drow_Minthara`) | `d1bc342f-…-GOB_DrowCommander_(Icon_Minthara)` |
| Ориджины (`ORIGIN_*`) | `…-EQ_<Имя>_(Icon_Origin_<Имя>)` |

Уровни `SYS_PortraitGeneration_A` и `SYS_PortraitPlayerRace_A` в `Shared.pak`, судя по названию,
служат для отрисовки портретов героя из редактора персонажа. NPC-спутникам достаточно готового DDS.

## Альфира: ваниль и Alfira Redux

- **Ваниль.** `Mods/Gustav/GUI/Assets/Portraits/1ab11041-…-EQP_Unarmed_Lute_(Icon_Tiefling_Female).DDS`
  (и перекрывающая копия в `GustavDev`) в `Gustav_Textures.pak`. Через ту же привязку `Icon` этот
  портрет показывается и там, где она NPC: в очерёдности хода и в подсказках.
- **Наш мод** переопределяет её глобальный объект (`scripts/dialogs/build.py → character_override`):
  копия из игры + `HasPlayerApprovalRating`. `Icon` и `CharacterVisualResourceID` не меняются.
- **Alfira Redux** (`AlfiraRedone_1df474ce-…`) подменяет визуал под тем же UUID
  (`Public/…/Content/[PAK]_CharacterVisuals/1ab11041-….lsf`), кладёт свою текстуру под **тем же
  именем** `Icon` (`Mods/AlfiraRedone_…/GUI/Assets/Portraits/…`, байты отличаются от ванильных) и свою
  запись в `metadata.lsf`. Мод Redux загружается после `GustavDev`, поэтому его текстура перекрывает
  ванильную. Её глобальный объект тоже переопределён, `Icon` тот же.

Пара «ваниль / Redux» работает сама: `Icon` у Альфиры один и тот же в игре, у нас и у Redux, а текстуру
по этому имени выбирает порядок модулей. С Redux показывается портрет Redux, без него — ванильный.
Порядок нашего мода и Redux на портрет не влияет. На одобрение влияет: см. точки конфликта в
[ARCHITECTURE.md](ARCHITECTURE.md).

## Что проверить в игре

В новой игре с 0.8.0 завербовать Альфиру и посмотреть портрет в панели отряда, инвентаре, лагере и
окне выбора спутников. Проверить дважды: с Redux (портрет Redux) и без него (ванильный). Если на месте
портрета пусто или силуэт, записать, в каком окне. Тогда разбирать дальше.

## Если понадобится свой портрет

Раскладка та же, что у Redux: `Mods/_MOD_/GUI/Assets/Portraits/<Icon>.DDS` (152×152, BC1, 8 мипмапов)
и `Mods/_MOD_/GUI/metadata.lsf` с ключом `Assets/Portraits/<Icon>.png`. Файл под ванильным именем
`Icon` станет точкой конфликта с Redux: победит мод, который загружается ниже. Своё имя `Icon` в
переопределении объекта уберёт портрет Redux. Сейчас это не делаем.
