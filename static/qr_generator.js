document.addEventListener('DOMContentLoaded', function() {
    // bodyタグから学籍番号を取得
    const userId = document.body.dataset.studentId;
    const qrcodeCanvas = document.getElementById("qrcode");
    
    if (!userId || !qrcodeCanvas) {
        console.error('必要な要素が見つかりません。');
        return;
    }

    // 今日の日付を取得
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const dateString = `${year}-${month}-${day}`;
    
    // QRコード用のデータを作成
    const uniqueData = `${userId},${dateString}`;
    
    console.log('生成するデータ:', uniqueData);

    // ★★★ 新しいライブラリ「qrious」を使ってQRコードを生成 ★★★
    new QRious({
      element: qrcodeCanvas,
      value: uniqueData,
      size: 256,
      padding: 10
    });
});