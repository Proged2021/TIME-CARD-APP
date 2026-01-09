import sqlite3
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import qrcode
import io
import base64
import os

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# --- データベース接続情報 ---
DB_PATH = 'timecard.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """データベースとテーブルを初期化"""
    if os.path.exists(DB_PATH):
        return
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # student_masterテーブル
    cur.execute('''
        CREATE TABLE IF NOT EXISTS student_master (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    
    # timetableテーブル
    cur.execute('''
        CREATE TABLE IF NOT EXISTS timetable (
            class_id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL
        )
    ''')
    
    # attendance_recordsテーブル
    cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            attendance_date TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            UNIQUE(student_id, class_id, attendance_date)
        )
    ''')
    
    # サンプルデータ挿入
    cur.execute("INSERT INTO student_master (id, name) VALUES ('S001', '山田太郎')")
    cur.execute("INSERT INTO student_master (id, name) VALUES ('S002', '佐藤花子')")
    cur.execute("INSERT INTO student_master (id, name) VALUES ('S003', '鈴木一郎')")
    
    cur.execute("INSERT INTO timetable (class_name, day_of_week, start_time, end_time) VALUES ('数学', 0, '09:00', '10:30')")
    cur.execute("INSERT INTO timetable (class_name, day_of_week, start_time, end_time) VALUES ('英語', 0, '10:45', '12:15')")
    cur.execute("INSERT INTO timetable (class_name, day_of_week, start_time, end_time) VALUES ('国語', 1, '09:00', '10:30')")
    
    conn.commit()
    conn.close()
    print("データベースを初期化しました")

# --- ルート設定 ---

@app.route('/')
def index():
    return render_template('admin.html')

@app.route('/qr/<string:student_id>')
def generate_qr(student_id):
    # 1. QRコードに含めるデータを作成
    today_str = datetime.now().strftime('%Y-%m-%d')
    unique_data = f"{student_id},{today_str}"

    # 2. PythonでQRコード画像をメモリ上に生成
    img = qrcode.make(unique_data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    
    # 3. 画像データを、HTMLに埋め込めるBase64形式の文字列に変換
    qr_image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    # 4. 画像データをHTMLテンプレートに渡す
    return render_template('generate_qr.html', student_id=student_id, qr_image_data=qr_image_base64)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# --- API設定 ---

@app.route('/api/class_names')
def get_class_names():
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT class_name FROM timetable ORDER BY class_name;")
        class_names = [row['class_name'] for row in cur.fetchall()]
        cur.close()
        return jsonify(class_names)
    except Exception as e:
        print(f"[/api/class_names] データベースエラー: {e}")
        return jsonify([]), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/attendance/<string:class_name>')
def get_attendance_by_class(class_name):
    records = []
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        sql = """
            SELECT
                m.id, m.name,
                (SELECT status FROM attendance_records WHERE student_id = m.id AND attendance_date = ? AND class_id IN (SELECT class_id FROM timetable WHERE class_name = ?) ORDER BY timestamp DESC LIMIT 1) AS today_status,
                (SELECT COUNT(*) FROM attendance_records WHERE student_id = m.id AND status = '遅刻' AND class_id IN (SELECT class_id FROM timetable WHERE class_name = ?)) AS late_count,
                ((SELECT COUNT(*) FROM attendance_records WHERE student_id = m.id AND status IN ('出席', '遅刻') AND class_id IN (SELECT class_id FROM timetable WHERE class_name = ?)) * 100.0 / NULLIF((SELECT COUNT(*) FROM timetable WHERE class_name = ?), 0)) AS attendance_rate
            FROM student_master m ORDER BY m.id;
        """
        cur.execute(sql, (today, class_name, class_name, class_name, class_name))
        records = [dict(row) for row in cur.fetchall()]
        cur.close()
    except Exception as e:
        print(f"[/api/attendance] データベースエラー: {e}")
    finally:
        if conn:
            conn.close()
    return jsonify(records)

@app.route('/api/check_in', methods=['POST'])
def check_in():
    data = request.get_json()
    if not data or 'qr_data' not in data:
        return jsonify({'status': 'error', 'message': 'データがありません'}), 400
    
    qr_data = data['qr_data']
    try:
        student_id, date_str = qr_data.split(',')
    except ValueError:
        return jsonify({'status': 'error', 'message': '無効なQRデータ形式です'}), 400
    
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    if date_str != today_str:
        return jsonify({'status': 'error', 'message': 'QRコードの日付が有効ではありません'}), 400
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        day_of_week = now.weekday()
        current_time = now.strftime('%H:%M')
        
        # 15分前から終了時刻までの授業を検索
        sql_find_class = """
            SELECT class_id, class_name, start_time 
            FROM timetable 
            WHERE day_of_week = ? 
            AND time(?) BETWEEN time(start_time, '-15 minutes') AND time(end_time)
            LIMIT 1
        """
        cur.execute(sql_find_class, (day_of_week, current_time))
        current_class = cur.fetchone()
        
        if not current_class:
            return jsonify({'status': 'error', 'message': '現在、受付時間中の授業がありません'}), 400
        
        class_id = current_class['class_id']
        class_name = current_class['class_name']
        start_time = current_class['start_time']
        attendance_status = '出席' if current_time <= start_time else '遅刻'
        
        # INSERT OR REPLACE を使用
        sql_upsert = """
            INSERT OR REPLACE INTO attendance_records 
            (student_id, class_id, attendance_date, status, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        """
        cur.execute(sql_upsert, (student_id, class_id, now.strftime('%Y-%m-%d'), attendance_status, now.strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        cur.close()
        
        return jsonify({'status': 'success', 'message': f"'{class_name}'に'{attendance_status}'として記録しました"})
    except Exception as e:
        print(f"データベース更新エラー: {e}")
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': 'データベースの更新に失敗しました'}), 500
    finally:
        if conn:
            conn.close()

# 起動用コード
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)
