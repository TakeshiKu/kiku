"""Пробник посадки STS3215: две обоймы-кольца с разным зазором.

Надеть на корпус привода со стороны дна (разъёмы внизу). Выбрать зазор, где
привод входит рукой, без люфта и не распирает кольцо; записать в каталог.
Кольца низкие, чтобы не упираться в уступ у выходного торца.

Печать 09.11, v1: одно кольцо оторвалось от стола и съехало — тонкая стенка,
острые углы, связь с соседом только узкой перемычкой. v2: общая пластина
под обоими кольцами, скруглённые внешние углы, подписи рельефом на пластине.
"""
from build123d import (Align, Axis, Box, Part, Pos, Text, extrude, fillet)

from kiku_cad.parts import STS3215

FITS = (0.15, 0.30)       # зазор на сторону
WALL = 2.4
HEIGHT = 8.0
GAP_BETWEEN = 6.0
CORNER_R = 3.0            # внешнее скругление кольца
BASE_T = 0.6              # пластина-основание: 3 слоя по 0,2
BASE_MARGIN = 3.0         # пластина шире колец по торцам и в зазоре
LABEL_BAND = 7.0          # полоса под подпись снаружи длинной стороны
LABEL_H = 0.6             # рельеф подписи над пластиной

ZMIN = (Align.CENTER, Align.CENTER, Align.MIN)


def _inner(fit: float) -> tuple[float, float]:
    L, W, _ = STS3215.body
    return L + 2 * fit, W + 2 * fit


def _rounded_box(x: float, y: float, z: float, r: float) -> Part:
    return fillet(Box(x, y, z, align=ZMIN).edges().filter_by(Axis.Z), radius=r)


def build() -> Part:
    il_max, iw_max = _inner(max(FITS))
    ring_l, ring_w = il_max + 2 * WALL, iw_max + 2 * WALL
    pitch = ring_w + GAP_BETWEEN
    ys = [(i - (len(FITS) - 1) / 2) * pitch for i in range(len(FITS))]

    # общая пластина: кольца + полосы под подписи по внешним длинным сторонам
    base_l = ring_l + 2 * BASE_MARGIN
    base_w = (ys[-1] - ys[0]) + ring_w + 2 * LABEL_BAND
    body = _rounded_box(base_l, base_w, BASE_T, CORNER_R + BASE_MARGIN)

    for y, fit in zip(ys, FITS):
        il, iw = _inner(fit)
        body += Pos(0, y, 0) * _rounded_box(il + 2 * WALL, iw + 2 * WALL, HEIGHT, CORNER_R)
        body -= Pos(0, y, -0.01) * Box(il, iw, HEIGHT + 0.02, align=ZMIN)
        # подпись рельефом на пластине снаружи кольца
        side = -1 if y < 0 else 1
        ly = y + side * (iw / 2 + WALL + LABEL_BAND / 2 - 0.5)
        label = Text(f"{fit:.2f}", font_size=4.0, align=(Align.CENTER, Align.CENTER))
        body += Pos(0, ly, BASE_T) * extrude(label, LABEL_H)
    return body
