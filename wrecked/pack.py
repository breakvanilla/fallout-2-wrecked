"""Shrinks the Blender renders to game size and writes sprites.dat.

Shade is 128 where the art looks like flat ground under the same light, so
the game can darken or lighten any color with its own intensity table.

Usage: pack.py <render folder> <sprites.dat>
"""

import math
import os
import struct
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

SCALE = 8


def load(path):
    image = np.asarray(Image.open(path).convert("RGBA"), dtype=np.float32) / 255.0
    return image


def shrink(image):
    """Box filter by SCALE with premultiplied alpha: (grey, alpha)."""
    height, width = image.shape[0] // SCALE, image.shape[1] // SCALE
    grey = image[..., :3].mean(axis=2)
    alpha = image[..., 3]
    blocks = lambda a: a[:height * SCALE, :width * SCALE].reshape(height, SCALE, width, SCALE).mean(axis=(1, 3))
    covered = blocks(alpha)
    value = blocks(grey * alpha) / np.maximum(covered, 1e-6)
    return value, covered


def flat_level(path):
    value, covered = shrink(load(path))
    return float(np.median(value[covered > 0.99]))


def to_shade(value, level, low=16, high=240):
    return np.clip(np.round(128.0 * value / level), low, high).astype(np.uint8)


def sprite(name, frames, anchor, channels):
    height, width = frames[0][0].shape
    data = b"".join(np.stack(frame, axis=-1).astype(np.uint8).tobytes() for frame in frames)
    header = name.encode("ascii").ljust(16, b"\0")
    header += struct.pack("<4H2h", len(frames), width, height, channels, anchor[0], anchor[1])
    return header + data


def main():
    folder, output = sys.argv[1:3]
    path = lambda name: os.path.join(folder, name)
    sprites = []

    level = flat_level(path("rock_flat.png"))
    # Spinning chunks of stone, wood, metal and cloth.
    for kind in ("rock", "plank", "shard", "scrap"):
        for variant in range(4):
            frames = []
            bottom = 0
            for index in range(8):
                value, covered = shrink(load(path(f"{kind}{variant}_{index}.png")))
                alpha = np.where(covered > 0.45, 255, 0)
                rows = np.nonzero(alpha.any(axis=1))[0]
                bottom = max(bottom, int(rows.max()) if len(rows) else 0)
                frames.append((value, alpha))
            # Chunks take the color they are given on average; metal keeps
            # more of its glints.
            middle = np.median(np.concatenate([value[alpha > 0] for value, alpha in frames]))
            high = 190 if kind == "shard" else 150
            frames = [(to_shade(value, middle * 1.05, 50, high), alpha) for value, alpha in frames]
            width = frames[0][0].shape[1]
            sprites.append(sprite(f"{kind}{variant}", frames, (width // 2, bottom), 2))

    for variant in range(4):
        value, covered = shrink(load(path(f"puff{variant}.png")))
        inside = covered > 0.2
        low, high = np.percentile(value[inside], 3), np.percentile(value[inside], 97)
        shade = np.clip((value - low) / max(high - low, 1e-6), 0, 1)
        alpha = gaussian_filter(covered, 1.1)
        height, width = alpha.shape
        y, x = np.mgrid[0:height, 0:width]
        radial = np.clip(1.15 - np.hypot((x - width / 2) / (width / 2), (y - height / 2) / (height / 2)), 0, 1)
        rng = np.random.default_rng(variant)
        noise = gaussian_filter(rng.random((height, width)), 1.5)
        noise = (noise - noise.min()) / (noise.max() - noise.min())
        alpha = np.clip(alpha * (0.55 + 0.45 * radial) * (0.7 + 0.5 * noise), 0, 1)
        sprites.append(sprite(f"puff{variant}", [(np.round(shade * 255), np.round(alpha * 255))], (width // 2, height // 2), 2))

    for size, radius in {"s": 19, "m": 27, "l": 39}.items():
        level_value, _ = shrink(load(path(f"crater{size}_flat.png")))
        frames = []
        for variant in range(2):
            value, covered = shrink(load(path(f"crater{size}{variant}.png")))
            height, width = value.shape
            ratio = np.where(covered > 0.01, value / np.maximum(level_value, 1e-6), 1.0)
            y, x = np.mgrid[0:height, 0:width]
            ground_x = x + 0.5 - width / 2
            ground_y = (y + 0.5 - height / 2) * 2.0
            r = np.hypot(ground_x, ground_y) / radius
            angle = np.arctan2(ground_y, ground_x)
            rng = np.random.default_rng(40 + variant + radius)
            noise = gaussian_filter(rng.random((height, width)), 1.2)
            noise = (noise - noise.min()) / (noise.max() - noise.min())
            # Scorch: blotchy and black at the heart, then thin rays of soot
            # thrown out over the rim.
            blotch = gaussian_filter(rng.random((height, width)), 2.5)
            blotch = (blotch - blotch.min()) / (blotch.max() - blotch.min())
            scorch = 1 - 0.6 * np.exp(-(r / 0.8) ** 2) * (0.55 + 0.45 * blotch)
            rays = np.clip(np.sin(angle * 23 + variant * 5 + 4 * noise) * np.sin(angle * 7 + variant), 0, 1) ** 3
            scorch *= 1 - 0.3 * rays * np.clip((r - 0.7) / 0.2, 0, 1) * np.clip((1.5 - r) / 0.5, 0, 1)
            shade = 128.0 * ratio * scorch
            alpha = np.clip((1.45 - r) / 0.5, 0, 1)
            shade = 128.0 + (shade - 128.0) * np.clip((1.35 - r) / 0.4, 0, 1)
            frames.append((np.clip(np.round(shade), 8, 245), np.round(alpha * 255)))
        height, width = frames[0][0].shape
        for variant, frame in enumerate(frames):
            sprites.append(sprite(f"crater{size}{variant}", [frame], (width // 2, height // 2), 2))

    # Rubble: stone heaps, then boards, sheets and rags.
    piles = [(f"pile{size}{variant}", radius) for size, radius in {"s": 11, "l": 18}.items() for variant in range(3)]
    piles += [(f"pile{prefix}{size}{variant}", radius) for prefix in "wmc" for size, radius in {"s": 11, "l": 18}.items() for variant in range(2)]
    for name, radius in piles:
        value, covered = shrink(load(path(f"{name}_shade.png")))
        id_value, id_covered = shrink(load(path(f"{name}_id.png")))
        chunk = np.clip(np.round((id_value - 1 / 16) * 8), 0, 7)
        alpha = np.where(covered > 0.5, 255, 0)
        height, width = value.shape
        anchor = (width // 2, int(round(height / 2 + radius * 0.15 * math.cos(math.radians(30)))))
        sprites.append(sprite(name, [(to_shade(value, level, 50, 175), chunk, alpha)], anchor, 3))

    with open(output, "wb") as stream:
        stream.write(b"DST1" + struct.pack("<I", len(sprites)))
        for item in sprites:
            stream.write(item)
    print(f"{len(sprites)} sprites, {os.path.getsize(output)} bytes")


main()
