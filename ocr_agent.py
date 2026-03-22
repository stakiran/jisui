"""
文字起こしエージェント
=======================
- 指定ディレクトリを監視し、新しい .png ファイルを検知
- Claude API (Vision) で文字起こし
- text.md に `# (番号)` の見出し付きで append

必要パッケージ:
    pip install anthropic watchdog

環境変数:
    ANTHROPIC_API_KEY=sk-ant-...

使い方:
    python ocr_agent.py [--watch-dir ./captures] [--output text.md] [--model claude-sonnet-4-6]
"""

import argparse
import base64
import re
import sys
import time
from pathlib import Path

from anthropic import Anthropic
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def extract_number(filename: str) -> str | None:
    """ファイル名から番号部分を取得。 '3.png' → '3'"""
    m = re.match(r"^(\d+)\.png$", filename)
    return m.group(1) if m else None


def transcribe_image(client: Anthropic, image_path: Path, model: str) -> str:
    """Claude API で画像を文字起こし"""
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # 拡張子からメディアタイプを判定
    suffix = image_path.suffix.lower()
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(suffix, "image/png")

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "この画像に含まれるテキストをすべて正確に文字起こししてください。"
                            "レイアウトや構造もできるだけ保持してください。"
                            "テキスト以外の説明は不要です。テキストのみを出力してください。"
                        ),
                    },
                ],
            }
        ],
    )

    return response.content[0].text


def append_to_markdown(output_path: Path, number: str, text: str):
    """text.md に見出し付きで追記"""
    with open(output_path, "a", encoding="utf-8") as f:
        f.write(f"\n# {number}\n\n")
        f.write(text.strip())
        f.write("\n")

    print(f"[SAVED] #{number} → {output_path}")


class ImageHandler(FileSystemEventHandler):
    """新しい PNG ファイルを検知して文字起こしするハンドラ"""

    def __init__(self, client: Anthropic, output_path: Path, model: str):
        super().__init__()
        self.client = client
        self.output_path = output_path
        self.model = model
        self.processed: set[str] = set()

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle(Path(event.src_path))

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle(Path(event.src_path))

    def _handle(self, path: Path):
        if path.suffix.lower() != ".png":
            return

        number = extract_number(path.name)
        if number is None:
            return

        # 重複処理を防止
        if path.name in self.processed:
            return
        self.processed.add(path.name)

        # ファイルの書き込み完了を少し待つ
        time.sleep(0.5)

        print(f"[DETECT] {path.name} を検知しました。文字起こし中...")

        try:
            text = transcribe_image(self.client, path, self.model)
            append_to_markdown(self.output_path, number, text)
        except Exception as e:
            print(f"[ERROR] {path.name} の文字起こしに失敗: {e}")
            self.processed.discard(path.name)


def process_existing(client: Anthropic, watch_dir: Path, output_path: Path, model: str) -> set[str]:
    """既に text.md に記録済みの番号を取得し、未処理のファイルを処理"""
    processed_numbers: set[str] = set()

    # 既存の text.md から処理済み番号を取得
    if output_path.exists():
        content = output_path.read_text(encoding="utf-8")
        processed_numbers = set(re.findall(r"^# (\d+)$", content, re.MULTILINE))

    # 未処理の既存ファイルを処理
    existing_files = sorted(
        watch_dir.glob("*.png"),
        key=lambda p: int(m.group(1)) if (m := re.match(r"^(\d+)\.png$", p.name)) else 0,
    )

    for f in existing_files:
        number = extract_number(f.name)
        if number and number not in processed_numbers:
            print(f"[BACKFILL] {f.name} を文字起こし中...")
            try:
                text = transcribe_image(client, f, model)
                append_to_markdown(output_path, number, text)
                processed_numbers.add(number)
            except Exception as e:
                print(f"[ERROR] {f.name}: {e}")

    return processed_numbers


def main():
    parser = argparse.ArgumentParser(description="文字起こしエージェント")
    parser.add_argument(
        "--watch-dir", "-w",
        default="./captures",
        help="監視ディレクトリ (default: ./captures)",
    )
    parser.add_argument(
        "--output", "-o",
        default="text.md",
        help="出力 Markdown ファイル (default: text.md)",
    )
    parser.add_argument(
        "--model", "-m",
        default="claude-sonnet-4-6",
        help="使用モデル (default: claude-sonnet-4-6)",
    )
    args = parser.parse_args()

    watch_dir = Path(args.watch_dir)
    output_path = Path(args.output)

    if not watch_dir.exists():
        watch_dir.mkdir(parents=True)

    # API クライアント初期化
    client = Anthropic()  # ANTHROPIC_API_KEY 環境変数を使用

    print(f"=== 文字起こしエージェント ===")
    print(f"  監視先:   {watch_dir.resolve()}")
    print(f"  出力先:   {output_path.resolve()}")
    print(f"  モデル:   {args.model}")
    print(f"  終了:     Ctrl+C")
    print()

    # 既存ファイルの処理
    print("[INIT] 既存ファイルをチェック中...")
    already_processed = process_existing(client, watch_dir, output_path, args.model)
    processed_names = {f"{n}.png" for n in already_processed}
    print(f"[INIT] 処理済み: {len(already_processed)} 件")
    print()

    # ファイル監視を開始
    handler = ImageHandler(client, output_path, args.model)
    handler.processed = processed_names

    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)
    observer.start()

    print("[WATCHING] ファイル監視中...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n終了します")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
