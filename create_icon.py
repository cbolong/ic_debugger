"""產生 icon.ico / icon.png（IC 晶片＋檢視游標的意象）。

只在改圖示時需要跑（需要 Pillow）；產物 icon.ico 已 commit 進 repo，
CI build 不需要執行本檔。用法：python create_icon.py
"""

from PIL import Image, ImageDraw

SIZES = [16, 24, 32, 48, 64, 128, 256]

BG = (28, 28, 30, 255)        # 深灰底（同 UI topbar #1c1c1e）
CHIP = (58, 58, 60, 255)      # 晶片本體
PIN = (151, 161, 176, 255)    # 接腳
ACCENT = (74, 158, 255, 255)  # 藍 accent（同深色主題 --c-accent）
GRID = (230, 234, 240, 255)   # die 上的格線


def draw_icon(size: int) -> Image.Image:
    s = 16  # 以 16 為基準格放大
    img = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = size * s / 16.0  # 1 格

    # 圓角底
    d.rounded_rectangle([u * 0.5, u * 0.5, u * 15.5, u * 15.5], radius=u * 3, fill=BG)

    # 接腳（上下左右各 3 根）
    pin_w, pin_l = u * 0.9, u * 1.6
    for i in range(3):
        c = u * (5 + i * 3)
        d.rectangle([c - pin_w / 2, u * 2.2, c + pin_w / 2, u * 2.2 + pin_l], fill=PIN)
        d.rectangle([c - pin_w / 2, u * 13.8 - pin_l, c + pin_w / 2, u * 13.8], fill=PIN)
        d.rectangle([u * 2.2, c - pin_w / 2, u * 2.2 + pin_l, c + pin_w / 2], fill=PIN)
        d.rectangle([u * 13.8 - pin_l, c - pin_w / 2, u * 13.8, c + pin_w / 2], fill=PIN)

    # 晶片本體與 die
    d.rounded_rectangle([u * 3.6, u * 3.6, u * 12.4, u * 12.4], radius=u * 1.2, fill=CHIP)
    d.rounded_rectangle([u * 5.2, u * 5.2, u * 10.8, u * 10.8], radius=u * 0.7,
                        outline=GRID, width=max(1, int(u * 0.35)))

    # die 內的「register bits」：一列亮一列暗
    bar_h = u * 0.9
    for r, on in enumerate([True, False, True]):
        y = u * (6.1 + r * 1.6)
        d.rounded_rectangle(
            [u * 6.1, y, u * 9.9, y + bar_h], radius=bar_h / 2,
            fill=ACCENT if on else (PIN[0], PIN[1], PIN[2], 140),
        )

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    imgs = {s: draw_icon(s) for s in SIZES}
    imgs[256].save("icon.png")
    imgs[256].save("icon.ico", sizes=[(s, s) for s in SIZES])
    print("寫出 icon.ico / icon.png")


if __name__ == "__main__":
    main()
