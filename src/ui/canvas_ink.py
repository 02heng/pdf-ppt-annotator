"""桌面画布手绘墨迹（与 Web 预览 preview_ink 格式一致）。"""
from __future__ import annotations

import tkinter as tk
from typing import Any, Dict, List, Optional, Tuple

from src.utils.ink_style import HIGHLIGHTER_OPACITY, blend_hex_over_white

INK_COLORS = [
    "#ffffff",
    "#000000",
    "#7f1d1d",
    "#ef4444",
    "#f97316",
    "#eab308",
    "#84cc16",
    "#16a34a",
    "#22d3ee",
    "#2563eb",
    "#1e3a8a",
    "#7c3aed",
]

INK_DRAW_TOOLS = frozenset({"pen", "highlighter"})
ERASER_HIT_RADIUS = 0.025


def stroke_width_for_tool(tool: str, page_width_px: float) -> float:
    if tool == "highlighter":
        return max(14.0, page_width_px * 0.018)
    if tool == "eraser":
        return max(18.0, page_width_px * 0.022)
    return max(3.0, page_width_px * 0.004)


def canvas_to_norm(
    cx: float,
    cy: float,
    offset_x: float,
    offset_y: float,
    page_w: float,
    page_h: float,
) -> Dict[str, float]:
    if page_w <= 0 or page_h <= 0:
        return {"x": 0.0, "y": 0.0}
    return {
        "x": max(0.0, min(1.0, (cx - offset_x) / page_w)),
        "y": max(0.0, min(1.0, (cy - offset_y) / page_h)),
    }


def norm_to_canvas(
    nx: float,
    ny: float,
    offset_x: float,
    offset_y: float,
    page_w: float,
    page_h: float,
) -> Tuple[float, float]:
    return offset_x + nx * page_w, offset_y + ny * page_h


def new_stroke(
    tool: str,
    color: str,
    width: float,
    points: List[Dict[str, float]],
    *,
    page_width_px: float,
) -> Dict[str, Any]:
    pw = max(page_width_px, 1.0)
    return {
        "tool": tool,
        "color": color,
        "width": width,
        "width_norm": width / pw,
        "points": points,
    }


def append_stroke_point(
    stroke: Dict[str, Any],
    nx: float,
    ny: float,
    *,
    min_dist: float = 0.002,
) -> bool:
    pts = stroke.setdefault("points", [])
    if pts:
        last = pts[-1]
        if (nx - last["x"]) ** 2 + (ny - last["y"]) ** 2 < min_dist**2:
            return False
    pts.append({"x": nx, "y": ny})
    return True


def erase_strokes_at(
    strokes: List[Dict[str, Any]],
    nx: float,
    ny: float,
    *,
    radius: float = ERASER_HIT_RADIUS,
) -> List[Dict[str, Any]]:
    kept: List[Dict[str, Any]] = []
    for stroke in strokes:
        if stroke.get("tool") not in INK_DRAW_TOOLS:
            continue
        hit = False
        for p in stroke.get("points") or []:
            try:
                px = float(p.get("x", 0))
                py = float(p.get("y", 0))
            except (TypeError, ValueError):
                continue
            if (px - nx) ** 2 + (py - ny) ** 2 < radius**2:
                hit = True
                break
        if not hit:
            kept.append(stroke)
    return kept


def draw_stroke_on_canvas(
    canvas: tk.Canvas,
    stroke: Dict[str, Any],
    offset_x: float,
    offset_y: float,
    page_w: float,
    page_h: float,
    *,
    tag: str = "ink",
) -> None:
    tool = str(stroke.get("tool", "pen"))
    if tool not in INK_DRAW_TOOLS:
        return
    pts = stroke.get("points") or []
    if len(pts) < 2:
        return

    color = str(stroke.get("color", "#ef4444"))
    width = float(stroke.get("width", 2) or 2)
    if stroke.get("width_norm") is not None and page_w > 0:
        width = max(0.8, float(stroke["width_norm"]) * page_w)

    canvas_points: List[float] = []
    for p in pts:
        nx = float(p.get("x", p.get("nx", 0)))
        ny = float(p.get("y", p.get("ny", 0)))
        cx, cy = norm_to_canvas(nx, ny, offset_x, offset_y, page_w, page_h)
        canvas_points.extend([cx, cy])

    if len(canvas_points) < 4:
        return

    line_w = max(1, int(round(width)))
    fill = color
    if tool == "highlighter":
        line_w = max(line_w, int(round(width * 1.05)))
        fill = blend_hex_over_white(color, HIGHLIGHTER_OPACITY)

    canvas.create_line(
        *canvas_points,
        fill=fill,
        width=line_w,
        capstyle=tk.ROUND,
        joinstyle=tk.ROUND,
        smooth=tool != "highlighter",
        tags=tag,
    )


def redraw_page_ink(
    canvas: tk.Canvas,
    strokes: List[Dict[str, Any]],
    offset_x: float,
    offset_y: float,
    page_w: float,
    page_h: float,
) -> None:
    canvas.delete("ink")
    for stroke in strokes:
        if isinstance(stroke, dict):
            draw_stroke_on_canvas(
                canvas, stroke, offset_x, offset_y, page_w, page_h
            )
