"""
Validates the simulator against the model of the covert channel.

Usage
-----
    python validate_model.py [sessions] [--jitter=0.25] [--k=4-10] [--noise=0,0.03]

defaults to 500 per arm per (k, noise) setting.
"""
import sys
import os
import json
import csv
import random
import datetime
import numpy
import scipy.stats

import covert_noise_experiment as covert_experiment
import baseline_noise_experiment as baseline_experiment

S_LENGTH = 65536
TEST_MSG = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0]
ALPHA = 0.05
POWER = 0.80
BOOTSTRAP_DRAWS = 400


def run_arm(covert, k, noise, jitter, sessions, tag):
    """Returns per-session QBERs (as fractions) and trigger counts."""
    qbers, triggers = [], []
    for i in range(sessions):
        if covert:
            exp = covert_experiment.covert_noise_experiment(
                S_LENGTH, TEST_MSG, k, noise, jitter=jitter, session_id=f"{tag}s{i}")
        else:
            exp = baseline_experiment.variable_noisy_qkd_experiment(S_LENGTH, noise, jitter=jitter)
        exp.execute()
        qbers.append(exp.calc_perc_error / 100.0)
        triggers.append(exp.b0.actual_capacity)
    return numpy.array(qbers), numpy.array(triggers)


def predicted_sessions(delta, sd_b, sd_c):
    z = scipy.stats.norm.ppf(1 - ALPHA / 2) + scipy.stats.norm.ppf(POWER)
    return z**2 * (sd_b**2 + sd_c**2) / delta**2


def empirical_sessions(base, cov, rng):
    """
    Smallest n (on a grid) at which a Welch t-test detects the channel with
    power >= POWER, estimated by resampling n sessions from each arm.
    Returns None if not reached within the number of sessions simulated.
    """
    max_n = min(len(base), len(cov))
    grid = sorted({int(x) for x in numpy.unique(numpy.geomspace(5, max_n, 80).astype(int))})
    for n in grid:
        hits = 0
        for _ in range(BOOTSTRAP_DRAWS):
            b = rng.choice(base, n, replace=True)
            c = rng.choice(cov, n, replace=True)
            if scipy.stats.ttest_ind(c, b, equal_var=False).pvalue < ALPHA:
                hits += 1
        if hits / BOOTSTRAP_DRAWS >= POWER:
            return n
    return None


def parse_args(argv):
    sessions, jitter = 500, 0.25
    k_values, noise_values = list(range(4, 12)), [0.0, 0.03]
    for a in argv:
        if a.startswith("--jitter="):
            jitter = float(a.split("=", 1)[1])
        elif a.startswith("--k="):
            lo, hi = a.split("=", 1)[1].split("-")
            k_values = list(range(int(lo), int(hi) + 1))
        elif a.startswith("--noise="):
            noise_values = [float(x) for x in a.split("=", 1)[1].split(",")]
        else:
            sessions = int(a)
    return sessions, jitter, k_values, noise_values


def main():
    sessions, jitter, k_values, noise_values = parse_args(sys.argv[1:])

    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = os.path.join("Data", "runs", f"validation_{stamp}")
    os.makedirs(run_dir, exist_ok=False)
    seed = int(datetime.datetime.now().timestamp())
    numpy.random.seed(seed)
    random.seed(seed)
    rng = numpy.random.default_rng(seed)

    with open(os.path.join(run_dir, "params.json"), "w") as f:
        json.dump({"sessions": sessions, "jitter": jitter, "k_values": k_values,
                   "noise_values": noise_values, "s_length": S_LENGTH, "seed": seed,
                   "alpha": ALPHA, "power": POWER, "bootstrap_draws": BOOTSTRAP_DRAWS,
                   "argv": sys.argv}, f, indent=2)

    rows = []
    for noise in noise_values:
        for k in k_values:
            tag = f"e{noise}k{k}"
            cov, trig = run_arm(True, k, noise, jitter, sessions, tag)
            if noise > 0:
                base, _ = run_arm(False, k, noise, jitter, sessions, tag)
            else:
                base = numpy.zeros(sessions)   # no noise: honest QBER is exactly 0

            r_meas = trig.mean() / S_LENGTH
            r_pred = 1.0 / (2**k + k - 1)
            delta_meas = cov.mean() - base.mean()
            delta_se = numpy.sqrt(cov.var(ddof=1) / sessions + base.var(ddof=1) / sessions)
            delta_pred = r_pred * (1 - 2 * noise) / 4
            row = {
                "noise": noise, "jitter": jitter, "k": k, "sessions": sessions,
                "r_pred": r_pred, "r_meas": r_meas,
                "delta_pred_pct": 100 * delta_pred, "delta_meas_pct": 100 * delta_meas,
                "delta_se_pct": 100 * delta_se,
                "z_vs_pred": (delta_meas - delta_pred) / delta_se if delta_se > 0 else float("nan"),
                "sd_baseline_pct": 100 * base.std(ddof=1), "sd_covert_pct": 100 * cov.std(ddof=1),
                "n_pred": None, 
                "n_empirical": None,
                "n_pred_measured": None
            }
            if noise > 0:
                row["n_pred"] = predicted_sessions(delta_pred, base.std(ddof=1), cov.std(ddof=1))
                if delta_meas > 3 * delta_se:   # only meaningful when the gap is clearly resolved
                    row["n_pred_measured"] = predicted_sessions(delta_meas, base.std(ddof=1), cov.std(ddof=1))
                row["n_empirical"] = empirical_sessions(base, cov, rng)
            rows.append(row)
            numpy.save(os.path.join(run_dir, f"covert_qbers_{tag}.npy"), cov)
            numpy.save(os.path.join(run_dir, f"baseline_qbers_{tag}.npy"), base)

            n_p = "-" if row["n_pred"] is None else f"{row['n_pred']:.0f}"
            n_e = "-" if noise == 0 else (f">{sessions}" if row["n_empirical"] is None else str(row["n_empirical"]))
            n_pm = "-" if row.get("n_pred_measured") is None else f"{row['n_pred_measured']:.0f}"
            print(f"e={noise:<5} k={k:<3} r: {r_meas:.5f} (pred {r_pred:.5f})  "
                  f"dQBER: {row['delta_meas_pct']:.4f} +/- {row['delta_se_pct']:.4f}% "
                  f"(pred {row['delta_pred_pct']:.4f}%, z={row['z_vs_pred']:+.2f})  "
                  f"sessions to detect: pred {n_p}, empirical {n_e} "
                  f"pred {n_p} (from measured gap {n_pm})", flush=True)

    with open(os.path.join(run_dir, "validation.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nResults written to {run_dir}")


if __name__ == "__main__":
    main()