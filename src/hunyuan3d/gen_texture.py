"""Texture the AI ghost mesh with Hunyuan3D's paint pipeline.

    tools/hunyuan3d/venv/Scripts/python.exe tools/hunyuan3d/gen_texture.py

Requires the compiled custom_rasterizer + differentiable_renderer
extensions (see docs). Renders multiview diffusion from the cleaned
reference image, bakes to an xatlas UV atlas.
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(ROOT, "Hunyuan3D-2")
sys.path.insert(0, REPO)
os.environ.setdefault("HF_HOME", os.path.join(ROOT, "hf-cache"))
# real-file weight copies (predownload_paint.py) — the hub cache
# symlinks need Windows Developer Mode
os.environ.setdefault("HY3DGEN_MODELS",
                      os.path.join(ROOT, "hy3dgen-models"))

import trimesh  # noqa: E402
from PIL import Image  # noqa: E402

from hy3dgen.texgen import Hunyuan3DPaintPipeline  # noqa: E402

mesh = trimesh.load(os.path.join(ROOT, "out", "ghost_ai_8k.glb"),
                    force="mesh")
image = Image.open(os.path.join(ROOT, "out", "input_clean.png")
                   ).convert("RGBA")

t0 = time.time()
pipeline = Hunyuan3DPaintPipeline.from_pretrained(
    "tencent/Hunyuan3D-2", subfolder="hunyuan3d-paint-v2-0-turbo")
print(f"paint pipeline loaded in {time.time() - t0:.0f}s")

# fit 8 GB VRAM: halve render/texture resolutions
cfg = pipeline.config
print(f"config: render={cfg.render_size} tex={cfg.texture_size} "
      f"azims={cfg.candidate_camera_azims}")
cfg.render_size = 1024
cfg.texture_size = 1024

t0 = time.time()
textured = pipeline(mesh, image=image)
print(f"textured in {time.time() - t0:.0f}s")

OUT = os.path.join(ROOT, "out", "ghost_ai_tex_8k.glb")
textured.export(OUT)
print("SAVED", OUT)
