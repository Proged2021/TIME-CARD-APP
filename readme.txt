//仮想環境を有効にする
source venv/bin/activate

//サーバーの起動
python3 app.py

//ngrokの起動
./ngrok http 5001

# 管理画ページ
（http://127.0.0.1:5001/admin）

#スキャナーのページ
（http://127.0.0.1:5001/scan）
timecard-db-postgres.cluster-chws42kecqe9.ap-southeast-2.rds.amazonaws.com