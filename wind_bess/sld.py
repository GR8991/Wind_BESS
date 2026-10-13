"""Generate a project-input-driven preliminary wind + BESS single-line diagram (SVG)."""
from __future__ import annotations
from html import escape
from math import ceil


def _txt(x: float, y: float, value: object, size: int = 14, weight: str = "normal", anchor: str = "middle") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="#172033">{escape(str(value))}</text>'


def _line(x1: float, y1: float, x2: float, y2: float, width: int = 3, color: str = "#25364a", dash: str = "") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{d}/>'


def _breaker(x: float, y: float, label: str = "CB") -> str:
    # Simplified one-line breaker symbol; actual interrupting ratings are intentionally not assumed.
    return (_line(x, y - 22, x, y - 7, 2) +
            f'<rect x="{x-10:.1f}" y="{y-7:.1f}" width="20" height="24" rx="2" fill="#ffffff" stroke="#25364a" stroke-width="2"/>' +
            _line(x, y + 17, x, y + 30, 2) + _txt(x + 15, y + 7, label, 10, anchor="start"))


def _transformer(x: float, y: float, label: str, rating: str, width: int = 44) -> str:
    return (f'<circle cx="{x-width/4:.1f}" cy="{y}" r="{width/4:.1f}" fill="#fff" stroke="#25364a" stroke-width="2.5"/>'
            f'<circle cx="{x+width/4:.1f}" cy="{y}" r="{width/4:.1f}" fill="#fff" stroke="#25364a" stroke-width="2.5"/>'
            + _txt(x, y + 40, label, 13, "bold") + _txt(x, y + 57, rating, 12))


def _wtg(x: float, y: float, label: str, rating: str) -> str:
    # Standardized simplified turbine/generator marker with connection terminal.
    return (_line(x, y + 3, x, y + 19, 2) +
            f'<circle cx="{x}" cy="{y}" r="8" fill="#ffffff" stroke="#1b6b57" stroke-width="2.2"/>' +
            _line(x, y, x - 7, y - 9, 2, "#1b6b57") + _line(x, y, x + 9, y - 3, 2, "#1b6b57") +
            _line(x, y, x - 2, y + 10, 2, "#1b6b57") + _txt(x, y + 34, label, 10) + _txt(x, y + 47, rating, 9))


def generate_wind_bess_sld(*, project_name: str, n_wtg: int, p_wtg_mw: float,
                           feeder_counts: list[int], p_bess_mw: float, e_bess_mwh: float,
                           n_bess_feeders: int, v_mv_kv: float, v_hv_kv: float,
                           gsu_mva: float, poi_export_mw: float, poi_import_mw: float,
                           gsu_status: str = "Candidate only — not approved") -> str:
    """Return an SVG SLD based only on supplied project inputs.

    The diagram is a preliminary topology schematic, not a protection or construction drawing.
    Breaker interrupting ratings, cable sizes, CT/VT ratios, relay functions and earthing details
    are marked TBD because they are not defined by these inputs.
    """
    counts = [max(0, int(c)) for c in feeder_counts]
    if not counts or sum(counts) != int(n_wtg):
        raise ValueError(f"Wind feeder allocation must total {int(n_wtg)} WTGs; received {sum(counts)}.")
    if int(n_bess_feeders) < 1:
        raise ValueError("At least one BESS MV feeder is required.")
    if min(float(p_wtg_mw), float(p_bess_mw), float(e_bess_mwh), float(v_mv_kv), float(v_hv_kv), float(gsu_mva)) < 0:
        raise ValueError("Equipment ratings and voltage inputs cannot be negative.")

    width = 1500
    margin = 55
    panel_w = 270
    panel_gap = 18
    cols = 4
    rows = max(1, ceil(len(counts) / cols))
    feeder_top = 180
    panel_h = 165
    bus_y = feeder_top + rows * (panel_h + 28) + 10
    bess_y = bus_y + 170
    hv_y = bess_y + 140
    height = hv_y + 180
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
             '<rect x="18" y="18" width="1464" height="100" rx="8" fill="#f4f7fb" stroke="#c7d2df"/>',
             _txt(42, 48, "WIND + BESS ENGINEERING WORKBENCH", 14, "bold", "start"),
             _txt(42, 78, f"{project_name} — Preliminary Single-Line Diagram", 22, "bold", "start"),
             _txt(1455, 48, "PRELIMINARY • NOT FOR CONSTRUCTION", 13, "bold", "end"),
             _txt(1455, 76, f"Wind: {n_wtg} × {p_wtg_mw:g} MW = {n_wtg*p_wtg_mw:.2f} MW", 13, anchor="end"),
             _txt(1455, 96, f"BESS: {p_bess_mw:g} MW / {e_bess_mwh:g} MWh", 13, anchor="end")]

    # Wind feeder panels with per-WTG markers. A feeder allocation is displayed as entered.
    for i, count in enumerate(counts):
        col = i % cols
        row = i // cols
        x = margin + col * (panel_w + panel_gap)
        y = feeder_top + row * (panel_h + 28)
        parts.append(f'<rect x="{x}" y="{y}" width="{panel_w}" height="{panel_h}" rx="7" fill="#fbfdfd" stroke="#8da9a2" stroke-width="1.5"/>')
        parts.append(_txt(x + 12, y + 23, f"WF-{i+1:02d} • {count} WTGs", 13, "bold", "start"))
        parts.append(_txt(x + 12, y + 42, f"Feeder generation: {count*p_wtg_mw:.2f} MW (nameplate)", 10, anchor="start"))
        if count == 0:
            parts.append(_txt(x + panel_w/2, y + 90, "No WTGs allocated", 12))
        else:
            shown = min(count, 7)
            spacing = (panel_w - 34) / max(shown, 1)
            icon_y = y + 77
            # Show all turbines if <=7; otherwise show 6 icons plus an explicit omitted count marker.
            display_count = shown if count <= 7 else 6
            for j in range(display_count):
                xx = x + 18 + (j + 0.5) * spacing
                parts.append(_wtg(xx, icon_y, f"WTG-{sum(counts[:i])+j+1:02d}", f"{p_wtg_mw:g} MW"))
            if count > 7:
                parts.append(_txt(x + panel_w - 23, icon_y + 4, f"+{count-6}", 11, "bold"))
        # Feeder breaker and cable termination at the panel bottom.
        bx = x + panel_w/2
        parts.append(_line(bx, y + panel_h - 29, bx, y + panel_h - 10, 2))
        parts.append(_breaker(bx, y + panel_h - 24, "CB • TBD"))
        channel_y = y + panel_h + 12
        trunk_x = 1230
        parts.append(_line(bx, y + panel_h, bx, channel_y, 2, "#557b92"))
        parts.append(_line(bx, channel_y, trunk_x, channel_y, 2, "#557b92"))

    # Collector bus and main transformer connection.
    bus_x1, bus_x2 = margin, margin + cols * panel_w + (cols - 1) * panel_gap
    trunk_x = 1230
    parts.append(_line(trunk_x, feeder_top + panel_h + 12, trunk_x, bus_y, 3, "#557b92"))
    parts.append(_line(bus_x1, bus_y, trunk_x, bus_y, 6, "#1f5d80"))
    parts.append(_txt((bus_x1+trunk_x)/2, bus_y - 15, f"{v_mv_kv:g} kV WIND COLLECTOR BUS", 17, "bold"))
    gsu_x = 1340
    parts.append(_line(trunk_x, bus_y, gsu_x, bus_y, 3))
    parts.append(_breaker(gsu_x, bus_y, "MV CB • TBD"))
    gsu_center_y = bus_y + 85
    parts.append(_line(gsu_x, bus_y + 30, gsu_x, gsu_center_y - 12, 3))
    parts.append(f'<circle cx="{gsu_x-11}" cy="{gsu_center_y}" r="11" fill="#fff" stroke="#25364a" stroke-width="2.5"/><circle cx="{gsu_x+11}" cy="{gsu_center_y}" r="11" fill="#fff" stroke="#25364a" stroke-width="2.5"/>')
    parts.append(_txt(gsu_x + 36, gsu_center_y - 5, "GSU", 13, "bold", "start"))
    parts.append(_txt(gsu_x + 36, gsu_center_y + 13, f"{gsu_mva:g} MVA • {v_mv_kv:g}/{v_hv_kv:g} kV", 11, anchor="start"))
    parts.append(_txt(gsu_x + 36, gsu_center_y + 29, f"Status: {gsu_status}", 9, anchor="start"))
    parts.append(_line(gsu_x, gsu_center_y + 12, gsu_x, bess_y + 143, 3))

    # BESS: multiple feeder branches connect to the same MV collector bus; PCS/transformer internals are schematic.
    bbus_y = bess_y + 100
    bx1, bx2 = 70, 850
    parts.append(_line(bx1, bbus_y, bx2, bbus_y, 5, "#8b5b23"))
    parts.append(_txt((bx1+bx2)/2, bbus_y - 17, f"BESS {v_mv_kv:g} kV AC COLLECTOR BUS", 15, "bold"))
    block_gap = (bx2 - bx1) / n_bess_feeders
    for j in range(n_bess_feeders):
        xx = bx1 + (j + 0.5) * block_gap
        parts.append(_line(xx, bbus_y, xx, bbus_y - 27, 2, "#8b5b23"))
        parts.append(_breaker(xx, bbus_y - 30, "CB • TBD"))
        parts.append(_line(xx, bbus_y - 60, xx, bbus_y - 78, 2, "#8b5b23"))
        parts.append(_transformer(xx, bbus_y - 92, f"MVT-{j+1:02d}", "Rating TBD", 34))
        parts.append(_line(xx, bbus_y - 92, xx, bbus_y - 145, 2, "#8b5b23"))
        parts.append(f'<rect x="{xx-35:.1f}" y="{bbus_y-190:.1f}" width="70" height="38" rx="4" fill="#fff8ed" stroke="#8b5b23" stroke-width="1.8"/>')
        parts.append(_txt(xx, bbus_y - 175, f"PCS-{j+1:02d}", 11, "bold"))
        parts.append(_txt(xx, bbus_y - 160, "Bi-dir.", 10))
    parts.append(_txt((bx1+bx2)/2, bbus_y + 30, f"Aggregate BESS: {p_bess_mw:g} MW / {e_bess_mwh:g} MWh", 13, "bold"))
    parts.append(_txt((bx1+bx2)/2, bbus_y + 49, "PCS/MVT allocation is illustrative; equipment ratings TBD", 10))

    # BESS connection to common MV bus, with separate point to avoid implying DC coupling.
    parts.append(_line(bx2, bbus_y, 960, bbus_y, 3, "#8b5b23"))
    parts.append(_line(960, bbus_y, 960, bus_y + 5, 3, "#8b5b23", "7 5"))
    parts.append(_txt(975, (bbus_y+bus_y)/2, "AC-coupled tie\n(proposed topology)", 11, anchor="start"))

    # HV breaker, metering, POI and grid.
    hv_bus_y = hv_y + 25
    parts.append(_breaker(gsu_x, hv_bus_y, "HV CB • TBD"))
    parts.append(_line(gsu_x, hv_bus_y + 30, gsu_x, hv_bus_y + 62, 3))
    parts.append(f'<rect x="{gsu_x-65}" y="{hv_bus_y+62}" width="130" height="44" rx="5" fill="#f1f5f9" stroke="#526579" stroke-width="1.5"/>')
    parts.append(_txt(gsu_x, hv_bus_y + 80, "Revenue metering", 12, "bold"))
    parts.append(_txt(gsu_x, hv_bus_y + 96, "CT/VT ratios TBD", 10))
    parts.append(_line(gsu_x, hv_bus_y + 106, gsu_x, hv_bus_y + 132, 3))
    parts.append(_line(gsu_x-20, hv_bus_y+132, gsu_x+20, hv_bus_y+132, 3))
    parts.append(_txt(gsu_x, hv_bus_y + 153, f"POI / GRID • {v_hv_kv:g} kV", 15, "bold"))
    parts.append(_txt(gsu_x, hv_bus_y + 174, f"Export limit: {poi_export_mw:g} MW • Import limit: {poi_import_mw:g} MW", 11))

    # Legend / missing-design-input callout.
    note_y = height - 92
    parts.append(f'<rect x="18" y="{note_y}" width="1464" height="72" rx="6" fill="#fff7ed" stroke="#d97706"/>')
    parts.append(_txt(35, note_y + 22, "ENGINEERING OPEN ITEMS", 12, "bold", "start"))
    parts.append(_txt(35, note_y + 43, "Breaker interrupting/continuous ratings, relay functions and settings, CT/VT ratios, cable types/sizes/lengths, grounding, bus ratings, and OEM PCS/MVT data are not specified by current inputs.", 11, anchor="start"))
    parts.append(_txt(35, note_y + 60, "Symbols are simplified and connections are topology-level only. Validate against approved OEM data, protection coordination, short-circuit/load-flow studies and utility requirements.", 11, anchor="start"))
    parts.append("</svg>")
    return "\n".join(parts)
