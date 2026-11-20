import qkd_bb84_base as bb
import covert_channel
import math

class covert_alice(bb.alice_con):
    def __init__(self, s_length, PSK, trigger_length, msg, session_id=None):
        """
        PSK (String) - Pre-Shared Key
        k (int) - size of trigger
        msg (bit list) - covert message
        session_id - per-session identifier for PRNG seeding (must match Bob's)
        """
        super().__init__(s_length)
        self.state_machine = covert_channel.CovertStateMachine(PSK, trigger_length, session_id)
        self.msg = msg
        self.covert_index = 0
        preamble_length = (s_length // 2**trigger_length).bit_length()
        preamble_string = bin(len(msg))[2:].zfill(preamble_length)
        self.preamble = [int(bit) for bit in preamble_string]
        self.full_msg = self.preamble + msg

    def misreport(self):
        counter = 0
        for i in range(self.s_length - 1):
            basis = self.basis_seq_a[i]
            if self.state_machine.feed(basis):
                #When the message bits end, send random data
                if self.covert_index >= len(self.full_msg):
                    next_bit = self.state_machine.next_keystream_bit()
                    if self.basis_seq_a[i+1] != next_bit:
                        counter += 1
                    self.basis_seq_a[i+1] = next_bit
                else:
                    #Encodes ciphertext bit in basis array as 0 for rectilinear (+) and 1 for diagonal (×)
                    covert_bit = self.full_msg[self.covert_index] ^ self.state_machine.next_keystream_bit()
                    if self.basis_seq_a[i + 1] != covert_bit:
                        counter += 1
                    self.basis_seq_a[i + 1] = covert_bit
                    self.covert_index += 1