import covert_channel
import qkd_experiment_base as base
import qkd_noise_model
import qkd_covert_alice
import qkd_covert_bob
import copy
import numpy

class covert_noise_experiment(base.qkd_experiment):

    def __init__(self, s_length, msg, trigger_length, noise_error_rate,
                 jitter=0.25, session_id=None, covert=True):
        """
        jitter (float) - session-to-session drift half-width of the noise rate
        session_id - per-session identifier for the covert PRNGs
        covert (bool) - if False, Alice announces her true bases (baseline arm).
                        Both arms then run identical code apart from misreporting.
        """
        super().__init__(s_length)
        self.s_length = s_length
        self.msg = msg
        self.PSK = "topsecret"
        self.trigger_length = trigger_length
        self.noise_error_rate = noise_error_rate
        self.jitter = jitter
        self.session_id = session_id
        self.covert = covert

    def build_phase(self):
        super().build_phase()
        self.q_c = qkd_noise_model.variable_noisy_q_channel(self.noise_error_rate, self.jitter)
        self.a0 = qkd_covert_alice.covert_alice(self.s_length, self.PSK, self.trigger_length, self.msg, self.session_id)
        self.b0 = qkd_covert_bob.covert_bob(self.s_length, self.PSK, self.trigger_length, self.session_id)

    def key_generation_phase(self):
        # Generating the key based on measurement basis used and covert channel misreporting
        self.c_c.get_basis_seq(self.b0.basis_seq_b)
        if self.covert:
            self.a0.misreport()
        self.a0.key_gen_alice(self.c_c.put_basis_seq())
        #self.a0.print_key_alice()
        self.c_c.ch_reset()
    
        self.c_c.get_basis_seq(self.a0.basis_seq_a)
        if self.covert:
            self.b0.extract_msg(self.a0.basis_seq_a)
        else:
            self.b0.actual_capacity = 0
        self.b0.key_gen_bob(self.c_c.put_basis_seq())
        #self.b0.print_key_bob()
        self.c_c.ch_reset()
    
    def validation_phase(self):
        super().validation_phase()
        #print("Covert Message: " + str(self.b0.msg) + "\n")
    
    

def main():
    test_msg = [1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0]
    test_trigger_length = 7
    QBERs = []
    num_experiments = 1

    for i in range(num_experiments):
        experiment = covert_noise_experiment(8192, test_msg, test_trigger_length, 0.03)
        experiment.execute()
        QBERs.append(experiment.calc_perc_error)

    print("Average QBER: " + str(numpy.mean(QBERs)) + "%")

if __name__ == '__main__':
    main()