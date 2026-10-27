"""Generate a 3D mesh from the ghost reference image via Hunyuan3D-2mini.

Run with the venv python AFTER torch + deps are installed:
    tools/hunyuan3d/venv/Scripts/python.exe tools/hunyuan3d/gen_shape.py

Output: tools/hunyuan3d/out/ghost_ai.glb (untextured geometry).
Model weights land in tools/hunyuan3d/hf-cache (~4 GB, first run only).
"""

import os
import sys
import time

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "tools", "hunyuan3d")
REPO = os.path.join(ROOT, "Hunyuan3D-2")
sys.path.insert(0, REPO)
os.environ.setdefault("HF_HOME", os.path.join(ROOT, "hf-cache"))

OUT_DIR = os.path.join(ROOT, "out")
os.makedirs(OUT_DIR, exist_ok=True)
OUT = os.path.join(OUT_DIR, "ghost_ai.glb")
INPUT = os.path.join(ROOT, "input", "ghost_reference.png")

import torch  # noqa: E402
from PIL import Image  # noqa: E402

from hy3dgen.rembg import BackgroundRemover  # noqa: E402
from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline  # noqa: E402

print("CUDA:", torch.cuda.is_available(),
      torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")

image = Image.open(INPUT).convert("RGB")
image = BackgroundRemover()(image)
image.save(os.path.join(OUT_DIR, "input_clean.png"))

t0 = time.time()
pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    "tencent/Hunyuan3D-2mini",
    subfolder="hunyuan3d-dit-v2-mini-turbo",
    dtype=torch.float16)
pipeline.enable_flashvdm(topk_mode="merge")
print(f"pipeline loaded in {time.time() - t0:.0f}s")

t0 = time.time()
mesh = pipeline(
    image=image,
    octree_resolution=256,
    num_inference_steps=15,
    guidance_scale=5.5,
    output_type="trimesh",
)[0]
print(f"shape generated in {time.time() - t0:.0f}s: "
      f"{len(mesh.faces)} faces, {len(mesh.vertices)} verts")

mesh.export(OUT)
print("SAVED", OUT)
