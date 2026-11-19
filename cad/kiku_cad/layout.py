"""Рабочая 3D-компоновка Кику «коробками» (Ревизия 2 — Вариант 1, утверждён 19.11).

Архитектура компоновки:
- Основание: усечённый конус ⌀140→120 × 70 мм (силуэт пролога); внутри стальной балласт,
  Raspberry Pi 4B, динамик 110 г (спереди), 2× Mini560 Pro, плата приводов Waveshare,
  вытяжка 25×25, гнездо DC-022B и утопленный привод поворота (Ось 1 · Yaw).
- Шея (4 оси, правильная кинематика): Ось 2 (Neck Pitch) на поворотном диске →
  две боковые щёчки → Ось 3 (Head Pitch) под основанием шлема → Ось 4 (Head Roll)
  внутри затылка головы (соосно центру масс, статический момент кивка в нейтрали ~0,00 кг·см).
- Голова (шлем-суперэллипсоид 136×96×100 мм, пропорции пролога):
  экран TFT 2,8" (82×50) за сферическим визором, камера IMX219 160° в бровной арке,
  Ось 4 (STS3215 Roll) в затылке, микрофонная плата ReSpeaker Lite (86×35×8, ~18 г)
  в короне шлема (разведена с динамиком в базе), датчик касания TTP223 под макушкой.

Выгружает cad/out/layout_assembly.step для просмотра во Fusion / Bambu Studio.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from build123d import (
    Axis,
    Box,
    Compound,
    Cone,
    Cylinder,
    Pos,
    Rot,
    Solid,
    Sphere,
    chamfer,
    export_step,
)

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

# Габариты корпуса (Ревизия 2 — выровнено по силуэту пролога KIKU || 01)
BASE_D_BOTTOM = 140.0
BASE_D_TOP = 120.0
BASE_WALL = 3.0
BASE_H = 70.0  # пол 3 мм + балласт 6 мм + проставка 2 мм + 2 яруса электроники + привод Yaw

BALLAST_SIDE = 110.0
BALLAST_CORNER_CUT = 25.0  # срез 4 углов 25×25 мм -> габарит ⌀125,3 мм
BALLAST_H = 6.0

# Шлем-суперэллипсоид (E1=0.60, E2=0.45, taper=0.115)
HEAD_W = 136.0
HEAD_D = 96.0
HEAD_H = 100.0
HEAD_E1 = 0.60
HEAD_E2 = 0.45
HEAD_TOP_TAPER = 0.115

Z_NECK_PITCH = 92.5
Z_HEAD_PITCH = 136.0
Z_HEAD_BOTTOM = 146.0
Z_HEAD_C = Z_HEAD_BOTTOM + HEAD_H / 2  # 196.0 мм -> верх 246.0 мм
Z_VISOR = Z_HEAD_C - 10.0              # 186.0 мм


@dataclass(frozen=True)
class PlacedBox:
    """Габаритный блок компонента в мировой системе координат (Z вверх, Y вперёд)."""

    name: str
    shape: Solid


def _box(name: str, sx: float, sy: float, sz: float, x: float, y: float, z: float) -> PlacedBox:
    """Создаёт блок с центром в (x, y, z)."""
    return PlacedBox(name=name, shape=Pos(x, y, z) * Box(sx, sy, sz))


def build_base_blocks() -> list[PlacedBox]:
    """Узлы в конусном основании ⌀140→120 × 70 мм (пол Z=3 мм, балласт Z=3..9, платы с Z=11)."""
    z_floor = BASE_WALL
    blocks: list[PlacedBox] = []

    # Стальная пластина балласта 110×110×6 мм со срезами углов 25×25 мм (~490 г)
    ballast_raw = Pos(0.0, 0.0, z_floor + BALLAST_H / 2) * Box(BALLAST_SIDE, BALLAST_SIDE, BALLAST_H)
    ballast_s = chamfer(ballast_raw.edges().filter_by(Axis.Z), length=BALLAST_CORNER_CUT)
    blocks.append(PlacedBox("base_ballast_steel_110x110", ballast_s))

    z0 = z_floor + BALLAST_H + 2.0  # 11.0 мм (проставка/изолятор 2 мм над сталью)

    # Raspberry Pi 4B (85×56×17.4, сдвинута к Y-)
    pi_h = Pi4.pcb[2] + Pi4.top_max
    blocks.append(_box("base_pi4", Pi4.pcb[0], Pi4.pcb[1], pi_h, 0.0, -18.0, z0 + pi_h / 2))

    # Динамик 4 Ом / 5 Вт (50×45×22, ~110 г) спереди базы под решёткой
    sp_x, sp_y, sp_z = Speaker.size
    blocks.append(_box("base_speaker", sp_x, sp_y, sp_z, 0.0, 33.0, z0 + sp_z / 2))

    # 2× Mini560 Pro (35×20×8) вторым этажом по бокам (открыты для обдува)
    m_x, m_y, m_z = Mini560Pro.keepout
    blocks.append(_box("base_mini560_1", m_y, m_x, m_z, -38.0, 16.0, z0 + sp_z + 3.0 + m_z / 2))
    blocks.append(_box("base_mini560_2", m_y, m_x, m_z, 38.0, 16.0, z0 + sp_z + 3.0 + m_z / 2))

    # Плата сервоприводов Waveshare (42×33×12) над задней частью Pi 4
    blocks.append(_box("base_servo_board", 42.0, 33.0, 12.0, 10.0, -31.5, z0 + pi_h + 3.5 + 6.0))

    # Вентилятор вытяжки 25×25×10 мм у задней стенки
    blocks.append(_box("base_fan_25x25", 25.0, 10.0, 25.0, -25.0, -37.0, z0 + pi_h + 15.0))

    # Гнездо питания DC-022B сзади (Y-)
    dc_y = -(BASE_D_BOTTOM / 2 - DC022B.behind_panel / 2 - 2.0)
    dc_s = Pos(0.0, dc_y, z0 + 10.0) * Rot(90, 0, 0) * Cylinder(DC022B.flange[0] / 2, DC022B.behind_panel)
    blocks.append(PlacedBox("base_dc022b", dc_s))

    return blocks


def build_neck_blocks() -> list[PlacedBox]:
    """Приводы осей 1–3 и две боковые щёчки шеи (Ось 4 живёт внутри затылка головы)."""
    c = STS3215.fit_clearance
    l = STS3215.body[0] + 2 * c
    w = STS3215.body[1] + 2 * c
    h = STS3215.height_total

    arm_h = Z_HEAD_PITCH - Z_NECK_PITCH + 22.0
    arm_z = (Z_NECK_PITCH + Z_HEAD_PITCH) / 2.0

    return [
        # Ось 1: поворот (yaw) утоплен в верхней части конусного основания
        _box("servo_1_yaw", l, w, h, 0.0, 0.0, BASE_H - h / 2 - 0.5),
        # Ось 2: наклон шеи (pitch) поперёк на поворотном диске (ось вдоль X)
        _box("servo_2_neck_pitch", h, l, w, 0.0, -6.0, Z_NECK_PITCH),
        # Две боковые щёчки параллельной вилки шеи
        _box("neck_arm_left", 7.0, 22.0, arm_h, -(h / 2 + 4.5), 0.0, arm_z),
        _box("neck_arm_right", 7.0, 22.0, arm_h, +(h / 2 + 4.5), 0.0, arm_z),
        # Ось 3: кивок головы (pitch) наверху между щёчками (ось вдоль X)
        _box("servo_3_head_pitch", h, l, w, 0.0, -6.0, Z_HEAD_PITCH),
    ]


def build_head_blocks() -> list[PlacedBox]:
    """Узлы внутри шлема 136×96×100 мм: экран, камера, Ось 4 (Roll), ReSpeaker Lite, TTP223."""
    c = STS3215.fit_clearance
    l = STS3215.body[0] + 2 * c
    w = STS3215.body[1] + 2 * c
    h = STS3215.height_total
    y_front = HEAD_D / 2

    blocks: list[PlacedBox] = []

    # Ось 4: склон головы (roll) внутри затылка (ось вдоль Y, противовес экрану)
    blocks.append(_box("servo_4_head_roll", l, h, w, 0.0, -17.5, 182.0))

    # Экран TFT 2.8" ST7789V (82×50×12.8) спереди за сферическим визором
    scr_x, scr_y, scr_z = TFT28.pcb[0], TFT28.with_header, TFT28.pcb[1]
    blocks.append(_box("head_tft28", scr_x, scr_y, scr_z, 0.0, y_front - 14.0 - scr_y / 2, Z_VISOR))

    # Камера IMX219 160° (25×24×17.7) в бровной арке над экраном (целиком внутри шлема)
    cam_x, cam_y, cam_z = CameraIMX219_160.pcb[0], CameraIMX219_160.height_total, CameraIMX219_160.pcb[1]
    blocks.append(
        _box("head_camera_forehead", cam_x, cam_y, cam_z, 0.0, y_front - 15.0 - cam_y / 2, Z_VISOR + scr_z / 2 + 1.0 + cam_z / 2)
    )

    # Микрофонная плата ReSpeaker Lite (86×35×8, ~18 г) в короне шлема за камерой и над Осью 4
    rs_x, rs_y, rs_z = ReSpeakerLite.pcb[0], ReSpeakerLite.pcb[1], 8.0
    blocks.append(_box("head_respeaker", rs_x, rs_y, rs_z, 0.0, -10.0, 219.0))

    # Датчик касания TTP223 (24×24×4) под макушкой
    ttp_x, ttp_y = TTP223.variants["большой"]
    blocks.append(_box("head_ttp223_top", ttp_x, ttp_y, 4.0, 0.0, -8.0, Z_HEAD_C + HEAD_H / 2 - 9.0))

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
    """Проверяет, не вылезают ли блоки основания за внутренний конус ⌀134→114 мм."""
    inner = Pos(0.0, 0.0, BASE_WALL + (BASE_H - BASE_WALL) / 2) * Cone(
        BASE_D_BOTTOM / 2 - BASE_WALL, BASE_D_TOP / 2 - BASE_WALL, BASE_H - BASE_WALL
    )
    outside: list[str] = []
    for b in base_blocks:
        if b.name == "base_dc022b":
            continue  # разъём выходит в заднюю стенку
        vol = _shape_volume(b.shape - inner)
        if vol > 1e-2:
            outside.append(f"{b.name} (выступает на {vol / 1000:.2f} см³)")
    return outside


def check_head_envelope(head_blocks: list[PlacedBox], wall: float = 3.0) -> list[str]:
    """Проверяет вершины и центры граней блоков головы против суперэллипсоида шлема."""
    ai, bi, ci = HEAD_W / 2 - wall, HEAD_D / 2 - wall, HEAD_H / 2 - wall

    def f_val(x: float, y: float, z: float) -> float:
        zl = z - Z_HEAD_C
        k = 1.0 - HEAD_TOP_TAPER * max(0.0, zl / ci)
        xt = x / max(k, 0.2)
        t = abs(xt / ai) ** (2.0 / HEAD_E2) + abs(y / bi) ** (2.0 / HEAD_E2)
        return t ** (HEAD_E2 / HEAD_E1) + abs(zl / ci) ** (2.0 / HEAD_E1)

    outside: list[str] = []
    for b in head_blocks:
        bb = b.shape.bounding_box()
        xs = (bb.min.X, (bb.min.X + bb.max.X) / 2, bb.max.X)
        ys = (bb.min.Y, (bb.min.Y + bb.max.Y) / 2, bb.max.Y)
        zs = (bb.min.Z, (bb.min.Z + bb.max.Z) / 2, bb.max.Z)
        max_f = max(f_val(x, y, z) for x in xs for y in ys for z in zs)
        if max_f > 1.0:
            outside.append(f"{b.name} (F={max_f:.3f})")
    return outside


def export_layout(out_dir: Path) -> tuple[Path, list[tuple[str, str, float]], list[str], list[str]]:
    """Собирает компоновку Ревизии 2, проверяет коллизии/стенки и сохраняет STEP."""
    base = build_base_blocks()
    neck = build_neck_blocks()
    head = build_head_blocks()
    all_blocks = base + neck + head

    # Контур конусного основания и головы (для STEP-просмотра)
    shell_base = Pos(0, 0, BASE_H / 2) * Cone(BASE_D_BOTTOM / 2, BASE_D_TOP / 2, BASE_H)
    shell_head = Pos(0, 0, Z_HEAD_C) * Sphere(1.0).scale((HEAD_W / 2, HEAD_D / 2, HEAD_H / 2))
    r_vis = Visor.sphere_r
    visor_outer = Pos(0, HEAD_D / 2 - r_vis + 2.0, Z_VISOR) * (Sphere(r_vis) - Sphere(r_vis - 2.5))
    visor_window = Pos(0, HEAD_D / 2 - 10.0, Z_VISOR) * Box(Visor.cut[0], 40.0, Visor.cut[1])
    visor_hit = visor_outer.intersect(visor_window)
    shell_visor = visor_hit if hasattr(visor_hit, "volume") else visor_hit.solids()[0]

    shapes = []
    for b in all_blocks:
        b.shape.label = b.name
        shapes.append(b.shape)
    for name, s in (
        (f"envelope_base_cone_{int(BASE_D_BOTTOM)}to{int(BASE_D_TOP)}", shell_base),
        ("envelope_head_136x96x100", shell_head),
        ("envelope_visor_108x50", shell_visor),
    ):
        s.label = name
        shapes.append(s)

    path = out_dir / "layout_assembly.step"
    export_step(Compound(children=shapes), str(path))

    collisions = check_collisions(all_blocks)
    outside_base = check_base_envelope(base + [neck[0]])
    outside_head = check_head_envelope(head)
    return path, collisions, outside_base, outside_head


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "out"
    out.mkdir(exist_ok=True)
    step_path, cols, out_base, out_head = export_layout(out)
    print(f"ok      layout -> {step_path.name}")
    print("Коллизии между блоками:", cols if cols else "нет")
    print(f"Выход за конус основания ⌀{int(BASE_D_BOTTOM)}→{int(BASE_D_TOP)}:", out_base if out_base else "нет")
    print(f"Выход за шлем головы {int(HEAD_W)}×{int(HEAD_D)}×{int(HEAD_H)}:", out_head if out_head else "нет")
