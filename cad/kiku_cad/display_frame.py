"""Рамка под экран TFT 2.8" (82×50 мм, окно 58×43,6 мм) для проверки за визором и печати."""
from __future__ import annotations

from build123d import Axis, Box, Cylinder, Pos, Solid, fillet

from kiku_cad.parts import TFT28

# Габариты рамки
FRAME_X = TFT28.pcb[0] + 6.0   # 88.0 мм
FRAME_Y = TFT28.pcb[1] + 6.0   # 56.0 мм
FRONT_T = 2.0                  # толщина лицевой стенки
RIM_H = 4.5                    # бортик сзади (закрывает стекло и край платы)
WALL_T = 2.6                   # ширина бортика вокруг платы (с зазором +0.4 мм на сторону)
STANDOFF_H = 2.8               # упор под плату (LCD 2.3 + скотч 0.5 = 2.8 мм)
STANDOFF_D = 5.6
PILOT_D = 2.6                  # под саморез M3 или винт M2.5

# Смещение активной области по X: плата 82 мм, от края SD до окна 9.3 мм -> центр окна на -2.9 мм
WIN_W = TFT28.active[0] + 0.4  # 58.0 мм
WIN_H = TFT28.active[1] + 0.4  # 43.6 мм
WIN_OFFSET_X = -(TFT28.pcb[0] / 2 - TFT28.active_from_top - TFT28.active[0] / 2)


def build() -> Solid:
    """Строит лицевую рамку под TFT 2.8\" со стойками и задним бортиком."""
    total_h = FRONT_T + RIM_H

    # Основной скруглённый корпус рамки (Z: 0..total_h, лицо снизу Z=0)
    base = Pos(0, 0, total_h / 2) * Box(FRAME_X, FRAME_Y, total_h)
    base = fillet(base.edges().filter_by(Axis.Z), radius=4.0)

    # Задняя полость под плату (82.8 × 50.8 мм, от Z=FRONT_T вверх)
    pocket_x = TFT28.pcb[0] + 0.8
    pocket_y = TFT28.pcb[1] + 0.8
    pocket = Pos(0, 0, FRONT_T + RIM_H / 2 + 0.5) * Box(pocket_x, pocket_y, RIM_H + 1.0)
    frame = base - pocket

    # Окно под видимую область экрана (насквозь по Z)
    window = Pos(WIN_OFFSET_X, 0, FRONT_T / 2) * Box(WIN_W, WIN_H, FRONT_T + 2.0)
    frame = frame - window

    # 4 стойки под крепёжные отверстия платы (76.08 × 44.0 мм)
    hx = TFT28.holes_pitch[0] / 2
    hy = TFT28.holes_pitch[1] / 2
    for sx in (-hx, hx):
        for sy in (-hy, hy):
            boss = Pos(sx, sy, FRONT_T + STANDOFF_H / 2) * Cylinder(STANDOFF_D / 2, STANDOFF_H)
            hole = Pos(sx, sy, FRONT_T + STANDOFF_H / 2) * Cylinder(PILOT_D / 2, STANDOFF_H + 1.0)
            frame = frame + boss - hole

    return frame.solids()[0]
