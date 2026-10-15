# RoboLab background rendering evidence

Corrected investigation for issue #39. The visible gray ground mesh occludes the office panorama. Gray object materials are intentional and remain unchanged. The previous object-color diagnosis was a misunderstanding of the report.

Only the two images used in the issue are included. Text evidence contains a minimal background-only patch, audit summary, and reproduction script. The three original scene files match public revision `ad45d4f974725d020f82c2b0d77d78533aeba2b3`.

With an installed RoboLab checkout and LFS assets, capture the baseline:

```sh
PYTHONPATH="$PWD" .venv/bin/python /absolute/path/to/reproduce.py \
  --task-file robolab/tasks/benchmark/one_bottle_on_shelf_task.py \
  --output /tmp/robolab-background-before
```

Apply `background-fix.patch` with `git apply`, then run the same script in a separate process with `--output /tmp/robolab-background-after`. Review `over_shoulder_left_camera.png`. The script uses seed 0 and 150 warm-up frames without policy actions or material overrides.
