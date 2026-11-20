"""
File containing covert channel class. 
Note: the Python random library is not considered cryptographically secure and is used for simulation purposes.
"""
import random
from collections import deque


class CovertStateMachine:
    
    def __init__(self, PSK, trigger_length, session_id=None):
        # session_id gives each QKD session its own trigger and keystream sequence,
        # so the keystream is never reused across sessions. None keeps the original
        # (single-session) seeding for backward compatibility.
        prefix = PSK if session_id is None else f"{PSK}|{session_id}|"
        self.trigger_PRNG = random.Random(prefix + "TRIGGER")
        self.keystream_PRNG = random.Random(prefix + "KEYSTREAM")
        self.trigger_length = trigger_length
        self.buffer = deque(maxlen=self.trigger_length)
        self.generate_trigger()


    def generate_trigger(self):
        self.trigger = [self.trigger_PRNG.getrandbits(1) for i in range(self.trigger_length)]

    def feed(self, basis_announcment):
        self.buffer.append(basis_announcment)
        if list(self.buffer) == self.trigger:
            self.buffer = deque(maxlen=self.trigger_length)
            self.generate_trigger()
            return True
        else:
            return False

    def next_keystream_bit(self):
        return self.keystream_PRNG.getrandbits(1)