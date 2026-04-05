import covert_channel
import qkd_experiment_base as base
import qkd_covert_alice
import qkd_covert_bob

class covert_experiment(base.qkd_experiment):

    def __init__(self, s_length, msg, trigger_length):
        super().__init__(s_length)
        self.s_length = s_length
        self.msg = msg
        self.PSK = "topsecret"
        self.trigger_length = trigger_length

    def build_phase(self):
        super().build_phase()
        self.a0 = qkd_covert_alice.covert_alice(self.s_length, self.PSK, self.trigger_length, self.msg)
        self.b0 = qkd_covert_bob.covert_bob(self.s_length, self.PSK, self.trigger_length)

    def key_generation_phase(self):
        # Generating the key based on measurement basis used and covert channel misreporting
        self.c_c.get_basis_seq(self.b0.basis_seq_b)
        self.a0.misreport()
        self.a0.key_gen_alice(self.c_c.put_basis_seq())
        self.a0.print_key_alice()
        self.c_c.ch_reset()
    
        self.c_c.get_basis_seq(self.a0.basis_seq_a)
        self.b0.extract_msg(self.a0.basis_seq_a)
        self.b0.key_gen_bob(self.c_c.put_basis_seq())
        self.b0.print_key_bob()
        self.c_c.ch_reset()

    def validation_phase(self):
        super().validation_phase()
        print("Covert Message: " + str(self.b0.msg) + "\n")
    
def main():
    test_msg = [1, 0, 1, 1]
    test_trigger_length = 7
    experiment = covert_experiment(4096, test_msg, test_trigger_length)
    experiment.execute()

if __name__ == '__main__':
    main()

