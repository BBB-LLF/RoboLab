# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import cv2
import json
import os
from pathlib import Path
from isaaclab.app import AppLauncher

launcher = AppLauncher(headless=True, enable_cameras=True)
app = launcher.app

import omni.usd
from pxr import UsdShade, Sdf, Gf
from PIL import Image
import robolab
from robolab.constants import set_output_dir
from robolab.core.environments.runtime import create_env
from robolab.core.environments.factory import get_envs
from robolab.registrations.droid.auto_env_registrations_jointpos import auto_register_droid_envs
from robolab.registrations.droid.camera_presets import WRIST_LEFT_RIGHT

out = Path(os.environ.get('ROBOLAB_RENDER_OUTPUT', 'output/material-render-reproduction')).resolve()
out.mkdir(parents=True, exist_ok=True)
set_output_dir(str(out / 'runtime'))
print('INVESTIGATION_CODE', robolab.__file__, flush=True)
auto_register_droid_envs(task='OneBottleOnShelfTask', cameras=WRIST_LEFT_RIGHT)
names = get_envs(task=['OneBottleOnShelfTask'])
print('INVESTIGATION_ENVS', names, flush=True)
env, cfg = create_env(names[0], seed=0, num_envs=1)
env.reset()
print('INVESTIGATION_SENSORS', list(env.scene.sensors), flush=True)

def capture(label, frames):
    for _ in range(frames):
        env.sim.render()
        env.scene.update(env.physics_dt)
    for name, sensor in env.scene.sensors.items():
        if not hasattr(sensor.data, 'output') or 'rgb' not in sensor.data.output:
            continue
        sensor.update(env.physics_dt, force_recompute=True)
        rgb = sensor.data.output['rgb'][0].cpu().numpy()[:, :, :3]
        Image.fromarray(rgb).save(out / f'{label}-{name}.png')
    print('INVESTIGATION_CAPTURE', label, flush=True)

capture('main-warmup-30', 30)
capture('main-warmup-150', 120)
stage = omni.usd.get_context().get_stage()
changes = []
with __import__('pxr.Usd', fromlist=['EditContext']).EditContext(stage, stage.GetSessionLayer()):
    for prim in stage.Traverse():
        path = str(prim.GetPath())
        if prim.IsA(UsdShade.Shader) and any('/'+obj+'/' in path for obj in ['whitepackerbottle_a02', 'whitepackerbottle_a03', 'squarepail_a01']):
            if 'opaque__plastic__' in path:
                before = prim.GetAttribute('inputs:diffuse_color_constant').Get()
                UsdShade.Shader(prim).CreateInput('diffuse_color_constant', Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.85))
                changes.append({'shader': path, 'before': str(before), 'after': [0.85]*3})
capture('diagnostic-white-base-color', 60)
(out / 'diagnostic-changes.json').write_text(json.dumps(changes, indent=2)+'\n')
print('INVESTIGATION_DONE', json.dumps(changes), flush=True)
env.close()
app.close()
