import covert_channel
import qkd_experiment_base as base
import qkd_noise_model
import qkd_covert_alice
import qkd_covert_bob
import copy
import numpy

class covert_experiment(base.qkd_experiment):

    def __init__(self, s_length, msg, trigger_length, noise_error_rate):
        super().__init__(s_length)
        self.s_length = s_length
        self.msg = msg
        self.PSK = "topsecret"
        self.trigger_length = trigger_length
        self.noise_error_rate = noise_error_rate

    def build_phase(self):
        super().build_phase()
        self.q_c = qkd_noise_model.variable_noisy_q_channel(self.noise_error_rate)
        self.a0 = qkd_covert_alice.covert_alice(self.s_length, self.PSK, self.trigger_length, self.msg)
        self.b0 = qkd_covert_bob.covert_bob(self.s_length, self.PSK, self.trigger_length)

    def run_phase(self):
        
        # Generating Alice's qubits, measuring them after transmitting to Bob
        self.a0.seq_init_alice()
        self.a0.generate_qubit_stream()
        
        self.q_c.get_state(self.a0.return_state())
        self.q_c.corrupt_state()

        self.b0.seq_init_bob()
        self.b0.obtain_state(self.q_c.put_state())
        self.b0.meas_qubit_stream_bob()

    def key_generation_phase(self):
        # Generating the key based on measurement basis used and covert channel misreporting
        self.c_c.get_basis_seq(self.b0.basis_seq_b)
        true_basis_seq_a = copy.deepcopy(self.a0.basis_seq_a)
        self.a0.misreport()
        false_basis_seq_a = copy.deepcopy(self.a0.basis_seq_a)
        self.a0.basis_seq_a = true_basis_seq_a
        self.a0.key_gen_alice(self.c_c.put_basis_seq())
        self.a0.basis_seq_a = false_basis_seq_a
        #self.a0.print_key_alice()
        self.c_c.ch_reset()
    
        self.c_c.get_basis_seq(self.a0.basis_seq_a)
        self.b0.extract_msg(self.a0.basis_seq_a)
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

    for i in range(100):
        experiment = covert_experiment(2048, test_msg, test_trigger_length, 0.03)
        experiment.execute()
        QBERs.append(experiment.calc_perc_error)

    print("Average QBER: " + str(numpy.mean(QBERs)) + "%")

if __name__ == '__main__':
    main()