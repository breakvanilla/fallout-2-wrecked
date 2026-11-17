"""Draws every sprite of sprites.dat on a sandy floor color, 4 times larger.

Usage: preview.py <sprites.dat> <output.png>
"""

import struct
import sys

import numpy as np
from PIL import Image

PILE_COLORS = np.array([[120, 110, 100], [140, 120, 90], [90, 85, 80], [160, 150, 130], [110, 90, 70], [130, 130, 120], [100, 100, 95], [150, 140, 120]], float)


def main():
    data = open(sys.argv[1], "rb").read()
    count = struct.unpack("<I", data[4:8])[0]
    position = 8
    tiles = []
    base = np.array([150, 120, 85.0])
    for _ in range(count):
        name = data[position:position + 16].rstrip(b"\0").decode()
        frames, width, height, channels, _, _ = struct.unpack("<4H2h", data[position + 16:position + 28])
        position += 28
        size = frames * width * height * channels
        pixels = np.frombuffer(data[position:position + size], np.uint8).reshape(frames, height, width, channels)
        position += size
        for frame in range(min(frames, 8)):
            shade = pixels[frame, ..., 0] / 128.0
            alpha = pixels[frame, ..., -1][..., None] / 255.0
            if name.startswith("crater"):
                image = base * (1 + (shade[..., None] - 1) * alpha)
            elif name.startswith("puff"):
                image = np.dstack([shade * 128 * 0.5 + 60] * 3) * alpha + base * (1 - alpha)
            elif name.startswith("pile"):
                image = np.where(alpha >= 0.5, PILE_COLORS[pixels[frame, ..., 1]] * shade[..., None], base)
            else:
                image = np.where(alpha >= 0.5, np.array([120, 115, 105.0]) * shade[..., None], base)
            tiles.append(Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).resize((width * 4, height * 4), Image.NEAREST))
    sheet_width = 1400
    x = y = row = 0
    sheet = Image.new("RGB", (sheet_width, 2000), tuple(int(v) for v in base))
    for tile in tiles:
        if x + tile.width > sheet_width:
            x, y, row = 0, y + row + 6, 0
        sheet.paste(tile, (x, y))
        x += tile.width + 6
        row = max(row, tile.height)
    sheet.crop((0, 0, sheet_width, y + row)).save(sys.argv[2])


main()
