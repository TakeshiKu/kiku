"""Сборка Кику: собрать все детали, проверить габарит стола, выгрузить в cad/out/.

Запуск из корня репозитория:  .venv/bin/python cad/build.py [имя ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from build123d import export_step, export_stl

from kiku_cad.probes import insert_probe, pi4_probe, servo_probe

BED = 180.0  # A1 mini: 180×180×180 мм
OUT = Path(__file__).resolve().parent / "out"

PARTS = {
    "probe_insert_m3": insert_probe.build,
    "probe_pi4": pi4_probe.build,
    "probe_servo_sts3215": servo_probe.build,
}


def main(names: list[str]) -> int:
    OUT.mkdir(exist_ok=True)
    failed = 0
    for name, make in PARTS.items():
        if names and name not in names:
            continue
        part = make()
        bb = part.bounding_box()
        size = (bb.size.X, bb.size.Y, bb.size.Z)
        ok_bed = all(s <= BED for s in size)
        ok_solid = part.is_valid and len(part.solids()) == 1
        status = "ok" if ok_bed and ok_solid else "ОШИБКА"
        if not (ok_bed and ok_solid):
            failed += 1
        export_stl(part, str(OUT / f"{name}.stl"))
        export_step(part, str(OUT / f"{name}.step"))
        print(f"{status:7} {name:24} {size[0]:6.1f}×{size[1]:6.1f}×{size[2]:6.1f} мм  "
              f"объём {part.volume / 1000:5.1f} см³"
              + ("" if ok_bed else "  > стол 180")
              + ("" if ok_solid else f"  тел: {len(part.solids())}, valid={part.is_valid}"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
