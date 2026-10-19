# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Run RoboLab (written for Isaac Lab 2.2 / 2.3) on Isaac Lab 3.0 / Isaac Sim 6.0.

Four things changed in Isaac Lab 3.0; everything here is the identity on Isaac Lab 2.x.

1. Scene objects are created through backend factories, so the robot in the scene is an
   ``isaaclab_physx`` Articulation and ``isinstance(robot, isaaclab.assets.Articulation)`` is False.
   The class names exported below resolve to the ``Base*`` classes every backend inherits from.
2. Every ``asset.data.*`` / ``sensor.data.*`` property returns a ProxyArray (a thin wrapper over a
   warp array) instead of a ``torch.Tensor``. ``to_torch`` returns the zero-copy torch view.
3. Quaternions are stored ``(x, y, z, w)`` instead of ``(w, x, y, z)``. ``cfg_quat`` converts a
   hand-written ``(w, x, y, z)`` literal to the order the running Isaac Lab expects, and ``quat_wxyz``
   converts a quaternion read back from Isaac Lab to ``(w, x, y, z)``.
4. Isaac Sim 6.0 ships ``isaacsim.core.prims``, ``isaacsim.core.api``, ``isaacsim.core.utils`` and
   ``isaacsim.sensors.camera`` under ``extsDeprecated``, which is not on the default path.
   ``import_deprecated_isaacsim`` enables those extensions and imports the module.
"""

import importlib
import os
from pathlib import Path

import torch
import warp as wp

try:
    from isaaclab.utils.warp.proxy_array import ProxyArray
except ImportError:  # Isaac Lab 2.x
    ProxyArray = None

ISAACLAB_3 = ProxyArray is not None

import isaaclab.assets as _assets  # noqa: E402
import isaaclab.sensors as _sensors  # noqa: E402

try:
    from isaaclab.assets import DeformableObject as _DeformableObject
except ImportError:  # Isaac Lab 2.3 moved deformables into isaaclab_physx
    from isaaclab_physx.assets import DeformableObject as _DeformableObject


def _base_class(factory_cls):
    """The ``Base<Name>`` class behind an Isaac Lab 3.0 factory class; the class itself on 2.x."""
    return next((c for c in factory_cls.__mro__ if c.__name__ == "Base" + factory_cls.__name__), factory_cls)


Articulation = _base_class(_assets.Articulation)
RigidObject = _base_class(_assets.RigidObject)
DeformableObject = _base_class(_DeformableObject)
ContactSensor = _base_class(_sensors.ContactSensor)
FrameTransformer = _base_class(_sensors.FrameTransformer)


def to_torch(value):
    """ProxyArray (Isaac Lab 3.0) -> its torch view; warp array (Isaac Lab 2.3) -> torch; else unchanged."""
    if ProxyArray is not None and isinstance(value, ProxyArray):
        return value.torch
    if isinstance(value, wp.array):
        return wp.to_torch(value)
    return value


def cfg_quat(wxyz):
    """A quaternion literal written as (w, x, y, z), in the order the running Isaac Lab expects."""
    w, x, y, z = wxyz
    return (x, y, z, w) if ISAACLAB_3 else (w, x, y, z)


def quat_wxyz(quat: torch.Tensor) -> torch.Tensor:
    """A quaternion read from Isaac Lab (last axis of size 4), reordered to (w, x, y, z)."""
    return quat[..., [3, 0, 1, 2]] if ISAACLAB_3 else quat


def import_deprecated_isaacsim(module_name: str):
    """Import an ``isaacsim.*`` module that Isaac Sim 6.0 moved under ``extsDeprecated``.

    Tries the plain import first, so on Isaac Sim 5.x this is just ``importlib.import_module``.
    Must be called after the Kit app has been launched (the extension manager is what enables them).
    """
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        pass
    import isaacsim
    import omni.kit.app

    manager = omni.kit.app.get_app().get_extension_manager()
    isaac_roots = (Path(isaacsim.__file__).parent, Path(os.environ.get("ISAAC_PATH", "/isaac-sim")))
    for folder in (root / "extsDeprecated" for root in isaac_roots):
        if folder.is_dir():
            manager.add_path(str(folder))
    for ext in ("isaacsim.core.utils", "isaacsim.core.prims", "isaacsim.core.api", "isaacsim.sensors.camera"):
        manager.set_extension_enabled_immediate(ext, True)
    return importlib.import_module(module_name)
