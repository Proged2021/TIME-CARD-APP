document.addEventListener('DOMContentLoaded', function() {
    const scanResultEl = document.getElementById('scan-result');
    const scanSound = document.getElementById('scan-sound');
    const startScanBtn = document.getElementById('start-scan-btn');
    const startScreen = document.getElementById('start-screen');
    const qrReaderEl = document.getElementById('qr-reader');

    const processedCodes = new Set();
    let isScanningPaused = false;

    startScanBtn.addEventListener('click', () => {
        scanSound.play();
        scanSound.pause();
        scanSound.currentTime = 0;
        startScreen.style.display = 'none';
        qrReaderEl.style.display = 'block';
        startScanner();
    });

    /**
     * スキャンデータをサーバーに送信し、結果を待って返す非同期関数
     */
    async function recordAttendance(qrData) {
        try {
            const response = await fetch('/api/check_in', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ qr_data: qrData }),
            });
            const data = await response.json();
            console.log('サーバーからの応答:', data);
            return data; // サーバーからの応答データを返す
        } catch (error) {
            console.error('サーバーへの送信エラー:', error);
            // エラーが発生した場合も、同じ形式のエラーオブジェクトを返す
            return { status: 'error', message: 'サーバー通信エラー' };
        }
    }

    /**
     * QRコードのスキャンが成功した時に実行される非同期関数
     */
    async function onScanSuccess(decodedText, decodedResult) {
        if (isScanningPaused) return;
        
        isScanningPaused = true;

        const validFormatRegex = /^[A-Za-z0-9]+,\d{4}-\d{2}-\d{2}$/;
        if (!validFormatRegex.test(decodedText)) {
            // 無効な形式の場合は、何もせずスキャンを再開
            isScanningPaused = false;
            return; 
        }

        if (processedCodes.has(decodedText)) {
            scanResultEl.innerHTML = `<span class="badge bg-info fs-5">処理済みです</span>`;
        } else {
            // --- ここからが新しいロジック ---
            // サーバーからの応答を 'await' で待つ
            const serverResponse = await recordAttendance(decodedText);

            // 応答の内容に応じて、表示と音を制御する
            if (serverResponse.status === 'success') {
                scanSound.play();
                scanResultEl.innerHTML = `<span class="badge bg-success fs-4">読み取り完了</span>`;
                processedCodes.add(decodedText);
            } else {
                // エラーメッセージを画面に表示する
                scanResultEl.innerHTML = `<span class="badge bg-danger fs-5">${serverResponse.message}</span>`;
            }
        }
        
        // 全ての処理が終わった後で、2秒タイマーをセット
        setTimeout(() => {
            scanResultEl.innerHTML = '';
            isScanningPaused = false;
        }, 2000);
    }

    function onScanFailure(error) { }

    function startScanner() {
        const html5Qrcode = new Html5Qrcode("qr-reader");
        const config = {
            fps: 10,
            qrbox: { width: 350, height: 350 }
        };
        html5Qrcode.start({ facingMode: "environment" }, config, onScanSuccess, onScanFailure)
            .catch((err) => {
                startScreen.style.display = 'flex';
                qrReaderEl.style.display = 'none';
                alert(`カメラの起動に失敗しました: ${err}`);
            });
    }
});