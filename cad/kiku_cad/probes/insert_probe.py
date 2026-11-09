"""Пробник термовставки M3×5×4: ряд глухих отверстий разного диаметра.

Вплавить по вставке в каждое, вкрутить винт M3 и подёргать. Выбрать диаметр,
где вставка села ровно, без вздутия стенки и без проворота; записать в
parts.INSERT_M3.hole_d. Второй ряд — сквозные отверстия под винт M3 (зазор).
"""
from build123d import (Align, Box, Cylinder, Mode, Part, Pos, Text, extrude)

from kiku_cad.parts import INSERT_M3

HOLE_DS = (3.6, 3.7, 3.8, 3.9, 4.0)       # под вставку ⌀4, глухие; правило «⌀ вставки − 0,2…0,3»
CLEAR_DS = (3.2, 3.4)                     # под винт M3 насквозь
PITCH = 10.0
DEPTH = INSERT_M3.hole_depth              # 6 мм, вставка 5 мм + запас под расплав
HEIGHT = 9.0                              # дно под отверстием 3 мм
WIDTH = 22.0
TEXT_DEPTH = 0.5


def build() -> Part:
    n = len(HOLE_DS) + len(CLEAR_DS)
    length = PITCH * n + 4
    body = Box(length, WIDTH, HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
    x0 = -PITCH * (n - 1) / 2
    hole_y = 4.0
    for i, d in enumerate(HOLE_DS + CLEAR_DS):
        x = x0 + i * PITCH
        through = d in CLEAR_DS
        depth = HEIGHT if through else DEPTH
        body -= Pos(x, hole_y, HEIGHT - depth) * Cylinder(
            d / 2, depth + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        label = Text(f"{d:.1f}", font_size=3.6,
                     align=(Align.CENTER, Align.CENTER))
        body -= Pos(x, -5.5, HEIGHT - TEXT_DEPTH) * extrude(label, TEXT_DEPTH + 0.01)
    # насечка у ряда сквозных, чтобы не перепутать ряды
    sep_x = x0 + (len(HOLE_DS) - 0.5) * PITCH
    body -= Pos(sep_x, 0, HEIGHT - 0.6) * Box(0.8, WIDTH + 1, 1.2)
    return body
