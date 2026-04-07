# BB84 Covert Channel

A covert channel embedded in the classical sifting phase of the BB84 Quantum Key Distribution protocol. The channel transmits hidden data by intentionally misreporting basis announcements, hiding the covert payload within the hardware's expected QBER noise floor.

**Paper:** [Covert Channel via Error-Injection by Classical Misreporting in the BB84 Sifting Phase](https://arxiv.org/abs/XXXX.XXXXX) (link TBD)

## Overview

This project extends an existing BB84 QKD simulation by [Dhruv Bhatnagar](https://github.com/dhruvbhq/quantum_key_distrib_simple) with a covert channel implementation and statistical analysis tools.

## Requirements

- Python 3.10+
- NumPy
- SciPy
- Matplotlib

## Project Structure

### Base BB84 Simulation (by Dhruv Bhatnagar)
| File | Description |
|------|-------------|
| `qkd_bb84_base.py` | Core classes for Alice, Bob, quantum channel, and classical channel |
| `qkd_experiment_base.py` | Base experiment class with build, run, key generation, and validation phases |
| `qkd_bb84_noiseless.py` | Noiseless BB84 experiment driver |
| `qkd_noise_model.py` | Noisy channel and Hadamard gate failure models |
| `qkd_eavesdropping_2.py` | Intercept-resend eavesdropping simulation |

### Covert Channel Implementation (by Albie Snyder)
| File | Description |
|------|-------------|
| `covert_channel.py` | `CovertStateMachine` class — rolling trigger mechanism, dual PRNGs, keystream |
| `qkd_covert_alice.py` | Covert Alice subclass — basis misreporting with message preamble and padding |
| `qkd_covert_bob.py` | Covert Bob subclass — covert bit extraction and preamble parsing |
| `covert_experiment.py` | Noiseless covert channel experiment driver |
| `covert_noise_experiment.py` | Noisy covert channel experiment driver |
| `baseline_noise_experiment.py` | Baseline noisy experiment (no covert channel) for comparison |
| `statistical_analysis.py` | KS test analysis for QBER and inter-error distance detectability |
| `generate_figures.py` | Generates all paper figures from saved experimental data |
| `covert_test.py` | Unit test for CovertStateMachine synchronization |

### Data and Figures
| Directory | Description |
|-----------|-------------|
| `Data/` | Saved NumPy arrays from 1000-trial experiments (`.npy` files) |
| `Figures/` | Generated SVG and PNG figures for the paper |

## Quick Start

### Run a basic covert channel demo (noiseless)
```bash
python covert_experiment.py
```
This transmits a 24-bit test message through the covert channel with trigger length k=7 and prints the recovered message.

### Run a noisy covert channel experiment
```bash
python covert_noise_experiment.py
```
Same as above but with 3% channel noise simulating depolarizing errors.

### Run the full statistical analysis
```bash
python statistical_analysis.py <k>
```
where `<k>` is the trigger length (e.g., 7, 8, 9, 10). Runs 1000 baseline and 1000 covert trials, performs KS tests on QBER and inter-error distance distributions, and saves results to `.npy` files.

### Generate figures
```bash
python generate_figures.py
```
Loads saved data from `Data/` and generates all paper figures to `Figures/`.

## Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `s_length` | Number of qubits per session | 65,536 |
| `trigger_length` (k) | Length of trigger sequence | 7 |
| `noise_error_rate` | Channel depolarizing error rate | 0.03 |
| `PSK` | Pre-Shared Key (string) | "topsecret" |

## License

The base BB84 simulation is by [Dhruv Bhatnagar](https://github.com/dhruvbhq/quantum_key_distrib_simple). The covert channel extension is by Albert Snyder.