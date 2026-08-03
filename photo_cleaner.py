
# Part 1 skeleton. Further parts needed for full CLIP implementation.
import argparse, hashlib
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("folder")
    args=p.parse_args()
    files=[x for x in Path(args.folder).rglob("*") if x.suffix.lower() in {".jpg",".jpeg",".png",".webp"}]
    print(f"Found {len(files)} images")
    hashes={}
    for f in files:
        hashes.setdefault(sha256(f),[]).append(f)
    dups=[v for v in hashes.values() if len(v)>1]
    print(f"Exact duplicate groups: {len(dups)}")
    print("CLIP similarity search will be added in the next parts.")

if __name__=="__main__":
    main()
