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

  <!-- Meter background arc -->
  <path d="M80 250 A170 170 0 0 1 420 250" fill="none" stroke="#333" stroke-width="20" stroke-linecap="round" opacity="0.3"/>

  <!-- Active speed arc -->
  <path id="activeArc" d="M80 250 A170 170 0 0 1 250 80" fill="none" stroke="url(#speedArcGradient)" stroke-width="20" stroke-linecap="round" opacity="0.8" stroke-dasharray="0, 534" filter="url(#glowEffect)" style="animation: arcFill 1.5s ease-out forwards"/>

  <!-- Speed markings and labels -->
  <g font-family="Arial, sans-serif" font-weight="bold">
    <g transform="rotate(-135 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">0</text>
    </g>

    <g transform="rotate(-105 250 250)">
      <line x1="250" y1="80" x2="250" y2="65" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">5</text>
    </g>

    <g transform="rotate(-75 250 250)">
      <line x1="250" y1="80" x2="250" y2="65" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">10</text>
    </g>

    <g transform="rotate(-45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">20</text>
    </g>

    <g transform="rotate(-15 250 250)">
      <line x1="250" y1="80" x2="250" y2="65" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">30</text>
    </g>

    <g transform="rotate(15 250 250)">
      <line x1="250" y1="80" x2="250" y2="65" stroke="#00F0FF" stroke-width="2"/>
      <text x="250" y="50" text-anchor="middle" font-size="14" fill="#00F0FF" opacity="0.7">50</text>
    </g>

    <g transform="rotate(45 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">75</text>
    </g>

    <g transform="rotate(75 250 250)">
      <line x1="250" y1="80" x2="250" y2="60" stroke="#00F0FF" stroke-width="3"/>
      <text x="250" y="50" text-anchor="middle" font-size="16" fill="#00F0FF">100</text>
    </g>
    
    <!-- Small tick marks -->
    <g transform="rotate(-120 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
    <g transform="rotate(-90 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
    <g transform="rotate(-60 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
    <g transform="rotate(-30 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
    <g transform="rotate(0 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
    <g transform="rotate(30 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
    <g transform="rotate(60 250 250)"><line x1="250" y1="80" x2="250" y2="70" stroke="#00F0FF" stroke-width="1" opacity="0.5"/></g>
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
    <text x="250" y="340" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" fill="#00F0FF" opacity="0.8">Mbps</text>
  </g>

  <!-- Settings button  -->
  <g id="settingsIcon" transform="translate(420 80)" class="button" opacity="0.8">
    <circle cx="30" cy="30" r="20" fill="#111111" stroke="#00F0FF" stroke-width="1.5" />
    <circle cx="30" cy="30" r="15" fill="none" stroke="#00F0FF" stroke-width="1.5"/>
    <path d="M30 15 L30 10 M30 45 L30 50 M39.6 20.4 L43.3 16.7 M16.7 43.3 L20.4 39.6 M45 30 L50 30 M10 30 L5 30 M20.4 20.4 L16.7 16.7 M39.6 39.6 L43.3 43.3"
          stroke="#00F0FF" stroke-width="1.5" stroke-linecap="round"/>
    <circle cx="30" cy="30" r="3" fill="#00F0FF"/>
  </g>

  <!-- Signal strength indicator with animated bars -->
  <g id="signalStrength" transform="translate(380 70)">
    <rect x="0" y="0" width="5" height="15" rx="1" fill="#00F0FF" opacity="0.3" class="signal-bar">
      <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" begin="0s" repeatCount="indefinite" />
    </rect>
    <rect x="8" y="-5" width="5" height="20" rx="1" fill="#00F0FF" opacity="0.5" class="signal-bar">
      <animate attributeName="opacity" values="0.5;1;0.5" dur="2s" begin="0.5s" repeatCount="indefinite" />
    </rect>
    <rect x="16" y="-10" width="5" height="25" rx="1" fill="#00F0FF" opacity="0.7" class="signal-bar">
      <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" begin="1s" repeatCount="indefinite" />
    </rect>
    <rect x="24" y="-15" width="5" height="30" rx="1" fill="#00F0FF" opacity="0.9" class="signal-bar">
      <animate attributeName="opacity" values="0.9;1;0.9" dur="2s" begin="1.5s" repeatCount="indefinite" />
    </rect>
  </g>

  <!-- Connection status indicator -->
  <text id="connectionStatus" x="460" y="70" text-anchor="end" font-family="Arial, sans-serif" font-size="16" fill="#00F0FF" opacity="0.8">Connected</text>

  <!-- Network type indicator -->
  <text id="networkType" x="460" y="90" text-anchor="end" font-family="Arial, sans-serif" font-size="14" fill="#00F0FF" opacity="0.6">WiFi 5GHz</text>

  <!-- Test Network button with improved design -->
  <g id="testButtonGroup" class="interactive-button">
    <rect id="testButton" x="175" y="400" width="150" height="40" rx="20" fill="url(#buttonGradient)" class="button" stroke="#00F0FF" stroke-width="1" opacity="0.9"/>
    <text x="250" y="425" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white">TEST NETWORK</text>
  </g>

  <!-- Float button with improved design -->
  <g id="floatButtonGroup" class="interactive-button">
    <rect id="floatButton" x="50" y="400" width="100" height="40" rx="20" fill="url(#floatButtonGradient)" class="button" stroke="#00F0FF" stroke-width="1" opacity="0.9"/>
    <text x="100" y="425" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white">FLOAT</text>
  </g>
  
  <!-- New History button -->
  <g id="historyButtonGroup" class="interactive-button">
    <rect id="historyButton" x="350" y="400" width="100" height="40" rx="20" fill="url(#buttonGradient)" class="button" stroke="#00F0FF" stroke-width="1" opacity="0.9"/>
    <text x="400" y="425" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="white">HISTORY</text>
  </g>

  <style>
    <![CDATA[
      @keyframes arcFill {
        from { stroke-dasharray: 0, 534; }
        to { stroke-dasharray: 267, 267; }
      }
      
      @keyframes pulse {
        0% { opacity: 0.7; }
        50% { opacity: 1; }
        100% { opacity: 0.7; }
      }
      
      .interactive-button {
        cursor: pointer;
        transition: all 0.3s ease;
      }
      
      .interactive-button:hover rect {
        fill: url(#buttonHoverGradient);
        transform: translateY(-2px);
        filter: brightness(1.2);
        opacity: 1 !important;
      }
      
      .interactive-button:active rect {
        transform: translateY(1px);
        filter: brightness(0.9);
      }
      
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
        animation: pulse 2s infinite ease-in-out;
      }
      
      #settingsIcon:hover {
        transform: translate(420px, 80px) rotate(30deg);
        opacity: 1 !important;
        filter: brightness(1.2);
      }
    ]]>
  </style>
</svg>
"""

# Floating mode SVG template with improved design
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
    <!-- Base shape with rounded corners and shadow -->
    <rect width="250" height="80" rx="15" ry="15" fill="url(#darkGradient)" filter="url(#shadow)" />
    
    <!-- Decorative line -->
    <line x1="10" y1="20" x2="240" y2="20" stroke="#00FF8F" stroke-width="1" opacity="0.2" />
    <line x1="10" y1="60" x2="240" y2="60" stroke="#00FF8F" stroke-width="1" opacity="0.2" />
    
    <!-- Speed value with gradient text -->
    <text id="speedValue" x="60" y="45" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="url(#speedTextGradient)" text-anchor="middle" filter="url(#glow)">54.2</text>
    <text x="60" y="65" font-family="Arial, sans-serif" font-size="14" fill="#00FF8F" text-anchor="middle" opacity="0.8">Mbps</text>
    
    <!-- Signal strength with animated bars -->
    <g transform="translate(130, 30)">
      <rect x="0" y="10" width="5" height="10" rx="2" fill="#00FF8F" opacity="0.4">
        <animate attributeName="opacity" values="0.4;1;0.4" dur="2s" begin="0s" repeatCount="indefinite" />
      </rect>
      <rect x="10" y="5" width="5" height="15" rx="2" fill="#00FF8F" opacity="0.6">
        <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" begin="0.5s" repeatCount="indefinite" />
      </rect>
      <rect x="20" y="0" width="5" height="20" rx="2" fill="#00FF8F" opacity="0.8">
        <animate attributeName="opacity" values="0.8;1;0.8" dur="2s" begin="1s" repeatCount="indefinite" />
      </rect>
      <rect x="30" y="-5" width="5" height="25" rx="2" fill="#00FF8F" opacity="0.3" />
    </g>
    
    <!-- Connection type with icons -->
    <g transform="translate(190, 40)">
      <!-- WiFi icon -->
      <path d="M10,15 Q20,5 30,15 Q20,25 10,15 Z" fill="none" stroke="#00FF8F" stroke-width="1.5" />
      <circle cx="20" cy="15" r="2" fill="#00FF8F" />
    </g>
    
    <!-- Connection info -->
    <text x="200" y="35" font-family="Arial, sans-serif" font-size="14" fill="#00FF8F" text-anchor="middle">WiFi</text>
    <text x="200" y="55" font-family="Arial, sans-serif" font-size="12" fill="#00FF8F" text-anchor="middle" opacity="0.7">5GHz</text>
    
    <!-- Close button -->
    <g id="closeButton" class="button" transform="translate(230, 20)">
      <circle cx="0" cy="0" r="8" fill="#0D1A26" stroke="#00FF8F" stroke-width="1" opacity="0.8" />
      <path d="M-4,-4 L4,4 M-4,4 L4,-4" stroke="#00FF8F" stroke-width="1.5" />
    </g>
    
    
  </g>
  
  <style>
    <![CDATA[
      @keyframes pulse {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
      }
      
      #speedValue {
        animation: pulse 2s infinite ease-in-out;
      }
      
      .button {
        cursor: pointer;
        transition: all 0.3s ease;
      }
      
      .button:hover {
        transform: scale(1.2);
        opacity: 1 !important;
      }
      
      .button:active {
        transform: scale(0.9);
      }
    ]]>
  </style>
</svg>
"""

# Updated settings icon
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
  
  <!-- Gear icon -->
  <path d="M16 7 L16 9 M16 23 L16 25 M7 16 L9 16 M23 16 L25 16 M9 9 L11 11 M21 21 L23 23 M9 23 L11 21 M21 9 L23 7" 
        stroke="url(#iconGradient)" stroke-width="2" stroke-linecap="round" />
  <circle cx="16" cy="16" r="6" fill="none" stroke="url(#iconGradient)" stroke-width="1.5" />
  <circle cx="16" cy="16" r="2" fill="url(#iconGradient)" filter="url(#glow)" />
  
  <style>
    <![CDATA[
      svg:hover {
        filter: brightness(1.2);
      }
    ]]>
  </style>
</svg>
"""

# Updated notification icon
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
  
  <!-- Bell shape -->
  <path d="M16 4 C20 4, 24 8, 24 16 L24 22 L26 26 L6 26 L8 22 L8 16 C8 8, 12 4, 16 4 Z" 
        fill="none" stroke="url(#notifyGradient)" stroke-width="1.5" />
  
  <!-- Bell clapper -->
  <path d="M16 26 L16 30" stroke="url(#notifyGradient)" stroke-width="1.5" stroke-linecap="round" />
  
  <!-- Notification dot -->
  <circle cx="24" cy="8" r="4" fill="url(#notifyGradient)" filter="url(#glow)">
    <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite" />
  </circle>
  
  <style>
    <![CDATA[
      svg:hover {
        filter: brightness(1.2);
      }
    ]]>
  </style>
</svg>
"""

# New history button icon
HISTORY_ICON_SVG = """
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="historyGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#00F0FF" />
      <stop offset="100%" stop-color="#0050FF" />
    </linearGradient>
    <filter id="glow">
      <feGaussianBlur stdDeviation="1" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>
  
  <!-- Clock face -->
  <circle cx="16" cy="16" r="14" fill="none" stroke="url(#historyGradient)" stroke-width="2" />
  
  <!-- Clock hands -->
  <path d="M16 16 L16 8" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" />
  <path d="M16 16 L22 20" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" />
  
  <!-- Arrow indicating history -->
  <path d="M5 10 A12 12 0 0 1 10 5" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" fill="none" />
  <path d="M3 10 L5 7 L8 10" stroke="url(#historyGradient)" stroke-width="2" stroke-linecap="round" fill="none" />
  
  <style>
    <![CDATA[
      svg:hover {
        filter: brightness(1.2);
      }
    ]]>
  </style>
</svg>
"""

TEST_NETWORK_SVG = '''<svg viewBox="0 0 300 340" xmlns="http://www.w3.org/2000/svg">
  <!-- Definitions -->
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
  <!-- Dialog Border with Dark Background -->
  <rect x="10" y="10" width="280" height="320" fill="url(#backgroundGradient)" stroke="#333" stroke-width="2" rx="10" ry="10" filter="url(#shadowEffect)"/>
  <!-- Title Bar -->
  <rect x="10" y="10" width="280" height="40" fill="url(#backgroundGradient)" stroke="none" rx="10" ry="10"/>
  <text x="150" y="35" font-family="Arial" font-size="16" fill="#00F0FF" text-anchor="middle" filter="url(#glowEffect)">Network Test</text>
  <!-- Title Label -->
  <text x="150" y="75" font-family="Arial" font-size="18" font-weight="bold" fill="#FFFFFF" text-anchor="middle">Testing Network Speed...</text>
  <!-- Animated Spinner with Gradient Effect -->
  <circle cx="150" cy="120" r="40" fill="none" stroke="#222" stroke-width="8"/>
  <!-- Animated Speed Arcs -->
  <path d="M150,80 A40,40 0 0,1 186,106" stroke="url(#speedArcGradient)" stroke-width="8" fill="none" filter="url(#glowEffect)">
    <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 150 120" to="360 150 120" dur="2s" repeatCount="indefinite"/>
  </path>
  <path d="M186,134 A40,40 0 0,1 164,158" stroke="url(#speedArcGradient)" stroke-width="8" fill="none" opacity="0.7" filter="url(#glowEffect)">
    <animateTransform attributeName="transform" attributeType="XML" type="rotate" from="0 150 120" to="360 150 120" dur="2s" repeatCount="indefinite"/>
  </path>
  <!-- Status Label -->
  <text x="150" y="185" font-family="Arial" font-size="14" fill="#AAAAAA" text-anchor="middle">Running speed test...</text>
  <!-- Speed Results Panel - Dark with edges -->
  <rect x="50" y="195" width="200" height="80" fill="rgba(30,30,30,0.7)" stroke="#333" stroke-width="1" rx="8" ry="8"/>
  <!-- Download Speed -->
  <text x="75" y="220" font-family="Arial" font-size="14" font-weight="bold" fill="#FFFFFF" text-anchor="start">Download:</text>
  <text x="225" y="220" font-family="Arial" font-size="14" fill="#00F0FF" filter="url(#glowEffect)" text-anchor="end">24.5 Mbps</text>
  <!-- Download Speed Bar -->
  <rect x="75" y="225" width="150" height="4" fill="#222" rx="2" ry="2"/>
  <rect x="75" y="225" width="95" height="4" fill="url(#speedArcGradient)" rx="2" ry="2" filter="url(#glowEffect)"/>
  <!-- Upload Speed -->
  <text x="75" y="250" font-family="Arial" font-size="14" font-weight="bold" fill="#FFFFFF" text-anchor="start">Upload:</text>
  <text x="225" y="250" font-family="Arial" font-size="14" fill="#00F0FF" filter="url(#glowEffect)" text-anchor="end">8.2 Mbps</text>
  <!-- Upload Speed Bar -->
  <rect x="75" y="255" width="150" height="4" fill="#222" rx="2" ry="2"/>
  <rect x="75" y="255" width="35" height="4" fill="url(#speedArcGradient)" rx="2" ry="2" filter="url(#glowEffect)"/>
  <!-- Close Button with Gradient -->
  <rect x="75" y="290" width="150" height="40" fill="url(#buttonGradient)" stroke="none" rx="20" ry="20" filter="url(#shadowEffect)"/>
  <text x="150" y="315" font-family="Arial" font-size="14" fill="#FFFFFF" font-weight="bold" text-anchor="middle">CLOSE</text>
</svg>'''