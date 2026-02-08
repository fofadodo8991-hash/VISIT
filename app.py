import httpx
import time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json
import threading
from flask import Flask, request, jsonify, render_template_string
import asyncio
import sys
import os
import itertools
from datetime import datetime

# ================= إعدادات النظام =================
sys.setrecursionlimit(20000)

app = Flask(__name__)

# إعدادات الهجوم
TARGET_VISITS = 1000       # عدد الزوار للطلب الواحد
CONCURRENCY = 500          # سرعة التنفيذ (عدد الاتصالات المتزامنة)
TOKEN_VALIDITY = 5 * 3600  # تحديث التوكين كل 5 ساعات

# إعدادات BOOM (كل ساعة لمدة أسبوع)
BOOM_INTERVAL = 3600       
BOOM_DURATION = 7 * 24 * 3600 

# ملفات التخزين
TOKENS_FILE = "tokens.json"
BOOM_FILE = "boom_tasks.json"
PROTECTED_FILE = "protected.json"

# ================= قوائم الحسابات =================
ACCOUNTS_LIST_TEXT = """
4322227808:KIRAEH5DKKMZP-CORTEX_TEAM
4322227804:KIRALAPBTZLMF-CORTEX_TEAM
4322227812:KIRAIYTYPNZ6P-CORTEX_TEAM
4322227816:KIRANSTGVMVXL-CORTEX_TEAM
4322227806:KIRABGCX2SJA1-CORTEX_TEAM
4322227805:KIRAV1RMRPD9B-CORTEX_TEAM
4322227807:KIRAJBSSBNMRR-CORTEX_TEAM
4322227859:KIRA8IEODFTJD-CORTEX_TEAM
4322227851:KIRAUEJNGNCWI-CORTEX_TEAM
4322227852:KIRAKYD2NOMYI-CORTEX_TEAM
4322227809:KIRAR470XWKWS-CORTEX_TEAM
4322227856:KIRARLBWNOQ66-CORTEX_TEAM
4322227850:KIRASK9AKQLJA-CORTEX_TEAM
4322227854:KIRAWRYARET55-CORTEX_TEAM
4322230168:KIRAU7IMJ8VTQ-CORTEX_TEAM
4322230157:KIRAACA0AY7V0-CORTEX_TEAM
4322230158:KIRANHH0TODFO-CORTEX_TEAM
4322230086:KIRAYU6ZOSGZ6-CORTEX_TEAM
4322230084:KIRA759L1A1MR-CORTEX_TEAM
4322230156:KIRA6HW3UX8AW-CORTEX_TEAM
4322230087:KIRA24L0HDDN1-CORTEX_TEAM
4322230092:KIRANNKFBZWKW-CORTEX_TEAM
4322230085:KIRAHKGC8DUKX-CORTEX_TEAM
4322230088:KIRAVQUKRUEJ6-CORTEX_TEAM
4322230093:KIRA443JX1D5M-CORTEX_TEAM
4322230161:KIRATZ8BJ1PUO-CORTEX_TEAM
4322230155:KIRANEWZVGEOP-CORTEX_TEAM
4322230096:KIRA8XXXX6ZEH-CORTEX_TEAM
4322230094:KIRAAPBRRLEYV-CORTEX_TEAM
4322230170:KIRASSY1E9CT1-CORTEX_TEAM
4322230160:KIRA0FZ8ILA0I-CORTEX_TEAM
4322230169:KIRAEWKMGU8OV-CORTEX_TEAM
4322230091:KIRACK8LVQAKS-CORTEX_TEAM
4322230208:KIRA2DKYD2TOY-CORTEX_TEAM
4322230517:KIRA5P4OSWRWE-CORTEX_TEAM
4322230519:KIRA1ONP0HADV-CORTEX_TEAM
4322230518:KIRA7FPWWCZSJ-CORTEX_TEAM
4322230515:KIRACRHL0OEWO-CORTEX_TEAM
4322230521:KIRAXOLDZNLDL-CORTEX_TEAM
4322230520:KIRAVFY6BKP5T-CORTEX_TEAM
4322230529:KIRAUC13GWBMW-CORTEX_TEAM
4322230516:KIRAFSH7LXX8U-CORTEX_TEAM
4322230576:KIRAEJFIBRSZT-CORTEX_TEAM
4322230579:KIRAVHLM13ECH-CORTEX_TEAM
4322230570:KIRAMRF7DCELW-CORTEX_TEAM
4322230586:KIRA30RVQDNOW-CORTEX_TEAM
4322230578:KIRADNZ1IBKEC-CORTEX_TEAM
4322230592:KIRAV1EVM9DRY-CORTEX_TEAM
4322230577:KIRAK3SVINXU8-CORTEX_TEAM
4322230591:KIRAUTRSI97FP-CORTEX_TEAM
4322230590:KIRALXOGGNJCW-CORTEX_TEAM
4322230575:KIRANVBEXFKTE-CORTEX_TEAM
4322230647:KIRACXVX4OG7O-CORTEX_TEAM
4322230657:KIRAOVT4XPIGN-CORTEX_TEAM
4322232191:KIRAWJRBCKJVS-CORTEX_TEAM
4322232204:KIRAXCQAW140V-CORTEX_TEAM
4322232203:KIRAWNXBW9I8C-CORTEX_TEAM
4322232193:KIRAI3LWDTUKZ-CORTEX_TEAM
4322232188:KIRACE6WU2KEY-CORTEX_TEAM
4322232207:KIRAEWTRXFWS0-CORTEX_TEAM
4322232205:KIRATLXL3WZWP-CORTEX_TEAM
4322232206:KIRAKJRKZF6CA-CORTEX_TEAM
4322232228:KIRAQQNYWW152-CORTEX_TEAM
4322232230:KIRAD2N4VVOI4-CORTEX_TEAM
4322232231:KIRACWYNLYPAZ-CORTEX_TEAM
4322232245:KIRARFRJVBMQA-CORTEX_TEAM
4322232244:KIRARHMBQJOIR-CORTEX_TEAM
4322232256:KIRAGLXSRPETR-CORTEX_TEAM
4322232257:KIRAT6AK2DBZN-CORTEX_TEAM
4322232258:KIRAYCC1PMCMB-CORTEX_TEAM
4322232286:KIRAPJS5RQGRM-CORTEX_TEAM
4322232270:KIRACUZ0F6K3E-CORTEX_TEAM
4322232296:KIRAXONWDN2GL-CORTEX_TEAM
4322232295:KIRAXKSYPTS0L-CORTEX_TEAM
4322233849:KIRAG8OZZC2FH-CORTEX_TEAM
4322233874:KIRASFHP8LKSO-CORTEX_TEAM
4322233872:KIRATVQRHPZ7A-CORTEX_TEAM
4322233869:KIRA2JOCB17PJ-CORTEX_TEAM
4322233901:KIRAXD9CRJW91-CORTEX_TEAM
4322233898:KIRA9XYPWCTED-CORTEX_TEAM
4322233875:KIRAFSSGBORTO-CORTEX_TEAM
4322233879:KIRAGHRUJLOXL-CORTEX_TEAM
4322233900:KIRAVGSXTETL8-CORTEX_TEAM
4322233870:KIRA6FGDWIOGL-CORTEX_TEAM
4322233876:KIRA1PDUPGJWY-CORTEX_TEAM
4322233902:KIRARXIV6UQHD-CORTEX_TEAM
4322233942:KIRAYV4ZVW03Y-CORTEX_TEAM
4322233899:KIRAYBJF7NZHL-CORTEX_TEAM
4322233958:KIRAYGBTPQKDK-CORTEX_TEAM
4322233897:KIRAE560YVQH7-CORTEX_TEAM
4322233971:KIRA91TOHOQ01-CORTEX_TEAM
4322233972:KIRAKOPXH7INU-CORTEX_TEAM
4322233970:KIRAKWDDBLVHS-CORTEX_TEAM
4322233993:KIRAUE8CQTMQV-CORTEX_TEAM
4322241387:KIRA8ENOD8CRQ-CORTEX_TEAM
4322241383:KIRAXU1UGUHUD-CORTEX_TEAM
4322241388:KIRADELXVPVEE-CORTEX_TEAM
4322241465:KIRADKPQ8GRJY-CORTEX_TEAM
4322241382:KIRA6ZO4CZZWE-CORTEX_TEAM
4322241432:KIRA0O0FF0HA7-CORTEX_TEAM
4322241385:KIRAFOTENOCIU-CORTEX_TEAM
4322241416:KIRADJOHYGYMT-CORTEX_TEAM
"""

IDENTITY_ACCOUNTS_LIST = [
  {"uid": 4321971692, "password": "XC3R_V6UEE_XC3_TOP_ONE_6SKGJ"},
  {"uid": 4321971698, "password": "XC3R_5K9Z0_XC3_TOP_ONE_2UTHX"},
  {"uid": 4321971703, "password": "XC3R_H1P2E_XC3_TOP_ONE_J6K7D"},
  {"uid": 4321971972, "password": "XC3R_SXGNZ_XC3_TOP_ONE_097Y8"},
  {"uid": 4321971979, "password": "XC3R_37738_XC3_TOP_ONE_QU98J"},
  {"uid": 4321972052, "password": "XC3R_8FYDN_XC3_TOP_ONE_5ULEL"},
  {"uid": 4321972188, "password": "XC3R_0VS8T_XC3_TOP_ONE_P4YYU"},
  {"uid": 4321972241, "password": "XC3R_0L0YH_XC3_TOP_ONE_3ZKDK"},
  {"uid": 4321972285, "password": "XC3R_60OGS_XC3_TOP_ONE_HBA6T"},
  {"uid": 4321972471, "password": "XC3R_9LKH5_XC3_TOP_ONE_GY984"},
  {"uid": 4321972527, "password": "XC3R_YR0TG_XC3_TOP_ONE_NIKNQ"},
  {"uid": 4321972617, "password": "XC3R_NQ67I_XC3_TOP_ONE_MGUIT"}
]

# ================= متغيرات الذاكرة =================
VISIT_ACCOUNTS = {}
jwt_tokens = {}
token_db = {}
client = None
loop_instance = None
background_tasks = {}    
protected_users = set()  
boom_data = {}           
last_token_update_time = "Not yet"

def load_accounts():
    accs = {}
    lines = ACCOUNTS_LIST_TEXT.strip().split('\n')
    for line in lines:
        line = line.strip()
        if ":" in line:
            parts = line.split(":", 1)
            if len(parts) == 2:
                accs[parts[0].strip()] = parts[1].strip()
    return accs

VISIT_ACCOUNTS = load_accounts()

# ================= التشفير (AES) =================
key = bytes([89, 103, 38, 116, 99, 37, 68, 69, 117, 104, 54, 37, 90, 99, 94, 56])
iv = bytes([54, 111, 121, 90, 68, 114, 50, 50, 69, 51, 121, 99, 104, 106, 77, 37])

def Encrypt_ID(x):
    try:
        x = int(x)
        dec = [ '80', '81', '82', '83', '84', '85', '86', '87', '88', '89', '8a', '8b', '8c', '8d', '8e', '8f', '90', '91', '92', '93', '94', '95', '96', '97', '98', '99', '9a', '9b', '9c', '9d', '9e', '9f', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'aa', 'ab', 'ac', 'ad', 'ae', 'af', 'b0', 'b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8', 'b9', 'ba', 'bb', 'bc', 'bd', 'be', 'bf', 'c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'ca', 'cb', 'cc', 'cd', 'ce', 'cf', 'd0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8', 'd9', 'da', 'db', 'dc', 'dd', 'de', 'df', 'e0', 'e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'ea', 'eb', 'ec', 'ed', 'ee', 'ef', 'f0', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'fa', 'fb', 'fc', 'fd', 'fe', 'ff']
        xxx= [ '1','01', '02', '03', '04', '05', '06', '07', '08', '09', '0a', '0b', '0c', '0d', '0e', '0f', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '1a', '1b', '1c', '1d', '1e', '1f', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '2a', '2b', '2c', '2d', '2e', '2f', '30', '31', '32', '33', '34', '35', '36', '37', '38', '39', '3a', '3b', '3c', '3d', '3e', '3f', '40', '41', '42', '43', '44', '45', '46', '47', '48', '49', '4a', '4b', '4c', '4d', '4e', '4f', '50', '51', '52', '53', '54', '55', '56', '57', '58', '59', '5a', '5b', '5c', '5d', '5e', '5f', '60', '61', '62', '63', '64', '65', '66', '67', '68', '69', '6a', '6b', '6c', '6d', '6e', '6f', '70', '71', '72', '73', '74', '75', '76', '77', '78', '79', '7a', '7b', '7c', '7d', '7e', '7f']
        x= x/128 
        if x>128:
            x =x/128
            if x >128:
                x= x/128
                if x>128:
                    x= x/128
                    strx= int(x)
                    y= (x-int(strx))*128
                    stry =str(int(y))
                    z = (y-int(stry))*128
                    strz =str(int(z))
                    n =(z-int(strz))*128
                    strn=str(int(n))
                    m=(n-int(strn))*128
                    return dec[int(m)]+dec[int(n)]+dec[int(z)]+dec[int(y)]+xxx[int(x)]
                else:
                    strx= int(x)
                    y= (x-int(strx))*128
                    stry =str(int(y))
                    z = (y-int(stry))*128
                    strz =str(int(z))
                    n =(z-int(strz))*128
                    strn=str(int(n))
                    return dec[int(n)]+dec[int(z)]+dec[int(y)]+xxx[int(x)]
    except: return "error"
    return "error"

def encrypt_api(plain_text):
    plain_text = bytes.fromhex(plain_text)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    cipher_text = cipher.encrypt(pad(plain_text, AES.block_size))
    return cipher_text.hex()

# ================= إدارة البيانات (التخزين والاسترجاع) =================

def load_data_from_files():
    global token_db, protected_users, boom_data
    if os.path.exists(TOKENS_FILE):
        try:
            with open(TOKENS_FILE, 'r') as f: token_db = json.load(f)
        except: token_db = {}
    
    if os.path.exists(PROTECTED_FILE):
        try:
            with open(PROTECTED_FILE, 'r') as f: 
                protected_list = json.load(f)
                protected_users = set(protected_list)
        except: protected_users = set()

    if os.path.exists(BOOM_FILE):
        try:
            with open(BOOM_FILE, 'r') as f: boom_data = json.load(f)
        except: boom_data = {}

def save_persistent_data():
    try:
        with open(TOKENS_FILE, 'w') as f: json.dump(token_db, f)
        with open(PROTECTED_FILE, 'w') as f: json.dump(list(protected_users), f)
        with open(BOOM_FILE, 'w') as f: json.dump(boom_data, f)
    except Exception as e:
        print(f"[ERROR] Saving data: {e}")

# ================= إدارة التوكينات (خلفية) =================

async def fetch_token(uid, password):
    url = f"http://82.25.115.96:5003/GeneRate-Jwt?Uid={uid}&Pw={password}"
    try:
        res = await client.get(url, timeout=15.0)
        if res.status_code == 200 and len(res.text) > 20:
            return str(uid), res.text.strip()
    except: pass
    return str(uid), None

async def manage_tokens():
    global last_token_update_time
    current_time = time.time()
    to_update = []
    
    for uid, pw in VISIT_ACCOUNTS.items():
        uid = str(uid)
        if uid in token_db:
            data = token_db[uid]
            if (current_time - data.get('time', 0)) < TOKEN_VALIDITY:
                jwt_tokens[uid] = data['token']
                continue
        to_update.append((uid, pw))

    for acc in IDENTITY_ACCOUNTS_LIST:
        uid = str(acc['uid'])
        if uid not in token_db or (current_time - token_db[uid].get('time', 0)) >= TOKEN_VALIDITY:
            to_update.append((uid, acc['password']))
        else:
            jwt_tokens[uid] = token_db[uid]['token']

    if to_update:
        print(f"[SYSTEM] REFRESHING {len(to_update)} TOKENS...")
        batch_size = 50
        for i in range(0, len(to_update), batch_size):
            batch = to_update[i:i+batch_size]
            tasks = [fetch_token(u, p) for u, p in batch]
            results = await asyncio.gather(*tasks)
            for uid, token in results:
                if token:
                    jwt_tokens[uid] = token
                    token_db[uid] = {'token': token, 'time': time.time()}
            save_persistent_data() 
            await asyncio.sleep(1.0)
    
    last_token_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[SYSTEM] TOKENS READY: {len(jwt_tokens)} at {last_token_update_time}")

async def token_maintainer():
    while True:
        await manage_tokens()
        await asyncio.sleep(TOKEN_VALIDITY)

# ================= وظائف الإرسال (Async) =================

async def send_visit(target_payload, uid):
    if uid not in jwt_tokens: return False
    url = "https://clientbp.common.ggbluefox.com/GetPlayerPersonalShow"
    headers = {
        "Authorization": f"Bearer {jwt_tokens.get(uid)}",
        "X-Unity-Version": "2018.4.11f1",
        "X-GA": "v1 1",
        "ReleaseVersion": "ob52",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-N975F Build/PI)",
        "Host": "clientbp.common.ggbluefox.com",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br",
    }
    try:
        res = await client.post(url, headers=headers, data=target_payload)
        return res.status_code == 200
    except: return False

async def perform_attack(target_uid, count=TARGET_VISITS):
    eid = Encrypt_ID(target_uid)
    if eid == "error": return 0

    eapi = encrypt_api(f"08{eid}1007")
    payload = bytes.fromhex(eapi)
    
    all_ready_uids = list(jwt_tokens.keys())
    if not all_ready_uids: return 0

    selected_uids = all_ready_uids[:100] 
    account_cycler = itertools.cycle(selected_uids)
    
    tasks = []
    for _ in range(count):
        uid = next(account_cycler)
        tasks.append(send_visit(payload, uid))
    
    sent_count = 0
    chunk_size = CONCURRENCY
    for i in range(0, len(tasks), chunk_size):
        chunk = tasks[i:i+chunk_size]
        results = await asyncio.gather(*chunk)
        sent_count += sum(1 for r in results if r)
        await asyncio.sleep(0.1)
    
    return sent_count

# ================= BOOM Task =================

async def auto_sender_task(target_uid, start_timestamp):
    print(f"[BOOM] STARTED Task for {target_uid}")
    while True:
        current_ts = time.time()
        if current_ts - start_timestamp > BOOM_DURATION:
            print(f"[BOOM] EXPIRED Task for {target_uid}")
            if target_uid in background_tasks: del background_tasks[target_uid]
            if target_uid in boom_data: del boom_data[target_uid]
            save_persistent_data()
            break
        
        try:
            print(f"[BOOM] Sending batch to {target_uid}...")
            await perform_attack(target_uid, count=1000)
            await asyncio.sleep(BOOM_INTERVAL) 
        except asyncio.CancelledError:
            print(f"[BOOM] STOPPED Task for {target_uid}")
            break
        except Exception as e:
            print(f"[BOOM] Error for {target_uid}: {e}")
            await asyncio.sleep(60)

async def restore_boom_tasks():
    print("[SYSTEM] Restoring BOOM tasks...")
    count = 0
    for uid, start_time in list(boom_data.items()):
        if time.time() - start_time < BOOM_DURATION:
            task = loop_instance.create_task(auto_sender_task(uid, start_time))
            background_tasks[uid] = task
            count += 1
        else:
            del boom_data[uid]
    save_persistent_data()
    print(f"[SYSTEM] Restored {count} active tasks.")

# ================= لوحة التحكم =================
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XC3 API PANEL</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
        :root { --primary: #00ff41; --bg: #0d0d0d; --card-bg: #1a1a1a; --text: #e0e0e0; --danger: #ff3333; }
        body { background-color: var(--bg); color: var(--text); font-family: 'Share Tech Mono', monospace; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }
        .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid var(--primary); padding-bottom: 10px; width: 100%; max-width: 800px; }
        h1 { margin: 0; color: var(--primary); text-shadow: 0 0 10px var(--primary); font-size: 2.5em; }
        .subtitle { font-size: 0.9em; opacity: 0.7; letter-spacing: 2px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; width: 100%; max-width: 1000px; }
        .card { background: var(--card-bg); border: 1px solid #333; padding: 20px; border-radius: 5px; position: relative; overflow: hidden; transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); border-color: var(--primary); }
        .card::before { content: ''; position: absolute; top: 0; left: 0; width: 4px; height: 100%; background: var(--primary); }
        .card-title { font-size: 1.2em; margin-bottom: 15px; color: var(--primary); }
        .stat-value { font-size: 2.5em; font-weight: bold; }
        .stat-label { font-size: 0.8em; opacity: 0.6; }
        .status-badge { display: inline-block; padding: 5px 10px; background: rgba(0, 255, 65, 0.1); color: var(--primary); border: 1px solid var(--primary); border-radius: 3px; font-size: 0.8em; margin-top: 10px; }
        .footer { margin-top: 50px; font-size: 0.8em; opacity: 0.4; }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(0, 255, 65, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(0, 255, 65, 0); } 100% { box-shadow: 0 0 0 0 rgba(0, 255, 65, 0); } }
        .live-dot { width: 10px; height: 10px; background: var(--primary); border-radius: 50%; display: inline-block; margin-right: 5px; animation: pulse 2s infinite; }
        .card.danger::before { background: var(--danger); }
        .card.danger .card-title { color: var(--danger); }
    </style>
    <script> setTimeout(() => window.location.reload(), 30000); </script>
</head>
<body>
    <div class="header">
        <h1>XC3 API PANEL</h1>
        <div class="subtitle">SYSTEM OPERATIONAL | ENCRYPTED CONNECTION</div>
    </div>
    <div class="dashboard-grid">
        <div class="card">
            <div class="card-title">ACTIVE TOKENS</div>
            <div class="stat-value">{{ token_count }}</div>
            <div class="stat-label">Ready for Attack</div>
            <div class="status-badge"><span class="live-dot"></span>Updated: {{ last_update }}</div>
        </div>
        <div class="card">
            <div class="card-title">BOOM TASKS</div>
            <div class="stat-value">{{ task_count }}</div>
            <div class="stat-label">Running Weekly Cycles</div>
            <div class="status-badge">Interval: 1 Hour</div>
        </div>
        <div class="card danger">
            <div class="card-title">PROTECTED IDS</div>
            <div class="stat-value">{{ protected_count }}</div>
            <div class="stat-label">Immune to BOOM</div>
            <div class="status-badge" style="color:var(--danger); border-color:var(--danger)">Shield Active</div>
        </div>
        <div class="card">
            <div class="card-title">SYSTEM HEALTH</div>
            <div class="stat-value">OK</div>
            <div class="stat-label">Port: 8002</div>
            <div class="status-badge">Concurrency: {{ concurrency }}</div>
        </div>
    </div>
    <div class="footer">POWERED BY CORTEX TEAM | XC3 BOT API V3.0</div>
</body>
</html>
"""

# ================= مسارات FLASK (Routes) =================

@app.route('/')
def index():
    return render_template_string(HTML_DASHBOARD, 
                                  token_count=len(jwt_tokens), 
                                  task_count=len(background_tasks),
                                  protected_count=len(protected_users),
                                  last_update=last_token_update_time,
                                  concurrency=CONCURRENCY)

# >>>>>>> التعديل الرئيسي: الرد الفوري وتنفيذ الخلفية <<<<<<<@app.route('/visit/<uid>')
def visit_one_time(uid):
    if not uid: return jsonify({"status": "error", "msg": "No UID"})
    
    if loop_instance:
        # 1. إطلاق المهمة في الخلفية (Fire and Forget)
        asyncio.run_coroutine_threadsafe(perform_attack(uid), loop_instance)
        # 2. الرد الفوري على البوت بنجاح
        return jsonify({"status": "success", "msg": "Sent"}), 200
    
    return jsonify({"status": "error", "msg": "Loop not ready"}), 500

@app.route('/add')
def add_auto():
    uid = request.args.get('id')
    if not uid: return jsonify({"status": "error"})
    if uid in protected_users: return jsonify({"status": "blocked"}), 403
    if uid in background_tasks: return jsonify({"status": "added"}), 200
    if loop_instance:
        start_time = time.time()
        boom_data[uid] = start_time
        save_persistent_data()
        task = loop_instance.create_task(auto_sender_task(uid, start_time))
        background_tasks[uid] = task
        return jsonify({"status": "added"}), 200
    return jsonify({"status": "error"}), 500

@app.route('/remov')
def remove_auto():
    uid = request.args.get('id')
    if not uid: return jsonify({"status": "error"})
    removed = False
    if uid in background_tasks:
        background_tasks[uid].cancel()
        del background_tasks[uid]
        removed = True
    if uid in boom_data:
        del boom_data[uid]
        save_persistent_data()
        removed = True
    if removed: return jsonify({"status": "removed"}), 200
    return jsonify({"status": "not_found"}), 200

@app.route('/protect')
def protect_id():
    uid = request.args.get('id')
    if not uid: return jsonify({"status": "error"})
    protected_users.add(uid)
    save_persistent_data()
    eid = Encrypt_ID(uid)
    eapi = encrypt_api(f"08{eid}1007")
    payload = bytes.fromhex(eapi)
    async def run_hide():
        tasks = [send_visit(payload, str(acc['uid'])) for acc in IDENTITY_ACCOUNTS_LIST]
        await asyncio.gather(*tasks)
    if loop_instance:
        asyncio.run_coroutine_threadsafe(run_hide(), loop_instance)
        return jsonify({"status": "protected"}), 200
    return jsonify({"status": "error"}), 500

# ================= التشغيل =================
def run_app():
    load_data_from_files()
    def loop_thread():
        global client, loop_instance
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop_instance = loop
        limits = httpx.Limits(max_keepalive_connections=CONCURRENCY, max_connections=CONCURRENCY+100)
        client = httpx.AsyncClient(limits=limits, timeout=20.0, verify=False)
        loop.run_until_complete(manage_tokens())
        loop.run_until_complete(restore_boom_tasks())
        loop.create_task(token_maintainer())
        print("[SYSTEM] EVENT LOOP STARTED.")
        loop.run_forever()
    t = threading.Thread(target=loop_thread)
    t.daemon = True
    t.start()
    
    # تم تغيير البورت إلى 8002
    print("[SYSTEM] FLASK SERVER RUNNING ON PORT 8002...")
    app.run(host='0.0.0.0', port=8002, debug=False, use_reloader=False)

if __name__ == '__main__':
    run_app()
