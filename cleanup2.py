"""
cleanup.py

Выбор лучшей фотографии из группы похожих
и перемещение остальных в папку Duplicates.
"""

from pathlib import Path
from PIL import Image
import shutil
from typing import List, Tuple


# ===========================================================
# Настройки
# ===========================================================

DUPLICATE_FOLDER = "Duplicates"


# ===========================================================
# Информация о фотографии
# ===========================================================

def image_info(path: Path):

    try:
        with Image.open(path) as img:
            width, height = img.size
    except Exception:
        width = 0
        height = 0

    stat = path.stat()

    return {
        "path": path,
        "width": width,
        "height": height,
        "pixels": width * height,
        "size": stat.st_size,
        "mtime": stat.st_mtime,
    }


# ===========================================================
# Оценка качества
# ===========================================================

def score(info):

    return (
        info["pixels"],
        info["size"],
        info["mtime"],
    )


# ===========================================================
# Выбрать лучшую фотографию
# ===========================================================

def choose_best(group: List[Path]) -> Path:

    infos = []

    for photo in group:
        infos.append(image_info(photo))

    infos.sort(key=score, reverse=True)

    return infos[0]["path"]


# ===========================================================
# Создать папку Duplicates
# ===========================================================

def ensure_duplicate_folder(root: Path):

    dst = root / DUPLICATE_FOLDER

    dst.mkdir(exist_ok=True)

    return dst


# ===========================================================
# Получить уникальное имя файла
# ===========================================================

def unique_destination(folder: Path, filename: str):

    dst = folder / filename

    if not dst.exists():
        return dst

    stem = dst.stem
    suffix = dst.suffix

    i = 1

    while True:

        new = folder / f"{stem}_{i}{suffix}"

        if not new.exists():
            return new

        i += 1


# ===========================================================
# Перемещение файла
# ===========================================================

def move_photo(photo: Path, folder: Path):

    dst = unique_destination(folder, photo.name)

    shutil.move(str(photo), str(dst))

    return dst


# ===========================================================
# Очистка одной группы
# ===========================================================

def process_group(group: List[Path], duplicate_folder: Path):

    best = choose_best(group)

    moved = []

    for photo in group:

        if photo == best:
            continue

        dst = move_photo(photo, duplicate_folder)

        moved.append((photo, dst))

    return best, moved


# ===========================================================
# Очистка всех групп
# ===========================================================

def cleanup(groups: List[List[Path]], root_folder: str):

    root = Path(root_folder)

    duplicate_folder = ensure_duplicate_folder(root)

    kept = []

    moved = []

    print()
    print("=" * 70)
    print("Обработка похожих фотографий")
    print("=" * 70)

    for index, group in enumerate(groups, start=1):

        print()
        print(f"Группа {index}")

        best, result = process_group(group, duplicate_folder)

        kept.append(best)

        print(f"  Оставляем : {best.name}")

        for src, dst in result:

            moved.append((src, dst))

            print(f"  Перемещено -> {dst.name}")

    return kept, moved


# ===========================================================
# Красивый отчет
# ===========================================================

def report(kept, moved):

    print()
    print("=" * 70)
    print("ГОТОВО")
    print("=" * 70)

    print(f"Оставлено фотографий : {len(kept)}")
    print(f"Перемещено           : {len(moved)}")

    print("=" * 70)