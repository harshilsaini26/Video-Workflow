"""imagesize.py: an image's pixel size from its own header (PNG, JPEG, WebP, GIF), with the standard library only, so a
scene can lay a creator's image out before any browser sees it (and no machine needs PIL).

  size(path) -> (width, height) as shown (a phone JPEG turned by its EXIF orientation is measured turned);
                ValueError("... not a PNG, JPEG, WebP or GIF") otherwise
  alpha(path) -> True when the file can hold transparency (a PNG with an alpha channel or tRNS, a WebP with alpha,
                a GIF): a cut-out a title can sit behind; False for a JPEG or an opaque PNG or WebP
"""
import struct

SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}   # JPEG frame headers (not C4, C8, CC)


def _orientation(app1):
    """The EXIF orientation (1 to 8) in an APP1 segment's data, or 1."""
    if app1[:6] != b"Exif\x00\x00" or len(app1) < 14:
        return 1
    t = app1[6:]
    end = {b"MM": ">", b"II": "<"}.get(t[:2])
    if not end:
        return 1
    try:
        ifd = struct.unpack(end + "I", t[4:8])[0]
        for k in range(struct.unpack(end + "H", t[ifd:ifd + 2])[0]):
            e = t[ifd + 2 + 12 * k: ifd + 14 + 12 * k]
            if struct.unpack(end + "H", e[:2])[0] == 0x0112:
                return struct.unpack(end + "H", e[8:10])[0]
    except struct.error:
        pass
    return 1


def _jpeg(f):
    turned = False
    f.seek(2)
    while True:
        b = f.read(1)
        while b and b != b"\xff":
            b = f.read(1)
        while b == b"\xff":
            b = f.read(1)
        if not b:
            return None
        marker = b[0]
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:      # no length
            continue
        seg = f.read(2)
        if len(seg) < 2:
            return None
        n = struct.unpack(">H", seg)[0]
        if marker in SOF:
            data = f.read(5)
            h, w = struct.unpack(">xHH", data)
            return (h, w) if turned else (w, h)
        if marker == 0xE1:
            turned = turned or _orientation(f.read(n - 2)) in (5, 6, 7, 8)
            continue
        f.seek(n - 2, 1)


def _webp(head, f):
    kind = head[12:16]
    if kind == b"VP8X":
        return 1 + int.from_bytes(head[24:27], "little"), 1 + int.from_bytes(head[27:30], "little")
    if kind == b"VP8L":
        b = head[21:25]
        bits = int.from_bytes(b, "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if kind == b"VP8 ":
        w, h = struct.unpack("<HH", head[26:30])
        return w & 0x3FFF, h & 0x3FFF
    return None


def size(path):
    with open(path, "rb") as f:
        head = f.read(32)
        wh = None
        if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
            wh = struct.unpack(">II", head[16:24])
        elif head[:2] == b"\xff\xd8":
            wh = _jpeg(f)
        elif head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            wh = _webp(head, f)
        elif head[:6] in (b"GIF87a", b"GIF89a"):
            wh = struct.unpack("<HH", head[6:10])
    if not wh or not wh[0] or not wh[1]:
        raise ValueError("%s is not a PNG, JPEG, WebP or GIF (or its header is damaged)" % path)
    return int(wh[0]), int(wh[1])


def alpha(path):
    with open(path, "rb") as f:
        head = f.read(32)
        if head[:8] == b"\x89PNG\r\n\x1a\n":
            if head[25] in (4, 6):                    # grey + alpha, RGB + alpha
                return True
            f.seek(8)
            while True:                               # a tRNS chunk before the image data makes a colour transparent
                c = f.read(8)
                if len(c) < 8 or c[4:8] == b"IDAT":
                    return False
                if c[4:8] == b"tRNS":
                    return True
                f.seek(struct.unpack(">I", c[:4])[0] + 4, 1)
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return (head[12:16] == b"VP8X" and bool(head[20] & 0x10)) or (head[12:16] == b"VP8L" and bool(head[24] & 0x10))
        return head[:6] in (b"GIF87a", b"GIF89a")
