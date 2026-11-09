"""Пробник посадки STS3215: две обоймы-кольца с разным зазором.

Надеть на корпус привода со стороны дна (разъёмы внизу). Выбрать зазор, где
привод входит рукой, без люфта и не распирает кольцо; записать в
STS3215_FIT. Кольца низкие, чтобы не упираться в уступ у выходного торца.
"""
from build123d import (Align, Box, Part, Pos, Text, extrude)

from kiku_cad.parts import STS3215

FITS = (0.15, 0.30)       # зазор на сторону
WALL = 2.4
HEIGHT = 8.0
GAP_BETWEEN = 6.0
TEXT_DEPTH = 0.5


def _ring(fit: float) -> Part:
    L, W, _ = STS3215.body
    il, iw = L + 2 * fit, W + 2 * fit
    zmin = (Align.CENTER, Align.CENTER, Align.MIN)
    outer = Box(il + 2 * WALL, iw + 2 * WALL, HEIGHT, align=zmin)
    inner = Box(il, iw, HEIGHT + 0.02, align=zmin)
    ring = outer - Pos(0, 0, -0.01) * inner
    # подпись на торце кольца со стороны длинной стенки
    label = Text(f"{fit:.2f}", font_size=3.0, align=(Align.CENTER, Align.CENTER))
    ring -= Pos(0, -(iw / 2 + WALL / 2), HEIGHT - TEXT_DEPTH) * extrude(label, TEXT_DEPTH + 0.01)
    return ring


def build() -> Part:
    L, W, _ = STS3215.body
    pitch = W + 2 * WALL + GAP_BETWEEN + max(FITS) * 2
    parts = [Pos(0, (i - (len(FITS) - 1) / 2) * pitch, 0) * _ring(f) for i, f in enumerate(FITS)]
    body = parts[0]
    for p in parts[1:]:
        body += p
    # перемычка в зазоре между кольцами (не внутри колец — там дно привода)
    body += Box(10, GAP_BETWEEN + WALL, HEIGHT / 2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body
