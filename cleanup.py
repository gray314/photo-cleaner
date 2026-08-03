from pathlib import Path
from PIL import Image
import shutil
from datetime import datetime

# ============================================
# Оценка качества фотографии
# ============================================

def image_score(path: Path):
    """
    Возвращает рейтинг фотографии.

    Чем больше значение — тем лучше фотография.
    """

    try:
        with Image.open(path) as img:
            width, height = img.size
            pixels = width * height
    except Exception:
        pixels = 0

    stat = path.stat()

    filesize = stat.st_size
    modified = stat.st_mtime

    return (
        pixels,        # сначала разрешение
        filesize,      # потом размер файла
        modified       # потом дата изменения
    )


# ============================================
# Выбор лучшей фотографии
# ============================================

def choose_best(group):

    best = None
    best_score = None

    for photo in group:

        score = image_score(photo)

        if best is None:
            best = photo
            best_score = score
            continue

        if score > best_score:
            best = photo
            best_score = score

    return best


# ============================================
# Создание папки Duplicates
# ============================================

def create_duplicates_folder(root):

    dup = Path(root) / "Duplicates"

    dup.mkdir(exist_ok=True)

    return dup


# ============================================
# Перемещение файла
# ============================================

def move_file(src, dst_folder):

    dst = dst_folder / src.name

    counter = 1

    while dst.exists():

        dst = dst_folder / f"{src.stem}_{counter}{src.suffix}"

        counter += 1

    shutil.move(str(src), str(dst))

    return dst


# ============================================
# Обработка всех групп
# ============================================

def cleanup(groups, root_folder):

    duplicate_folder = create_duplicates_folder(root_folder)

    kept = []
    moved = []

    for group in groups:

        best = choose_best(group)

        kept.append(best)

        print("=" * 70)
        print("Группа похожих фотографий:\n")

        for img in group:

            print(" ", img.name)

        print("\nОставляем:")

        print(" ", best.name)

        for img in group:

            if img == best:
                continue

            new_location = move_file(img, duplicate_folder)

            moved.append((img, new_location))

            print("   ->", new_location.name)

    return kept, moved


# ============================================
# Отчет
# ============================================

def print_report(kept, moved):

    print("\n")

    print("=" * 70)

    print("ОБРАБОТКА ЗАВЕРШЕНА")

    print("=" * 70)

    print(f"Оставлено фотографий : {len(kept)}")

    print(f"Перемещено           : {len(moved)}")

    print("=" * 70)