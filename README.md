# RoboLab material rendering evidence

Two before/after images, a portable reproduction script, the public-main material audit, exact diagnostic color changes, and relevant renderer warnings for the OneBottleOnShelf issue.

Public revision: `ad45d4f974725d020f82c2b0d77d78533aeba2b3`. The displayed images are from the confirming upstream-main run; all 12 composed scene USD layers were verified identical to this public revision.

From an installed RoboLab checkout with LFS assets:

```sh
PYTHONPATH="$PWD" ROBOLAB_RENDER_OUTPUT=/tmp/robolab-material-reproduction \
  .venv/bin/python /absolute/path/to/reproduce.py
```

The diagnostic changes material colors in the temporary USD session layer only. No source assets were modified.
