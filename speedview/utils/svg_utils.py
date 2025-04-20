import re
import os
import tempfile
from speedview.config.config import TEMP_SVG_FILE

def update_svg_speed(svg_template, speed, max_speed, angle=None):
    """Update the speed value and angle in SVG template"""
    if angle is None:
        # Calculate angle based on speed and max speed
        angle = -135 + (speed / max_speed) * 270
        angle = max(min(angle, 135), -135)
    
    # Update speed text
    updated_svg = re.sub(
        r'<text id="speedValue".*?>.*?</text>',
        f'<text id="speedValue" x="250" y="300" text-anchor="middle" '
        f'font-family="Arial" font-size="48" font-weight="bold" fill="#00F0FF">{speed:.2f}</text>',
        svg_template
    )
    
    # Update needle angle
    updated_svg = re.sub(
        r'<g id="needle" transform="rotate\(.*? 250 250\)".*?>',
        f'<g id="needle" transform="rotate({angle:.2f} 250 250)" filter="url(#shadowEffect)">',
        updated_svg
    )
    
    return updated_svg

def update_svg_connection_status(svg_template, status, signal_strength):
    """Update connection status and signal bars in SVG template"""
    # Update connection status text with color based on status
    color = "#00F0FF" if status == "Connected" else "#FF5050"
    updated_svg = re.sub(
        r'<text id="connectionStatus".*?>.*?</text>',
        f'<text id="connectionStatus" x="460" y="70" text-anchor="end" '
        f'font-family="Arial" font-size="16" fill="{color}" opacity="0.7">{status}</text>',
        svg_template
    )
    
    # Update signal strength bars
    signal_bars = ["#333333"] * 4  # Default all gray
    
    if status == "Connected":
        if signal_strength > 0:
            signal_bars[0] = "#00F0FF"
        if signal_strength >= 25:
            signal_bars[1] = "#00F0FF"
        if signal_strength >= 50:
            signal_bars[2] = "#00F0FF"
        if signal_strength >= 75:
            signal_bars[3] = "#00F0FF"
    
    signal_replacement = f"""<g id="signalStrength" transform="translate(380 70)">
    <rect x="0" y="0" width="5" height="15" rx="1" fill="{signal_bars[0]}"/>
    <rect x="8" y="-5" width="5" height="20" rx="1" fill="{signal_bars[1]}"/>
    <rect x="16" y="-10" width="5" height="25" rx="1" fill="{signal_bars[2]}"/>
    <rect x="24" y="-15" width="5" height="30" rx="1" fill="{signal_bars[3]}"/>
  </g>"""
    
    updated_svg = re.sub(r'<g id="signalStrength".*?</g>', signal_replacement, updated_svg)
    
    return updated_svg

def save_svg_to_file(svg_content):
    """Save SVG content to temporary file and return the path"""
    try:
        # Create temporary file in a secure way
        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg', mode='w') as temp_file:
            temp_file.write(svg_content)
            return temp_file.name
    except Exception as e:
        print(f"Error saving SVG to file: {e}")
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