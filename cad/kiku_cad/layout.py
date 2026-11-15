"""Черновая 3D-компоновка Кику «коробками» (Вариант 1: камера на лбу над визором).

Проверяет габариты, взаимные пересечения узлов в основании и голове
по фактическим замерам из parts.py (экран 82×50, STS3215 зазор 0,15).
Выгружает cad/out/layout_assembly.step для просмотра во Fusion / Bambu Studio.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import Axis, Box, Compound, Cylinder, Pos, Rot, Solid, Sphere, chamfer, export_step

from kiku_cad.parts import (
    DC022B,
    STS3215,
    TFT28,
    CameraIMX219_160,
    Mini560Pro,
    Pi4,
    ReSpeakerLite,
    Speaker,
    TTP223,
    Visor,
)

# Ориентиры габаритов корпуса из концепции (kiku/planning/concept.md) + ревью 14.11
BASE_D = 138.0
BASE_WALL = 3.0
BASE_INNER_D = BASE_D - 2 * BASE_WALL  # 132 мм
BASE_H = 74.0  # 68 + 6 мм под стальной диск балласта на дне

BALLAST_SIDE = 110.0
BALLAST_CORNER_CUT = 25.0  # срез 4 углов 25×25 мм -> габарит ⌀125,3 мм (запас ~3,3 мм к ⌀132)
BALLAST_H = 6.0  # ориентир толщины (уточнится по факту замера пластины 110×110)

HEAD_W = 130.0
HEAD_D = 106.0
HEAD_H = 92.0
NECK_H = 65.0


@dataclass(frozen=True)
class PlacedBox:
    """Габаритный блок компонента в мировой системе координат (Z вверх, Y вперёд)."""

    name: str
    shape: Solid


def _box(name: str, sx: float, sy: float, sz: float, x: float, y: float, z: float) -> PlacedBox:
    """Создаёт блок с центром в (x, y, z)."""
    return PlacedBox(name=name, shape=Pos(x, y, z) * Box(sx, sy, sz))


def build_base_blocks() -> list[PlacedBox]:
    """Узлы в основании ⌀138×74 мм (пол Z=3 мм, стальной балласт Z=3..9, платы с Z=11)."""
    z_floor = BASE_WALL
    blocks: list[PlacedBox] = []

    # Стальная пластина балласта 110×110×6 мм со срезами углов 25×25 мм
    ballast_raw = Pos(0.0, 0.0, z_floor + BALLAST_H / 2) * Box(BALLAST_SIDE, BALLAST_SIDE, BALLAST_H)
    ballast_s = chamfer(ballast_raw.edges().filter_by(Axis.Z), length=BALLAST_CORNER_CUT)
    blocks.append(PlacedBox("base_ballast_steel_110x110", ballast_s))

    z0 = z_floor + BALLAST_H + 2.0  # 2 мм проставка/изолятор над стальным диском

    # Pi 4 (85×56×17.4, сдвинута к Y-)
    pi_h = Pi4.pcb[2] + Pi4.top_max
    blocks.append(_box("base_pi4", Pi4.pcb[0], Pi4.pcb[1], pi_h, 0.0, -20.0, z0 + pi_h / 2))

    # Динамик (50×45×22) спереди от Pi 4
    sp_x, sp_y, sp_z = Speaker.size
    blocks.append(_box("base_speaker", sp_x, sp_y, sp_z, 0.0, 32.0, z0 + sp_z / 2))

    # ReSpeaker Lite (86×35×8) под верхней крышкой спереди (доступ к Mute, LED и микрофонам)
    rs_x, rs_y, rs_z = ReSpeakerLite.pcb[0], ReSpeakerLite.pcb[1], 8.0
    blocks.append(_box("base_respeaker", rs_x, rs_y, rs_z, 0.0, 32.0, BASE_H - BASE_WALL - rs_z / 2 - 1.0))

    # 2× Mini560 (35×20×8) вторым этажом по бокам
    m_x, m_y, m_z = Mini560Pro.keepout
    blocks.append(_box("base_mini560_1", m_y, m_x, m_z, -42.0, 14.0, z0 + sp_z + 3.0 + m_z / 2))
    blocks.append(_box("base_mini560_2", m_y, m_x, m_z, 42.0, 14.0, z0 + sp_z + 3.0 + m_z / 2))

    # Плата сервоприводов Waveshare (42×33×12) вторым этажом сзади над Pi 4
    blocks.append(_box("base_servo_board", 42.0, 33.0, 12.0, 8.0, -34.0, z0 + pi_h + 4.0 + 6.0))

    # Вентилятор вытяжки 25×25×10 мм у задней стенки
    blocks.append(_box("base_fan_25x25", 25.0, 10.0, 25.0, -34.0, -40.0, z0 + pi_h + 14.0))

    # Гнездо питания DC-022B сзади (Y-)
    dc_s = Pos(0.0, -(BASE_D / 2 - DC022B.behind_panel / 2), z0 + 10.0) * Rot(90, 0, 0) * Cylinder(
        DC022B.flange[0] / 2, DC022B.behind_panel
    )
    blocks.append(PlacedBox("base_dc022b", dc_s))

    return blocks


def build_neck_blocks() -> list[PlacedBox]:
    """Четыре привода STS3215 (корпус + зазор 0,15 на сторону)."""
    c = STS3215.fit_clearance
    l = STS3215.body[0] + 2 * c
    w = STS3215.body[1] + 2 * c
    h = STS3215.height_total

    z_base_top = BASE_H
    return [
        # Привод 1: поворот (yaw) в верхней части основания
        _box("servo_1_yaw", l, w, h, 0.0, 0.0, z_base_top - h / 2),
        # Привод 2: наклон шеи снизу
        _box("servo_2_neck_pitch", w, l, h, 0.0, -4.0, z_base_top + h / 2 + 4.0),
        # Приводы 3 и 4: наклон и склон головы у основания черепа (сдвинуты назад от экрана)
        _box("servo_3_head_pitch", w, l, h, -16.0, -14.0, z_base_top + NECK_H - 6.0),
        _box("servo_4_head_roll", w, l, h, 16.0, -14.0, z_base_top + NECK_H - 6.0),
    ]


def build_head_blocks() -> list[PlacedBox]:
    """Голова (Вариант 1): экран 82×50 по центру за визором, камера на лбу над визором."""
    z_head_c = BASE_H + NECK_H + HEAD_H / 2
    y_front = HEAD_D / 2  # передняя плоскость головы

    blocks: list[PlacedBox] = []

    # Экран TFT 2.8" (факт 82×50×12.8 с гребёнкой) по центру за визором, утоплен внутрь головы
    scr_x, scr_y, scr_z = TFT28.pcb[0], TFT28.with_header, TFT28.pcb[1]
    blocks.append(_box("head_tft28", scr_x, scr_y, scr_z, 0.0, y_front - 18.0 - scr_y / 2, z_head_c - 4.0))

    # Камера IMX219 160° (25×24×17.7) — Вариант 1: на лбу над экраном/визором
    cam_x, cam_y, cam_z = CameraIMX219_160.pcb[0], CameraIMX219_160.height_total, CameraIMX219_160.pcb[1]
    blocks.append(_box("head_camera_forehead", cam_x, cam_y, cam_z, 0.0, y_front - 6.0 - cam_y / 2, z_head_c + 35.0))

    # Датчик касания TTP223 (24×24×4) на макушке
    ttp_x, ttp_y = TTP223.variants["большой"]
    blocks.append(_box("head_ttp223_top", ttp_x, ttp_y, 4.0, 0.0, -10.0, z_head_c + HEAD_H / 2 - 5.0))

    return blocks


def _shape_volume(shape: object) -> float:
    """Возвращает суммарный объём тела или ShapeList (0.0 для пустого результата)."""
    if shape is None:
        return 0.0
    if hasattr(shape, "volume"):
        return float(shape.volume)
    return float(sum(s.volume for s in shape if hasattr(s, "volume")))


def check_collisions(blocks: list[PlacedBox]) -> list[tuple[str, str, float]]:
    """Возвращает пары пересекающихся блоков с объёмом пересечения (см³)."""
    hits: list[tuple[str, str, float]] = []
    for i in range(len(blocks)):
        for j in range(i + 1, len(blocks)):
            a, b = blocks[i], blocks[j]
            vol = _shape_volume(a.shape.intersect(b.shape))
            if vol > 1e-3:
                hits.append((a.name, b.name, vol / 1000.0))
    return hits


def check_base_envelope(base_blocks: list[PlacedBox]) -> list[str]:
    """Проверяет, не вылезают ли блоки основания за внутренний цилиндр ⌀124 мм."""
    inner = Pos(0.0, 0.0, BASE_WALL + BASE_H / 2) * Cylinder(BASE_INNER_D / 2, BASE_H)
    outside: list[str] = []
    for b in base_blocks:
        if b.name == "base_dc022b":
            continue  # разъём выходит в заднюю стенку
        vol = _shape_volume(b.shape - inner)
        if vol > 1e-2:
            outside.append(f"{b.name} (выступает на {vol / 1000:.2f} см³)")
    return outside


def export_layout(out_dir: Path) -> tuple[Path, list[tuple[str, str, float]], list[str]]:
    """Собирает черновую компоновку, проверяет коллизии и сохраняет STEP."""
    base = build_base_blocks()
    neck = build_neck_blocks()
    head = build_head_blocks()
    all_blocks = base + neck + head

    # Контур основания и головы (условные габариты для наглядности)
    shell_base = Pos(0, 0, BASE_H / 2) * Cylinder(BASE_D / 2, BASE_H)
    z_head_c = BASE_H + NECK_H + HEAD_H / 2
    shell_head = Pos(0, 0, z_head_c) * Sphere(1.0).scale((HEAD_W / 2, HEAD_D / 2, HEAD_H / 2))
    # Реальный сферический сегмент визора R=100 мм (вырез 108×50 из шара ⌀200 мм)
    r_vis = Visor.sphere_r
    visor_outer = Pos(0, HEAD_D / 2 - r_vis + 2.0, z_head_c - 4.0) * (Sphere(r_vis) - Sphere(r_vis - 2.5))
    visor_window = Pos(0, HEAD_D / 2 - 10.0, z_head_c - 4.0) * Box(Visor.cut[0], 40.0, Visor.cut[1])
    visor_hit = visor_outer.intersect(visor_window)
    shell_visor = visor_hit if hasattr(visor_hit, "volume") else visor_hit.solids()[0]

    shapes = []
    for b in all_blocks:
        b.shape.label = b.name
        shapes.append(b.shape)
    for name, s in ((f"envelope_base_d{int(BASE_D)}", shell_base), ("envelope_head", shell_head), ("envelope_visor_108x50", shell_visor)):
        s.label = name
        shapes.append(s)

    path = out_dir / "layout_assembly.step"
    export_step(Compound(children=shapes), str(path))

    collisions = check_collisions(all_blocks)
    outside = check_base_envelope(base)
    return path, collisions, outside


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "out"
    out.mkdir(exist_ok=True)
    step_path, cols, out_base = export_layout(out)
    print(f"ok      layout -> {step_path.name}")
    print("Коллизии между блоками:", cols if cols else "нет")
    print(f"Выход за стенки основания ⌀{int(BASE_INNER_D)}:", out_base if out_base else "нет")
