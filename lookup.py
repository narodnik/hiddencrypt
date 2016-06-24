import os
import pickle
import pyscrypt
import pyaes
import hashlib
import struct

class Lookup:

    def __init__(self, filename):
        self._filename = filename

    def setup(self):
        self._salt = os.urandom(20)
        self._lookup = []
        for i in range(1000):
            key = os.urandom(32)
            data = os.urandom(8)
            aes = pyaes.AESModeOfOperationCTR(key)
            ciphertext = aes.encrypt(data)
            self._lookup.append(ciphertext)
        self._save()

    def _save(self):
        info = {"salt": self._salt,
                "lookup": self._lookup}
        with open(self._filename, "wb") as f:
            pickle.dump(info, f)

    def load(self):
        with open(self._filename, "rb") as f:
            info = pickle.load(f)
        self._salt = info["salt"]
        self._lookup = info["lookup"]

    def add(self, password, offset):
        key = self._generate_key(password)
        slot = self._compute_slot(key)
        data = struct.pack("Q", offset)
        aes = pyaes.AESModeOfOperationCTR(key)
        ciphertext = aes.encrypt(data)
        self._lookup[slot] = ciphertext
        self._save()

    def _generate_key(self, password):
        return pyscrypt.hash(password,
                             self._salt,
                             N = 2**2, 
                             r = 8, 
                             p = 1, 
                             dkLen = 32)

    def _compute_slot(self, hashed):
        return struct.unpack("Q", hashed[:8])[0] % len(self._lookup)

    def get(self, password):
        key = self._generate_key(password)
        slot = self._compute_slot(key)
        ciphertext = self._lookup[slot]
        aes = pyaes.AESModeOfOperationCTR(key)
        data = aes.decrypt(ciphertext)
        offset = struct.unpack("Q", data)[0]
        return offset

if __name__ == "__main__":
    l = Lookup("lookup")
    l.setup()
    l.add(b"foobar", 419419)
    l = Lookup("lookup")
    l.load()
    print(l.get(b"foobar"))

