import qkd_bb84_base as bb
import covert_channel

class covert_alice(bb.alice_con):
    def __init__(self, s_length, PSK, k, msg):
        """
        PSK (String) - Pre-Shared Key
        k (int) - size of trigger
        msg (bitstring) - covert message
        """
        super().__init__(s_length)
        self.state_machine = covert_channel.CovertStateMachine(PSK, k)
        self.msg = msg
        self.msg_index = 0

    def misreport(self):
        for i in range(self.s_length - 1):
            basis = self.basis_seq_a[i]
            if self.state_machine.feed(basis):
                #Encodes ciphertext bit in basis array as 0 for rectilinear (+) and 1 for diagonal (×)
                self.basis_seq_a[i + 1] = int(self.msg[self.msg_index]) ^ self.state_machine.next_keystream_bit()
                self.msg_index += 1
                if self.msg_index == len(self.msg):
                    break
