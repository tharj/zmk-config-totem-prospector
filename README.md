# TOTEM + Prospector on current ZMK

Personal 38-key TOTEM configuration with two Seeed XIAO nRF52840 halves and a XIAO-based Prospector display dongle. The dongle is the central; both keyboard halves connect to it wirelessly. USB Studio access is enabled on the dongle.

This migration starts from [tharj/zmk-config-2, commit 278074e](https://github.com/tharj/zmk-config-2/tree/278074e322a3eed99a44d1fc16884020235c6130). The original repository remains the working ZMK v0.3 fallback.

## Firmware

Open [Build firmware](https://github.com/tharj/zmk-config-totem-prospector/actions/workflows/build.yml), select a successful run, and download its `firmware` artifact. Every push or manual workflow run builds:

| File | Device |
| --- | --- |
| `totem_left.uf2` | Left TOTEM half |
| `totem_right.uf2` | Right TOTEM half |
| `totem_dongle_prospector.uf2` | Prospector dongle |
| `settings_reset.uf2` | Optional settings reset for any of the three XIAO controllers |

Use all three device firmware files from the same successful run for the migration. Enter each controller's UF2 bootloader and copy its matching UF2 to the mounted drive. Settings reset is a recovery tool, not the normal keyboard firmware.

## Current dependencies

| Component | Tracked revision |
| --- | --- |
| ZMK and its official build workflow | `main` |
| Zephyr and LVGL | Versions selected by ZMK's manifest |
| Prospector | `feat/new-status-screens`, the upstream Zephyr 4.1-compatible branch |
| ZMK Unicode | `main` |

As of the migration, the latest published ZMK release is still v0.3.0. This repository intentionally follows current development to use the newer platform. Prospector's compatible branch is marked work in progress upstream. Branches can change between builds; preserve a successful firmware ZIP before rebuilding. Moving to a future stable release means changing both the ZMK revision and reusable workflow reference together after checking module compatibility.

The root `CMakeLists.txt` enables a small compatibility header in `compat/include/` that supplies the missing ZMK keycode include when the Unicode behavior loads its header. It preserves the required system-header order and leaves upstream source files untouched. Remove this workaround once the missing include is fixed upstream.

## Keymap and behavior

Edit `config/totem.keymap`. The shield default includes that same file, so there is only one personal keymap to maintain.

- Layers: Base (0), Num (1), Nav (2), Mouse (3).
- OS-key hold-taps: tap-preferred, 280 ms prior idle, 450 ms tapping term, 175 ms quick tap; includes GUI/1 on Num.
- Other home-row hold-taps: balanced, 130 ms prior idle, 280 ms tapping term, 175 ms quick tap.
- Opposite-hand and thumb positional triggers are retained, including the corrected Q position.
- Outer right thumb holds Mouse momentarily. Right-click is also available on the left Space thumb while Mouse is active.
- Existing modifier morphs, combos, Shift/Enter thumbs, Tab/Nav, and Backspace/Num behavior are preserved.
- Unicode ä/ö still uses WinCompose with Right Alt as the compose key. Keep the host's US layout and existing WinCompose setup.

The layer constants now agree with the actual layer order. The B+N combo is named `ToNav` to reflect its existing action; its destination has not changed.

## Prospector

The Classic status screen is selected with fixed brightness 30%, ambient-light sensing disabled, and Windows-style modifier indicators. The current module provides active layer names, peripheral battery/connection status, output status, active modifiers, and Caps Word indication.

Radio settings and peripheral battery reporting are retained. Device-specific display, mouse, and central settings live in `config/totem_dongle.conf`; common radio and Unicode timing settings live in `config/totem.conf`.

If re-pairing is needed, follow [ZMK's split connection troubleshooting](https://zmk.dev/docs/troubleshooting/connection-issues). For correct left/right battery ordering, pair the left half before the right, as described by Prospector upstream. A settings reset clears saved pairing and other settings; flash the correct normal firmware again afterward.

## Validation

A successful Actions run verifies compilation and artifact packaging. Physical testing is still needed for all 38 keys, the new HRM timings, Unicode, mouse buttons, USB/Studio, wireless reconnect after power cycling, and the Prospector layer, Caps Word, and battery indicators. Existing Studio overrides may differ from this compiled keymap; check or reset those overrides if the flashed map does not match the source.

## Repository layout

- `config/`: personal keymap, settings, and West dependency manifest.
- `boards/shields/totem/`: matrix wiring, physical layout, and shield definitions.
- `zephyr/module.yml`: unified configuration/module registration.
- `build.yaml`: modern `xiao_ble//zmk` build targets and firmware names.
- `.github/workflows/build.yml`: official reusable ZMK build workflow.

## Upstream projects

- [ZMK](https://github.com/zmkfirmware/zmk) and its [current hardware migration guide](https://zmk.dev/blog/2025/12/09/zephyr-4-1).
- [TOTEM hardware](https://github.com/GEIGEIGEIST/TOTEM).
- [Prospector module and setup instructions](https://github.com/carrefinho/prospector-zmk-module/tree/feat/new-status-screens).
- [ZMK Unicode](https://github.com/urob/zmk-unicode).
- [Unified ZMK configuration template](https://github.com/zmkfirmware/unified-zmk-config-template).

Original source copyright notices have been preserved.
