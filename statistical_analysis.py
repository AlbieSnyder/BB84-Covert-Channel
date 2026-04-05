import baseline_noise_experiment as baseline_experiment
import covert_noise_experiment as covert_experiment
import scipy

def test(k):
    #Global Parameters
    error_rate = 0.03
    s_length = 65536

    #Baseline Parameters
    baseline_QBERs = []

    #Covert parameters
    test_msg = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]
    test_trigger_length = k
    covert_QBERs = []

    for i in range(1000):
        c_exp = covert_experiment.covert_experiment(s_length, test_msg, test_trigger_length, error_rate)
        c_exp.execute()
        covert_QBERs.append(c_exp.calc_perc_error)

        b_exp = baseline_experiment.variable_noisy_qkd_experiment(s_length, error_rate)
        b_exp.execute()
        baseline_QBERs.append(b_exp.calc_perc_error)

    print(f"Average Baseline QBER for k={k}: {str(numpy.mean(baseline_QBERs))}% \n")
    print(f"Average Covert QBER for k={k}: {str(numpy.mean(covert_QBERs))}% \n")
    print(f"For k={k}: {str(scipy.stats.ks_2samp(baseline_QBERs, covert_QBERs))} \n")

def main():
    for i in range(7, 10):
        test(i)

if __name__ == '__main__':
    main()