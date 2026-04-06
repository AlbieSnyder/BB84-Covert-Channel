import baseline_noise_experiment as baseline_experiment
import covert_noise_experiment as covert_experiment
import scipy
import numpy
import sys

def detectability_analysis(baseline_QBERs, covert_QBERs, k):
    sample_sizes = [10, 20, 50, 100, 200, 300, 500, 750, 1000]
    print(f"\nDetectability analysis for k={k}:")
    for n in sample_sizes:
        result = scipy.stats.ks_2samp(baseline_QBERs[:n], covert_QBERs[:n])
        print(f"  n={n}: p-value={result.pvalue:.6f} {'DETECTABLE' if result.pvalue < 0.05 else 'UNDETECTABLE'}")

def test(k):
    #Global Parameters
    error_rate = 0.03
    s_length = 65536
    experiment_count = 1000

    #Baseline Parameters
    baseline_QBERs = []

    #Covert parameters
    test_msg = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]
    test_trigger_length = k
    covert_QBERs = []

    for i in range(experiment_count):
        c_exp = covert_experiment.covert_noise_experiment(s_length, test_msg, test_trigger_length, error_rate)
        c_exp.execute()
        covert_QBERs.append(c_exp.calc_perc_error)
        b_exp = baseline_experiment.variable_noisy_qkd_experiment(s_length, error_rate)
        b_exp.execute()
        baseline_QBERs.append(b_exp.calc_perc_error)

        if i % 5 == 0:
             print(i)

    detectability_analysis(baseline_QBERs, covert_QBERs, test_trigger_length)
    print(f"Average Baseline QBER for k={k}: {str(numpy.mean(baseline_QBERs))}% \n")
    print(f"Average Covert QBER for k={k}: {str(numpy.mean(covert_QBERs))}% \n")
    print(f"For k={k}: {str(scipy.stats.ks_2samp(baseline_QBERs, covert_QBERs))} \n")
    numpy.save(f"baseline_qbers_k{k}.npy", baseline_QBERs)
    numpy.save(f"covert_qbers_k{k}.npy", covert_QBERs)

def main():
        test(int(sys.argv[1]))

if __name__ == '__main__':
    main()