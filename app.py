import psycopg2
import psycopg2.extras # 辞書形式でデータを扱うために必要
from flask import Flask, render_template, jsonify, request
from datetime import datetime

# Flaskアプリケーションの初期化
app = Flask(__name__)
# jsonifyが日本語を正しく扱うための設定
app.config['JSON_AS_ASCII'] = False


# --- データベース接続情報 ---
DB_HOST = "timecard-db-postgres.cluster-chws42kecqe9.ap-southeast-2.rds.amazonaws.com"
DB_NAME = "postgres"
DB_USER = "postgresadmin"
DB_PASS = "nifmon-veQhe1-vevzaz" # あなたが設定したパスワード


def get_db_connection():
    """データベースへの接続を確立する関数"""
    conn = psycopg2.connect(host=DB_HOST,
                            database=DB_NAME,
                            user=DB_USER,
                            password=DB_PASS,
                            sslmode='require',
                            cursor_factory=psycopg2.extras.DictCursor)
    return conn


# --- ルート設定 (各ページの表示) ---

@app.route('/')
def index():
    return render_template('admin.html')

@app.route('/qr/<string:student_id>')
def generate_qr(student_id):
    return render_template('generate_qr.html', student_id=student_id)

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')


# --- API設定 (データのやり取り) ---

# 授業名の一覧を返すAPI
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
        if conn: conn.close()

# 指定された授業名の詳細な出席データを返すAPI
@app.route('/api/attendance/<string:class_name>')
def get_attendance_by_class(class_name):
    records = []
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        sql = """
            SELECT
                m.id,
                m.name,
                (SELECT status FROM attendance_records
                 WHERE student_id = m.id AND attendance_date = CURRENT_DATE
                 AND class_id IN (SELECT class_id FROM timetable WHERE class_name = %s)
                 ORDER BY timestamp DESC LIMIT 1) AS today_status,
                (SELECT COUNT(*) FROM attendance_records
                 WHERE student_id = m.id AND status = '遅刻'
                 AND class_id IN (SELECT class_id FROM timetable WHERE class_name = %s)) AS late_count,
                (
                    (SELECT COUNT(*) FROM attendance_records
                     WHERE student_id = m.id AND status IN ('出席', '遅刻')
                     AND class_id IN (SELECT class_id FROM timetable WHERE class_name = %s))
                    * 100.0
                    /
                    (SELECT COUNT(*) FROM timetable WHERE class_name = %s)
                ) AS attendance_rate
            FROM
                student_master m
            ORDER BY
                m.id;
        """
        cur.execute(sql, (class_name, class_name, class_name, class_name))
        records = [dict(row) for row in cur.fetchall()]
        cur.close()
    except Exception as e:
        print(f"[/api/attendance] データベースエラー: {e}")
    finally:
        if conn: conn.close()
    return jsonify(records)

# 出席を記録するためのAPI
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
        current_time = now.time()
        sql_find_class = "SELECT class_id, class_name, start_time FROM timetable WHERE day_of_week = %s AND %s BETWEEN start_time - interval '15 minutes' AND end_time LIMIT 1;"
        cur.execute(sql_find_class, (day_of_week, current_time))
        current_class = cur.fetchone()
        if not current_class:
            return jsonify({'status': 'error', 'message': '現在、受付時間中の授業がありません'}), 400
        class_id = current_class['class_id']
        class_name = current_class['class_name']
        start_time = current_class['start_time']
        attendance_status = '出席' if current_time <= start_time else '遅刻'
        sql_upsert = "INSERT INTO attendance_records (student_id, class_id, attendance_date, status, timestamp) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (student_id, class_id, attendance_date) DO UPDATE SET status = EXCLUDED.status, timestamp = EXCLUDED.timestamp;"
        cur.execute(sql_upsert, (student_id, class_id, now.date(), attendance_status, now))
        conn.commit()
        cur.close()
        return jsonify({'status': 'success', 'message': f"'{class_name}'に'{attendance_status}'として記録しました"})
    except Exception as e:
        print(f"データベース更新エラー: {e}")
        if conn: conn.rollback()
        return jsonify({'status': 'error', 'message': 'データベースの更新に失敗しました'}), 500
    finally:
        if conn: conn.close()

# このファイルが直接実行された場合にのみ、サーバーを起動する
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)