// HTMLが読み込み終わったら処理を開始
document.addEventListener('DOMContentLoaded', function() {

    // app.pyで作ったAPIのURLからデータを取得
    fetch('/api/students')
        .then(response => response.json()) // データをJSONとして解釈
        .then(students => { // 解釈後のデータ（学生のリスト）
            
            // HTMLからid="attendance-body"を持つ要素（tbody）を取得
            const tableBody = document.getElementById('attendance-body');

            // 学生リストをループ処理
            for (const student of students) {
                // 新しいテーブル行（<tr>）要素を作成
                const row = document.createElement('tr');

                // statusの値に応じてバッジのHTMLを決定
                let statusBadgeHtml = '';
                if (student.status === '出席') {
                    statusBadgeHtml = `<span class="badge bg-success">${student.status}</span>`;
                } else if (student.status === '遅刻') {
                    statusBadgeHtml = `<span class="badge bg-warning">${student.status}</span>`;
                } else {
                    statusBadgeHtml = `<span class="badge bg-danger">${student.status}</span>`;
                }

                // 1行分のセル（<td>）のHTMLを組み立てる
                row.innerHTML = `
                    <td>${student.id}</td>
                    <td>${student.name}</td>
                    <td>${statusBadgeHtml}</td>
                    <td>${student.timestamp ? student.timestamp : '-'}</td>
                `;

                // 完成した行（<tr>）をtbodyに追加する
                tableBody.appendChild(row);
            }
        })
        .catch(error => {
            console.error('データの取得中にエラーが発生しました:', error);
            const tableBody = document.getElementById('attendance-body');
            tableBody.innerHTML = '<tr><td colspan="4" class="text-center text-danger">データの読み込みに失敗しました。</td></tr>';
        });
});