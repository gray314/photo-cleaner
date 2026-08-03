#!/usr/bin/env python3
"""
Photo Cleaner

Поиск точных и похожих фотографий.

Использует OpenCLIP.

Python 3.12+
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

from tqdm import tqdm
from PIL import Image


# ============================================================
# НАСТРОЙКИ
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".heic",
    ".heif",
}

CACHE_FILE = ".photo_cleaner_cache.json"

DUPLICATE_FOLDER = "Duplicates"

SIMILARITY_THRESHOLD = 0.90


# ============================================================
# CLI
# ============================================================

def parse_args():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "folder",
        type=Path,
        help="Папка с фотографиями",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ничего не перемещать",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=SIMILARITY_THRESHOLD,
    )

    return parser.parse_args()


# ============================================================
# Поиск фотографий
# ============================================================

def find_images(folder: Path):

    images = []

    for path in folder.rglob("*"):

        if not path.is_file():
            continue

        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        images.append(path)

    images.sort()

    return images


# ============================================================
# SHA256
# ============================================================

def sha256(path: Path):

    h = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(1024 * 1024)

            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()




# ============================================================
# Cache
# ============================================================

def load_cache(folder: Path):

    cache = folder / CACHE_FILE

    if not cache.exists():
        return {}

    with open(cache, "r", encoding="utf8") as f:
        return json.load(f)


def save_cache(folder: Path, cache):

    with open(folder / CACHE_FILE, "w", encoding="utf8") as f:
        json.dump(cache, f)

# ============================================================
# OpenCLIP
# ============================================================

import numpy as np
import torch
import open_clip

from sklearn.metrics.pairwise import cosine_similarity


def get_device():

    if torch.cuda.is_available():
        return "cuda"

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"

    return "cpu"


DEVICE = get_device()


print(f"Using device: {DEVICE}")


MODEL = None
PREPROCESS = None


def load_model():

    global MODEL
    global PREPROCESS

    if MODEL is not None:
        return

    print("Loading OpenCLIP model...")

    MODEL, _, PREPROCESS = open_clip.create_model_and_transforms(
        "ViT-B-32",
        pretrained="laion2b_s34b_b79k",
    )

    MODEL.eval()

    MODEL.to(DEVICE)


# ============================================================
# Embedding
# ============================================================

def image_embedding(path: Path):

    load_model()

    image = Image.open(path).convert("RGB")

    image = PREPROCESS(image)

    image = image.unsqueeze(0)

    image = image.to(DEVICE)

    with torch.no_grad():

        embedding = MODEL.encode_image(image)

        embedding /= embedding.norm(dim=-1, keepdim=True)

    return embedding.cpu().numpy()[0].astype(np.float32)


# ============================================================
# Cache helpers
# ============================================================

def cache_key(path: Path):

    stat = path.stat()

    return f"{path}:{stat.st_mtime}:{stat.st_size}"


def get_embeddings(images, folder):

    cache = load_cache(folder)

    embeddings = {}

    changed = False

    for image in tqdm(images, desc="OpenCLIP"):

        key = cache_key(image)

        if key in cache:

            embeddings[image] = np.array(cache[key], dtype=np.float32)

            continue

        emb = image_embedding(image)

        embeddings[image] = emb

        cache[key] = emb.tolist()

        changed = True

    if changed:
        save_cache(folder, cache)

    return embeddings


# ============================================================
# Similarity matrix
# ============================================================

def build_similarity_matrix(embeddings):

    files = list(embeddings.keys())

    vectors = np.vstack(
        [embeddings[f] for f in files]
    )

    similarity = cosine_similarity(vectors)

    return files, similarity

# ============================================================
# Union-Find (Disjoint Set Union)
# ============================================================

class UnionFind:

    def __init__(self, n):

        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):

        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]

        return x

    def union(self, a, b):

        ra = self.find(a)
        rb = self.find(b)

        if ra == rb:
            return

        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb

        elif self.rank[ra] > self.rank[rb]:
            self.parent[rb] = ra

        else:
            self.parent[rb] = ra
            self.rank[ra] += 1


# ============================================================
# Поиск похожих фотографий
# ============================================================

def find_similar_groups(
    embeddings,
    threshold=SIMILARITY_THRESHOLD,
):

    files, similarity = build_similarity_matrix(embeddings)

    uf = UnionFind(len(files))

    # -----------------------------------------
    # Объединяем точные дубликаты (SHA256)
    # -----------------------------------------

    hashes = {}

    for index, file in enumerate(files):

        digest = sha256(file)

        if digest in hashes:

            uf.union(index, hashes[digest])

        else:

            hashes[digest] = index

    print()
    print("Searching similar images...")

    for i in tqdm(range(len(files))):

        for j in range(i + 1, len(files)):

            if similarity[i, j] >= threshold:

                uf.union(i, j)

    groups = {}

    for i, file in enumerate(files):

        root = uf.find(i)

        groups.setdefault(root, []).append(file)

    result = []

    for group in groups.values():

        if len(group) > 1:
            result.append(sorted(group))

    return result


# ============================================================
# Красивый вывод
# ============================================================

def print_groups(groups):

    if not groups:

        print()
        print("No similar photos found.")
        return

    print()
    print("=" * 70)
    print("SIMILAR GROUPS")
    print("=" * 70)

    for i, group in enumerate(groups, start=1):

        print()
        print(f"Group {i}")

        for photo in group:

            print("   ", photo.name)


# ============================================================
# Статистика
# ============================================================

def print_statistics(images, exact_groups, similar_groups):

    print()
    print("=" * 70)
    print("STATISTICS")
    print("=" * 70)

    print(f"Images scanned          : {len(images)}")
    print(f"Exact duplicate groups  : {len(exact_groups)}")
    print(f"Similar groups          : {len(similar_groups)}")

    exact_files = sum(len(x) - 1 for x in exact_groups)
    similar_files = sum(len(x) - 1 for x in similar_groups)

    print(f"Exact duplicate files   : {exact_files}")
    print(f"Similar files           : {similar_files}")

# ============================================================
# Optional OpenCV (резкость)
# ============================================================

try:
    import cv2

    HAS_OPENCV = True

except ImportError:

    HAS_OPENCV = False


# ============================================================
# EXIF Date
# ============================================================

def exif_datetime(path: Path):

    try:

        img = Image.open(path)

        exif = img.getexif()

        if not exif:
            return 0

        value = exif.get(306)

        if value is None:
            value = exif.get(36867)

        if value is None:
            return 0

        from datetime import datetime

        dt = datetime.strptime(
            value,
            "%Y:%m:%d %H:%M:%S",
        )

        return dt.timestamp()

    except Exception:

        return 0


# ============================================================
# Sharpness
# ============================================================

def image_sharpness(path: Path):

    if not HAS_OPENCV:
        return 0

    try:

        image = cv2.imread(str(path))

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        return cv2.Laplacian(
            gray,
            cv2.CV_64F,
        ).var()

    except Exception:

        return 0


# ============================================================
# Score
# ============================================================

def image_score(path: Path):

    try:

        with Image.open(path) as img:

            width, height = img.size

    except Exception:

        width = 0
        height = 0

    stat = path.stat()

    pixels = width * height

    filesize = stat.st_size

    exif_date = exif_datetime(path)

    modified = stat.st_mtime

    sharpness = image_sharpness(path)

    return (

        pixels,

        sharpness,

        filesize,

        exif_date,

        modified,

    )


# ============================================================
# Best image
# ============================================================

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


# ============================================================
# Preview
# ============================================================

def print_best(groups):

    print()
    print("=" * 70)
    print("BEST IMAGES")
    print("=" * 70)

    for i, group in enumerate(groups, start=1):

        best = choose_best(group)

        print()

        print(f"Group {i}")

        print(" Keep :", best.name)

        print(" Move :")

        for photo in group:

            if photo != best:

                print("    ", photo.name)


# ============================================================
# Move files
# ============================================================

def ensure_duplicates_folder(root: Path):

    dst = root / DUPLICATE_FOLDER

    dst.mkdir(exist_ok=True)

    return dst


def unique_destination(folder: Path, file: Path):

    dst = folder / file.name

    if not dst.exists():
        return dst

    i = 1

    while True:

        candidate = folder / f"{file.stem}_{i}{file.suffix}"

        if not candidate.exists():
            return candidate

        i += 1


def move_duplicates(groups, root, dry_run=False):

    duplicate_folder = ensure_duplicates_folder(root)

    moved = []

    skipped = set()

    print()
    print("=" * 70)
    print("MOVING DUPLICATES")
    print("=" * 70)

    for group in groups:

        best = choose_best(group)

        print()
        print(f"Keeping : {best.name}")

        for photo in group:

            if photo == best:
                continue

            if photo in skipped:
                continue

            skipped.add(photo)

            dst = unique_destination(
                duplicate_folder,
                photo,
            )

            if dry_run:

                print(f"[DRY] {photo.name} -> {dst.name}")

            else:

                shutil.move(photo, dst)

                print(f"{photo.name} -> {dst.name}")

            moved.append(photo)

    return moved


# ============================================================
# Main
# ============================================================

def main():

    args = parse_args()

    root = args.folder.resolve()

    if not root.exists():

        print("Folder does not exist.")

        return

    print()
    print("=" * 70)
    print("PHOTO CLEANER")
    print("=" * 70)

    images = find_images(root)

    print(f"Found {len(images)} images")

    if not images:

        return

    print()
    print("Building embeddings...")

    embeddings = get_embeddings(images, root)

    print()
    print("Searching similar photos...")

    similar_groups = find_similar_groups(
        embeddings,
        threshold=args.threshold,
    )

    print_statistics(
        images,
        [],
        similar_groups,
    )

    print_groups(similar_groups)

    print_best(similar_groups)

    moved = move_duplicates(
        similar_groups,
        root,
        args.dry_run,
    )

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)

    if args.dry_run:

        print(f"[DRY RUN] Would move {len(moved)} files")

    else:

        print(f"Moved {len(moved)} files")

    print()
    print("Finished.")


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    main()