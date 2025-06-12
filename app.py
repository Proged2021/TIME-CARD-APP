import psycopg2
from flask import Flask, render_template, jsonify, request
from datetime import datetime

# Flaskアプリケーションの初期化
app = Flask(__name__)

# --- データベース接続情報 ---
# 註：この情報は、本来は環境変数などを使って安全に管理します。
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
                            sslmode='require') # SSLモードを必須に設定
    return conn


# --- ルート設定 (各ページの表示) ---

@app.route('/')
def index():
    # 本来はここにトップページの内容を書きますが、今回は作成していないので、
    # 代わりに管理画面のテンプレートを表示します。
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

# 管理画面に表示する学生リストを返すAPI
@app.route('/api/students')
def get_students_data():
    students = []
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # student_masterとattendance_recordsを結合(JOIN)して、今日の記録だけを取得
        sql = """
            SELECT
                m.id,
                m.name,
                r.status,
                r.timestamp
            FROM
                student_master m
            LEFT JOIN
                attendance_records r ON m.id = r.student_id AND r.attendance_date = CURRENT_DATE
            ORDER BY
                m.id;
        """
        cur.execute(sql)
        
        db_students = cur.fetchall()
        for row in db_students:
            students.append({
                'id': row[0], 
                'name': row[1], 
                'status': row[2] if row[2] is not None else '未記録',
                'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] is not None else None
            })
        cur.close()
    except Exception as e:
        print(f"[/api/students] データベース接続エラー: {e}")
    finally:
        if conn is not None:
            conn.close()
    
    return jsonify(students)


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
    
    # QRコードの日付が今日の日付と一致するかチェック
    today_str = datetime.now().strftime('%Y-%m-%d')
    if date_str != today_str:
        return jsonify({'status': 'error', 'message': 'QRコードの日付が有効ではありません'}), 400

    # --- 遅刻判定ロジック ---
    now = datetime.now()
    # 授業の開始時刻を定義（今日の9時30分0秒）
    class_start_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # 現在時刻が、授業開始時刻より後か、同じかそれ以前かで判定
    if now > class_start_time:
        attendance_status = '遅刻'
    else:
        attendance_status = '出席'
    
    print(f"判定ステータス: {attendance_status}")

    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # UPDATEクエリで、該当学生のステータスとタイムスタンプを更新
        cur.execute(
            "UPDATE attendance_records SET status = %s, timestamp = %s WHERE student_id = %s AND attendance_date = CURRENT_DATE",
            (attendance_status, now, student_id)
        )
        
        conn.commit()
        cur.close()
        
        return jsonify({'status': 'success', 'message': f'{student_id}の出席を記録しました'})
    except Exception as e:
        print(f"データベース更新エラー: {e}")
        if conn:
            conn.rollback()
        return jsonify({'status': 'error', 'message': 'データベースの更新に失敗しました'}), 500
    finally:
        if conn is not None:
            conn.close()