import baseline_noise_experiment as baseline_experiment
import covert_noise_experiment as covert_experiment
import scipy
import numpy
import sys

def QBER_detectability_analysis(baseline_QBERs, covert_QBERs, k):
    sample_sizes = [10, 20, 50, 100, 200, 300, 500, 750, 1000]
    print(f"\nDetectability analysis for k={k}:")
    for n in sample_sizes:
        result = scipy.stats.ks_2samp(baseline_QBERs[:n], covert_QBERs[:n])
        print(f"  n={n}: p-value={result.pvalue:.6f} {'QBERs DETECTABLE' if result.pvalue < 0.05 else 'QBERs UNDETECTABLE'}")

def inter_error_analysis(baseline_inter_errors, covert_inter_errors, k):
    result = scipy.stats.ks_2samp(baseline_inter_errors, covert_inter_errors)
    print(f"\nInter-error distance analysis for k={k}:")
    print(f"  Baseline distances: {len(baseline_inter_errors)}, Covert distances: {len(covert_inter_errors)}")
    print(f"Mean baseline distance: {str(numpy.mean(baseline_inter_errors))}, Mean covert distances: {str(numpy.mean(covert_inter_errors))}")
    print(f"Median baseline distance: {str(numpy.median(baseline_inter_errors))}, Median covert distances: {str(numpy.median(covert_inter_errors))}")
    print(f"  p-value={result.pvalue:.6f} {'DETECTABLE' if result.pvalue < 0.05 else 'UNDETECTABLE'}")

def test(k):
    #Global Parameters
    error_rate = 0.03
    s_length = 65536
    experiment_count = 1000

    #Baseline Parameters
    baseline_QBERs = []
    baseline_inter_errors = []

    #Covert parameters
    test_msg = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]
    test_trigger_length = k
    covert_QBERs = []
    covert_inter_errors = []

    for i in range(experiment_count):
        c_exp = covert_experiment.covert_noise_experiment(s_length, test_msg, test_trigger_length, error_rate)
        c_exp.execute()
        covert_QBERs.append(c_exp.calc_perc_error)
        covert_inter_errors.extend(c_exp.a0.inter_error_distances)
        b_exp = baseline_experiment.variable_noisy_qkd_experiment(s_length, error_rate)
        b_exp.execute()
        baseline_QBERs.append(b_exp.calc_perc_error)
        baseline_inter_errors.extend(b_exp.a0.inter_error_distances)

        if i % 5 == 0:
             print(i)

    QBER_detectability_analysis(baseline_QBERs, covert_QBERs, test_trigger_length)
    inter_error_analysis(baseline_inter_errors, covert_inter_errors, test_trigger_length)

    print(f"Average Baseline QBER for k={k}: {str(numpy.mean(baseline_QBERs))}% \n")
    print(f"Average Covert QBER for k={k}: {str(numpy.mean(covert_QBERs))}% \n")
    print(f"For k={k}: {str(scipy.stats.ks_2samp(baseline_QBERs, covert_QBERs))} \n")
    numpy.save(f"baseline_qbers_k{k}.npy", baseline_QBERs)
    numpy.save(f"covert_qbers_k{k}.npy", covert_QBERs)
    numpy.save(f"baseline_inter_error_distances_k{k}.npy", baseline_inter_errors)
    numpy.save(f"covert_inter_error_distances_k{k}.npy", covert_inter_errors)

def main():
        test(int(sys.argv[1]))

if __name__ == '__main__':
    main()