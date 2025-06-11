//仮想環境を有効にする
source venv/bin/activate

//サーバーの起動
flask --app app --debug run

//# QRコード生成ページ 
(http://127.0.0.1:5000/qr) 

# 管理画ページ
（http://127.0.0.1:5000/admin）

#スキャナーのページ
（http://127.0.0.1:5000/scan）
timecard-db-postgres.cluster-chws42kecqe9.ap-southeast-2.rds.amazonaws.com