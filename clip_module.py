
import open_clip, torch
from PIL import Image

device="cuda" if torch.cuda.is_available() else "cpu"
model,_,preprocess=open_clip.create_model_and_transforms("ViT-B-32",pretrained="laion2b_s34b_b79k")
model=model.to(device).eval()

def embedding(path):
    img=preprocess(Image.open(path).convert("RGB")).unsqueeze(0).to(device)
    with torch.no_grad():
        e=model.encode_image(img)
        e/=e.norm(dim=-1,keepdim=True)
    return e.cpu().numpy()[0]
