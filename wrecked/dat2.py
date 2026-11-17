"""Reads files from a Fallout 2 DAT archive."""

import struct
import zlib


class Dat:
    def __init__(self, path):
        self.stream = open(path, "rb")
        self.stream.seek(-8, 2)
        tree_size, data_size = struct.unpack("<II", self.stream.read(8))
        self.stream.seek(data_size - tree_size - 8)
        count = struct.unpack("<I", self.stream.read(4))[0]
        self.entries = {}
        for _ in range(count):
            length = struct.unpack("<I", self.stream.read(4))[0]
            name = self.stream.read(length).decode("latin-1").replace("\\", "/").lower()
            compressed, size, packed, offset = struct.unpack("<BIII", self.stream.read(13))
            self.entries[name] = (compressed, size, packed, offset)

    def names(self, prefix=""):
        return [name for name in self.entries if name.startswith(prefix.lower())]

    def read(self, name):
        compressed, size, packed, offset = self.entries[name.replace("\\", "/").lower()]
        self.stream.seek(offset)
        data = self.stream.read(packed)
        return zlib.decompress(data) if compressed else data
