document.addEventListener('DOMContentLoaded', function() {
    const classListEl = document.getElementById('class-list');
    const classDetailEl = document.getElementById('class-detail');
    const classTitleEl = document.getElementById('class-title');
    const tableBodyEl = document.getElementById('attendance-body');

    // 最初に、授業名の一覧をサーバーから取得してボタンを作成する
    fetch('/api/class_names')
        .then(response => response.json())
        .then(classNames => {
            // もし授業名が一つもなければ、メッセージを表示
            if (classNames.length === 0) {
                classListEl.innerHTML = '<p class="text-muted">表示できる授業がありません。</p>';
                return;
            }

            // 取得した授業名一つひとつに対して、ボタンを作成
            classNames.forEach(name => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'list-group-item list-group-item-action';
                button.textContent = name;
                // ボタンがクリックされた時の動作を設定
                button.addEventListener('click', () => {
                    // その授業の詳細データを取得して表示する関数を呼び出す
                    fetchAttendanceForClass(name);
                });
                classListEl.appendChild(button);
            });
        })
        .catch(error => {
            console.error('授業名リストの取得に失敗しました:', error);
            classListEl.innerHTML = '<p class="text-danger">授業名リストの読み込みに失敗しました。</p>';
        });

    // 授業名をクリックした時に、詳細データを取得してテーブルを描画する関数
    function fetchAttendanceForClass(className) {
        // 詳細表示エリアを表示し、タイトルをセット
        classTitleEl.textContent = `${className} の出席状況`;
        classDetailEl.style.display = 'block';
        tableBodyEl.innerHTML = '<tr><td colspan="5" class="text-center">読み込み中...</td></tr>';

        // クリックされたボタンをアクティブ（青色）にする
        document.querySelectorAll('#class-list button').forEach(btn => {
            btn.classList.toggle('active', btn.textContent === className);
        });

        // サーバーに、その授業の詳細データをリクエスト
        fetch(`/api/attendance/${className}`)
            .then(response => response.json())
            .then(records => {
                tableBodyEl.innerHTML = ''; // テーブルの中身を一度空にする
                records.forEach(record => {
                    const row = document.createElement('tr');
                    
                    // 今日のステータスに応じたバッジを生成
                    let statusBadge = '';
                    // record.today_status が null や undefined の場合も考慮
                    switch (record.today_status) {
                        case '出席':
                            statusBadge = `<span class="badge bg-success">出席</span>`;
                            break;
                        case '遅刻':
                            statusBadge = `<span class="badge bg-warning">遅刻</span>`;
                            break;
                        case '欠席':
                            statusBadge = `<span class="badge bg-danger">欠席</span>`;
                            break;
                        default:
                            statusBadge = `<span class="badge bg-secondary">未記録</span>`;
                    }

                    // テーブルの1行分のHTMLを組み立てる
                    row.innerHTML = `
                        <td>${record.id}</td>
                        <td>${record.name}</td>
                        <td>${statusBadge}</td>
                        <td>${record.late_count} 回</td>
                        <td>${parseFloat(record.attendance_rate).toFixed(1)} %</td>
                    `;
                    tableBodyEl.appendChild(row);
                });
            })
            .catch(error => {
                console.error(`${className}の出席データの取得に失敗しました:`, error);
                tableBodyEl.innerHTML = '<tr><td colspan="5" class="text-center text-danger">データの読み込みに失敗しました。</td></tr>';
            });
    }
});