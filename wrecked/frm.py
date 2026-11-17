"""Fallout FRM art and the game palette."""

import struct

import numpy as np


def palette(data):
    colors = np.frombuffer(data[:768], dtype=np.uint8).reshape(256, 3).astype(np.int32)
    return np.clip(colors * 4, 0, 255).astype(np.uint8)


def read_frm(data):
    """Returns (fps, action frame, frames per direction, [direction][frame] = (w, h, dx, dy, pixels), offsets)."""
    version, fps, action, count = struct.unpack(">IHHH", data[:10])
    shifts_x = struct.unpack(">6h", data[10:22])
    shifts_y = struct.unpack(">6h", data[22:34])
    offsets = struct.unpack(">6I", data[34:58])
    directions = []
    base = 62
    for direction in range(6):
        if direction > 0 and offsets[direction] == offsets[0]:
            directions.append(directions[0])
            continue
        position = base + offsets[direction]
        frames = []
        for _ in range(count):
            width, height, size, dx, dy = struct.unpack(">HHIhh", data[position:position + 12])
            pixels = np.frombuffer(data[position + 12:position + 12 + size], dtype=np.uint8).reshape(height, width)
            frames.append((width, height, dx, dy, pixels))
            position += 12 + size
        directions.append(frames)
    return fps, action, count, directions, (shifts_x, shifts_y)
