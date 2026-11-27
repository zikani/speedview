import math
import os
import re
import logging
import tempfile
from xml.sax.saxutils import escape
from speedview.config.config import TEMP_SVG_FILE


def apply_rounded_mask(widget, x=0, y=0, width=None, height=None, radius=15):
    """Clip a frameless widget to its rounded SVG card bounds (works with or without compositor)."""
    from PyQt5.QtGui import QPainterPath, QRegion
    w = width if width is not None else widget.width()
    h = height if height is not None else widget.height()
    path = QPainterPath()
    path.addRoundedRect(float(x), float(y), float(w), float(h), float(radius), float(radius))
    region = QRegion(path.toFillPolygon().toPolygon())
    widget.setMask(region)


def convert_speed(speed_mbps, unit="Mbps"):
    """Convert speed from Mbps to requested display unit."""
    val = max(0.0, float(speed_mbps or 0.0))
    if unit == "MB/s":
        return val / 8.0
    if unit == "Kbps":
        return val * 1000.0
    return val


def _format_scale_label(value):
    if value >= 100:
        return f"{int(round(value))}"
    if value >= 10:
        return f"{value:.0f}"
    if value == 0:
        return "0"
    return f"{value:.1f}"


def _build_arc_path(start_deg, end_deg, cx=250, cy=250, r=170):
    """Build SVG arc path from start_deg to end_deg (0 deg = top/12 o'clock, clockwise)."""
    if end_deg <= start_deg + 0.5:
        return ""
    start_rad = math.radians(start_deg - 90)
    end_rad = math.radians(end_deg - 90)
    x1 = cx + r * math.cos(start_rad)
    y1 = cy + r * math.sin(start_rad)
    x2 = cx + r * math.cos(end_rad)
    y2 = cy + r * math.sin(end_rad)
    large_arc = 1 if (end_deg - start_deg) > 180 else 0
    return f"M {x1:.1f} {y1:.1f} A {r} {r} 0 {large_arc} 1 {x2:.1f} {y2:.1f}"


def update_svg_speed(svg_template, speed, max_speed, show_upload=False, angle=None, speed_unit="Mbps"):
    """Update the speed value, unit, needle angle, active arc, and dial markings in SVG template."""
    raw_speed = max(0.0, float(speed or 0.0))
    safe_max = max(1.0, float(max_speed or 100.0))

    if angle is None:
        angle = -135.0 + (raw_speed / safe_max) * 270.0
        angle = max(min(angle, 135.0), -135.0)

    display_speed = convert_speed(raw_speed, speed_unit)
    display_max = convert_speed(safe_max, speed_unit)
    speed_label = f"{display_speed:.1f}" if speed_unit == "Kbps" and display_speed >= 100 else f"{display_speed:.2f}"

    updated_svg = re.sub(
        r'<text id="speedValue".*?>.*?</text>',
        f'<text id="speedValue" x="250" y="308" text-anchor="middle" '
        f'font-size="52" font-weight="700" fill="#F2F6FF" filter="url(#glowEffect)">{speed_label}</text>',
        svg_template,
    )

    updated_svg = re.sub(
        r'<text id="speedUnit".*?>.*?</text>',
        f'<text id="speedUnit" x="250" y="338" text-anchor="middle" '
        f'font-size="18" font-weight="500" fill="#7DD3FC" opacity="0.9">{escape(speed_unit)}</text>',
        updated_svg,
    )

    type_text = "Upload" if show_upload else "Download"
    updated_svg = re.sub(
        r'<text id="speedType".*?>.*?</text>',
        f'<text id="speedType" x="250" y="362" text-anchor="middle" '
        f'font-size="12" font-weight="500" letter-spacing="1" fill="#8FA3C9">{type_text}</text>',
        updated_svg,
    )

    updated_svg = re.sub(
        r'<g id="needle" transform="rotate\(.*? 250 250\)".*?>',
        f'<g id="needle" transform="rotate({angle:.2f} 250 250)" filter="url(#shadowEffect)">',
        updated_svg,
    )

    arc_d = _build_arc_path(-135.0, angle)
    updated_svg = re.sub(
        r'<path id="activeArc" d="[^"]*"',
        f'<path id="activeArc" d="{arc_d}"',
        updated_svg,
    )

    # Update upright dial scale labels and cyan->blue->violet ticks across -135..+135
    marks = []
    for idx in range(7):
        deg = -135 + idx * 45
        val = (display_max * idx) / 6.0
        major = idx % 2 == 0
        y2 = 56 if major else 60
        sw = "2.5" if major else "2"
        fs = 12 if major else 11
        tick_color = "#22D3EE" if deg < 0 else ("#3B82F6" if deg <= 45 else "#8B5CF6")
        line_op = "" if major else ' opacity="0.6"'
        text_op = "" if major else ' opacity="0.7"'
        counter_rot = f' transform="rotate({-deg} 250 50)"' if deg != 0 else ""
        marks.append(
            f'    <g transform="rotate({deg} 250 250)">\n'
            f'      <line x1="250" y1="66" x2="250" y2="{y2}" stroke="{tick_color}" stroke-width="{sw}" stroke-linecap="round"{line_op}/>\n'
            f'      <text x="250" y="50" text-anchor="middle" font-size="{fs}" fill="#9FB3D9"{text_op}{counter_rot}>{_format_scale_label(val)}</text>\n'
            f'    </g>'
        )
    dial_block = (
        '<g id="dialMarks" font-family="Inter, \'SF Pro Display\', \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif" font-weight="600">\n'
        + "\n".join(marks)
        + '\n  </g>'
    )
    updated_svg = re.sub(
        r'<g id="dialMarks"[^>]*>.*?</g>\s*</g>',
        dial_block,
        updated_svg,
        flags=re.DOTALL,
    )

    return updated_svg


def update_svg_connection_status(svg_template, status, connection_type="Unknown", meta_text=""):
    """Update connection status, real interface type/detail, and metadata in SVG template."""
    color = "#F2F6FF" if status == "Connected" else ("#FBBF24" if status == "Checking..." else "#FF8CA1")
    safe_status = escape(str(status or "Unknown"))
    safe_type = escape(str(connection_type or "Unknown"))
    safe_meta = escape(str(meta_text or ""))

    updated_svg = re.sub(
        r'<text id="connectionStatus".*?>.*?</text>',
        f'<text id="connectionStatus" x="76" y="58" text-anchor="start" '
        f'font-size="14" font-weight="700" fill="{color}">{safe_status}</text>',
        svg_template,
    )
    updated_svg = re.sub(
        r'<text id="networkType".*?>.*?</text>',
        f'<text id="networkType" x="76" y="76" text-anchor="start" '
        f'font-size="12" font-weight="500" fill="#8FA3C9">{safe_type}</text>',
        updated_svg,
    )
    updated_svg = re.sub(
        r'<text id="networkMeta".*?>.*?</text>',
        f'<text id="networkMeta" x="250" y="384" text-anchor="middle" '
        f'font-size="11" fill="#6B7A9E">{safe_meta}</text>',
        updated_svg,
    )
    return updated_svg


def update_svg_ping(svg_template, latency_ms):
    """Update real-time ping/latency indicator (#pingBadge) next to speed gauge."""
    if latency_ms is None:
        ping_text = "-- ms"
        color = "#FF8CA1"
    else:
        ms_val = max(1, int(round(float(latency_ms))))
        ping_text = f"{ms_val} ms"
        if ms_val <= 50:
            color = "#2EE6A6"
        elif ms_val <= 120:
            color = "#22D3EE"
        else:
            color = "#FBBF24"

    updated_svg = re.sub(
        r'<circle id="pingDot"[^>]*/>',
        f'<circle id="pingDot" cx="422" cy="358" r="3" fill="{color}"/>',
        svg_template,
    )
    updated_svg = re.sub(
        r'<text id="pingValue".*?>.*?</text>',
        f'<text id="pingValue" x="446" y="377" text-anchor="middle" '
        f'font-size="13" font-weight="700" fill="{color}">{escape(ping_text)}</text>',
        updated_svg,
    )
    return updated_svg


def update_test_network_svg(svg_template, status, download, upload):
    """Update the test network SVG with real status, download/upload values, and progress bars."""
    dl = max(0.0, float(download or 0.0))
    ul = max(0.0, float(upload or 0.0))
    raw_status = str(status or "Ready")

    title = "Network Speed Test"
    display_status = raw_status
    if "Complete" in raw_status:
        title = "Test Complete!"
        if raw_status == "Test Complete!":
            display_status = "Speed test finished"
    elif "Failed" in raw_status or "error" in raw_status.lower():
        title = "Test Failed"
        if raw_status == "Test Failed":
            display_status = "Check connection and try again"
    elif any(k in raw_status for k in ("Running", "Testing", "Downloading", "Uploading", "Connecting")):
        title = "Testing Network Speed..."

    if len(display_status) > 36:
        display_status = display_status[:35] + "…"
    safe_status = escape(display_status)

    # Scale progress bars up to 160px (100 Mbps reference, capped at 160px)
    dl_width = min(160.0, (dl / 100.0) * 160.0) if dl > 0 else 0.0
    ul_width = min(160.0, (ul / 100.0) * 160.0) if ul > 0 else 0.0

    updated_svg = re.sub(
        r'<text id="testTitle".*?>.*?</text>',
        f'<text id="testTitle" x="150" y="72" font-size="18" font-weight="700" fill="#F2F6FF" text-anchor="middle">{title}</text>',
        svg_template,
    )
    updated_svg = re.sub(
        r'<text id="testStatus".*?>.*?</text>',
        f'<text id="testStatus" x="150" y="186" font-size="13" fill="#8FA3C9" text-anchor="middle">{safe_status}</text>',
        updated_svg,
    )
    updated_svg = re.sub(
        r'<text id="downloadSpeed".*?>.*?</text>',
        f'<text id="downloadSpeed" x="230" y="220" font-size="14" font-weight="700" fill="#22D3EE" text-anchor="end">{dl:.2f} Mbps</text>',
        updated_svg,
    )
    updated_svg = re.sub(
        r'<text id="uploadSpeed".*?>.*?</text>',
        f'<text id="uploadSpeed" x="230" y="250" font-size="14" font-weight="700" fill="#A78BFA" text-anchor="end">{ul:.2f} Mbps</text>',
        updated_svg,
    )
    updated_svg = re.sub(
        r'<rect id="downloadBar" x="70" y="226" width="[^"]*"',
        f'<rect id="downloadBar" x="70" y="226" width="{dl_width:.1f}"',
        updated_svg,
    )
    updated_svg = re.sub(
        r'<rect id="uploadBar" x="70" y="256" width="[^"]*"',
        f'<rect id="uploadBar" x="70" y="256" width="{ul_width:.1f}"',
        updated_svg,
    )
    return updated_svg


def update_svg_signal_strength(svg_content, strength):
    """
    Update signal strength bars in the main SVG template.
    Accepts either 0-4 bar count or 0-100 percentage.
    """
    raw = float(strength or 0)
    if raw > 4:
        if raw >= 75:
            bars = 4
        elif raw >= 50:
            bars = 3
        elif raw >= 25:
            bars = 2
        elif raw > 0:
            bars = 1
        else:
            bars = 0
    else:
        bars = max(0, min(4, int(raw)))

    new_svg = svg_content
    for i in range(4):
        bar_opacity = "1.0" if i < bars else "0.25"
        new_svg = re.sub(
            rf'(<rect x="{i*8}" [^>]*?opacity=")([0-9.]+)(")',
            rf'\g<1>{bar_opacity}\g<3>',
            new_svg,
        )
    return new_svg


def update_floating_svg(svg_template, speed, signal_strength, connection_type=None, band=None, speed_unit="Mbps"):
    """Update the compact 136x40 transparent floating SVG (signal + speed only)."""
    display_speed = convert_speed(speed, speed_unit)
    speed_str = f"{display_speed:.0f}" if speed_unit == "Kbps" and display_speed >= 100 else f"{display_speed:.1f}"

    updated_svg = re.sub(
        r'<text id="speedValue".*?>.*?</text>',
        f'<text id="speedValue" x="64" y="22" font-size="16" font-weight="700" '
        f'fill="url(#speedTextGradient)" text-anchor="middle" filter="url(#glow)">{speed_str}</text>',
        svg_template,
    )

    updated_svg = re.sub(
        r'<text id="speedUnit".*?>.*?</text>',
        f'<text id="speedUnit" x="64" y="34" font-size="8.5" font-weight="600" fill="#8FA3C9" text-anchor="middle">{escape(speed_unit)}</text>',
        updated_svg,
    )


    raw_sig = float(signal_strength or 0)
    if raw_sig <= 4 and raw_sig > 0:
        filled_bars = int(raw_sig)
    elif raw_sig >= 75:
        filled_bars = 4
    elif raw_sig >= 50:
        filled_bars = 3
    elif raw_sig >= 25:
        filled_bars = 2
    elif raw_sig > 0:
        filled_bars = 1
    else:
        filled_bars = 0

    fills = ["#2EE6A6" if i < filled_bars else "#1B2540" for i in range(4)]
    opacities = ["0.95" if i < filled_bars else "0.55" for i in range(4)]

    signal_replacement = (
        '<g id="signalBars" transform="translate(10, 11)">\n'
        f'      <rect class="signal-bar" x="0" y="10" width="3.5" height="7" rx="1.5" fill="{fills[0]}" opacity="{opacities[0]}"/>\n'
        f'      <rect class="signal-bar" x="5.5" y="7" width="3.5" height="10" rx="1.5" fill="{fills[1]}" opacity="{opacities[1]}"/>\n'
        f'      <rect class="signal-bar" x="11" y="4" width="3.5" height="13" rx="1.5" fill="{fills[2]}" opacity="{opacities[2]}"/>\n'
        f'      <rect class="signal-bar" x="16.5" y="0" width="3.5" height="17" rx="1.5" fill="{fills[3]}" opacity="{opacities[3]}"/>\n'
        '    </g>'
    )

    updated_svg = re.sub(
        r'<g id="signalBars"[^>]*>.*?</g>',
        signal_replacement,
        updated_svg,
        flags=re.DOTALL,
    )

    return updated_svg


def update_data_usage_svg(svg_template, daily_total_str, monthly_total_str, rows, mode="daily"):
    """Update DATA_USAGE_SVG_TEMPLATE with real daily/monthly totals and App | Data | Date rows."""
    from speedview.models.data_usage import format_bytes

    subtitle = "Daily Breakdown" if mode == "daily" else "Monthly Breakdown"
    updated = re.sub(
        r'<text id="usageModeSubtitle".*?>.*?</text>',
        f'<text id="usageModeSubtitle" x="158" y="34" font-size="12" font-weight="500" fill="#6FA8C0">{subtitle}</text>',
        svg_template,
    )
    updated = re.sub(
        r'<text id="dailyTotal".*?>.*?</text>',
        f'<text id="dailyTotal" x="44" y="102" font-size="24" font-weight="700" fill="#22D3EE">{escape(str(daily_total_str))}</text>',
        updated,
    )
    updated = re.sub(
        r'<text id="monthlyTotal".*?>.*?</text>',
        f'<text id="monthlyTotal" x="284" y="102" font-size="24" font-weight="700" fill="#34D399">{escape(str(monthly_total_str))}</text>',
        updated,
    )

    daily_fill = "url(#usageBtnGradient)" if mode == "daily" else "#18222D"
    daily_stroke = "#22D3EE" if mode == "daily" else "#2D4A63"
    daily_text = "#FFFFFF" if mode == "daily" else "#8FA3C9"

    monthly_fill = "url(#usageBtnGradient)" if mode == "monthly" else "#18222D"
    monthly_stroke = "#22D3EE" if mode == "monthly" else "#2D4A63"
    monthly_text = "#FFFFFF" if mode == "monthly" else "#8FA3C9"

    tabs_block = (
        '<g id="usageTabs">\n'
        f'    <rect id="dailyTabRect" x="28" y="130" width="105" height="30" rx="15" fill="{daily_fill}" stroke="{daily_stroke}" stroke-width="1"/>\n'
        f'    <text x="80.5" y="149.5" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.6" fill="{daily_text}">DAILY</text>\n'
        f'    <rect id="monthlyTabRect" x="143" y="130" width="115" height="30" rx="15" fill="{monthly_fill}" stroke="{monthly_stroke}" stroke-width="1"/>\n'
        f'    <text x="200.5" y="149.5" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.6" fill="{monthly_text}">MONTHLY</text>\n'
        '    <rect id="resetUsageRect" x="392" y="130" width="100" height="30" rx="15" fill="#FF5C7A" fill-opacity="0.10" stroke="#FF5C7A" stroke-opacity="0.55" stroke-width="1"/>\n'
        '    <text x="442" y="149.5" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.6" fill="#FF8CA1">RESET</text>\n'
        '  </g>'
    )
    updated = re.sub(r'<g id="usageTabs">.*?</g>', tabs_block, updated, flags=re.DOTALL)

    row_elements = []
    if not rows:
        row_elements.append(
            '<text x="260" y="308" text-anchor="middle" font-size="13" fill="#6B7A9E">'
            'No network app traffic recorded for this period yet.</text>'
        )
    else:
        max_bytes = max(1, max(r.get("bytes", 0) for r in rows[:7]))
        for idx, row in enumerate(rows[:7]):
            y_top = 208 + idx * 29
            y_text = y_top + 17
            app_name = str(row.get("app", "Unknown"))
            if len(app_name) > 22:
                app_name = app_name[:21] + "…"
            data_str = format_bytes(row.get("bytes", 0))
            date_str = str(row.get("date", ""))
            bar_w = max(4.0, (row.get("bytes", 0) / max_bytes) * 165.0)
            bg_fill = "#111B2E" if idx % 2 == 0 else "#0B121A"

            row_elements.append(
                f'    <rect x="34" y="{y_top}" width="452" height="25" rx="6" fill="{bg_fill}"/>\n'
                f'    <rect x="46" y="{y_top + 21}" width="{bar_w:.1f}" height="2" rx="1" fill="url(#usageArcGradient)" opacity="0.8"/>\n'
                f'    <text x="46" y="{y_text}" font-size="12" font-weight="500" fill="#F2F6FF">{escape(app_name)}</text>\n'
                f'    <text x="332" y="{y_text}" text-anchor="end" font-size="12" font-weight="700" fill="#22D3EE">{escape(data_str)}</text>\n'
                f'    <text x="474" y="{y_text}" text-anchor="end" font-size="11" fill="#8FA3C9">{escape(date_str)}</text>'
            )

    rows_block = '<g id="usageRows">\n' + "\n".join(row_elements) + '\n  </g>'
    updated = re.sub(r'<g id="usageRows">.*?</g>', rows_block, updated, flags=re.DOTALL)
    return updated


def save_svg_to_file(svg_content):
    """Save SVG content to temporary file and return the path (legacy helper)."""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg', mode='w') as temp_file:
            temp_file.write(svg_content)
            return temp_file.name
    except Exception as e:
        logging.error(f"Error saving SVG to file: {e}")
        with open(TEMP_SVG_FILE, 'w') as f:
            f.write(svg_content)
        return TEMP_SVG_FILE


def cleanup_temp_files():
    """Clean up any temporary SVG files"""
    try:
        if os.path.exists(TEMP_SVG_FILE):
            os.remove(TEMP_SVG_FILE)
    except Exception as e:
        print(f"Error cleaning up temp files: {e}")