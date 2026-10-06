"""Generate simple PWA icons for ResQGrid AI."""

import struct
import zlib
from pathlib import Path


def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    chunk = chunk_type + data
    crc = zlib.crc32(chunk) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", crc)


def make_png(size: int, output_path: Path) -> None:
    """Create a size x size PNG with a blue background and white center circle."""
    bg = (30, 58, 138)  # dark blue #1e3a8a
    fg = (255, 255, 255)  # white
    cx, cy = size / 2, size / 2
    radius = size * 0.28

    raw = bytearray()
    for y in range(size):
        raw.append(0)  # filter byte: none
        for x in range(size):
            dx = x + 0.5 - cx
            dy = y + 0.5 - cy
            if dx * dx + dy * dy <= radius * radius:
                raw.extend(fg)
            else:
                raw.extend(bg)

    compressed = zlib.compress(bytes(raw), level=9)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    idat = png_chunk(b"IDAT", compressed)
    iend = png_chunk(b"IEND", b"")

    output_path.write_bytes(signature + png_chunk(b"IHDR", ihdr) + idat + iend)


if __name__ == "__main__":
    out_dir = Path(__file__).parent.parent / "public" / "icons"
    out_dir.mkdir(parents=True, exist_ok=True)
    make_png(192, out_dir / "icon-192x192.png")
    make_png(512, out_dir / "icon-512x512.png")
    print(f"Icons written to {out_dir}")
