import qkd_bb84_base as bb
import covert_channel

class covert_bob(bb.bob_con):
    def __init__(self, s_length, PSK, k):
        """
        PSK (String) - Pre-Shared Key
        k (int) - size of trigger
        """
        super().__init__(s_length)
        self.state_machine = covert_channel.CovertStateMachine(PSK, k)
        self.msg = list()


    def extract_msg(self, alice_bases):
        for i in range(self.s_length - 1):
            basis = alice_bases[i]
            if self.state_machine.feed(basis):
                self.msg.append(alice_bases[i + 1] ^ self.state_machine.next_keystream_bit())