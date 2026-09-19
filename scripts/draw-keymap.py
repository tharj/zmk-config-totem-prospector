"""Draw the repository keymap using the firmware's physical layout."""
from pathlib import Path
import subprocess
import sys

import resvg_py

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "keymap-drawer"


def keymap(*args):
    subprocess.run(
        [sys.executable, "-m", "keymap_drawer", "-c", "keymap-drawer/config.yaml", *args],
        cwd=ROOT,
        check=True,
    )


keymap("parse", "-z", "config/totem.keymap", "-o", "keymap-drawer/totem.yaml")
keymap(
    "draw", "keymap-drawer/totem.yaml",
    "-d", "boards/shields/totem/totem.dtsi", "-l", "default_layout",
    "-o", "keymap-drawer/totem.svg",
)
(OUT / "totem.png").write_bytes(resvg_py.svg_to_bytes(
    svg_path=str(OUT / "totem.svg"),
    zoom=2, background="white",
))
print("Generated keymap-drawer/totem.svg and totem.png")
