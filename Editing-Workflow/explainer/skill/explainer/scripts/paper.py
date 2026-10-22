#!/usr/bin/env python3
"""paper.py: the paper look's texture, a 540x960 RGBA PNG laid over the base ground at 1080x1920.

  paper.py [--out ../assets/paper.png]

Soft blotches, short fibres and a fine grain in a warm brown, from a fixed-seed LCG (after ClaudeAnimationBase's
makePaper in core.js, MIT), so it is the same bytes every time. No pixel darkens the ground by more than 6%, so every
role keeps the contrast gate E5 measured on the flat ground. Static: it never counts as motion (E4, E6). The composer
copies the shipped file (assets/paper.png); run this again only when the texture itself changes. Standard library only.
"""
import argparse, math, os, struct, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED = os.path.join(HERE, "..", "assets", "paper.png")
W, H = 540, 960
INK = (70, 50, 30)


def lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (x * 1664525 + 1013904223) & 0xFFFFFFFF
        yield x / 4294967296.0


def texture(path, seed=7, darkest=0.06):
    r = lcg(seed)
    a = [0.0] * (W * H)
    for _ in range(70):                                       # blotches: soft, wide, faint
        cx, cy, rad, k = next(r) * W, next(r) * H, 40 + next(r) * 100, darkest * (0.2 + 0.3 * next(r))
        for y in range(max(0, int(cy - rad)), min(H, int(cy + rad) + 1)):
            for x in range(max(0, int(cx - rad)), min(W, int(cx + rad) + 1)):
                d = ((x - cx) ** 2 + (y - cy) ** 2) / (rad * rad)
                if d < 1:
                    a[y * W + x] += k * (1 - d) ** 2
    for _ in range(600):                                      # fibres: short, thin, a little darker
        x, y, ang, n, k = next(r) * W, next(r) * H, next(r) * math.pi, 8 + int(next(r) * 22), darkest * (0.2 + 0.25 * next(r))
        for _ in range(n):
            if 0 <= int(x) < W and 0 <= int(y) < H:
                a[int(y) * W + int(x)] += k
            x, y = x + math.cos(ang), y + math.sin(ang)
    top = int(darkest * 255)
    rows = bytearray()
    for y in range(H):
        rows.append(0)
        for x in range(W):
            v = min(top, int((a[y * W + x] + 0.25 * darkest * next(r)) * 255))
            rows += bytes((INK[0], INK[1], INK[2], v))
    png = b"\x89PNG\r\n\x1a\n"
    for kind, body in ((b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0)), (b"IDAT", zlib.compress(bytes(rows), 9)), (b"IEND", b"")):
        png += struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return path


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=SHIPPED)
    print("wrote %s" % texture(ap.parse_args().out))
