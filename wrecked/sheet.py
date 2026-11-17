"""Puts the middle of test frames side by side, twice as large.

Usage: sheet.py <test folder> <explosion> <frames,comma separated> <output.png>
"""

import sys

from PIL import Image

folder, explosion, frames, output = sys.argv[1:5]
box = (160, 60, 480, 300)
images = [Image.open(f"{folder}/e{explosion}_f{int(frame):03d}.png").crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.NEAREST) for frame in frames.split(",")]
sheet = Image.new("RGB", (images[0].width * len(images), images[0].height))
for index, image in enumerate(images):
    sheet.paste(image, (index * images[0].width, 0))
sheet.save(output)
