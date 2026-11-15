"""Сборка Кику: собрать все детали, проверить габарит стола, выгрузить в cad/out/.

Запуск из корня репозитория:  .venv/bin/python cad/build.py [имя ...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from build123d import Mesher, Pos, export_step, export_stl

from kiku_cad import display_frame
from kiku_cad.probes import insert_probe, pi4_probe, servo_probe

BED = 180.0  # A1 mini: 180×180×180 мм
OUT = Path(__file__).resolve().parent / "out"

PARTS = {
    "probe_insert_m3": insert_probe.build,
    "probe_pi4": pi4_probe.build,
    "probe_servo_sts3215": servo_probe.build,
    "display_frame_tft28": display_frame.build,
}


# Стол пробников: (имя, X, Y) центра детали на столе A1 mini, 0..180
PROBE_PLATE = (
    ("probe_pi4", 90, 135),
    ("probe_servo_sts3215", 135, 55),
    ("probe_insert_m3", 55, 40),
)


def plate_probes() -> Path:
    """Все пробники на одном столе — один 3MF для Bambu Studio."""
    mesher = Mesher()
    for name, x, y in PROBE_PLATE:
        part = PARTS[name]()
        c = part.bounding_box().center()
        part = Pos(x - c.X, y - c.Y, -part.bounding_box().min.Z) * part
        part.label = name
        mesher.add_shape(part, part_number=name)
    path = OUT / "plate_probes.3mf"
    mesher.write(str(path))
    return path


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
    if not names or "plate_probes" in names:
        print("ok      plate_probes ->", plate_probes().name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
