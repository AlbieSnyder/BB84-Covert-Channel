import qkd_experiment_base as base
import qkd_bb84_base as bb
import qkd_noise_model
import copy
import numpy

class variable_noisy_qkd_experiment(qkd_noise_model.noisy_qkd_experiment):
    
    def __init__(self, s_length, error_rate):
        #Setting P_H_FAIL to 0 as the covert model assumes perfect Hadamard gates
        super().__init__(s_length, 0)
        self.s_length = s_length
        self.error_rate = error_rate
    
    def build_phase(self):
        super().build_phase()
        self.q_c = qkd_noise_model.variable_noisy_q_channel(self.error_rate)

def main():
    
    s_length = 2**16
    error_rate = 0.03
    QBERs = []

    for i in range(100):
        experiment = variable_noisy_qkd_experiment(s_length, error_rate)
        experiment.execute()
        QBERs.append(experiment.calc_perc_error)

        if i < 5:
            print(f"k=NA, run {i}: errors={experiment.a0.errors}, check_bits={experiment.a0.size_of_check_bits}")

    print("Average QBER: " + str(numpy.mean(QBERs)) + "%")

if __name__ == "__main__":
    main()