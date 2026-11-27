"""SVG templates for the speed meter display (modernized UI)

Design language
---------------
* Deep navy surfaces with a soft center glow instead of flat black
* Cyan -> blue -> violet accent gradient (mapped to dial position)
* Glass-style secondary surfaces (white at 4-8% opacity + hairline border)
* Thin tapered needle, slim 14px arc, upright dial labels, muted secondary text
* Modern system font stack, set once on the root <svg> so dynamically
  injected rows / marks inherit it

All element ids, classes, canvas sizes and hit-area positions are unchanged,
so existing JS/Python code that updates them keeps working.
"""

# Main speedometer SVG template
MAIN_SVG_TEMPLATE = """
<svg width="500" height="500" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg"
     font-family="Inter, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif">
  <defs>
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0E1628" />
      <stop offset="100%" stop-color="#05080F" />
    </linearGradient>

    <radialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#22D3EE" stop-opacity="0.14" />
      <stop offset="60%" stop-color="#3B82F6" stop-opacity="0.05" />
      <stop offset="100%" stop-color="#3B82F6" stop-opacity="0" />
    </radialGradient>

    <!-- Mapped to dial position (userSpaceOnUse) so colour = how fast you are going -->
    <linearGradient id="speedArcGradient" gradientUnits="userSpaceOnUse" x1="80" y1="0" x2="420" y2="0">
      <stop offset="0%" stop-color="#22D3EE" />
      <stop offset="55%" stop-color="#3B82F6" />
      <stop offset="100%" stop-color="#8B5CF6" />
    </linearGradient>

    <linearGradient id="needleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="100%" stop-color="#22D3EE" />
    </linearGradient>

    <filter id="shadowEffect" x="-50%" y="-50%" width="200%" height="200%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#22D3EE" flood-opacity="0.45"/>
    </filter>

    <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="3" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#2563EB" />
      <stop offset="100%" stop-color="#1E40AF" />
    </linearGradient>

    <linearGradient id="buttonHoverGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#3B82F6" />
      <stop offset="100%" stop-color="#2563EB" />
    </linearGradient>

    <linearGradient id="floatButtonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0891B2" />
      <stop offset="100%" stop-color="#155E75" />
    </linearGradient>
  </defs>

  <!-- Card surface -->
  <rect width="500" height="500" fill="url(#backgroundGradient)" rx="28" ry="28"/>
  <rect width="500" height="500" fill="url(#centerGlow)" rx="28" ry="28"/>
  <rect x="0.5" y="0.5" width="499" height="499" rx="27.5" ry="27.5" fill="none" stroke="#FFFFFF" stroke-opacity="0.07"/>

  <!-- Subtle decorative rings -->
  <circle cx="250" cy="250" r="232" fill="none" stroke="#FFFFFF" stroke-width="1" opacity="0.05"/>
  <circle cx="250" cy="250" r="146" fill="none" stroke="#FFFFFF" stroke-width="1" stroke-dasharray="2 7" opacity="0.10"/>

  <!-- Meter background track (-135 deg to +135 deg around 250,250 r=170) -->
  <path d="M 129.8 370.2 A 170 170 0 1 1 370.2 370.2" fill="none" stroke="#1B2540" stroke-width="14" stroke-linecap="round"/>

  <!-- Active speed arc -->
  <path id="activeArc" d="" fill="none" stroke="url(#speedArcGradient)" stroke-width="14" stroke-linecap="round" filter="url(#glowEffect)"/>

  <!-- Minor ticks every 15 degrees (static) -->
  <g id="minorTicks" stroke="#33415F" stroke-width="1.5" stroke-linecap="round">
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(-120 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(-105 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(-75 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(-60 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(-30 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(-15 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(15 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(30 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(60 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(75 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(105 250 250)"/>
    <line x1="250" y1="66" x2="250" y2="61" transform="rotate(120 250 250)"/>
  </g>

  <!-- Speed markings and labels (dynamically scaled). Labels are counter-rotated so they stay upright. -->
  <g id="dialMarks" font-family="Inter, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif" font-weight="600">
    <g transform="rotate(-135 250 250)">
      <line x1="250" y1="66" x2="250" y2="56" stroke="#22D3EE" stroke-width="2.5" stroke-linecap="round"/>
      <text x="250" y="50" text-anchor="middle" font-size="12" fill="#9FB3D9" transform="rotate(135 250 50)">0</text>
    </g>
    <g transform="rotate(-90 250 250)">
      <line x1="250" y1="66" x2="250" y2="60" stroke="#22D3EE" stroke-width="2" stroke-linecap="round" opacity="0.6"/>
      <text x="250" y="50" text-anchor="middle" font-size="11" fill="#9FB3D9" opacity="0.7" transform="rotate(90 250 50)">17</text>
    </g>
    <g transform="rotate(-45 250 250)">
      <line x1="250" y1="66" x2="250" y2="56" stroke="#22D3EE" stroke-width="2.5" stroke-linecap="round"/>
      <text x="250" y="50" text-anchor="middle" font-size="12" fill="#9FB3D9" transform="rotate(45 250 50)">33</text>
    </g>
    <g transform="rotate(0 250 250)">
      <line x1="250" y1="66" x2="250" y2="56" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round"/>
      <text x="250" y="50" text-anchor="middle" font-size="12" fill="#9FB3D9">50</text>
    </g>
    <g transform="rotate(45 250 250)">
      <line x1="250" y1="66" x2="250" y2="56" stroke="#3B82F6" stroke-width="2.5" stroke-linecap="round"/>
      <text x="250" y="50" text-anchor="middle" font-size="12" fill="#9FB3D9" transform="rotate(-45 250 50)">67</text>
    </g>
    <g transform="rotate(90 250 250)">
      <line x1="250" y1="66" x2="250" y2="60" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round" opacity="0.6"/>
      <text x="250" y="50" text-anchor="middle" font-size="11" fill="#9FB3D9" opacity="0.7" transform="rotate(-90 250 50)">83</text>
    </g>
    <g transform="rotate(135 250 250)">
      <line x1="250" y1="66" x2="250" y2="56" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round"/>
      <text x="250" y="50" text-anchor="middle" font-size="12" fill="#9FB3D9" transform="rotate(-135 250 50)">100</text>
    </g>
  </g>

  <!-- Needle: thin tapered blade + ringed hub -->
  <g id="needle" transform="rotate(-135 250 250)" filter="url(#shadowEffect)">
    <path d="M246 252 L250 122 L254 252 Z" fill="url(#needleGradient)"/>
    <circle cx="250" cy="250" r="13" fill="#0B1220" stroke="#22D3EE" stroke-width="2"/>
    <circle cx="250" cy="250" r="4.5" fill="#22D3EE"/>
  </g>

  <!-- Speed value display -->
  <g id="speedDisplay">
    <text id="speedValue" x="250" y="308" text-anchor="middle" font-size="52" font-weight="700" fill="#F2F6FF" filter="url(#glowEffect)">0.00</text>
    <text id="speedUnit" x="250" y="338" text-anchor="middle" font-size="18" font-weight="500" fill="#7DD3FC" opacity="0.9">Mbps</text>
    <text id="speedType" x="250" y="362" text-anchor="middle" font-size="12" font-weight="500" letter-spacing="1" fill="#8FA3C9">Download</text>
  </g>

  <!-- Window controls (minimize & close for frameless card) -->
  <g id="minimizeWindowBtn" class="interactive-button" opacity="0.9">
    <circle cx="442" cy="24" r="11" fill="#FFFFFF" fill-opacity="0.06" stroke="#FFFFFF" stroke-opacity="0.18" stroke-width="1"/>
    <line x1="437" y1="24" x2="447" y2="24" stroke="#CBD5F5" stroke-width="1.8" stroke-linecap="round"/>
  </g>
  <g id="closeWindowBtn" class="interactive-button" opacity="0.9">
    <circle cx="472" cy="24" r="11" fill="#FF5C7A" fill-opacity="0.12" stroke="#FF5C7A" stroke-opacity="0.55" stroke-width="1"/>
    <path d="M468 20 L476 28 M476 20 L468 28" stroke="#FF8CA1" stroke-width="1.8" stroke-linecap="round"/>
  </g>

  <!-- Settings button -->
  <g id="settingsIcon" transform="translate(420 50)" class="button" opacity="0.9">
    <circle cx="30" cy="30" r="20" fill="#FFFFFF" fill-opacity="0.05" stroke="#FFFFFF" stroke-opacity="0.14" stroke-width="1"/>
    <circle cx="30" cy="30" r="7" fill="none" stroke="#7DD3FC" stroke-width="2"/>
    <path d="M30 16.5 L30 19.5 M30 40.5 L30 43.5 M16.5 30 L19.5 30 M40.5 30 L43.5 30
             M20.45 20.45 L22.58 22.58 M39.55 20.45 L37.42 22.58 M20.45 39.55 L22.58 37.42 M39.55 39.55 L37.42 37.42"
          stroke="#7DD3FC" stroke-width="2" stroke-linecap="round" fill="none"/>
    <circle cx="30" cy="30" r="2.5" fill="#22D3EE"/>
  </g>

  <!-- Signal strength indicator -->
  <g id="signalStrength" transform="translate(36 48)">
    <rect x="0" y="15" width="5" height="15" rx="2.5" fill="#22D3EE" opacity="0.3" class="signal-bar"/>
    <rect x="8" y="10" width="5" height="20" rx="2.5" fill="#22D3EE" opacity="0.3" class="signal-bar"/>
    <rect x="16" y="5" width="5" height="25" rx="2.5" fill="#22D3EE" opacity="0.3" class="signal-bar"/>
    <rect x="24" y="0" width="5" height="30" rx="2.5" fill="#22D3EE" opacity="0.3" class="signal-bar"/>
  </g>

  <!-- Real connection status & interface metadata -->
  <text id="connectionStatus" x="76" y="58" text-anchor="start" font-size="14" font-weight="700" fill="#F2F6FF">Checking...</text>
  <text id="networkType" x="76" y="76" text-anchor="start" font-size="12" font-weight="500" fill="#8FA3C9">Detecting interface...</text>
  <text id="networkMeta" x="250" y="384" text-anchor="middle" font-size="11" fill="#6B7A9E"></text>

  <!-- Test Network button (primary) -->
  <g id="testButtonGroup" class="interactive-button">
    <rect id="testButton" x="175" y="400" width="150" height="40" rx="20" fill="url(#buttonGradient)" class="button" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="1" opacity="0.95"/>
    <text x="250" y="425" text-anchor="middle" font-size="13" font-weight="700" letter-spacing="0.8" fill="#FFFFFF">TEST NETWORK</text>
  </g>

  <!-- Float button -->
  <g id="floatButtonGroup" class="interactive-button">
    <rect id="floatButton" x="50" y="400" width="100" height="40" rx="20" fill="url(#floatButtonGradient)" class="button" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="1" opacity="0.95"/>
    <text x="100" y="425" text-anchor="middle" font-size="13" font-weight="700" letter-spacing="0.8" fill="#FFFFFF">FLOAT</text>
  </g>

  <!-- Usage button -->
  <g id="usageButtonGroup" class="interactive-button">
    <rect id="usageButton" x="350" y="400" width="100" height="40" rx="20" fill="url(#buttonGradient)" class="button" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="1" opacity="0.95"/>
    <text x="400" y="425" text-anchor="middle" font-size="13" font-weight="700" letter-spacing="0.8" fill="#FFFFFF">USAGE</text>
  </g>
</svg>
"""

# Floating mode SVG template
FLOATING_SVG_TEMPLATE = """
<svg width="250" height="80" viewBox="0 0 250 80" xmlns="http://www.w3.org/2000/svg"
     font-family="Inter, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif">
  <defs>
    <linearGradient id="darkGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#101A2B" />
      <stop offset="100%" stop-color="#060A12" />
    </linearGradient>

    <linearGradient id="speedTextGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8CFFD6" />
      <stop offset="100%" stop-color="#2EE6A6" />
    </linearGradient>

    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>

    <filter id="shadow">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#2EE6A6" flood-opacity="0.22"/>
    </filter>
  </defs>

  <g transform="translate(0, 0)">
    <rect width="250" height="80" rx="24" ry="24" fill="url(#darkGradient)" filter="url(#shadow)" />
    <rect x="0.5" y="0.5" width="249" height="79" rx="23.5" ry="23.5" fill="none" stroke="#FFFFFF" stroke-opacity="0.08" />

    <!-- Dividers -->
    <line x1="114" y1="24" x2="114" y2="56" stroke="#FFFFFF" stroke-width="1" opacity="0.08" />
    <line x1="172" y1="24" x2="172" y2="56" stroke="#FFFFFF" stroke-width="1" opacity="0.08" />

    <!-- Speed value -->
    <text id="speedValue" x="60" y="45" font-size="26" font-weight="700" fill="url(#speedTextGradient)" text-anchor="middle" filter="url(#glow)">0.0</text>
    <text id="speedUnit" x="60" y="65" font-size="12" font-weight="500" fill="#8FA3C9" text-anchor="middle">Mbps</text>

    <!-- Signal strength bars -->
    <g transform="translate(130, 30)">
      <rect class="signal-bar" x="0" y="10" width="5" height="10" rx="2.5" fill="#2EE6A6" opacity="0.95"/>
      <rect class="signal-bar" x="10" y="5" width="5" height="15" rx="2.5" fill="#2EE6A6" opacity="0.95"/>
      <rect class="signal-bar" x="20" y="0" width="5" height="20" rx="2.5" fill="#2EE6A6" opacity="0.95"/>
      <rect class="signal-bar" x="30" y="-5" width="5" height="25" rx="2.5" fill="#2EE6A6" opacity="0.3"/>
    </g>

    <!-- Real connection info -->
    <text id="connectionType" x="195" y="38" font-size="13" font-weight="700" fill="#E6FFF6" text-anchor="middle">--</text>
    <text id="connectionBand" x="195" y="54" font-size="10" font-weight="500" fill="#8FA3C9" text-anchor="middle"></text>

    <!-- Expand button -->
    <g id="expandButton" class="button" transform="translate(20, 20)">
      <circle cx="0" cy="0" r="9" fill="#FFFFFF" fill-opacity="0.06" stroke="#2EE6A6" stroke-opacity="0.55" stroke-width="1" />
      <path d="M-3.5,0 L3.5,0 M0,-3.5 L0,3.5" stroke="#8CFFD6" stroke-width="1.6" stroke-linecap="round" />
    </g>

    <!-- Close button -->
    <g id="closeButton" class="button" transform="translate(230, 20)">
      <circle cx="0" cy="0" r="9" fill="#FFFFFF" fill-opacity="0.06" stroke="#FFFFFF" stroke-opacity="0.22" stroke-width="1" />
      <path d="M-3.5,-3.5 L3.5,3.5 M-3.5,3.5 L3.5,-3.5" stroke="#CBD5F5" stroke-width="1.6" stroke-linecap="round" />
    </g>
  </g>
</svg>
"""

# Icons: consistent 1.8px rounded line style on a 32px grid, user-space gradients
SETTINGS_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="iconGradient" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="32" y2="32">
      <stop offset="0%" stop-color="#22D3EE" />
      <stop offset="100%" stop-color="#3B82F6" />
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="1.2" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>
  <circle cx="16" cy="16" r="7.5" fill="none" stroke="url(#iconGradient)" stroke-width="1.8" />
  <path d="M16 4 L16 7.5 M16 24.5 L16 28 M4 16 L7.5 16 M24.5 16 L28 16
           M7.51 7.51 L9.99 9.99 M24.49 7.51 L22.01 9.99 M7.51 24.49 L9.99 22.01 M24.49 24.49 L22.01 22.01"
        fill="none" stroke="url(#iconGradient)" stroke-width="1.8" stroke-linecap="round" />
  <circle cx="16" cy="16" r="2.5" fill="url(#iconGradient)" filter="url(#glow)" />
</svg>
"""

NOTIFICATION_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="notifyGradient" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="32" y2="32">
      <stop offset="0%" stop-color="#22D3EE" />
      <stop offset="100%" stop-color="#3B82F6" />
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="1.2" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>
  <g transform="translate(2 2) scale(1.1667)" fill="none" stroke="url(#notifyGradient)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
    <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
    <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
  </g>
  <!-- Unread badge -->
  <circle cx="25" cy="7" r="4" fill="#FF5C7A" filter="url(#glow)"/>
</svg>
"""

HISTORY_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="historyGradient" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="32" y2="32">
      <stop offset="0%" stop-color="#22D3EE" />
      <stop offset="100%" stop-color="#3B82F6" />
    </linearGradient>
  </defs>
  <g transform="translate(2 2) scale(1.1667)" fill="none" stroke="url(#historyGradient)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
    <path d="M3 3v5h5" />
    <path d="M3.05 13A9 9 0 1 0 6 5.3L3 8" />
    <path d="M12 7v5l4 2" />
  </g>
</svg>
"""

TEST_NETWORK_SVG = '''<svg width="300" height="340" viewBox="0 0 300 340" xmlns="http://www.w3.org/2000/svg"
     font-family="Inter, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif">
  <defs>
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0E1628" />
      <stop offset="100%" stop-color="#05080F" />
    </linearGradient>
    <radialGradient id="spinnerGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#22D3EE" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#22D3EE" stop-opacity="0" />
    </radialGradient>
    <linearGradient id="speedArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22D3EE" />
      <stop offset="55%" stop-color="#3B82F6" />
      <stop offset="100%" stop-color="#8B5CF6" />
    </linearGradient>
    <filter id="shadowEffect" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#22D3EE" flood-opacity="0.25"/>
    </filter>
    <filter id="glowEffect" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2.5" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
    <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#2563EB" />
      <stop offset="100%" stop-color="#1E40AF" />
    </linearGradient>
  </defs>

  <!-- Card -->
  <rect x="10" y="10" width="280" height="320" fill="url(#backgroundGradient)" rx="24" ry="24" filter="url(#shadowEffect)"/>
  <rect x="10.5" y="10.5" width="279" height="319" rx="23.5" ry="23.5" fill="none" stroke="#FFFFFF" stroke-opacity="0.08"/>

  <!-- Header -->
  <text x="150" y="34" font-size="11" font-weight="600" letter-spacing="1.5" fill="#8FA3C9" text-anchor="middle">NETWORK TEST</text>
  <line x1="30" y1="46" x2="270" y2="46" stroke="#FFFFFF" stroke-width="1" opacity="0.07"/>

  <text id="testTitle" x="150" y="72" font-size="18" font-weight="700" fill="#F2F6FF" text-anchor="middle">Ready to test</text>

  <!-- Spinner -->
  <circle cx="150" cy="124" r="46" fill="url(#spinnerGlow)"/>
  <circle cx="150" cy="124" r="36" fill="none" stroke="#1B2540" stroke-width="6"/>
  <circle cx="150" cy="124" r="36" fill="none" stroke="url(#speedArcGradient)" stroke-width="6" stroke-linecap="round" stroke-dasharray="64 162.2" filter="url(#glowEffect)">
    <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 150 124" to="360 150 124" dur="1.6s" repeatCount="indefinite"/>
  </circle>
  <circle cx="150" cy="124" r="36" fill="none" stroke="url(#speedArcGradient)" stroke-width="6" stroke-linecap="round" stroke-dasharray="20 206.2" opacity="0.5">
    <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="150 150 124" to="510 150 124" dur="1.6s" repeatCount="indefinite"/>
  </circle>

  <text id="testStatus" x="150" y="186" font-size="13" fill="#8FA3C9" text-anchor="middle">Waiting to start...</text>

  <!-- Results card -->
  <rect x="50" y="195" width="200" height="80" fill="#FFFFFF" fill-opacity="0.04" stroke="#FFFFFF" stroke-opacity="0.09" stroke-width="1" rx="14" ry="14"/>
  <text x="70" y="220" font-size="13" font-weight="600" fill="#CBD5F5" text-anchor="start">Download</text>
  <text id="downloadSpeed" x="230" y="220" font-size="14" font-weight="700" fill="#22D3EE" text-anchor="end">0.00 Mbps</text>
  <rect x="70" y="226" width="160" height="4" fill="#1B2540" rx="2" ry="2"/>
  <rect id="downloadBar" x="70" y="226" width="0" height="4" fill="url(#speedArcGradient)" rx="2" ry="2"/>
  <text x="70" y="250" font-size="13" font-weight="600" fill="#CBD5F5" text-anchor="start">Upload</text>
  <text id="uploadSpeed" x="230" y="250" font-size="14" font-weight="700" fill="#A78BFA" text-anchor="end">0.00 Mbps</text>
  <rect x="70" y="256" width="160" height="4" fill="#1B2540" rx="2" ry="2"/>
  <rect id="uploadBar" x="70" y="256" width="0" height="4" fill="url(#speedArcGradient)" rx="2" ry="2"/>

  <!-- Close button -->
  <rect x="75" y="290" width="150" height="36" fill="url(#buttonGradient)" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="1" rx="18" ry="18"/>
  <text x="150" y="313" font-size="13" fill="#FFFFFF" font-weight="700" letter-spacing="0.8" text-anchor="middle">CLOSE</text>
</svg>'''

DATA_USAGE_SVG_TEMPLATE = '''<svg width="520" height="480" viewBox="0 0 520 480" xmlns="http://www.w3.org/2000/svg"
     font-family="Inter, 'SF Pro Display', 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif">
  <defs>
    <linearGradient id="usageBgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0E1628" />
      <stop offset="100%" stop-color="#05080F" />
    </linearGradient>
    <linearGradient id="usageCardGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#16202C" />
      <stop offset="100%" stop-color="#0D131B" />
    </linearGradient>
    <linearGradient id="usageArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#22D3EE" />
      <stop offset="100%" stop-color="#3B82F6" />
    </linearGradient>
    <linearGradient id="usageBtnGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#2563EB" />
      <stop offset="100%" stop-color="#1E40AF" />
    </linearGradient>
    <filter id="usageGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceGraphic" stdDeviation="2" result="blur" />
      <feMerge>
        <feMergeNode in="blur" />
        <feMergeNode in="SourceGraphic" />
      </feMerge>
    </filter>
  </defs>

  <!-- Main rounded card -->
  <rect x="4" y="4" width="512" height="472" rx="24" ry="24" fill="url(#usageBgGradient)" stroke="#223447" stroke-width="1.5"/>

  <!-- Header -->
  <text x="28" y="34" font-size="17" font-weight="700" letter-spacing="0.5" fill="#F2F6FF">DATA USAGE</text>
  <text id="usageModeSubtitle" x="158" y="34" font-size="12" font-weight="500" fill="#6FA8C0">Daily Breakdown</text>

  <!-- Close X icon -->
  <g id="usageCloseX">
    <circle cx="486" cy="26" r="11" fill="#FF5C7A" fill-opacity="0.12" stroke="#FF5C7A" stroke-opacity="0.55" stroke-width="1"/>
    <path d="M482 22 L490 30 M490 22 L482 30" stroke="#FF8CA1" stroke-width="1.8" stroke-linecap="round"/>
  </g>

  <!-- Daily & Monthly summary cards -->
  <rect x="28" y="52" width="224" height="66" rx="14" fill="url(#usageCardGradient)" stroke="#234057" stroke-width="1"/>
  <rect x="28" y="66" width="3" height="38" rx="1.5" fill="#22D3EE"/>
  <text x="44" y="74" font-size="10.5" font-weight="600" letter-spacing="0.8" fill="#6FA8C0">DAILY USAGE (TODAY)</text>
  <text id="dailyTotal" x="44" y="102" font-size="24" font-weight="700" fill="#22D3EE">0 B</text>

  <rect x="268" y="52" width="224" height="66" rx="14" fill="url(#usageCardGradient)" stroke="#234057" stroke-width="1"/>
  <rect x="268" y="66" width="3" height="38" rx="1.5" fill="#34D399"/>
  <text x="284" y="74" font-size="10.5" font-weight="600" letter-spacing="0.8" fill="#6FA8C0">MONTHLY USAGE</text>
  <text id="monthlyTotal" x="284" y="102" font-size="24" font-weight="700" fill="#34D399">0 B</text>

  <!-- View switch tabs & Reset button -->
  <g id="usageTabs">
    <rect id="dailyTabRect" x="28" y="130" width="105" height="30" rx="15" fill="url(#usageBtnGradient)" stroke="#00F0FF" stroke-width="1"/>
    <text x="80.5" y="149.5" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.6" fill="#FFFFFF">DAILY</text>

    <rect id="monthlyTabRect" x="143" y="130" width="115" height="30" rx="15" fill="#18222D" stroke="#2D4A63" stroke-width="1"/>
    <text x="200.5" y="149.5" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.6" fill="#88D8E6">MONTHLY</text>

    <rect id="resetUsageRect" x="392" y="130" width="100" height="30" rx="15" fill="#FF5C7A" fill-opacity="0.10" stroke="#FF5C7A" stroke-opacity="0.55" stroke-width="1"/>
    <text x="442" y="149.5" text-anchor="middle" font-size="12" font-weight="700" letter-spacing="0.6" fill="#FF8CA1">RESET</text>
  </g>

  <!-- App | Data | Date Table Container -->
  <rect x="28" y="172" width="464" height="242" rx="14" fill="#0B121A" stroke="#223447" stroke-width="1"/>
  <rect x="28" y="172" width="464" height="32" rx="14" fill="#15212E"/>
  <rect x="28" y="190" width="464" height="14" fill="#15212E"/>
  <line x1="28" y1="204.5" x2="492" y2="204.5" stroke="#FFFFFF" stroke-opacity="0.06" stroke-width="1"/>

  <!-- Column headers -->
  <text x="46" y="193" font-size="10.5" font-weight="600" letter-spacing="1" fill="#6FA8C0">APP</text>
  <text x="332" y="193" text-anchor="end" font-size="10.5" font-weight="600" letter-spacing="1" fill="#6FA8C0">DATA</text>
  <text x="474" y="193" text-anchor="end" font-size="10.5" font-weight="600" letter-spacing="1" fill="#6FA8C0">DATE</text>

  <!-- Dynamic Rows (inherit the root font-family) -->
  <g id="usageRows"></g>

  <!-- Bottom Close button -->
  <rect x="185" y="428" width="150" height="36" rx="18" fill="url(#usageBtnGradient)" stroke="#FFFFFF" stroke-opacity="0.2" stroke-width="1"/>
  <text x="260" y="451" text-anchor="middle" font-size="13" font-weight="700" letter-spacing="0.8" fill="#FFFFFF">CLOSE</text>
</svg>'''