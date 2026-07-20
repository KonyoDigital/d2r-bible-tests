#!/usr/bin/env python3
"""Decode D2R SpA1 sprite (raw RGBA8888, 40-byte header) to PNG, cropped to bbox."""
import sys, struct
from PIL import Image

def decode(path, out):
    with open(path, 'rb') as f:
        body = f.read()
    magic = body[0:4]
    if magic != b'SpA1':
        raise ValueError(f"{path}: bad magic {magic!r}")
    version = struct.unpack_from('<I', body, 4)[0]
    w = struct.unpack_from('<H', body, 0x06)[0]
    h = struct.unpack_from('<I', body, 0x0C)[0]
    pixels = body[0x28:]
    expected = w * h * 4
    if len(pixels) < expected:
        raise ValueError(f"{path}: pixel data too short ({len(pixels)} < {expected}) w={w} h={h}")
    img = Image.frombytes('RGBA', (w, h), pixels[:expected])
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img.save(out)
    print(f"{path} -> {out}  {w}x{h} (version={version:#x}) cropped={img.size}")

if __name__ == '__main__':
    for src in sys.argv[1:]:
        out = src.rsplit('.sprite', 1)[0] + '.png'
        decode(src, out)
