#!/usr/bin/env python3
"""Local print server for 58mm thermal printer (384 dots/line, ESC/POS).
No external dependencies — uses only the Python standard library."""

import struct
import zlib
from http.server import HTTPServer, BaseHTTPRequestHandler

PRINTER_DEV = "/dev/usb/lp1"
DOTS_PER_LINE = 384
BYTES_PER_LINE = DOTS_PER_LINE // 8  # 48


def decode_png(data):
    """Minimal PNG decoder — returns (width, height, rows) with grayscale values."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG file")

    pos = 8
    ihdr = None
    idat_chunks = []

    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        pos += 12 + length  # 4 len + 4 type + data + 4 crc

        if chunk_type == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk_data[:13])
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)

    width, height, bit_depth, color_type = ihdr[0], ihdr[1], ihdr[2], ihdr[3]

    raw = zlib.decompress(b"".join(idat_chunks))

    # Determine bytes per pixel
    if color_type == 0:
        bpp = 1       # grayscale
    elif color_type == 2:
        bpp = 3       # RGB
    elif color_type == 4:
        bpp = 2       # grayscale + alpha
    elif color_type == 6:
        bpp = 4       # RGBA
    else:
        raise ValueError(f"Unsupported PNG color type: {color_type}")

    stride = width * bpp
    rows = []
    rpos = 0
    prev_row = b"\x00" * stride

    for _y in range(height):
        filter_type = raw[rpos]
        rpos += 1
        scanline = bytearray(raw[rpos:rpos + stride])
        rpos += stride

        if filter_type == 1:    # Sub
            for i in range(stride):
                a = scanline[i - bpp] if i >= bpp else 0
                scanline[i] = (scanline[i] + a) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                scanline[i] = (scanline[i] + prev_row[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                a = scanline[i - bpp] if i >= bpp else 0
                scanline[i] = (scanline[i] + (a + prev_row[i]) // 2) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = scanline[i - bpp] if i >= bpp else 0
                b = prev_row[i]
                c = prev_row[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                scanline[i] = (scanline[i] + pr) & 0xFF

        # Convert to grayscale row
        gray_row = []
        for x in range(width):
            offset = x * bpp
            if bpp == 1:
                gray_row.append(scanline[offset])
            elif bpp == 2:
                gray_row.append(scanline[offset])
            elif bpp == 3:
                r, g, b_ = scanline[offset], scanline[offset + 1], scanline[offset + 2]
                gray_row.append(int(0.299 * r + 0.587 * g + 0.114 * b_))
            elif bpp == 4:
                r, g, b_, a = scanline[offset], scanline[offset + 1], scanline[offset + 2], scanline[offset + 3]
                # Blend alpha against white background
                gray = 0.299 * r + 0.587 * g + 0.114 * b_
                gray_row.append(int(gray * a / 255 + 255 * (255 - a) / 255))

        rows.append(gray_row)
        prev_row = bytes(scanline)

    return width, height, rows


def image_to_escpos(png_data):
    """Convert PNG data to ESC/POS raster print commands."""
    width, height, rows = decode_png(png_data)

    # Convert to packed bitmap (1 = black, threshold 128)
    bitmap = bytearray()
    for row in rows:
        for bx in range(BYTES_PER_LINE):
            byte = 0
            for bit in range(8):
                x = bx * 8 + bit
                gray = row[x] if x < width else 255
                if gray < 128:
                    byte |= 1 << (7 - bit)
            bitmap.append(byte)

    # ESC/POS: GS v 0 (raster bit image)
    esc_pos = bytearray()
    esc_pos += b"\x1b\x40"  # ESC @ — initialize printer
    esc_pos += b"\x1d\x76\x30\x00"  # GS v 0, mode 0 (normal)
    esc_pos += struct.pack("<HH", BYTES_PER_LINE, height)
    esc_pos += bitmap
    esc_pos += b"\n\n\n\n"  # feed after print
    return esc_pos


class PrintHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self, *_):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self, *_):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            esc_pos = image_to_escpos(body)

            with open(PRINTER_DEV, "wb") as printer:
                printer.write(esc_pos)
                printer.flush()

            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(b"OK")
            print(f"Printed {DOTS_PER_LINE}x{len(esc_pos) // BYTES_PER_LINE} image ({len(esc_pos)} bytes)")
        except Exception as e:
            self.send_response(500)
            self._cors()
            self.end_headers()
            self.wfile.write(str(e).encode())
            print(f"Error: {e}")

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        print(f"[print-server] {fmt % args}")


if __name__ == "__main__":
    port = 8432
    server = HTTPServer(("127.0.0.1", port), PrintHandler)
    print(f"Thermal print server on http://127.0.0.1:{port}")
    print(f"Printer device: {PRINTER_DEV}")
    server.serve_forever()
