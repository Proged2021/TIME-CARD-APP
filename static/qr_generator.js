// --- QRコードを生成するJavaScriptの処理 ---

// 【本来は】ログイン機能などを使ってサーバーから受け取ります。
// 【今回は】JavaScript内で仮の学籍番号（ユーザーID）を定義します。
const userId = '2400633'; 

// 今日の日付を「YYYY-MM-DD」形式の文字列で取得します。
const today = new Date();
const year = today.getFullYear();
const month = String(today.getMonth() + 1).padStart(2, '0'); // 月は0から始まるので+1
const day = String(today.getDate()).padStart(2, '0');
const dateString = `${year}-${month}-${day}`;

// ユーザーIDと日付をカンマで区切って結合し、QRコード用のデータを作成します。
// これで「毎日違う」「他の人と被らない」データになります。
const uniqueData = `${userId},${dateString}`;

// ブラウザの開発者ツールで、生成されたデータを確認できます。
console.log('QRコードのデータ:', uniqueData);

// qrcode.jsライブラリを使い、QRコードを生成して、<div id="qrcode"></div> の中に表示します。
new QRCode(document.getElementById('qrcode'), {
    text: uniqueData,
    width: 256,
    height: 256,
    colorDark : "#000000",
    colorLight : "#ffffff",
    correctLevel : QRCode.CorrectLevel.H
});