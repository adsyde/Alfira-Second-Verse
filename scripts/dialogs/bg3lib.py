"""Подключение bg3moddinglib (MIT, https://github.com/0x1amy0urdad/Guidance) как библиотеки.

Библиотека не копируется в репозиторий: путь к её исходникам задаётся в config/tools.local.json
(bg3moddinglib_path, проверенный коммит — bg3moddinglib_commit). Её окружение (скачанный LSLib,
индекс ресурсов игры, рабочая папка) — bg3moddinglib_env, вне репозитория. Первый запуск строит
индекс (~1,5 минуты). Нужны pip-пакеты numpy, requests, pythonnet и .NET 8.

Две доработки поверх библиотеки, без правки её файлов:
  * .NET-культура процесса — инвариантная. Иначе LSLib внутри процесса пишет в .lsx дроби
    через запятую (русская локаль Windows), а Divine.exe при сборке их не прочтёт;
  * все «случайные» UUID библиотеки берутся из детерминированного генератора, чтобы повторная
    сборка давала те же файлы (для git-диффов и для сохранений игры).
"""
from __future__ import annotations

import os
import random
import subprocess
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import config  # noqa: E402

DEFAULTS = {
    "bg3moddinglib_path": "C:/Tools/Guidance/src",
    "bg3moddinglib_env": "C:/Tools/bg3moddinglib-env",
}
PINNED_COMMIT = "2f25d73"


class Lib:
    """Окружение библиотеки: env, tool, files, assets и модуль b."""

    def __init__(self, cfg: dict | None = None) -> None:
        cfg = cfg or config()
        local = {**DEFAULTS, **cfg["local"]}
        src = Path(local["bg3moddinglib_path"])
        if not (src / "bg3moddinglib" / "__init__.py").exists():
            sys.exit(f"Нет bg3moddinglib в {src}: склонируйте https://github.com/0x1amy0urdad/Guidance "
                     f"(коммит {PINNED_COMMIT}) и укажите путь к src в config/tools.local.json → bg3moddinglib_path")
        self.commit = _git_head(src.parent)
        if self.commit and not self.commit.startswith(local.get("bg3moddinglib_commit", PINNED_COMMIT)):
            print(f"[внимание] bg3moddinglib на коммите {self.commit}, проверен {PINNED_COMMIT}")
        sys.path.insert(0, str(src))
        env_root = Path(local["bg3moddinglib_env"])
        env_root.mkdir(parents=True, exist_ok=True)
        cwd = os.getcwd()
        os.chdir(env_root)              # библиотека пишет логи и временные файлы в текущую папку
        try:
            import bg3moddinglib as b
            _invariant_culture()
            data = Path(local["game_dir"]) / "Data"
            self.b = b
            self.env = b.bg3_modding_env(str(env_root), bg3_data_path=str(data))
            self.tool = b.bg3_modding_tool(self.env)
            mod = cfg["mod"]
            self.files = b.game_files(self.tool, mod["name"], mod["uuid"])
            self.assets = b.bg3_assets(self.files)
        finally:
            os.chdir(cwd)

    def game_file(self, path: str):
        """Файл из паков игры (lsf/lsx/loca → дерево xml), без добавления в сборку библиотеки."""
        pak = self.assets.index.get_pak_by_file(path)
        return self.files.get_file(pak, path, exclude_from_build=True)


def _git_head(repo: Path) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def _invariant_culture() -> None:
    from System.Globalization import CultureInfo  # type: ignore
    from System.Threading import Thread  # type: ignore
    inv = CultureInfo.InvariantCulture
    CultureInfo.DefaultThreadCurrentCulture = inv
    CultureInfo.DefaultThreadCurrentUICulture = inv
    Thread.CurrentThread.CurrentCulture = inv
    Thread.CurrentThread.CurrentUICulture = inv


def seed_uuids(b, seed: str) -> None:
    """Подменяет new_random_uuid во всех модулях библиотеки генератором с зерном seed."""
    rng = random.Random(seed)

    def det_uuid() -> str:
        return str(uuid.UUID(int=rng.getrandbits(128), version=4))

    for name in ("_common", "_assets", "_timeline", "_dialog", "_scene", "_reactions", "_flags"):
        mod = sys.modules.get(f"bg3moddinglib.{name}")
        if mod is not None and hasattr(mod, "new_random_uuid"):
            mod.new_random_uuid = det_uuid
