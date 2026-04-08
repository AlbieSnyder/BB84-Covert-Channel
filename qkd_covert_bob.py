import qkd_bb84_base as bb
import covert_channel

class covert_bob(bb.bob_con):
    def __init__(self, s_length, PSK, trigger_length):
        """
        PSK (String) - Pre-Shared Key
        trigger_length (int) - size of trigger
        """
        super().__init__(s_length)
        self.state_machine = covert_channel.CovertStateMachine(PSK, trigger_length)
        self.full_msg = list()
        self.preamble_length = (s_length // 2**trigger_length).bit_length()


    def extract_msg(self, alice_bases):
        self.actual_capacity = 0
        for i in range(self.s_length - 1):
            basis = alice_bases[i]
            if self.state_machine.feed(basis):
                self.full_msg.append(int(alice_bases[i + 1]) ^ self.state_machine.next_keystream_bit())
                self.actual_capacity += 1
        preamble = self.full_msg[:self.preamble_length]
        msg_length = int(''.join(str(i) for i in preamble), 2)
        self.msg = self.full_msg[self.preamble_length:self.preamble_length+msg_length]