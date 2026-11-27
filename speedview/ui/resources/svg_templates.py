"""SVG templates for the speed meter display"""

# Main speedometer SVG template
MAIN_SVG_TEMPLATE = """
<svg width="500" height="500" viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#121212" />
      <stop offset="100%" stop-color="#000000" />
    </linearGradient>

    <linearGradient id="speedArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>

    <filter id="shadowEffect">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00F0FF" flood-opacity="0.5"/>
    </filter>

    <filter id="glowEffect">
      <feGaussianBlur stdDeviation="2" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0088FF" />
      <stop offset="100%" stop-color="#0038AA" />
    </linearGradient>

    <linearGradient id="buttonHoverGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00AAFF" />
      <stop offset="100%" stop-color="#0066DD" />
    </linearGradient>

    <linearGradient id="floatButtonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#00DDFF" />
      <stop offset="100%" stop-color="#0088CC" />
    </linearGradient>
  </defs>

  <rect width="500" height="500" fill="url(#backgroundGradient)" rx="15" ry="15"/>

  <!-- Background circles -->
  <circle cx="250" cy="250" r="220" fill="none" stroke="#333" stroke-width="2" opacity="0.5"/>
  <circle cx="250" cy="250" r="210" fill="none" stroke="#222" stroke-width="1" opacity="0.3"/>
  <circle cx="250" cy="250" r="200" fill="none" stroke="#444" stroke-width="1" opacity="0.2"/>

  <!-- Meter background arc (-135 deg to +135 deg around 250,250 r=170) -->
  <path d="M 129.8 370.2 A 170 170 0 1 1 370.2 370.2" fill="none" stroke="#333" stroke-width="20" stroke-linecap="round" opacity="0.3"/>

  <!-- Active speed arc -->
  <path id="activeArc" d="" fill="none" stroke="url(#speedArcGradient)" stroke-width="20" stroke-linecap="round" opacity="0.85" filter="url(#glowEffect)"/>

  <!-- Speed markings and labels (dynamically scaled) -->
  <g id="dialMarks" font-family="Arial, sans-serif" font-weight="bold">
    <g transform="rotate(-135 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="15" fill="#00F0FF">0</text>
    </g>
    <g transform="rotate(-90 250 250)">
      <line x1="250" y1="80" x2="250" y2="65" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="13" fill="#00F0FF" opacity="0.75">17</text>
    </g>
    <g transform="rotate(-45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="15" fill="#00F0FF">33</text>
    </g>
    <g transform="rotate(0 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="15" fill="#00F0FF">50</text>
    </g>
    <g transform="rotate(45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="15" fill="#00F0FF">67</text>
    </g>
    <g transform="rotate(90 250 250)">
      <line x1="250" y1="80" x2="250" y2="65" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="13" fill="#00F0FF" opacity="0.75">83</text>
    </g>
    <g transform="rotate(135 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="15" fill="#00F0FF">100</text>
    </g>
  </g>

  <!-- Needle -->
  <g id="needle" transform="rotate(-135 250 250)" filter="url(#shadowEffect)">
    <path d="M250 250 L255 125 L250 110 L245 125 Z" fill="#00F0FF"/>
    <circle cx="250" cy="250" r="12" fill="#00F0FF" opacity="0.8"/>
    <circle cx="250" cy="250" r="8" fill="#0066DD"/>
  </g>

  <circle cx="250" cy="250" r="4" fill="#ffffff"/>

  <!-- Speed value display -->
  <g id="speedDisplay">
    <text id="speedValue" x="250" y="300" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="#00F0FF" filter="url(#glowEffect)">0.00</text>
    <text id="speedUnit" x="250" y="336" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" fill="#00F0FF" opacity="0.8">Mbps</text>
    <text id="speedType" x="250" y="362" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#00F0FF" opacity="0.65">Download</text>
  </g>

  <!-- Settings button -->
  <g id="settingsIcon" transform="translate(420 50)" class="button" opacity="0.85">
    <circle cx="30" cy="30" r="20" fill="#111111" stroke="#00F0FF" stroke-width="1.5" />
    <circle cx="30" cy="30" r="15" fill="none" stroke="#00F0FF" stroke-width="1.5"/>
    <path d="M30 15 L30 10 M30 45 L30 50 M39.6 20.4 L43.3 16.7 M16.7 43.3 L20.4 39.6 M45 30 L50 30 M10 30 L5 30 M20.4 20.4 L16.7 16.7 M39.6 39.6 L43.3 43.3"
          stroke="#00F0FF" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="30" cy="30" r="3" fill="#00F0FF"/>
  </g>

  <!-- Signal strength indicator -->
  <g id="signalStrength" transform="translate(36 48)">
    <rect x="0" y="15" width="5" height="15" rx="1" fill="#00F0FF" opacity="0.3" class="signal-bar"/>
    <rect x="8" y="10" width="5" height="20" rx="1" fill="#00F0FF" opacity="0.3" class="signal-bar"/>
    <rect x="16" y="5" width="5" height="25" rx="1" fill="#00F0FF" opacity="0.3" class="signal-bar"/>
    <rect x="24" y="0" width="5" height="30" rx="1" fill="#00F0FF" opacity="0.3" class="signal-bar"/>
  </g>

  <!-- Real connection status & interface metadata -->
  <text id="connectionStatus" x="76" y="58" text-anchor="start" font-family="Arial, sans-serif" font-size="14" font-weight="bold" fill="#00F0FF" opacity="0.9">Checking...</text>
  <text id="networkType" x="76" y="76" text-anchor="start" font-family="Arial, sans-serif" font-size="12" fill="#00F0FF" opacity="0.75">Detecting interface...</text>
  <text id="networkMeta" x="250" y="384" text-anchor="middle" font-family="Arial, sans-serif" font-size="11" fill="#88D8E6" opacity="0.75"></text>

  <!-- Test Network button -->
  <g id="testButtonGroup" class="interactive-button">
    <rect id="testButton" x="175" y="400" width="150" height="40" rx="20" fill="url(#buttonGradient)" class="button" stroke="#00F0FF" stroke-width="1" opacity="0.9"/>
    <text x="250" y="425" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white">TEST NETWORK</text>
  </g>

  <!-- Float button -->
  <g id="floatButtonGroup" class="interactive-button">
    <rect id="floatButton" x="50" y="400" width="100" height="40" rx="20" fill="url(#floatButtonGradient)" class="button" stroke="#00F0FF" stroke-width="1" opacity="0.9"/>
    <text x="100" y="425" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white">FLOAT</text>
  </g>

  <!-- History button -->
  <g id="historyButtonGroup" class="interactive-button">
    <rect id="historyButton" x="350" y="400" width="100" height="40" rx="20" fill="url(#buttonGradient)" class="button" stroke="#00F0FF" stroke-width="1" opacity="0.9"/>
    <text x="400" y="425" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white">HISTORY</text>
  </g>
</svg>
"""

# Floating mode SVG template
FLOATING_SVG_TEMPLATE = """
<svg width="250" height="80" viewBox="0 0 250 80" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="darkGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0D1A26" />
      <stop offset="100%" stop-color="#000A14" />
    </linearGradient>

    <linearGradient id="speedTextGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00FFAA" />
      <stop offset="100%" stop-color="#00AA88" />
    </linearGradient>

    <filter id="glow">
      <feGaussianBlur stdDeviation="2" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <filter id="shadow">
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#00FF8F" flood-opacity="0.3"/>
    </filter>
  </defs>

  <g transform="translate(0, 0)">
    <rect width="250" height="80" rx="15" ry="15" fill="url(#darkGradient)" filter="url(#shadow)" />
    <line x1="10" y1="20" x2="240" y2="20" stroke="#00FF8F" stroke-width="1" opacity="0.2" />
    <line x1="10" y1="60" x2="240" y2="60" stroke="#00FF8F" stroke-width="1" opacity="0.2" />

    <!-- Speed value -->
    <text id="speedValue" x="60" y="45" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="url(#speedTextGradient)" text-anchor="middle" filter="url(#glow)">0.0</text>
    <text id="speedUnit" x="60" y="65" font-family="Arial, sans-serif" font-size="14" fill="#00FF8F" text-anchor="middle" opacity="0.8">Mbps</text>

    <!-- Signal strength bars -->
    <g transform="translate(130, 30)">
      <rect x="0" y="10" width="5" height="10" rx="2" fill="#222222" opacity="0.4"/>
      <rect x="10" y="5" width="5" height="15" rx="2" fill="#222222" opacity="0.6"/>
      <rect x="20" y="0" width="5" height="20" rx="2" fill="#222222" opacity="0.8"/>
      <rect x="30" y="-5" width="5" height="25" rx="2" fill="#222222" opacity="0.3"/>
    </g>

    <!-- Real connection info -->
    <text id="connectionType" x="195" y="36" font-family="Arial, sans-serif" font-size="13" fill="#00FF8F" text-anchor="middle">--</text>
    <text id="connectionBand" x="195" y="54" font-family="Arial, sans-serif" font-size="10" fill="#00FF8F" text-anchor="middle" opacity="0.75"></text>

    <!-- Expand button -->
    <g id="expandButton" class="button" transform="translate(20, 20)">
      <circle cx="0" cy="0" r="8" fill="#0D1A26" stroke="#00FF8F" stroke-width="1" opacity="0.8" />
      <path d="M-3,0 L3,0 M0,-3 L0,3" stroke="#00FF8F" stroke-width="1.5" />
    </g>

    <!-- Close button -->
    <g id="closeButton" class="button" transform="translate(230, 20)">
      <circle cx="0" cy="0" r="8" fill="#0D1A26" stroke="#00FF8F" stroke-width="1" opacity="0.8" />
      <path d="M-4,-4 L4,4 M-4,4 L4,-4" stroke="#00FF8F" stroke-width="1.5" />
    </g>
  </g>
</svg>
"""

SETTINGS_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="iconGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <circle cx="16" cy="16" r="14" fill="none" stroke="url(#iconGradient)" stroke-width="2" opacity="0.8" />
  <path d="M16 7 L16 9 M16 23 L16 25 M7 16 L9 16 M23 16 L25 16 M9 9 L11 11 M21 21 L23 23 M9 23 L11 21 M21 9 L23 7"
        stroke="url(#iconGradient)" stroke-width="2" stroke-linecap="round" />
  <circle cx="16" cy="16" r="6" fill="none" stroke="url(#iconGradient)" stroke-width="1.5" />
  <circle cx="16" cy="16" r="2" fill="url(#iconGradient)" filter="url(#glow)" />
</svg>
"""

NOTIFICATION_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="notifyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  <path d="M16 4 C20 4, 24 8, 24 16 L24 22 L26 26 L6 26 L8 22 L8 16 C8 8, 12 4, 16 4 Z"
        fill="none" stroke="url(#notifyGradient)" stroke-width="1.5" />
  <path d="M16 26 L16 30" stroke="url(#notifyGradient)" stroke-width="1.5" stroke-linecap="round" />
  <circle cx="24" cy="8" r="4" fill="url(#notifyGradient)" filter="url(#glow)"/>
</svg>
"""

HISTORY_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="historyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>
  </defs>
  <circle cx="16" cy="16" r="14" fill="none" stroke="url(#historyGradient)" stroke-width="2" />
  <path d="M16 16 L16 8" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" />
  <path d="M16 16 L22 20" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" />
  <path d="M5 10 A12 12 0 0 1 10 5" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" fill="none" />
  <path d="M3 10 L5 7 L8 10" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" fill="none" />
</svg>
"""

TEST_NETWORK_SVG = '''<svg width="300" height="340" viewBox="0 0 300 340" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="backgroundGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#121212" />
      <stop offset="100%" stop-color="#000000" />
    </linearGradient>
    <linearGradient id="speedArcGradient" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>
    <filter id="shadowEffect">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00F0FF" flood-opacity="0.5"/>
    </filter>
    <filter id="glowEffect">
      <feGaussianBlur stdDeviation="2" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0088FF" />
      <stop offset="100%" stop-color="#0038AA" />
    </linearGradient>
  </defs>
  <rect x="10" y="10" width="280" height="320" fill="url(#backgroundGradient)" stroke="#333" stroke-width="2" rx="10" ry="10" filter="url(#shadowEffect)"/>
  <rect x="10" y="10" width="280" height="40" fill="url(#backgroundGradient)" stroke="none" rx="10" ry="10"/>
  <text x="150" y="35" font-family="Arial" font-size="16" fill="#00F0FF" text-anchor="middle" filter="url(#glowEffect)">Network Test</text>
  <text id="testTitle" x="150" y="75" font-family="Arial" font-size="17" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Ready to test</text>
  <circle cx="150" cy="120" r="38" fill="none" stroke="#222" stroke-width="8"/>
  <path d="M150,82 A38,38 0 0,1 185,107" stroke="url(#speedArcGradient)" stroke-width="8" fill="none" filter="url(#glowEffect)">
    <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 150 120" to="360 150 120" dur="2s" repeatCount="indefinite"/>
  </path>
  <path d="M185,133 A38,38 0 0,1 163,156" stroke="url(#speedArcGradient)" stroke-width="8" fill="none" opacity="0.7" filter="url(#glowEffect)">
    <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 150 120" to="360 150 120" dur="2s" repeatCount="indefinite"/>
  </path>
  <text id="testStatus" x="150" y="182" font-family="Arial" font-size="13" fill="#AAAAAA" text-anchor="middle">Waiting to start...</text>
  <rect x="50" y="195" width="200" height="80" fill="#1E1E1E" stroke="#333" stroke-width="1" rx="8" ry="8"/>
  <text x="70" y="220" font-family="Arial" font-size="14" font-weight="bold" fill="#FFFFFF" text-anchor="start">Download:</text>
  <text id="downloadSpeed" x="230" y="220" font-family="Arial" font-size="14" fill="#00F0FF" filter="url(#glowEffect)" text-anchor="end">0.00 Mbps</text>
  <rect x="70" y="226" width="160" height="4" fill="#222" rx="2" ry="2"/>
  <rect id="downloadBar" x="70" y="226" width="0" height="4" fill="url(#speedArcGradient)" rx="2" ry="2"/>
  <text x="70" y="250" font-family="Arial" font-size="14" font-weight="bold" fill="#FFFFFF" text-anchor="start">Upload:</text>
  <text id="uploadSpeed" x="230" y="250" font-family="Arial" font-size="14" fill="#00F0FF" filter="url(#glowEffect)" text-anchor="end">0.00 Mbps</text>
  <rect x="70" y="256" width="160" height="4" fill="#222" rx="2" ry="2"/>
  <rect id="uploadBar" x="70" y="256" width="0" height="4" fill="url(#speedArcGradient)" rx="2" ry="2"/>
  <rect x="75" y="290" width="150" height="36" fill="url(#buttonGradient)" stroke="none" rx="18" ry="18" filter="url(#shadowEffect)"/>
  <text x="150" y="313" font-family="Arial" font-size="14" fill="#FFFFFF" font-weight="bold" text-anchor="middle">CLOSE</text>
</svg>'''