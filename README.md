# jisui
スクリーンキャプチャ → 自動文字起こしツール

2つのスクリプトが連携して動作します。

## セットアップ

```bash
pip install pynput Pillow anthropic watchdog
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Linux の場合（キャプチャ用に追加で必要）
```bash
sudo apt install imagemagick   # または scrot
```

## 使い方

### ターミナル1: キャプチャツール
```bash
python capture_tool.py --output-dir ./captures --hotkey f12
```

### ターミナル2: 文字起こしエージェント
```bash
python ocr_agent.py --watch-dir ./captures --output text.md
```

### 動作の流れ

1. **F12** を押すと画面が暗転し、矩形選択モードになる
2. マウスでドラッグして範囲を選択
3. `captures/1.png` として保存される（次回は `2.png`, `3.png`, ...）
4. エージェントがファイルを検知し、Claude API で文字起こし
5. `text.md` に以下の形式で追記される:

```markdown
# 1

（1.png の文字起こし結果）

# 2

（2.png の文字起こし結果）
```

## オプション

| 引数 | キャプチャ | エージェント | 説明 |
|------|-----------|-------------|------|
| `--output-dir` / `-o` | ✅ | — | キャプチャ保存先 |
| `--hotkey` / `-k` | ✅ | — | 起動キー (f1〜f12) |
| `--watch-dir` / `-w` | — | ✅ | 監視ディレクトリ |
| `--output` / `-o` | — | ✅ | 出力 Markdown |
| `--model` / `-m` | — | ✅ | Claude モデル名 |

## 注意事項

- エージェント起動時に、未処理の既存ファイルも自動的に処理します
- `text.md` に既に `# (番号)` がある場合はスキップします（重複防止）
- コスト重視なら `--model claude-haiku-4-5-20251001` を指定してください
