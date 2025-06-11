import psycopg2
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# --- データベース接続情報 ---
DB_HOST = "timecard-db-postgres.cluster-chws42kecqe9.ap-southeast-2.rds.amazonaws.com"
DB_NAME = "postgres"
DB_USER = "postgresadmin"
DB_PASS = "nifmon-veQhe1-vevzaz"


def get_db_connection():
    """データベースへの接続を確立する関数"""
    conn = psycopg2.connect(host=DB_HOST,
                            database=DB_NAME,
                            user=DB_USER,
                            password=DB_PASS,
                            sslmode='require') # 念のためSSLモードを必須に設定
    return conn


# --- ルート設定 ---

# トップページ用
@app.route('/')
def index():
    return render_template('index.html')

# QRコード生成ページ用
@app.route('/qr')
def generate_qr():
    return render_template('generate_qr.html')

# 管理画面用（骨組みのHTMLを返すだけ）
@app.route('/admin')
def admin():
    return render_template('admin.html')


# 【修正箇所】APIがデータベースからデータを取得して返すようにする
@app.route('/api/students')
def get_students_data():
    students = []
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, name, status, timestamp FROM students ORDER BY id;')
        
        db_students = cur.fetchall()
        for row in db_students:
            students.append({
                'id': row[0], 
                'name': row[1], 
                'status': row[2], 
                'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] is not None else None
            })
        cur.close()
    except Exception as e:
        print(f"データベース接続エラー: {e}")
    finally:
        if conn is not None:
            conn.close()
    
    # DBから取得したデータをJSON形式で返す
    return jsonify(students)