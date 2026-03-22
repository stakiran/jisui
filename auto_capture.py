"""
自動キャプチャスクリプト
========================
指定間隔で Left → F12 キーを自動送信する。
capture_tool.py と併用して、ページめくり＋キャプチャを自動化する。

必要パッケージ:
    pip install pynput

使い方:
    python auto_capture.py --count 120 --interval 2
    python auto_capture.py -n 120 -i 2 --wait 5
"""

import argparse
import time
import sys

from pynput.keyboard import Key, Controller


def main():
    parser = argparse.ArgumentParser(description="自動ページめくり＋キャプチャ")
    parser.add_argument(
        "--count", "-n",
        type=int,
        required=True,
        help="繰り返し回数（ページ数）",
    )
    parser.add_argument(
        "--interval", "-i",
        type=float,
        default=2.0,
        help="各回の間隔（秒） (default: 2.0)",
    )
    parser.add_argument(
        "--wait", "-w",
        type=float,
        default=5.0,
        help="開始前の待機時間（秒）。この間にキャプチャ対象ウィンドウをアクティブにする (default: 5.0)",
    )
    parser.add_argument(
        "--capture-key",
        default="f12",
        help="キャプチャキー (default: f12)",
    )
    args = parser.parse_args()

    key_map = {
        "f1": Key.f1, "f2": Key.f2, "f3": Key.f3, "f4": Key.f4,
        "f5": Key.f5, "f6": Key.f6, "f7": Key.f7, "f8": Key.f8,
        "f9": Key.f9, "f10": Key.f10, "f11": Key.f11, "f12": Key.f12,
    }
    capture_key = key_map.get(args.capture_key.lower())
    if not capture_key:
        print(f"[ERROR] 未対応のキー: {args.capture_key}")
        sys.exit(1)

    kb = Controller()

    print(f"=== 自動キャプチャ ===")
    print(f"  回数:         {args.count}")
    print(f"  間隔:         {args.interval}秒")
    print(f"  キャプチャキー: {args.capture_key.upper()}")
    print(f"  開始まで:     {args.wait}秒")
    print(f"  中断:         Ctrl+C")
    print()
    print(f"{args.wait}秒後に開始します。キャプチャ対象のウィンドウをアクティブにしてください...")

    time.sleep(args.wait)

    try:
        for i in range(1, args.count + 1):
            # Left キーでページめくり
            kb.press(Key.left)
            kb.release(Key.left)

            # キー入力が反映されるまで少し待つ
            time.sleep(0.5)

            # F12 キーでキャプチャ
            kb.press(capture_key)
            kb.release(capture_key)

            print(f"[{i}/{args.count}] Left → {args.capture_key.upper()}")

            # 最後の回はインターバル不要
            if i < args.count:
                time.sleep(args.interval)

    except KeyboardInterrupt:
        print(f"\n[中断] {i - 1}/{args.count} 回完了で中断しました")
        sys.exit(0)

    print(f"\n[完了] {args.count} 回すべて完了しました")


if __name__ == "__main__":
    main()
