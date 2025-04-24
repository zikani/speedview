import re
import os
import logging
import tempfile
from speedview.config.config import TEMP_SVG_FILE

def update_svg_speed(svg_template, speed, max_speed, show_upload=False, angle=None):
    """Update the speed value and angle in SVG template"""
    if angle is None:
        # Calculate angle based on speed and max speed
        angle = -135 + (speed / max_speed) * 270
        angle = max(min(angle, 135), -135)
    
    # Update speed text
    speed_label = f"{speed:.2f}"
    updated_svg = re.sub(
        r'<text id="speedValue".*?>.*?</text>',
        f'<text id="speedValue" x="250" y="300" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="#00F0FF" filter="url(#glowEffect)">{speed_label}</text>',
        svg_template
    )
    
    # Update needle angle
    updated_svg = re.sub(
        r'<g id="needle" transform="rotate\(.*? 250 250\)".*?>',
        f'<g id="needle" transform="rotate({angle:.2f} 250 250)" filter="url(#shadowEffect)">',
        updated_svg
    )
    
    # Add indicator for upload/download if needed
    type_text = "Upload" if show_upload else "Download"
    if "<text id=\"speedType\"" in updated_svg:
        updated_svg = re.sub(
            r'<text id="speedType".*?>.*?</text>',
            f'<text id="speedType" x="250" y="370" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="14" fill="#00F0FF" opacity="0.6">{type_text}</text>',
            updated_svg
        )
    
    return updated_svg

def update_svg_connection_status(svg_template, status, connection_type="Unknown"):
    """Update connection status and network type in SVG template"""
    color = "#00F0FF" if status == "Connected" else "#FF5050"
    updated_svg = re.sub(
        r'<text id="connectionStatus".*?>.*?</text>',
        f'<text id="connectionStatus" x="460" y="70" text-anchor="end" '
        f'font-family="Arial, sans-serif" font-size="16" fill="{color}" opacity="0.8">{status}</text>',
        svg_template
    )
    if "<text id=\"networkType\"" in updated_svg:
        updated_svg = re.sub(
            r'<text id="networkType".*?>.*?</text>',
            f'<text id="networkType" x="460" y="90" text-anchor="end" '
            f'font-family="Arial, sans-serif" font-size="14" fill="#00F0FF" opacity="0.6">{connection_type}</text>',
            updated_svg
        )
    return updated_svg

def update_test_network_svg(svg_template, status, download, upload):
    """Update the test network SVG with status, download, and upload values."""
    import re
    # Replace status
    updated_svg = re.sub(
        r'<text id="testStatus".*?>.*?</text>',
        f'<text id="testStatus" x="150" y="60" text-anchor="middle" font-family="Arial, sans-serif" font-size="18" fill="#00F0FF">{status}</text>',
        svg_template
    )
    # Replace download
    updated_svg = re.sub(
        r'<text id="downloadSpeed".*?>.*?</text>',
        f'<text id="downloadSpeed" x="150" y="140" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="#00F0FF">{download:.2f} Mbps</text>',
        updated_svg
    )
    # Replace upload
    updated_svg = re.sub(
        r'<text id="uploadSpeed".*?>.*?</text>',
        f'<text id="uploadSpeed" x="150" y="200" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" fill="#00F0FF">{upload:.2f} Mbps</text>',
        updated_svg
    )
    return updated_svg

def update_svg_signal_strength(svg_content, strength):
    """
    Update the signal strength bars in the SVG template.
    strength: int (0-4)
    """
    # Clamp strength to [0, 4]
    strength = max(0, min(4, int(strength)))
    # Opacities for each bar (4 bars)
    bar_opacities = [0.3, 0.5, 0.7, 0.9]
    # Set bars with index < strength to full opacity, others to original
    new_svg = svg_content
    for i, base_opacity in enumerate(bar_opacities):
        # If bar is active, set to 1.0, else base_opacity
        bar_opacity = "1.0" if i < strength else str(base_opacity)
        # Replace the opacity for each bar (rect)
        # x values are 0, 8, 16, 24 for the 4 bars
        def _replace_opacity(match):
            return f'{match.group(1)}{bar_opacity}{match.group(3)}'
        new_svg = re.sub(
            rf'(<rect x="{i*8}" [^>]*?opacity=")([0-9.]+)(")',
            _replace_opacity,
            new_svg
        )
    return new_svg

def update_floating_svg(svg_template, speed, signal_strength, connection_type, band):
    """Update the floating window SVG with current values"""
    # Format the speed value
    updated_svg = re.sub(
        r'<text id="speedValue".*?>.*?</text>',
        f'<text id="speedValue" x="60" y="45" font-family="Arial, sans-serif" '
        f'font-size="24" font-weight="bold" fill="url(#speedTextGradient)" text-anchor="middle" filter="url(#glow)">{speed:.1f}</text>',
        svg_template
    )
    
    # Update connection type and band
    connection_info = f"{connection_type}"
    updated_svg = re.sub(
        r'<text x="200" y="35".*?>.*?</text>',
        f'<text x="200" y="35" font-family="Arial, sans-serif" font-size="14" fill="#00FF8F" text-anchor="middle">{connection_info}</text>',
        updated_svg
    )
    
    band_info = f"{band}"
    updated_svg = re.sub(
        r'<text x="200" y="55".*?>.*?</text>',
        f'<text x="200" y="55" font-family="Arial, sans-serif" font-size="12" fill="#00FF8F" text-anchor="middle" opacity="0.7">{band_info}</text>',
        updated_svg
    )
    
    # Update signal strength bars
    filled_bars = 0
    if signal_strength > 0:
        filled_bars = 1
    if signal_strength >= 25:
        filled_bars = 2
    if signal_strength >= 50:
        filled_bars = 3
    if signal_strength >= 75:
        filled_bars = 4
    
    # Create signal bars with animations
    opacities = ["0.4", "0.6", "0.8", "0.3"]
    fills = ["#00FF8F", "#00FF8F", "#00FF8F", "#00FF8F"]
    
    # Adjust opacities based on signal strength
    for i in range(4):
        if i >= filled_bars:
            fills[i] = "#222222"  # Darker color for inactive bars
    
    signal_replacement = f"""<g transform="translate(130, 30)">
      <rect x="0" y="10" width="5" height="10" rx="2" fill="{fills[0]}" opacity="{opacities[0]}">
        <animate attributeName="opacity" values="{opacities[0]};1;{opacities[0]}" dur="2s" begin="0s" repeatCount="indefinite" />
      </rect>
      <rect x="10" y="5" width="5" height="15" rx="2" fill="{fills[1]}" opacity="{opacities[1]}">
        <animate attributeName="opacity" values="{opacities[1]};1;{opacities[1]}" dur="2s" begin="0.5s" repeatCount="indefinite" />
      </rect>
      <rect x="20" y="0" width="5" height="20" rx="2" fill="{fills[2]}" opacity="{opacities[2]}">
        <animate attributeName="opacity" values="{opacities[2]};1;{opacities[2]}" dur="2s" begin="1s" repeatCount="indefinite" />
      </rect>
      <rect x="30" y="-5" width="5" height="25" rx="2" fill="{fills[3]}" opacity="{opacities[3]}" />
    </g>"""
    
    updated_svg = re.sub(r'<g transform="translate\(130, 30\)".*?</g>', signal_replacement, updated_svg)
    
    return updated_svg

def save_svg_to_file(svg_content):
    """Save SVG content to temporary file and return the path"""
    try:
        # Create temporary file in a secure way
        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg', mode='w') as temp_file:
            temp_file.write(svg_content)
            return temp_file.name
    except Exception as e:
        logging.error(f"Error saving SVG to file: {e}")
        # Fallback to fixed filename if tempfile fails
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