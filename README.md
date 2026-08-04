# 📸 Photo Cleaner

> Offline photo duplicate finder powered by OpenCLIP.

Photo Cleaner automatically finds duplicate and visually similar photos, keeps the best image, and moves the rest into a **Duplicates** folder.

No cloud. No uploads. Everything runs locally on your computer.

---

## ✨ Features

- 🔍 Exact duplicate detection (SHA256)
- 🧠 Similar photo detection using OpenCLIP
- ⭐ Automatic best photo selection
- 📦 Moves duplicates into a `Duplicates` folder
- 🚀 Embedding cache for faster subsequent runs
- 🖥 Works completely offline
- 📊 Progress bars using `tqdm`
- 🔎 Dry Run mode
- 🍎 macOS support
- 🪟 Windows support

---

## 📷 Supported Formats

- JPG
- JPEG
- PNG
- WEBP
- HEIC
- HEIF

---

# Installation

## Requirements

- Python 3.14+
- Windows 10 / 11
- macOS

---

## Windows

Before installing dependencies you **must** install:

**Microsoft Visual C++ Redistributable 2015–2022 (x64)**

https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

Without it PyTorch may fail with:

```text
OSError: [WinError 1114]
Error loading c10.dll
```

Create virtual environment:

```bash
python -m venv venv

venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## macOS

```bash
python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt
```

---

# Usage

## Preview only (recommended)

```bash
python photo_cleaner.py "/path/to/photos" --dry-run
```

Nothing will be moved.

---

## Clean photos

```bash
python photo_cleaner.py "/path/to/photos"
```

---

## Custom similarity threshold

Default:

```text
0.97
```

Example:

```bash
python photo_cleaner.py "/path/to/photos" --threshold 0.94
```

Lower threshold finds more similar photos.

---

# How It Works

```text
Scan images
      │
      ▼
SHA256 duplicate detection
      │
      ▼
OpenCLIP embeddings
      │
      ▼
Similarity comparison
      │
      ▼
Grouping similar photos
      │
      ▼
Choose best photo
      │
      ▼
Move remaining photos
```

---

# Best Photo Selection

For every similar group Photo Cleaner keeps the best image based on:

1. Image resolution
2. Image sharpness (OpenCV)
3. File size
4. EXIF date
5. File modification date

Example:

```text
Group 1

Keep:
IMG_4128.JPG

Move:
IMG_4129.JPG
IMG_4130.JPG
```

---

# Example Output

```text
==================================================
PHOTO CLEANER
==================================================

Found 324 images

Searching similar images...

Group 1

Keep:
IMG_2314.JPG

Move:
IMG_2315.JPG
IMG_2316.JPG

Done.

Moved 2 files.
```

---

# Performance

Typical processing time:

| Photos | Time |
|---------|------|
| 100 | ~10 sec |
| 300 | ~25 sec |
| 1000 | ~1-2 min |

*(CPU, Apple M-series / modern Intel CPUs)*

---

# Project Structure

```
photo-cleaner/
│
├── photo_cleaner.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

---

# Roadmap

## Version 1.1

- [ ] Skip scanning `Duplicates` folder
- [ ] SQLite cache
- [ ] Faster SHA256 cache
- [ ] Better Windows error messages

## Version 1.2

- [ ] NearestNeighbors instead of full similarity matrix
- [ ] Faster embedding generation
- [ ] Better duplicate grouping

## Version 2.0

- [ ] Local Vision AI
- [ ] Automatic best-shot selection
- [ ] GUI
- [ ] AI quality scoring

---

# Limitations

Current version detects visually similar photos but **does not understand photo quality**.

For example it cannot determine:

- closed eyes
- smiles
- looking at the camera
- composition
- facial expressions

These features are planned for Version 2.0 using a local Vision AI model.

---

# Privacy

✅ No cloud services

✅ No internet required

✅ No photo uploads

Everything is processed locally on your computer.

---

# License

MIT License

---

# Contributing

Pull requests, bug reports and feature requests are welcome.

If you find a bug, please open an Issue describing:

- operating system
- Python version
- error message
- steps to reproduce

---

Made with ❤️ using Python and OpenCLIP.