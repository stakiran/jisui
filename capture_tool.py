"""
キャプチャツール
================
- 起動時に矩形範囲を一度だけ選択する
- 以降、F12 を押すたびにその範囲をキャプチャして保存
- ファイル名は連番 (1.png, 2.png, ...)
- 既存ファイルを見て次の番号を自動決定（上書きしない）

必要パッケージ:
    pip install pynput Pillow

macOS の場合は追加で:
    pip install pyobjc-framework-Quartz

Linux (X11) の場合は追加で:
    pip install python-xlib

使い方:
    python capture_tool.py [--output-dir ./captures] [--hotkey f12]
"""

import argparse
import os
import re
import subprocess
import sys
import platform
import tkinter as tk
from pathlib import Path

from pynput import keyboard


def get_next_number(output_dir: Path) -> int:
    """出力ディレクトリの既存ファイルを見て、次の連番を返す"""
    existing = []
    for f in output_dir.glob("*.png"):
        m = re.match(r"^(\d+)\.png$", f.name)
        if m:
            existing.append(int(m.group(1)))
    return max(existing, default=0) + 1


class RegionSelector:
    """透明オーバーレイで矩形範囲を選択するUI"""

    def __init__(self, on_selected):
        self.on_selected = on_selected
        self.start_x = 0
        self.start_y = 0
        self.rect_id = None

    def show(self):
        self.root = tk.Tk()
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)
        self.root.wait_visibility(self.root)

        # 半透明オーバーレイ（プラットフォーム依存）
        system = platform.system()
        if system == "Linux":
            self.root.attributes("-alpha", 0.3)
        elif system == "Darwin":
            self.root.attributes("-alpha", 0.3)
        elif system == "Windows":
            self.root.attributes("-alpha", 0.3)

        self.root.configure(cursor="crosshair", bg="black")

        self.canvas = tk.Canvas(
            self.root, highlightthickness=0, bg="black"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.bind("<Escape>", lambda e: self._cancel())

        self.root.mainloop()

    def _on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        self.rect_id = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="red", width=2
        )

    def _on_drag(self, event):
        if self.rect_id:
            # canvas座標で矩形を更新
            x0 = self.start_x - self.root.winfo_rootx()
            y0 = self.start_y - self.root.winfo_rooty()
            self.canvas.coords(self.rect_id, x0, y0, event.x, event.y)

    def _on_release(self, event):
        end_x = event.x_root
        end_y = event.y_root

        # 正規化（左上→右下）
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        self.root.destroy()

        # 小さすぎる選択は無視
        if (x2 - x1) > 5 and (y2 - y1) > 5:
            self.on_selected((x1, y1, x2, y2))

    def _cancel(self):
        self.root.destroy()


def capture_region(bbox, output_path: Path):
    """指定範囲をスクリーンキャプチャして保存"""
    system = platform.system()
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1

    if system == "Linux":
        # scrot / gnome-screenshot / import (ImageMagick) のいずれかを使用
        try:
            subprocess.run(
                ["import", "-window", "root", "-crop",
                 f"{w}x{h}+{x1}+{y1}", str(output_path)],
                check=True
            )
            return True
        except FileNotFoundError:
            pass

        try:
            subprocess.run(
                ["scrot", "-a", f"{x1},{y1},{w},{h}", str(output_path)],
                check=True
            )
            return True
        except FileNotFoundError:
            pass

        print("[ERROR] スクリーンキャプチャツールが見つかりません。")
        print("  sudo apt install imagemagick  または  sudo apt install scrot")
        return False

    elif system == "Darwin":
        subprocess.run(
            ["screencapture", "-R", f"{x1},{y1},{w},{h}", str(output_path)],
            check=True,
        )
        return True

    elif system == "Windows":
        # Pillow の ImageGrab を使用
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        img.save(str(output_path))
        return True

    return False


def select_region_once() -> tuple[int, int, int, int] | None:
    """起動時に一度だけ矩形範囲を選択させる。キャンセル時は None。"""
    result: list[tuple[int, int, int, int]] = []

    def on_selected(bbox):
        result.append(bbox)

    print("[SETUP] 画面上でキャプチャ範囲をドラッグで選択してください (Escでキャンセル)")
    selector = RegionSelector(on_selected)
    selector.show()

    return result[0] if result else None


def main():
    parser = argparse.ArgumentParser(description="スクリーンキャプチャツール")
    parser.add_argument(
        "--output-dir", "-o",
        default="./captures",
        help="保存先ディレクトリ (default: ./captures)",
    )
    parser.add_argument(
        "--hotkey", "-k",
        default="f12",
        help="キャプチャ起動キー (default: f12)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ホットキーのマッピング
    key_map = {
        "f1": keyboard.Key.f1, "f2": keyboard.Key.f2,
        "f3": keyboard.Key.f3, "f4": keyboard.Key.f4,
        "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
        "f7": keyboard.Key.f7, "f8": keyboard.Key.f8,
        "f9": keyboard.Key.f9, "f10": keyboard.Key.f10,
        "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
    }
    hotkey = key_map.get(args.hotkey.lower())
    if not hotkey:
        print(f"[ERROR] 未対応のキー: {args.hotkey}")
        sys.exit(1)

    # --- 起動時に一度だけ範囲を選択 ---
    bbox = select_region_once()
    if bbox is None:
        print("[CANCEL] 範囲が選択されませんでした。終了します。")
        sys.exit(0)

    x1, y1, x2, y2 = bbox
    print(f"\n=== キャプチャツール ===")
    print(f"  範囲:       ({x1}, {y1}) → ({x2}, {y2})  [{x2-x1}x{y2-y1}px]")
    print(f"  保存先:     {output_dir.resolve()}")
    print(f"  ホットキー: {args.hotkey.upper()} を押すとキャプチャ")
    print(f"  終了:       Ctrl+C")
    print()

    # --- 以降、ホットキーで同じ範囲を繰り返しキャプチャ ---
    def on_press(key):
        if key == hotkey:
            num = get_next_number(output_dir)
            output_path = output_dir / f"{num}.png"
            if capture_region(bbox, output_path):
                print(f"[CAPTURED] {output_path}")
            else:
                print("[ERROR] キャプチャに失敗しました")

    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    try:
        while listener.is_alive():
            listener.join(timeout=0.5)
    except KeyboardInterrupt:
        print("\n終了します")
    finally:
        listener.stop()


if __name__ == "__main__":
    main()
