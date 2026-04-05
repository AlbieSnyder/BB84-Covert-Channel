"""
File containing covert channel class. 
Note: the Python random library is not considered cryptographically secure and is used for simulation purposes.
"""
import random
from collections import deque


class CovertStateMachine:
    
    def __init__(self, PSK, k):
        self.trigger_PRNG = random.Random(PSK + "TRIGGER")
        self.keystream_PRNG = random.Random(PSK + "KEYSTREAM")
        self.k = k
        self.buffer = deque(maxlen=self.k)
        self.generate_trigger()


    def generate_trigger(self):
        self.trigger = [self.trigger_PRNG.getrandbits(1) for i in range(self.k)]

    def feed(self, basis_announcment):
        self.buffer.append(basis_announcment)
        if list(self.buffer) == self.trigger:
            self.buffer = deque(maxlen=self.k)
            self.generate_trigger()
            return True
        else:
            return False

    def next_keystream_bit(self):
        return self.keystream_PRNG.getrandbits(1)