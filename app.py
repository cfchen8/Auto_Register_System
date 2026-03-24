"""
國小課後社團自動報名系統 - Flask 後端
對接：廍子國小 BeClass 報名頁面
https://www.beclass.com/rid=3052575698eccf04320a
"""
import json
import os
import uuid
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import atexit

from beclass_submitter import submit_beclass, BECLASS_CLUBS

# ===== 設定 =====
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支援中文 JSON 回應

_log_handlers = [logging.StreamHandler()]
if os.environ.get('FLASK_ENV') != 'production':
    os.makedirs('data', exist_ok=True)
    _log_handlers.append(logging.FileHandler('data/system.log', encoding='utf-8'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=_log_handlers
)
logger = logging.getLogger(__name__)

# ===== 排程器 =====
scheduler = BackgroundScheduler(timezone='Asia/Taipei')
scheduler.start()

def shutdown_scheduler():
    """只在主程序結束時才 shutdown"""
    if scheduler.running:
        scheduler.shutdown()

atexit.register(shutdown_scheduler)

DATA_FILE = os.environ.get('DATA_FILE', 'data/registrations.json')

# ===== 工具函式 =====
def load_data():
    """讀取報名資料"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(data):
    """儲存報名資料"""
    os.makedirs('data', exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_taiwan_id(id_number: str) -> bool:
    """驗證台灣身分證字號（簡易版）"""
    import re
    pattern = r'^[A-Z][12]\d{8}$'
    return bool(re.match(pattern, id_number.upper()))

def validate_phone(phone: str) -> bool:
    """驗證台灣手機號碼"""
    import re
    pattern = r'^09\d{8}$'
    return bool(re.match(pattern, phone))

def _update_status(records, registration_id, status, message):
    """更新報名狀態"""
    for r in records:
        if r['id'] == registration_id:
            r['status']         = status
            r['result_message'] = message
            r['executed_at']    = datetime.now().isoformat()
            break
    save_data(records)

# ===== 自動報名核心（排程器呼叫） =====
def do_auto_register(registration_id: str):
    logger.info(f"🚀 開始執行自動報名 [ID: {registration_id}]")

    records = load_data()
    record  = next((r for r in records if r['id'] == registration_id), None)

    if not record:
        logger.error(f"找不到報名記錄 [ID: {registration_id}]")
        return
    if record.get('status') != 'pending':
        logger.warning(f"狀態非 pending，略過 [ID: {registration_id}]")
        return

    result  = submit_beclass(record)
    status  = 'success' if result['success'] else 'failed'
    records = load_data()   # 重新讀取（避免競態）
    _update_status(records, registration_id, status, result['message'])

    if result['success']:
        logger.info(f"✅ 自動報名成功 [ID: {registration_id}] - {result['message']}")
    else:
        logger.error(f"❌ 自動報名失敗 [ID: {registration_id}] - {result['message']}")


# ===== 路由 =====
@app.route('/')
def index():
    """首頁：傳入按星期分組的社團清單"""
    from collections import defaultdict
    grouped   = defaultdict(list)
    day_order = ['星期一', '星期二', '星期三', '星期四', '星期五']
    for club in BECLASS_CLUBS:
        grouped[club['day']].append(club)
    clubs_by_day = [(day, grouped[day]) for day in day_order if day in grouped]
    return render_template('index.html', clubs_by_day=clubs_by_day, all_clubs=BECLASS_CLUBS)

@app.route('/api/clubs')
def get_clubs():
    """取得社團列表"""
    return jsonify({'clubs': BECLASS_CLUBS})

@app.route('/api/register', methods=['POST'])
def register():
    """接收報名資料並排程自動報名"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '無效的請求資料'}), 400

    # ── 必填欄位 ──
    required = ['student_name', 'id_number', 'gender', 'parent_email',
                'phone', 'class_seat', 'club_indexes', 'register_time']
    missing = [f for f in required if not data.get(f) and data.get(f) != 0]
    if missing:
        return jsonify({'success': False, 'message': f'缺少必填欄位: {", ".join(missing)}'}), 400

    # ── 班級座號格式驗證（5碼：年1+班2+座2，如 10101） ──
    import re
    class_seat = str(data.get('class_seat', '')).strip()
    if not re.match(r'^[1-6]\d{4}$', class_seat):
        return jsonify({'success': False, 'message': '班級座號格式錯誤，需為5碼數字（如：10101 = 一年一班1號）'}), 400

    # ── 社團選擇（1~2個） ──
    club_indexes = data.get('club_indexes', [])
    if not isinstance(club_indexes, list) or len(club_indexes) == 0:
        return jsonify({'success': False, 'message': '請至少選擇一個社團'}), 400
    if len(club_indexes) > 2:
        return jsonify({'success': False, 'message': '最多只能選擇 2 個社團'}), 400

    valid_indexes = {c['index'] for c in BECLASS_CLUBS}
    for idx in club_indexes:
        if idx not in valid_indexes:
            return jsonify({'success': False, 'message': f'無效的社團編號: {idx}'}), 400

    # ── 驗證 ──
    if not validate_taiwan_id(data['id_number']):
        return jsonify({'success': False, 'message': '身分證字號格式不正確（如：A123456789）'}), 400
    if not validate_phone(data['phone']):
        return jsonify({'success': False, 'message': '手機號碼格式不正確（需 09 開頭共 10 碼）'}), 400

    try:
        register_time = datetime.fromisoformat(data['register_time'])
        if register_time <= datetime.now():
            return jsonify({'success': False, 'message': '報名時間必須是未來的時間'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': '報名時間格式不正確'}), 400

    # ── 社團名稱 ──
    idx_to_name = {c['index']: c['name'] for c in BECLASS_CLUBS}
    club_names  = '、'.join(idx_to_name.get(i, str(i)) for i in club_indexes)

    # ── 建立記錄 ──
    registration_id = str(uuid.uuid4())[:8].upper()
    record = {
        'id':             registration_id,
        'student_name':   data['student_name'],
        'id_number':      data['id_number'].upper(),
        'gender':         data['gender'],
        'parent_email':   data['parent_email'],
        'phone':          data['phone'],
        'class_seat':     class_seat,
        'club_indexes':   club_indexes,
        'club_name':      club_names,
        'register_time':  register_time.isoformat(),
        'status':         'pending',
        'created_at':     datetime.now().isoformat(),
        'result_message': '',
        'executed_at':    '',
    }

    records = load_data()
    records.append(record)
    save_data(records)

    # ── 排程 ──
    try:
        scheduler.add_job(
            func=do_auto_register,
            trigger=DateTrigger(run_date=register_time, timezone='Asia/Taipei'),
            args=[registration_id],
            id=f'reg_{registration_id}',
            replace_existing=True
        )
        logger.info(f"✅ 已排程 [ID: {registration_id}] 時間: {register_time}")
    except Exception as e:
        logger.error(f"排程失敗: {e}")
        return jsonify({'success': False, 'message': f'排程設定失敗: {e}'}), 500

    return jsonify({
        'success':         True,
        'message':         '報名資料已儲存，系統將於指定時間自動報名！',
        'registration_id': registration_id,
        'club_name':       club_names,
        'scheduled_time':  register_time.strftime('%Y/%m/%d %H:%M:%S'),
        'class_seat':      class_seat,
    })

@app.route('/api/status/<registration_id>')
def check_status(registration_id):
    """查詢報名狀態"""
    records = load_data()
    record = next((r for r in records if r['id'] == registration_id.upper()), None)
    
    if not record:
        return jsonify({'success': False, 'message': '找不到此報名記錄'}), 404
    
    return jsonify({
        'success': True,
        'id':            record['id'],
        'student_name':  record['student_name'],
        'club_name':     record['club_name'],
        'register_time': record['register_time'],
        'status':        record['status'],
        'result_message': record.get('result_message', ''),
        'executed_at':   record.get('executed_at', ''),
    })

@app.route('/api/cancel/<registration_id>', methods=['DELETE'])
def cancel_registration(registration_id):
    """取消排程報名"""
    records = load_data()
    record = next((r for r in records if r['id'] == registration_id.upper()), None)
    
    if not record:
        return jsonify({'success': False, 'message': '找不到此報名記錄'}), 404
    
    if record['status'] != 'pending':
        return jsonify({'success': False, 'message': f'無法取消，目前狀態為: {record["status"]}'}), 400
    
    # 移除排程
    job_id = f'reg_{registration_id.upper()}'
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    record['status'] = 'cancelled'
    record['result_message'] = '使用者取消'
    save_data(records)
    
    return jsonify({'success': True, 'message': '已成功取消報名排程'})

if __name__ == '__main__':
    logger.info("🏫 國小課後社團自動報名系統啟動中...")
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
