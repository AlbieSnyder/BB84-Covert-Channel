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

SPACING_NULL_DRAWS = 200

def _gap_ks_distance(sorted_positions, check_bits):
    """
    KS distance between the gaps of each row of sorted positions and an Exponential
    distribution with the expected mean gap. Works row-wise on 2D array.
    """
    gaps = numpy.sort(numpy.diff(sorted_positions, axis=-1), axis=-1)
    n = gaps.shape[-1]
    mean_gap = check_bits / (sorted_positions.shape[-1] + 1)
    cdf = 1.0 - numpy.exp(-gaps / mean_gap)
    i = numpy.arange(1, n + 1)
    return numpy.maximum((i / n - cdf).max(axis=-1), (cdf - (i - 1) / n).max(axis=-1))

def session_pattern_pvalues(error_locations, check_bits):
    """
    Tests whether one session's error positions look like a uniformly random set,
    given how many errors the session had. Conditioning on the count removes the
    QBER level (and its session-to-session drift), so only the placement is tested.

    Returns (p_position, p_spacing), or None if the session has fewer than 2 errors.

    p_position: one-sample KS test of the positions against Uniform(0, check_bits).
                Detects errors piling up in part of the key (e.g. near the start).
                Each integer position gets a random offset in [0, 1), which makes
                the positions exactly continuous-uniform under the null.
    p_spacing:  Monte Carlo test of the gaps between consecutive errors. The statistic
                is the KS distance between the session's gaps and an Exponential with
                the expected mean gap. It is compared against SPACING_NULL_DRAWS
                simulated honest sessions with the same check-bit count and the same
                number of errors, placed uniformly at random. Detects errors being more
                clustered, or more regularly spaced, than chance. (A Monte Carlo null
                is used because the gaps are integers and not independent, so the
                textbook KS p-value is not accurate here.)
    """
    errors = len(error_locations)
    if errors < 2:
        return None
    locs = numpy.sort(numpy.asarray(error_locations))
    positions = (locs + numpy.random.random(errors)) / check_bits
    p_position = scipy.stats.kstest(positions, "uniform").pvalue

    observed = _gap_ks_distance(locs[None, :].astype(float), check_bits)[0]
    # Null sessions: the same number of errors placed uniformly without replacement
    null = numpy.argpartition(numpy.random.random((SPACING_NULL_DRAWS, check_bits)), errors, axis=1)[:, :errors]
    null = numpy.sort(null, axis=1).astype(float)
    null_d = _gap_ks_distance(null, check_bits)
    p_spacing = (1 + numpy.sum(null_d >= observed)) / (SPACING_NULL_DRAWS + 1)
    return p_position, p_spacing

def pattern_analysis(pvalues, label):
    """
    Combines per-session p-values with Fisher's method. If the error pattern is
    indistinguishable from random noise, about 5% of sessions should have p < 0.05
    and the combined p-value should not be small.
    """
    result = {}
    for name, col in (("position", 0), ("spacing", 1)):
        p = numpy.array([pv[col] for pv in pvalues])
        combined = scipy.stats.combine_pvalues(p, method="fisher").pvalue
        print(f"  {label:<8} {name:<8} sessions={len(p):>5}  frac p<0.05={numpy.mean(p < 0.05):6.1%}  "
              f"Fisher combined p={combined:.4g} {'STRUCTURE DETECTED' if combined < 0.05 else 'no structure'}")
        result[name] = combined
    return result

def inter_error_analysis(baseline_inter_errors, covert_inter_errors, k):
    # LEGACY (v1): pools gaps across sessions, which mixes sessions with different
    # noise levels and mostly re-measures QBER. Kept only to reproduce v1 figures;
    # use pattern_analysis() for the corrected test.
    result = scipy.stats.ks_2samp(baseline_inter_errors, covert_inter_errors)
    print(f"\nInter-error distance analysis for k={k}:")
    print(f"  Baseline distances: {len(baseline_inter_errors)}, Covert distances: {len(covert_inter_errors)}")
    print(f"Mean baseline distance: {str(numpy.mean(baseline_inter_errors))}, Mean covert distances: {str(numpy.mean(covert_inter_errors))}")
    print(f"Median baseline distance: {str(numpy.median(baseline_inter_errors))}, Median covert distances: {str(numpy.median(covert_inter_errors))}")
    print(f"  p-value={result.pvalue:.6f} {'DETECTABLE' if result.pvalue < 0.05 else 'UNDETECTABLE'}")

def test(k, experiment_count=1000, out_dir="Data", jitter=0.25, rep=1):
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
    # Per-session error-pattern p-values (corrected inter-error test)
    baseline_pattern_p = []
    covert_pattern_p = []

    # Check once per k, before running sessions
    preamble_len = (s_length // 2**k).bit_length()
    expected_capacity = s_length / (2**k + k - 1)
    needed = preamble_len + len(test_msg)
    if needed > expected_capacity - 3 * numpy.sqrt(expected_capacity):
        print(f"Note: k={k} message needs {needed} bits but expected capacity is "
              f"{expected_capacity:.1f}; it may be truncated (does not affect QBER statistics).")

    for i in range(experiment_count):
        c_exp = covert_experiment.covert_noise_experiment(s_length, test_msg, test_trigger_length, error_rate, jitter=jitter, session_id=f"r{rep}s{i}")
        c_exp.execute()
        covert_QBERs.append(c_exp.calc_perc_error)
        covert_inter_errors.extend(c_exp.a0.inter_error_distances)
        covert_actual_capacities.append(c_exp.b0.actual_capacity)
        pv = session_pattern_pvalues(c_exp.a0.error_locations, c_exp.a0.size_of_check_bits)
        if pv is not None:
            covert_pattern_p.append(pv)
        b_exp = baseline_experiment.variable_noisy_qkd_experiment(s_length, error_rate, jitter=jitter)
        b_exp.execute()
        baseline_QBERs.append(b_exp.calc_perc_error)
        baseline_inter_errors.extend(b_exp.a0.inter_error_distances)
        pv = session_pattern_pvalues(b_exp.a0.error_locations, b_exp.a0.size_of_check_bits)
        if pv is not None:
            baseline_pattern_p.append(pv)

        if i % 250 == 0:
             print(i)

    QBER_detectability_analysis(baseline_QBERs, covert_QBERs, test_trigger_length)
    print(f"\nError-pattern analysis for k={k} (per session, conditioned on error count):")
    base_pattern = pattern_analysis(baseline_pattern_p, "baseline")
    cov_pattern = pattern_analysis(covert_pattern_p, "covert")

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
    numpy.save(os.path.join(out_dir, f"baseline_pattern_pvalues_k{k}.npy"), numpy.array(baseline_pattern_p))
    numpy.save(os.path.join(out_dir, f"covert_pattern_pvalues_k{k}.npy"), numpy.array(covert_pattern_p))
    return {
    "k": k,
    "jitter": jitter,
    "gap": numpy.mean(covert_QBERs) - numpy.mean(baseline_QBERs),
    "qber_p": scipy.stats.ks_2samp(baseline_QBERs, covert_QBERs).pvalue,
    "position_p_baseline": base_pattern["position"],
    "position_p_covert": cov_pattern["position"],
    "spacing_p_baseline": base_pattern["spacing"],
    "spacing_p_covert": cov_pattern["spacing"],
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
        w = csv.DictWriter(f, fieldnames=["rep", "seed", "k", "jitter", "gap", "qber_p",
                                          "position_p_baseline", "position_p_covert",
                                          "spacing_p_baseline", "spacing_p_covert", "capacity"])
        w.writeheader()
        w.writerows(results)

    print(f"{'k':>3} {'reps':>5} {'mean gap':>9} {'QBER det.':>10} {'median QBER p':>14} "
          f"{'pattern det. (covert)':>22} {'pattern det. (baseline)':>24}")
    for k in k_values:
        rk = [r for r in results if r["k"] == k]
        qp = numpy.array([r["qber_p"] for r in rk])
        # a repeat counts as "pattern detected" if either pattern test is significant;
        # with two tests, each is held to 0.025 (Bonferroni) to keep the overall rate at 5%
        cp = numpy.array([2 * min(r["position_p_covert"], r["spacing_p_covert"]) for r in rk])
        bp = numpy.array([2 * min(r["position_p_baseline"], r["spacing_p_baseline"]) for r in rk])
        gap = numpy.mean([r["gap"] for r in rk])
        print(f"{k:>3} {len(rk):>5} {gap:>9.4f} {numpy.mean(qp < 0.05):>9.0%} {numpy.median(qp):>14.3g} "
              f"{numpy.mean(cp < 0.05):>21.0%} {numpy.mean(bp < 0.05):>23.0%}")

def main():
    # Usage:
    # python statistical_analysis.py <k> <sessions> [repeats]
    # python statistical_analysis.py <k_start> <k_end> <sessions> [repeats]
    # Optional: --jitter=<half-width>  (default 0.25)
    jitter = 0.25
    raw = []
    for a in sys.argv[1:]:
        if a.startswith("--jitter="):
            jitter = float(a.split("=", 1)[1])
        else:
            raw.append(a)
    args = [int(a) for a in raw]
    if len(args) in (2, 3) and (len(args) == 2 or args[1] >= 10):
        # single k: <k> <sessions> [repeats]
        k_values, sessions = [args[0]], args[1]
        repeats = args[2] if len(args) == 3 else 1
    elif len(args) in (3, 4):
        k_values, sessions = list(range(args[0], args[1] + 1)), args[2]
        repeats = args[3] if len(args) == 4 else 1
    else:
        sys.exit("Usage: <k> <sessions> [repeats]  or  <k_start> <k_end> <sessions> [repeats] [--jitter=0.25]")

    run_dir = make_run_dir()
    base_seed = int(datetime.datetime.now().timestamp())

    with open(os.path.join(run_dir, "params.json"), "w") as f:
        json.dump({"k_values": k_values, "sessions": sessions, "repeats": repeats,
                   "s_length": 65536, "error_rate": 0.03, "jitter": jitter, "base_seed": base_seed,
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
                r = test(k, sessions, out_dir=rep_dir, jitter=jitter, rep=rep)
                r["rep"], r["seed"] = rep, seed
                results.append(r)
        summarise(results, k_values, run_dir)
    finally:
        sys.stdout = original_stdout
        log_file.close()


if __name__ == '__main__':
    main()