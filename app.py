from flask import Flask, render_template

app = Flask(__name__)

# --- 仮のデータを作成 ---
# この部分に文法ミスがないか確認してください
students_data = [
    {
        'id': 'B1234567', 
        'name': '山田 太郎', 
        'status': '出席', 
        'timestamp': '08:59:01'
    }, # <-- 辞書の後のカンマ
    {
        'id': 'B2345678', 
        'name': '鈴木 花子', 
        'status': '遅刻', 
        'timestamp': '09:15:23'
    }, # <-- 辞書の後のカンマ
    {
        'id': 'B3456789', 
        'name': '佐藤 次郎', 
        'status': '欠席', 
        'timestamp': None
    }  # <-- 最後の要素の後ろはカンマ不要
]
# --- ここまでが仮データ ---


# トップページ用のルート
@app.route('/')
def index():
    return render_template('index.html')

# QRコードページ (http://127.0.0.1:5000/qr) 用のルート
@app.route('/qr')
def generate_qr():
    return render_template('generate_qr.html')

# 管理画面用の新しいルート（http://127.0.0.1:5000/admin）用のルート
@app.route('/admin')
def admin():
    return render_template('admin.html', students=students_data)