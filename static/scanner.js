// HTMLドキュメントが完全に読み込まれたら、中の処理を実行する
document.addEventListener('DOMContentLoaded', function() {

    // HTMLから、結果を表示するための要素と、音を鳴らすための要素を取得
    const scanResultEl = document.getElementById('scan-result');
    const scanSound = document.getElementById('scan-sound');
    const startScanBtn = document.getElementById('start-scan-btn');
    const startScreen = document.getElementById('start-screen');
    const qrReaderEl = document.getElementById('qr-reader');

    // 処理済みのQRコードデータを記憶するためのSet（重複送信防止用）
    const processedCodes = new Set();
    
    // スキャンが一時的に停止中かどうかのフラグ（連続スキャン防止用）
    let isScanningPaused = false;

    // 「スキャンを開始する」ボタンがクリックされた時の処理
    startScanBtn.addEventListener('click', () => {
        // 音声再生のロックを解除するおまじない
        scanSound.play();
        scanSound.pause();
        scanSound.currentTime = 0;

        // スタート画面を非表示にし、スキャナーを表示
        startScreen.style.display = 'none';
        qrReaderEl.style.display = 'block';

        // スキャナーを起動
        startScanner();
    });

    /**
     * スキャンデータをサーバーに送信して、出席を記録する関数
     */
    function recordAttendance(qrData) {
        fetch('/api/check_in', {
            method: 'POST', // POSTメソッドで送信
            headers: {
                'Content-Type': 'application/json', // データ形式はJSON
            },
            body: JSON.stringify({ qr_data: qrData }), // 送信するデータ
        })
        .then(response => response.json())
        .then(data => {
            console.log('サーバーからの応答:', data);
            // サーバーからの応答がエラーだった場合に、特別な表示をすることも可能
            if (data.status === 'error') {
                 scanResultEl.innerHTML = `<span class="badge bg-danger fs-5">${data.message}</span>`;
            }
        })
        .catch((error) => {
            console.error('サーバーへの送信エラー:', error);
            scanResultEl.innerHTML = `<span class="badge bg-danger fs-5">サーバー通信エラー</span>`;
        });
    }

    /**
     * QRコードのスキャンが成功した時に実行される関数
     */
    function onScanSuccess(decodedText, decodedResult) {
        if (isScanningPaused) return;
        
        // 1. 形式チェック
        const validFormatRegex = /^[A-Za-z0-9]+,\d{4}-\d{2}-\d{2}$/;
        if (!validFormatRegex.test(decodedText)) return;

        // 2. 重複チェック
        if (processedCodes.has(decodedText)) {
            scanResultEl.innerHTML = `<span class="badge bg-info fs-5">スキャン済みです</span>`;
            isScanningPaused = true;
            setTimeout(() => {
                scanResultEl.innerHTML = '';
                isScanningPaused = false;
            }, 2000);
            return;
        }

        // --- 形式が正しく、かつ新規のQRコードの場合の処理 ---
        isScanningPaused = true;
        processedCodes.add(decodedText);
        scanSound.play();
        scanResultEl.innerHTML = `<span class="badge bg-success fs-4">読み取り完了</span>`;
        
        // サーバーにデータを送信する関数を呼び出す
        console.log(`スキャン成功・サーバー送信対象: ${decodedText}`);
        recordAttendance(decodedText); 
        
        setTimeout(() => {
            scanResultEl.innerHTML = '';
            isScanningPaused = false;
        }, 2000);
    }

    function onScanFailure(error) { }

    /**
     * スキャナーを起動する処理を関数
     */
    function startScanner() {
        const html5Qrcode = new Html5Qrcode("qr-reader");
        const config = {
            fps: 10,
            qrbox: { width: 350, height: 350 }
        };

        html5Qrcode.start(
            { facingMode: "environment" },
            config,
            onScanSuccess,
            onScanFailure
        ).catch((err) => {
            startScreen.style.display = 'flex'; // エラー時はスタート画面に戻す
            qrReaderEl.style.display = 'none';
            alert(`カメラの起動に失敗しました: ${err}`);
        });
    }
});