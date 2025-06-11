document.addEventListener('DOMContentLoaded', function() {

    const scanResultEl = document.getElementById('scan-result');
    const scanSound = document.getElementById('scan-sound');
    const startScanBtn = document.getElementById('start-scan-btn');
    const startScreen = document.getElementById('start-screen');
    const qrReaderEl = document.getElementById('qr-reader');

    const processedCodes = new Set();
    let isScanningPaused = false;

    // 「スキャンを開始する」ボタンがクリックされた時の処理
    startScanBtn.addEventListener('click', () => {
        // ★★★ 音声再生のロックを解除するおまじない ★★★
        scanSound.play();
        scanSound.pause();
        scanSound.currentTime = 0;

        // スタート画面を非表示にし、スキャナーを表示
        startScreen.style.display = 'none';
        qrReaderEl.style.display = 'block';

        // スキャナーを起動
        startScanner();
    });

    function onScanSuccess(decodedText, decodedResult) {
        if (isScanningPaused) return;
        
        const validFormatRegex = /^[A-Za-z0-9]+,\d{4}-\d{2}-\d{2}$/;
        if (!validFormatRegex.test(decodedText)) return;

        if (processedCodes.has(decodedText)) {
            scanResultEl.innerHTML = `<span class="badge bg-info fs-5">処理済みです</span>`;
            isScanningPaused = true;
            setTimeout(() => {
                scanResultEl.innerHTML = '';
                isScanningPaused = false;
            }, 2000);
            return;
        }

        isScanningPaused = true;
        processedCodes.add(decodedText);
        scanSound.play(); // ★★★ これで音が鳴るはず！ ★★★
        scanResultEl.innerHTML = `<span class="badge bg-success fs-4">読み取り完了</span>`;
        console.log(`スキャン成功・サーバー送信対象: ${decodedText}`);
        
        setTimeout(() => {
            scanResultEl.innerHTML = '';
            isScanningPaused = false;
        }, 2000);
    }

    function onScanFailure(error) { }

    // スキャナーを起動する処理を関数にまとめる
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
            scanResultEl.innerHTML = `<div class="alert alert-danger">カメラの起動に失敗しました。</div>`;
        });
    }
});