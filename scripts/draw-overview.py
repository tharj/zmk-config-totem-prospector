"""Generate light/dark four-layer overviews using keymap-drawer's corner labels."""
from copy import deepcopy
from io import StringIO
from math import cos, sin, radians
from pathlib import Path
import re
import xml.etree.ElementTree as ET

import resvg_py
from keymap_drawer.config import Config
from keymap_drawer.draw.draw import KeymapDrawer
from keymap_drawer.physical_layout import PhysicalLayoutGenerator

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
LAYERS = ("Base", "Num", "Nav", "Mouse")
CORNERS = ("tl", "tr", "bl", "br")
PALETTES = {
    "light": dict(bg="#f5f1e8", key="#fffdf7", border="#c9c1b5", ink="#302e33",
                  muted="#625d65", guide="#e5ded3", combo="#e8e1d7", wire="#79727e",
                  colors=("#303039", "#154e85", "#a34315", "#703b98")),
    "dark": dict(bg="#0c0b19", key="#17162b", border="#3b3658", ink="#f4efff",
                 muted="#b5accd", guide="#302945", combo="#26213d", wire="#8f80ae",
                 colors=("#ff59bf", "#42e8ff", "#ffe569", "#72ffc6")),
}
SHORT = {"Play/Pause": "Play/II", "Previous": "Prev", "Volume −": "Vol−", "Volume +": "Vol+",
         "Page Up": "PgUp", "Page Down": "PgDn", "Gui+Sft+S": "Win+Sft+S",
         "Studio Unlock": "Unlock", "Left Click": "Click L", "Right Click": "Click R",
         "Middle Click": "Click M", "Mouse ↑": "↑", "Mouse ↓": "↓", "Mouse ←": "←",
         "Mouse →": "→", "LShift": "LSft", "RShift": "RSft", "LCtrl": "LCtl", "RCtrl": "RCtl"}


def el(parent, tag, text=None, **attrs):
    node = ET.SubElement(parent, f"{{{NS}}}{tag}", {k.replace("_", "-"): str(v) for k, v in attrs.items()})
    node.text = text
    # Inline styles beat drawer's global text rules (presentation attributes do not).
    if tag == "text":
        properties = ("font-size", "font-weight", "text-anchor", "letter-spacing", "fill", "dominant-baseline")
        node.set("style", ";".join(f"{key}:{node.attrib.pop(key)}" for key in properties if key in node.attrib))
    return node


def binding(value):
    return value if isinstance(value, dict) else {"t": str(value) if value is not None else ""}


def edge(key, target, padding):
    """Intersect a center-to-target ray with the rotated, visible key rectangle."""
    angle = radians(key.rotation)
    dx, dy = target[0] - key.pos.x, target[1] - key.pos.y
    lx, ly = dx * cos(angle) + dy * sin(angle), -dx * sin(angle) + dy * cos(angle)
    sx = (key.width / 2 - padding) / abs(lx) if lx else float("inf")
    sy = (key.height / 2 - padding) / abs(ly) if ly else float("inf")
    factor = min(sx, sy)
    return key.pos.x + dx * factor, key.pos.y + dy * factor


def make_overviews(root: Path, data: dict):
    if tuple(data["layers"]) != LAYERS:
        raise ValueError(f"Overview expects layer order {LAYERS}; update corner mapping for new layers")
    notes = []
    details = {}
    overview = []
    size = len(data["layers"]["Base"])
    if any(len(layer) != size for layer in data["layers"].values()):
        raise ValueError("Layer key counts differ")
    for index in range(size):
        key = {}
        seen_taps, seen_holds = set(), set()
        for layer, corner in zip(LAYERS, CORNERS):
            value = binding(data["layers"][layer][index])
            tap, hold, shifted = (value.get(field, "") for field in ("t", "h", "s"))
            # Drawer replaces transparent entry keys with an empty held marker.
            if not tap and value.get("type") == "held":
                tap = "▽"
            label = SHORT.get(tap, tap) or "·"
            if hold == "go to":
                label, sub = "→" + label, "switch"
            elif hold == "hold":
                sub = "hold"
            else:
                sub = "h:" + SHORT.get(hold, hold) if hold else ""
            if shifted:
                note = f"{tap}: {shifted}"
                if note not in notes:
                    notes.append(note)
                label += str(notes.index(note) + 1).translate(str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹"))
            # Deduplicate by source action, never by shortened display text:
            # cursor arrows and mouse movement have different meanings.
            signature = (tap, shifted, hold if hold in ("go to", "hold") else "")
            if tap and signature in seen_taps:
                label = ""
            elif tap:
                seen_taps.add(signature)
            if hold and hold not in ("go to", "hold"):
                if hold in seen_holds:
                    sub = ""
                else:
                    seen_holds.add(hold)
            key[corner] = label
            details[index, corner] = (sub, value)
        overview.append(key)

    for theme, palette in PALETTES.items():
        config = Config(draw_config=dict(
            key_w=160, key_h=160, inner_pad_w=9, inner_pad_h=9, small_pad=10,
            outer_pad_w=70, outer_pad_h=55, combo_w=146, combo_h=44,
            key_rx=12, key_ry=12, shrink_wide_legends=0, style_layer_activators=False,
            footer_text="", svg_extra_style=styles(palette),
        ))
        layout = PhysicalLayoutGenerator(config=config, dts_layout=root / "boards/shields/totem/totem.dtsi",
                                         layout_name="default_layout").generate()
        combos = deepcopy(data.get("combos", []))
        for combo in combos:
            combo["l"] = ["Overview"]
            points = tuple(combo["p"])
            if points == (20, 31):
                # The only spanning combo with intervening keys: route below the board.
                source_bottom = max(layout.keys[p].pos.y + layout.keys[p].height / 2 for p in points)
                combo.update(a="bottom", o=(layout.height + 55 - source_bottom - config.draw_config.inner_pad_h / 2) / layout.min_height,
                             w=178, h=44)
            else:
                combo.update(a="mid", o=0, d=True)
                if points in ((19, 29), (30, 31)):
                    combo.update(w=40, h=34)
                elif points == (34, 35):
                    combo.update(w=76, h=32, type="thumb-combo")
                if isinstance(combo["k"], dict) and combo["k"].get("h") == "go to":
                    combo["k"] = "→" + combo["k"]["t"]
                elif combo["k"] == "Caps Word":
                    combo["k"] = "Caps  Word"  # double space keeps one line
        stream = StringIO()
        drawer = KeymapDrawer(config, stream, layout=layout, layers={"Overview": overview}, combos=combos)
        drawer.print_board()
        svg = ET.fromstring(stream.getvalue())
        width, board_height = float(svg.get("width")), float(svg.get("height"))
        header_height, footer_height = 220, 265
        height = board_height + header_height + footer_height
        svg.set("height", str(round(height)))
        svg.set("viewBox", f"0 0 {round(width)} {round(height)}")
        svg.set("role", "img")
        svg.set("aria-labelledby", "overview-title overview-description")
        el(svg, "title", f"TOTEM four-layer overview — {theme}", id="overview-title")
        el(svg, "desc", "38 physical keys. Base top left, Num top right, Nav bottom left, Mouse bottom right. Six combos connect their source keys.", id="overview-description")
        bg = ET.Element(f"{{{NS}}}rect", dict(width="100%", height="100%", fill=palette["bg"]))
        svg.insert(0, bg)
        drawing = el(svg, "g", transform=f"translate(0,{header_height})", id="keyboard")
        for child in list(svg):
            if child is not drawing and child.tag == f"{{{NS}}}g":
                svg.remove(child)
                drawing.append(child)
        # Drop the automatic layer heading, replaced by a designed page header.
        for group in drawing.iter():
            for child in list(group):
                if child.tag == f"{{{NS}}}text" and "label" in child.get("class", "").split():
                    group.remove(child)
        for group in drawing.iter(f"{{{NS}}}g"):
            match = re.search(r"\bkeypos-(\d+)\b", group.get("class", ""))
            if not match:
                continue
            index = int(match[1])
            # Quiet center ticks separate corner areas without boxing in all four labels.
            el(group, "path", d="M-7,0 H7 M0,-7 V7", fill="none", stroke=palette["guide"], stroke_width=1.3)
            for corner in CORNERS:
                text = next((t for t in group.findall(f"{{{NS}}}text")
                             if corner in t.get("class", "").split()), None)
                label = overview[index][corner]
                sub, original = details[index, corner]
                # Empty opposite corners let longer labels use more of the key width.
                opposite = corner[0] + ("r" if corner.endswith("l") else "l")
                other = overview[index][opposite]
                space = 60 if other not in ("", "·", "▽") else (112 if other else 128)
                font = min(28, space / (max(len(label), 1) * 0.57))
                if label in ("·", "▽"):
                    font = 22
                x = 65 if corner.endswith("r") else -65
                y = -61 if corner.startswith("t") else 61
                # Keep the inner thumb corners clear of the centered Base combo.
                if (index, corner) in ((34, "tr"), (35, "tl")):
                    x += -12 if corner.endswith("r") else 12
                    y -= 3
                if (index, corner) == (30, "tr"):
                    x -= 12
                elif (index, corner) == (31, "bl"):
                    x += 14
                if text is not None:
                    text.set("x", str(x))
                    text.set("y", str(y))
                    text.set("style", f"font-size:{font:.1f}px")
                    el(text, "title", f"{LAYERS[CORNERS.index(corner)]}: {original}")
                if sub:
                    sy = y + (36 if corner.startswith("t") else -34)
                    el(group, "text", sub, x=x, y=sy, font_weight=400, **{"class": f"sub {corner}"})
            el(group, "title", f"Physical key {index}")
        # Straight, edge-terminated connectors make cross-half midpoint placement explicit.
        for group in drawing.iter(f"{{{NS}}}g"):
            match = re.search(r"\bcombopos-(\d+)\b", group.get("class", ""))
            if not match:
                continue
            combo = combos[int(match[1])]
            if tuple(combo["p"]) == (20, 31):
                continue
            box = group.find(f"{{{NS}}}rect")
            center = (float(box.get("x")) + float(box.get("width")) / 2,
                      float(box.get("y")) + float(box.get("height")) / 2)
            for path in list(group.findall(f"{{{NS}}}path")):
                group.remove(path)
            for p in combo["p"]:
                x, y = edge(layout.keys[p], center, config.draw_config.inner_pad_w)
                path = ET.Element(f"{{{NS}}}path", {"d": f"M{center[0]:.2f},{center[1]:.2f} L{x:.2f},{y:.2f}", "class": "combo"})
                group.insert(0, path)
        add_header(svg, width, theme, palette)
        add_footer(svg, width, board_height + header_height, notes, palette)
        path = root / "keymap-drawer" / f"totem-overview-{theme}.svg"
        ET.indent(svg)
        path.write_text(ET.tostring(svg, encoding="unicode") + "\n", encoding="utf-8")
        path.with_suffix(".png").write_bytes(resvg_py.svg_to_bytes(svg_path=str(path), zoom=1.5))
        print(f"Generated {path.name} and {path.with_suffix('.png').name}")


def styles(p):
    corners = "\n".join(f"text.{c} {{ fill: {color}; }}" for c, color in zip(CORNERS, p["colors"]))
    return f"""
svg.keymap {{ font-family: Arial, DejaVu Sans, sans-serif; fill: {p['ink']}; }}
rect.key {{ fill: {p['key']}; stroke: {p['border']}; stroke-width: 1.6; }}
rect.combo {{ fill: {p['combo']}; stroke: {p['wire']}; stroke-width: 1.5; }}
path.combo {{ fill: none; stroke: {p['wire']}; stroke-width: 1.6; }}
.thumb-combo text.combo {{ font-size: 16px; }}
text.combo {{ fill: {p['ink']}; font-size: 21px; font-weight: 600; }}
text.sub {{ font-size: 17px; font-weight: 400; }}
text.tl, text.tr, text.bl, text.br {{ font-weight: 600; }}
text.tl, text.tr {{ dominant-baseline: hanging; }}
text.bl, text.br {{ dominant-baseline: auto; }}
text.tl, text.bl {{ text-anchor: start; }}
text.tr, text.br {{ text-anchor: end; }}
{corners}
"""


def add_header(svg, width, theme, p):
    g = el(svg, "g", id="legend")
    el(g, "text", "TOTEM", x=70, y=76, font_size=54, font_weight=700, text_anchor="start", letter_spacing=7)
    el(g, "text", "FOUR LAYERS / ONE KEYBOARD", x=73, y=120, font_size=19, text_anchor="start", letter_spacing=3, fill=p["muted"])
    el(g, "text", "CYBERPUNK" if theme == "dark" else "WARM PAPER", x=73, y=161, font_size=15, text_anchor="start", letter_spacing=3, fill=p["muted"])
    x, y, w, h = width - 475, 37, 180, 145
    el(g, "rect", x=x, y=y, width=w, height=h, rx=14, fill=p["key"], stroke=p["border"], stroke_width=1.5)
    for corner, label, color in zip(CORNERS, LAYERS, p["colors"]):
        right, bottom = corner.endswith("r"), corner.startswith("b")
        el(g, "text", label, x=x + (w - 16 if right else 16), y=y + (h - 18 if bottom else 20),
           **{"class": corner}, font_size=22)
    el(g, "text", "Corner = layer", x=x+210, y=63, font_size=21, text_anchor="start")
    el(g, "text", "h: = hold action", x=x+210, y=97, font_size=20, text_anchor="start", fill=p["muted"])
    el(g, "text", "▽ = fall through", x=x+210, y=129, font_size=20, text_anchor="start", fill=p["muted"])
    el(g, "text", "· = no action", x=x+210, y=161, font_size=20, text_anchor="start", fill=p["muted"])
    el(g, "path", d=f"M70,208 H{width-70}", stroke=p["border"], stroke_width=1)


def add_footer(svg, width, y, notes, p):
    g = el(svg, "g", id="notes")
    el(g, "path", d=f"M70,{y+10} H{width-70}", stroke=p["border"], stroke_width=1)
    el(g, "text", "MODIFIER ACTIONS", x=70, y=y+44, font_size=18, letter_spacing=2, text_anchor="start")
    for index, note in enumerate(notes):
        col, row = index // 4, index % 4
        el(g, "text", f"{index+1}   {note}", x=70 + col * 450, y=y+78+row*30, font_size=20,
           text_anchor="start", fill=p["muted"])
    x = width - 1330
    lines = ["COMBOS", "Caps Word: G + H (Base only). Other combos work on all layers.",
             "→Nav: B + N.  →Base: both Enter thumbs.  Bootloader: Esc + apostrophe.",
             "Arrows: ö + dot = ←; ä + apostrophe = →. Lines show physical source keys.",
             "LC/LA = Left Ctrl or Left Alt. Win = GUI. Sft = Shift. Click L/M/R = mouse buttons."]
    for i, line in enumerate(lines):
        el(g, "text", line, x=x, y=y+44+i*30, font_size=18 if i == 0 else 20,
           text_anchor="start", fill=p["ink"] if i == 0 else p["muted"])
    el(g, "text", "Repeated actions and holds are shown once per key; blank corners omit repeats.  •  Repository keymap; Studio overrides not included.",
       x=70, y=y+229, font_size=19, text_anchor="start", fill=p["muted"])
