import covert_noise_experiment
import numpy

class variable_noisy_qkd_experiment(covert_noise_experiment.covert_noise_experiment):
    """
    Baseline arm: the same classes and code path as the covert experiment,
    with misreporting switched off. Alice announces her true bases, so the
    only difference between the two arms is the covert channel itself.
    """

    def __init__(self, s_length, error_rate, jitter=0.25):
        super().__init__(s_length, msg=[], trigger_length=1,
                         noise_error_rate=error_rate, jitter=jitter, covert=False)
        self.error_rate = error_rate

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