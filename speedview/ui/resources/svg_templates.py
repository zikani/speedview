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

    <linearGradient id="buttonGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0066FF" />
      <stop offset="100%" stop-color="#0038AA" />
    </linearGradient>

    <linearGradient id="buttonHoverGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#0088FF" />
      <stop offset="100%" stop-color="#0050CC" />
    </linearGradient>
  </defs>

  <rect width="500" height="500" fill="url(#backgroundGradient)"/>

  <circle cx="250" cy="250" r="220" fill="none" stroke="#333" stroke-width="2" opacity="0.5"/>

  <path d="M80 250 A170 170 0 0 1 420 250" fill="none" stroke="#333" stroke-width="20" stroke-linecap="round" opacity="0.3"/>

  <path id="activeArc" d="M80 250 A170 170 0 0 1 250 80" fill="none" stroke="url(#speedArcGradient)" stroke-width="20" stroke-linecap="round" opacity="0.8" stroke-dasharray="0, 534" style="animation: arcFill 1.5s ease-out forwards"/>

  <g font-family="Arial" font-weight="bold">
    <g transform="rotate(-135 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">0</text>
    </g>

    <g transform="rotate(-105 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">5</text>
    </g>

    <g transform="rotate(-75 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">10</text>
    </g>

    <g transform="rotate(-45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">20</text>
    </g>

    <g transform="rotate(-15 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">30</text>
    </g>

    <g transform="rotate(15 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">50</text>
    </g>

    <g transform="rotate(45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">75</text>
    </g>

    <g transform="rotate(75 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">100</text>
    </g>
  </g>

  <g id="needle" transform="rotate(-135 250 250)" filter="url(#shadowEffect)">
    <path d="M250 250 L255 120 L250 110 L245 120 Z" fill="#00F0FF"/>
    <circle cx="250" cy="250" r="10" fill="#00F0FF"/>
  </g>

  <circle cx="250" cy="250" r="5" fill="#fff"/>

  <text id="speedValue" x="250" y="300" text-anchor="middle" font-family="Arial" font-size="48" font-weight="bold" fill="#00F0FF">0.00</text>
  <text x="250" y="340" text-anchor="middle" font-family="Arial" font-size="20" fill="#00F0FF" opacity="0.7">Mbps</text>

  <g id="settingsIcon" transform="translate(420 80)" class="button" opacity="0.8">
    <circle cx="30" cy="30" r="15" fill="none" stroke="#00F0FF" stroke-width="2"/>
    <path d="M30 15 L30 10 M30 45 L30 50 M39.6 20.4 L43.3 16.7 M16.7 43.3 L20.4 39.6 M45 30 L50 30 M10 30 L5 30 M20.4 20.4 L16.7 16.7 M39.6 39.6 L43.3 43.3"
          stroke="#00F0FF" stroke-width="2" stroke-linecap="round"/>
    <circle cx="30" cy="30" r="3" fill="#00F0FF"/>
  </g>

  <g transform="translate(0 10)">
    <path d="M250 360 L240 350 M250 360 L260 350 M250 360 L250 390" stroke="#00F0FF" stroke-width="3" fill="none"/>
  </g>

  <g transform="translate(50 50)">
    <path d="M20 10 L20 30 M30 5 L30 30 M40 0 L40 30" stroke="#00F0FF" stroke-width="3" fill="none" opacity="0.7"/>
  </g>

  <text id="connectionStatus" x="460" y="70" text-anchor="end" font-family="Arial" font-size="16" fill="#00F0FF" opacity="0.7">Connected</text>

  <!-- Signal Strength Indicator -->
  <g id="signalStrength" transform="translate(380 70)">
    <rect x="0" y="0" width="5" height="15" rx="1" fill="#333333"/>
    <rect x="8" y="-5" width="5" height="20" rx="1" fill="#333333"/>
    <rect x="16" y="-10" width="5" height="25" rx="1" fill="#333333"/>
    <rect x="24" y="-15" width="5" height="30" rx="1" fill="#333333"/>
  </g>

  <rect id="testButton" x="175" y="400" width="150" height="40" rx="20" fill="url(#buttonGradient)" class="button"/>
  <text x="250" y="427" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="white">Test Network</text>

  <rect id="floatButton" x="50" y="400" width="100" height="40" rx="20" fill="url(#buttonGradient)" class="button"/>
  <text x="100" y="427" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="white">Float</text>

  <style>
    <![CDATA[
      .button {
        cursor: pointer;
        transition: all 0.3s ease;
      }
      .button:hover {
        fill: url(#buttonHoverGradient);
        transform: translateY(-2px);
        opacity: 1 !important;
      }
      .button:active {
        transform: translateY(1px);
      }
      #speedValue {
        transition: all 0.5s ease-out;
      }
      #settingsIcon:hover {
        transform: translate(420px, 80px) rotate(30deg);
        opacity: 1 !important;
      }
    ]]>
  </style>
</svg>
"""

# Floating mode SVG template
FLOATING_SVG_TEMPLATE = """
<svg width="250" height="80" viewBox="0 0 250 80" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="darkGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#121212" />
      <stop offset="100%" stop-color="#000000" />
    </linearGradient>
    <filter id="shadow">
      <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#00FF8F" flood-opacity="0.5"/>
    </filter>
  </defs>
  
  <g transform="translate(0, 0)">
    <!-- Base shape -->
    <rect width="250" height="80" rx="10" ry="10" fill="url(#darkGradient)" filter="url(#shadow)" />
    
    <!-- Speed value -->
    <text id="speedValue" x="60" y="35" font-family="Arial, sans-serif" font-size="20" font-weight="bold" fill="#00FF8F" text-anchor="middle">54.2</text>
    <text x="60" y="55" font-family="Arial, sans-serif" font-size="14" fill="#00FF8F" text-anchor="middle">Mbps</text>
    
    <!-- Signal strength -->
    <g transform="translate(130, 30)">
      <rect x="0" y="10" width="5" height="10" rx="1" fill="#00FF8F" />
      <rect x="10" y="5" width="5" height="15" rx="1" fill="#00FF8F" />
      <rect x="20" y="0" width="5" height="20" rx="1" fill="#00FF8F" />
      <rect x="30" y="-5" width="5" height="25" rx="1" fill="#222" />
    </g>
    
    <!-- Connection type -->
    <text x="200" y="35" font-family="Arial, sans-serif" font-size="14" fill="#00FF8F" text-anchor="middle">WiFi</text>
    <text x="200" y="55" font-family="Arial, sans-serif" font-size="12" fill="#00FF8F" text-anchor="middle">5GHz</text>
    
    <text x="125" y="100" font-family="Arial, sans-serif" font-size="14" fill="#FFFFFF" text-anchor="middle">Mini Dashboard</text>
  </g>
</svg>
"""

# Add settings icon template
SETTINGS_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32">
    <circle cx="16" cy="16" r="14" fill="none" stroke="#00F0FF" stroke-width="2"/>
    <path d="M16 8 L16 24 M8 16 L24 16" stroke="#00F0FF" stroke-width="2"/>
</svg>
"""

# Add notification icon template
NOTIFICATION_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32">
    <path d="M16 4 L28 28 L16 24 L4 28 Z" fill="none" stroke="#00F0FF" stroke-width="2"/>
</svg>
"""