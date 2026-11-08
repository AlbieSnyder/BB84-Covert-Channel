import baseline_noise_experiment as baseline_experiment
import covert_noise_experiment as covert_experiment
import scipy
import numpy
import os
import json
import datetime
import sys
import random

class Tee:
    """Writes everything to both the console and a log file."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()

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

def test(k, experiment_count=1000, out_dir="Data"):
    #Global Parameters
    error_rate = 0.03
    s_length = 65536

    #Baseline Parameters
    baseline_QBERs = []
    baseline_inter_errors = []

    #Covert parameters
    test_msg = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]
    test_trigger_length = k
    covert_QBERs = []
    covert_inter_errors = []
    covert_actual_capacities = []

    # Check once per k, before running sessions
    preamble_len = (s_length // 2**k).bit_length()
    expected_capacity = s_length / (2**k + k - 1)
    needed = preamble_len + len(test_msg)
    if needed > expected_capacity - 3 * numpy.sqrt(expected_capacity):
        print(f"Note: k={k} message needs {needed} bits but expected capacity is "
              f"{expected_capacity:.1f}; it may be truncated (does not affect QBER statistics).")

    for i in range(experiment_count):
        c_exp = covert_experiment.covert_noise_experiment(s_length, test_msg, test_trigger_length, error_rate)
        c_exp.execute()
        covert_QBERs.append(c_exp.calc_perc_error)
        covert_inter_errors.extend(c_exp.a0.inter_error_distances)
        covert_actual_capacities.append(c_exp.b0.actual_capacity)
        b_exp = baseline_experiment.variable_noisy_qkd_experiment(s_length, error_rate)
        b_exp.execute()
        baseline_QBERs.append(b_exp.calc_perc_error)
        baseline_inter_errors.extend(b_exp.a0.inter_error_distances)

        if i % 250 == 0:
             print(i)

    QBER_detectability_analysis(baseline_QBERs, covert_QBERs, test_trigger_length)
    inter_error_analysis(baseline_inter_errors, covert_inter_errors, test_trigger_length)

    print(f"Average Baseline QBER for k={k}: {str(numpy.mean(baseline_QBERs))}% \n")
    print(f"Average Covert QBER for k={k}: {str(numpy.mean(covert_QBERs))}% \n")
    print(f"For k={k}: {str(scipy.stats.ks_2samp(baseline_QBERs, covert_QBERs))} \n")
    print(f"Expected Covert Capacity for k={k} = {s_length / (2**k + k - 1)}")
    print(f"Actual Covert Capacity for k={k} = {str(numpy.mean(covert_actual_capacities))}")
    numpy.save(os.path.join(out_dir, f"baseline_qbers_k{k}.npy"), baseline_QBERs)
    numpy.save(os.path.join(out_dir, f"covert_qbers_k{k}.npy"), covert_QBERs)
    numpy.save(os.path.join(out_dir, f"baseline_inter_error_distances_k{k}.npy"), baseline_inter_errors)
    numpy.save(os.path.join(out_dir, f"covert_inter_error_distances_k{k}.npy"), covert_inter_errors)
    numpy.save(os.path.join(out_dir, f"covert_actual_capacity_k{k}.npy"), covert_actual_capacities)
    return {
    "k": k,
    "gap": numpy.mean(covert_QBERs) - numpy.mean(baseline_QBERs),
    "qber_p": scipy.stats.ks_2samp(baseline_QBERs, covert_QBERs).pvalue,
    "inter_p": scipy.stats.ks_2samp(baseline_inter_errors, covert_inter_errors).pvalue,
    "capacity": numpy.mean(covert_actual_capacities),
    }

def make_run_dir():
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join("Data", "runs", stamp)
    os.makedirs(run_dir, exist_ok=False)   # fails rather than overwrite if the folder exists
    return run_dir

def summarise(results, k_values, run_dir):
    import csv
    with open(os.path.join(run_dir, "summary.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rep", "seed", "k", "gap", "qber_p", "inter_p", "capacity"])
        w.writeheader()
        w.writerows(results)

    print("\n===== Summary across repeats =====")
    print(f"{'k':>3} {'reps':>5} {'mean gap':>9} {'QBER det.':>10} {'median QBER p':>14} "
          f"{'inter det.':>11} {'median inter p':>15}")
    for k in k_values:
        rk = [r for r in results if r["k"] == k]
        qp = numpy.array([r["qber_p"] for r in rk])
        ip = numpy.array([r["inter_p"] for r in rk])
        gap = numpy.mean([r["gap"] for r in rk])
        print(f"{k:>3} {len(rk):>5} {gap:>9.4f} {numpy.mean(qp < 0.05):>9.0%} {numpy.median(qp):>14.3g} "
              f"{numpy.mean(ip < 0.05):>10.0%} {numpy.median(ip):>15.3g}")

def main():
    # Usage:
    # python statistical_analysis.py <k> <sessions> [repeats]
    # python statistical_analysis.py <k_start> <k_end> <sessions> [repeats]
    args = [int(a) for a in sys.argv[1:]]
    if len(args) in (2, 3) and (len(args) == 2 or args[1] >= 10):
        # single k: <k> <sessions> [repeats]
        k_values, sessions = [args[0]], args[1]
        repeats = args[2] if len(args) == 3 else 1
    elif len(args) in (3, 4):
        k_values, sessions = list(range(args[0], args[1] + 1)), args[2]
        repeats = args[3] if len(args) == 4 else 1
    else:
        sys.exit("Usage: <k> <sessions> [repeats]  or  <k_start> <k_end> <sessions> [repeats]")

    run_dir = make_run_dir()
    base_seed = int(datetime.datetime.now().timestamp())

    with open(os.path.join(run_dir, "params.json"), "w") as f:
        json.dump({"k_values": k_values, "sessions": sessions, "repeats": repeats,
                   "s_length": 65536, "error_rate": 0.03, "base_seed": base_seed,
                   "argv": sys.argv}, f, indent=2)

    log_file = open(os.path.join(run_dir, "log.txt"), "w")
    original_stdout = sys.stdout
    sys.stdout = Tee(original_stdout, log_file)
    results = []
    try:
        print(f"Run folder: {run_dir}")
        for rep in range(1, repeats + 1):
            seed = base_seed + rep
            numpy.random.seed(seed)
            random.seed(seed)
            rep_dir = os.path.join(run_dir, f"rep_{rep:02d}")
            os.makedirs(rep_dir)
            print(f"\n===== Repeat {rep}/{repeats} (seed {seed}) =====")
            for k in k_values:
                r = test(k, sessions, out_dir=rep_dir)
                r["rep"], r["seed"] = rep, seed
                results.append(r)
        summarise(results, k_values, run_dir)
    finally:
        sys.stdout = original_stdout
        log_file.close()


if __name__ == '__main__':
    main()