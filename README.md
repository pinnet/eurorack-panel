# eurorack_panel.py

Generates a KiCad 10 Eurorack front panel (`.kicad_pcb`) from an HP width. Pure Python, no KiCad needed to run it.

```
python eurorack_panel.py 8                            # 8HP outline + rail holes
python eurorack_panel.py 8 --jacks 8 --cols 2         # plus 8 jack holes, 2 x 4 grid
python eurorack_panel.py 12 --jacks 6 --slots -o mymodule.kicad_pcb
```

Options: `--jacks N`, `--cols C` (default balances the grid to the width), `--jack-hole 6.2`, `--rail-hole 3.2`, `--slots` (oval rail slots), `--origin X Y`, `-o file`.

Standards (Doepfer A-100): height 128.5 mm; width from Doepfer's table (e.g. 8HP = 40.3 mm), otherwise HP x 5.08 - 0.3 mm; rail holes 3 mm from top/bottom, 7.5 mm from the left, second hole at 7.5 + (HP-3) x 5.08 mm for 10HP and up.

Jack holes default to 6.2 mm for 3.5 mm Thonkiconn-style jacks. Holes are non-plated footprints excluded from BOM/placement.

`test_8hp.kicad_pcb` is a sample output (8HP, 8 jacks) that KiCad 10 loads cleanly.

## Licence

MIT - see [LICENSE](LICENSE).
