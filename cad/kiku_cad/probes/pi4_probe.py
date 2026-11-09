"""Пробник посадки Raspberry Pi 4: рамка со стойками и угловыми упорами.

Проверяет: шаг отверстий 58×49, диаметр под винт M2.5 саморезом (стойки
разные: 2.1 / 2.2 / 2.3 / 2.4 — выбрать, где винт идёт туго и не рвёт),
зазор по контуру платы 0,5 мм, высоту стоек над деталями снизу.
"""
from build123d import (Align, Box, Cylinder, Part, Pos, Text, extrude)

from kiku_cad.parts import Pi4

BASE_T = 2.0              # толщина рамки
BAR_W = 5.0               # ширина перемычек
STANDOFF_H = 5.0          # стойка над рамкой; снизу у Pi детали до ≈2 мм [оцен]
STANDOFF_D = 5.6          # меньше площадки ⌀6 [док]
SCREW_DS = (2.1, 2.2, 2.3, 2.4)   # по углам, в порядке Pi4.holes
SCREW_DEPTH = 5.0
GAP = 0.5                 # зазор упоров до края платы
STOP_H = 3.0              # упор выше стойки: доходит до середины толщины платы и выше
STOP_T = 1.6
STOP_L = 6.0              # короче, чтобы не задеть USB-C (выступ 1,2 у X≈7)
TEXT_DEPTH = 0.5


def build() -> Part:
    L, W, _ = Pi4.pcb
    holes = Pi4.holes
    top = BASE_T + STANDOFF_H
    # рамка: прямоугольник по осям отверстий + диагональ для жёсткости
    xs = sorted({x for x, _ in holes})
    ys = sorted({y for _, y in holes})
    span_x, span_y = xs[1] - xs[0], ys[1] - ys[0]
    cx, cy = (xs[0] + xs[1]) / 2, (ys[0] + ys[1]) / 2
    zmin = (Align.CENTER, Align.CENTER, Align.MIN)
    body = Part()
    for y in ys:
        body += Pos(cx, y, 0) * Box(span_x, BAR_W, BASE_T, align=zmin)
    for x in xs:
        body += Pos(x, cy, 0) * Box(BAR_W, span_y, BASE_T, align=zmin)
    # стойки
    for (x, y) in holes:
        body += Pos(x, y, 0) * Cylinder(STANDOFF_D / 2, top, align=zmin)
    # упоры-уголки у четырёх углов платы, с зазором GAP
    for (sx, sy) in ((0, 0), (1, 0), (0, 1), (1, 1)):
        x_edge = -GAP if sx == 0 else L + GAP
        y_edge = -GAP if sy == 0 else W + GAP
        dx = -1 if sx == 0 else 1
        dy = -1 if sy == 0 else 1
        h = top + STOP_H
        # перемычка от ближайшего отверстия к уголку
        hx, hy = min(holes, key=lambda p: abs(p[0] - x_edge) + abs(p[1] - y_edge))
        body += Pos((hx + x_edge) / 2, (hy + y_edge) / 2, 0) * Box(
            abs(x_edge - hx) + BAR_W, abs(y_edge - hy) + BAR_W, BASE_T, align=zmin)
        # две стенки уголка; на торце USB/Ethernet (X=L) разъёмы выступают
        # за плату на ≈3 мм — там только стенка вдоль длинной стороны
        if sx == 0:
            body += Pos(x_edge + dx * STOP_T / 2, y_edge - dy * (STOP_L / 2 - STOP_T), 0) * Box(
                STOP_T, STOP_L, h, align=zmin)
        body += Pos(x_edge - dx * (STOP_L / 2 - STOP_T), y_edge + dy * STOP_T / 2, 0) * Box(
            STOP_L, STOP_T, h, align=zmin)
    # отверстия под саморезы и подписи диаметров на рамке рядом со стойкой
    for (x, y), d in zip(holes, SCREW_DS):
        body -= Pos(x, y, top - SCREW_DEPTH) * Cylinder(d / 2, SCREW_DEPTH + 0.01, align=zmin)
        tx = x + (9.0 if x < cx else -9.0)
        label = Text(f"{d:.1f}", font_size=3.2, align=(Align.CENTER, Align.CENTER))
        body -= Pos(tx, y, BASE_T - TEXT_DEPTH) * extrude(label, TEXT_DEPTH + 0.01)
    return body
