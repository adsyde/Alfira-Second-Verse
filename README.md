# Alfira: Second Verse

«Альфира: Второй куплет».

Мод для Baldur's Gate 3: Альфира, тифлинг-бард из Изумрудной рощи, становится
полноценной спутницей. У неё будут вербовка, лагерь, одобрение, личные
разговоры, реплики в мире, романтика и своя цепочка квестов. Персонаж строго по
канону игры, а её бард играбелен на «Доблести».

Мод самостоятельный: «Alfira Joins The Party» и другие моды про Альфиру ему не
нужны. Внешность из Alfira Redux совместима.

**Статус:** 0.5.0 — вербовка, одобрение, главы разговоров 1–2, реплики на местах (акты 1–3) и
фразы в пути; собрано, ждёт проверки в игре ([docs/STAGE5.md](docs/STAGE5.md)). Как описываются
сцены, главы, места и фразы в пути — [scripts/dialogs/README.md](scripts/dialogs/README.md).
План — [docs/ROADMAP.md](docs/ROADMAP.md).

Игра: Patch 8 Hotfix 9.

## Устройство репозитория

| Путь | Что там | В git |
|------|---------|-------|
| `docs/` | план, архитектура, правила текста, голос, исследования | да |
| `docs/research/` | как устроены спутники в игре, канон Альфиры, инструменты сообщества | да |
| `design/` | сценарии: диалоги, беседы, квесты, сцены | да |
| `mod/` | исходники мода в раскладке пака (`_MOD_` = папка мода) | да |
| `scripts/` | инструменты | да |
| `config/tools.json` | общий конфиг, UUID мода, наборы распаковки | да |
| `config/tools.local.json` | пути на этой машине (Divine, игра, vgmstream) | нет |
| `game-data/` | распакованные данные игры | нет (права Larian) |
| `reports/dialogs/` | распечатки диалогов игры | нет (текст Larian) |
| `voice-work/` | аудио, датасеты, модели | нет |
| `build/`, `dist/` | сборка | нет |

## Быстрый старт

Нужны Python 3.11+ и [LSLib](https://github.com/Norbyte/lslib) (Divine.exe).

```bash
cp config/tools.local.example.json config/tools.local.json   # поправить пути
python scripts/unpack_game.py goals loca flags dialogs-alfira  # данные игры → game-data/
python scripts/dialog_dump.py DEN_TieflingBard_Bard            # диалог как читаемый сценарий
python scripts/build_pak.py                                    # mod/ → dist/AlfiraSecondVerse.pak
python scripts/install.py                                      # в игру (игра и BG3MM закрыты)
```

## Инструменты

| Скрипт | Назначение |
|--------|------------|
| `unpack_game.py` | достаёт из паков игры наборы файлов (сценарии Osiris, диалоги, флаги, статы, шаблоны, loca); `.loca` → `.xml`, `.lsf` → `.lsx` |
| `gamedb.py` | справочник: текст реплики по handle (EN/RU), имя флага или объекта по GUID |
| `dialog_dump.py` | диалог `.lsj` → Markdown: кто говорит, EN + официальный RU, флаги, броски, постановка; `--all-alfira` — все её диалоги |
| `build_pak.py` | сборка пака: подстановка папки мода, `.lsx → .lsf`, `meta.lsx`, проверки раскладки |
| `install.py` | копирует пак в Mods и прописывает в порядок загрузки (modsettings + BG3 Mod Manager) |
| `voice/extract_voice.py` | каталог всех озвученных реплик Альфиры (handle, текст, длительность) и их аудио |

## Лицензия и права

Код и тексты проекта принадлежат автору. Данные, тексты и аудио Baldur's Gate 3
принадлежат Larian Studios и в репозиторий не входят. Мод следует
[Fan Content Policy Larian](https://larian.com/fan-content-policy): в
публикуемой версии нет клонированного голоса актрисы (см. [docs/VOICE.md](docs/VOICE.md)).
