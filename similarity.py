
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
from clip_module import embedding

EXT={".jpg",".jpeg",".png",".webp"}

def build_embeddings(folder):
    files=[p for p in Path(folder).rglob("*") if p.suffix.lower() in EXT]
    embs=[]
    for f in tqdm(files,desc="Embedding"):
        embs.append(embedding(f))
    return files,np.vstack(embs)

def find_similar(folder,threshold=0.97):
    files,embs=build_embeddings(folder)
    sim=cosine_similarity(embs)
    groups=[]
    used=set()
    for i in range(len(files)):
        if i in used: continue
        grp=[i]
        for j in range(i+1,len(files)):
            if sim[i,j]>=threshold:
                grp.append(j); used.add(j)
        if len(grp)>1:
            groups.append([files[k] for k in grp])
    return groups
