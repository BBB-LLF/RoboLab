# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Capture a task's initial materials after renderer warm-up, without policy actions.

Run with the checkout on PYTHONPATH and an Isaac Lab Python environment. Compare
separate invocations before and after editing assets to exercise saved USD files.
"""

import argparse
import json
from pathlib import Path

import cv2  # noqa: F401 -- import before Isaac Lab
from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--task-file", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--warmup-frames", type=int, default=150)
parser.add_argument("--seed", type=int, default=0)
args = parser.parse_args()
args.output = args.output.resolve()
args.output.mkdir(parents=True, exist_ok=True)
app = AppLauncher(headless=True, enable_cameras=True).app

import omni.usd  # noqa: E402
from PIL import Image  # noqa: E402
from pxr import UsdShade  # noqa: E402

from robolab.constants import set_output_dir  # noqa: E402
from robolab.core.environments.factory import get_envs  # noqa: E402
from robolab.core.environments.runtime import create_env  # noqa: E402
from robolab.registrations.droid.auto_env_registrations_jointpos import auto_register_droid_envs  # noqa: E402
from robolab.registrations.droid.camera_presets import WRIST_LEFT_RIGHT  # noqa: E402

env = None
try:
    set_output_dir(str(args.output / "runtime"))
    auto_register_droid_envs(task=str(args.task_file.resolve()), cameras=WRIST_LEFT_RIGHT)
    names = get_envs()
    assert len(names) == 1, names
    env, cfg = create_env(names[0], seed=args.seed, num_envs=1)
    env.reset()
    for _ in range(args.warmup_frames):
        env.sim.render()
        env.scene.update(env.physics_dt)
    captures = []
    for name, sensor in env.scene.sensors.items():
        if not hasattr(sensor.data, "output") or "rgb" not in sensor.data.output:
            continue
        sensor.update(env.physics_dt, force_recompute=True)
        rgb = sensor.data.output["rgb"][0].cpu().numpy()[:, :, :3]
        Image.fromarray(rgb).save(args.output / f"{name}.png")
        captures.append(name)
    materials = {}
    for prim in omni.usd.get_context().get_stage().Traverse():
        if prim.IsA(UsdShade.Shader) and "/scene/" in str(prim.GetPath()):
            materials[str(prim.GetPath())] = {
                attr.GetName(): str(attr.Get())
                for attr in prim.GetAttributes() if attr.HasAuthoredValueOpinion()
            }
    (args.output / "capture.json").write_text(json.dumps({
        "task": names[0], "seed": args.seed, "warmup_frames": args.warmup_frames,
        "physics_actions": 0, "cameras": captures, "materials": materials,
    }, indent=2) + "\n")
    print("MATERIAL_RENDER_COMPLETE", args.output, flush=True)
finally:
    if env is not None:
        env.close()
    app.close()
