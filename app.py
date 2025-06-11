import psycopg2
from flask import Flask, render_template, jsonify

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


# --- ルート設定 ---

# トップページ用
@app.route('/')
def index():
    return render_template('index.html')

# 学生がQRコードを表示するページ用
@app.route('/qr')
def generate_qr():
    return render_template('generate_qr.html')

# スキャン専用ページ用
@app.route('/scan')
def scan():
    return render_template('scan.html')

# 管理者が一覧を見るページ用（骨組みのHTMLを返すだけ）
@app.route('/admin')
def admin():
    return render_template('admin.html')


# 管理画面のJavaScriptに学生データを返すためのAPI
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
                # タイムスタンプを綺麗な文字列に変換（Noneでなければ）
                'timestamp': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] is not None else None
            })

        cur.close()
    except Exception as e:
        # エラーが発生した場合、Flaskサーバーのコンソールにエラー内容を表示
        print(f"データベース接続エラー: {e}")
    finally:
        # 接続が確立されていたら、必ず閉じる
        if conn is not None:
            conn.close()
    
    # DBから取得したデータをJSON形式で返す
    return jsonify(students)