# auto_capture.py
指定間隔で Left → F12 キーを自動送信し、ページめくり＋キャプチャを自動化するスクリプト。

## セットアップ

```bash
pip install pynput
```

## 使い方

### 1. capture_tool.py を起動する（ターミナル1）

```bash
python capture_tool.py --output-dir ./captures --hotkey f12
```

範囲選択を済ませ、待機状態にしておく。

### 2. auto_capture.py を実行する（ターミナル2）

```bash
python auto_capture.py --count 120 --interval 2
```

5秒のカウントダウン中にビューアのウィンドウをクリックしてアクティブにする。

### 動作の流れ

1. 開始前に `--wait` 秒（デフォルト5秒）待機する
2. Left キーを押す（ページめくり）
3. 0.5秒待つ
4. F12 キーを押す（キャプチャ）
5. `--interval` 秒待つ
6. 2〜5 を `--count` 回繰り返す
7. Ctrl+C でいつでも中断できる

## オプション

| 引数 | 説明 | デフォルト |
|------|------|-----------|
| `-n`, `--count` | 繰り返し回数（必須） | — |
| `-i`, `--interval` | 各回の間隔（秒） | 2.0 |
| `-w`, `--wait` | 開始前の待機時間（秒） | 5.0 |
| `--capture-key` | キャプチャキー | f12 |

## 使用例

```bash
# 120ページを2秒間隔でキャプチャ
python auto_capture.py -n 120 -i 2

# 間隔を長めに、開始待機も10秒に
python auto_capture.py -n 200 -i 3 --wait 10

# F9 キーでキャプチャする場合
python auto_capture.py -n 50 -i 2 --capture-key f9
```
