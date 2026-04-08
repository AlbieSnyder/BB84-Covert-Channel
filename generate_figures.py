import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

data_dir = "Data"
figure_dir = "Figures"
k_values = [6, 7, 8, 9, 10]

baseline_qbers = {}
covert_qbers = {}
baseline_inter = {}
covert_inter = {}

for k in k_values:
    baseline_qbers[k] = np.load(f'{data_dir}/baseline_qbers_k{k}.npy', allow_pickle=True)
    covert_qbers[k] = np.load(f'{data_dir}/covert_qbers_k{k}.npy', allow_pickle=True)
    baseline_inter[k] = np.load(f'{data_dir}/baseline_inter_error_distances_k{k}.npy', allow_pickle=True)
    covert_inter[k] = np.load(f'{data_dir}/covert_inter_error_distances_k{k}.npy', allow_pickle=True)

# Compute derived stats
qber_gaps = [np.mean(covert_qbers[k]) - np.mean(baseline_qbers[k]) for k in k_values]
theoretical_gaps = [0.125 * (0.5**k) * 100 for k in k_values]

# Session-count detectability
session_counts = [10, 20, 50, 100, 200, 300, 500, 750, 1000]
qber_p_by_k = {}
for k in k_values:
    p_vals = []
    for n in session_counts:
        n_actual = min(n, len(baseline_qbers[k]))
        result = stats.ks_2samp(baseline_qbers[k][:n_actual], covert_qbers[k][:n_actual])
        p_vals.append(result.pvalue)
    qber_p_by_k[k] = p_vals

# Inter-error and QBER p-values at full 1000 sessions
qber_p_1000 = {k: stats.ks_2samp(baseline_qbers[k], covert_qbers[k]).pvalue for k in k_values}
inter_p_1000 = {k: stats.ks_2samp(baseline_inter[k], covert_inter[k]).pvalue for k in k_values}

#Style
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'axes.spines.top': False,
    'axes.spines.right': False,
})


#FIGURE 1: QBER Gap vs k with theoretical prediction
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(k_values, qber_gaps, 'o-', color='#2c3e50', label='Observed QBER gap', linewidth=2, markersize=8, zorder=3)
ax.plot(k_values, theoretical_gaps, 's--', color='#c0392b', label=r'Predicted: $E_{covert} = 0.125 \times (1/2)^k$', linewidth=1.5, markersize=6, zorder=3)
ax.set_xlabel('Trigger Length (k)')
ax.set_ylabel('QBER Inflation (%)')
ax.set_title('Covert Channel QBER Inflation vs Trigger Length')
ax.legend()
ax.set_xticks(k_values)
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig(f'{figure_dir}/fig1_qber_gap_vs_k.svg')
plt.savefig(f'{figure_dir}/fig1_qber_gap_vs_k.png')
plt.close()

# FIGURE 2: Detection Comparison - QBER vs Inter-Error p-values
fig, ax = plt.subplots(figsize=(6, 4))
qber_p_list = [max(qber_p_1000[k], 1e-110) for k in k_values]
inter_p_list = [max(inter_p_1000[k], 1e-10) for k in k_values]
ax.plot(k_values, qber_p_list, 'o-', color='#2c3e50', label='QBER analysis (1000 sessions)', linewidth=2, markersize=8)
ax.plot(k_values, inter_p_list, 's-', color='#c0392b', label='Inter-error distance analysis (1000 sessions)', linewidth=2, markersize=8)
ax.axhline(y=0.05, color='#333333', linestyle='--', linewidth=1, label=r'$\alpha = 0.05$')
ax.set_yscale('log')
ax.set_xlabel('Trigger Length (k)')
ax.set_ylabel('KS Test p-value')
ax.set_title('Detection Sensitivity: QBER vs Inter-Error Distance')
ax.legend(fontsize=8)
ax.set_xticks(k_values)
ax.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig(f'{figure_dir}/fig2_detection_comparison.svg')
plt.savefig(f'{figure_dir}/fig2_detection_comparison.png')
plt.close()

# FIGURE 3: QBER Detectability Curve
fig, ax = plt.subplots(figsize=(7, 4.5))
colors = {6: '#e74c3c', 7: '#e67e22', 8: '#2ecc71', 9: '#2980b9', 10: '#8e44ad'}
for k in k_values:
    p_vals_plot = [max(p, 1e-12) for p in qber_p_by_k[k]]
    ax.plot(session_counts, p_vals_plot, 'o-', color=colors[k], label=f'k={k}', linewidth=2, markersize=5)

ax.axhline(y=0.05, color='#333333', linestyle='--', linewidth=1, label=r'$\alpha = 0.05$')
ax.set_yscale('log')
ax.set_xscale('log')
ax.set_xlabel('Number of Observed Sessions')
ax.set_ylabel('KS Test p-value')
ax.set_title('QBER Detectability vs Number of Observed Sessions')
ax.legend(loc='lower left', ncol=2)
ax.set_xticks(session_counts)
ax.set_xticklabels([str(n) for n in session_counts], rotation=45, ha='right')
ax.grid(True, alpha=0.2)
ax.set_ylim(1e-12, 2)
plt.tight_layout()
plt.savefig(f'{figure_dir}/fig3_detectability_curve.svg')
plt.savefig(f'{figure_dir}/fig3_detectability_curve.png')
plt.close()

# FIGURE 4: QBER Histograms per k value
fig, axes = plt.subplots(1, 5, figsize=(16, 3.5), sharey=True)
for idx, k in enumerate(k_values):
    ax = axes[idx]
    bins = np.linspace(
        min(np.min(baseline_qbers[k]), np.min(covert_qbers[k])),
        max(np.max(baseline_qbers[k]), np.max(covert_qbers[k])),
        40
    )
    ax.hist(baseline_qbers[k], bins=bins, alpha=0.6, color='#2c3e50', label='Baseline', density=True)
    ax.hist(covert_qbers[k], bins=bins, alpha=0.6, color='#c0392b', label='Covert', density=True)
    ax.set_title(f'k={k}')
    ax.set_xlabel('QBER (%)')
    if idx == 0:
        ax.set_ylabel('Density')
    if idx == 4:
        ax.legend(loc='upper right', fontsize=8)

fig.suptitle('QBER Distributions: Baseline vs Covert Channel', y=1.02, fontsize=13)
plt.tight_layout()
plt.savefig(f'{figure_dir}/fig4_qber_histograms.svg', bbox_inches='tight')
plt.savefig(f'{figure_dir}/fig4_qber_histograms.png', bbox_inches='tight')
plt.close()


# FIGURE 5: Inter-Error Distance Histograms per k value
fig, axes = plt.subplots(1, 5, figsize=(16, 3.5), sharey=True)
for idx, k in enumerate(k_values):
    ax = axes[idx]
    # Cap at 500 for visibility
    b_clipped = np.clip(baseline_inter[k], 0, 500)
    c_clipped = np.clip(covert_inter[k], 0, 500)
    bins = np.linspace(0, 500, 50)
    ax.hist(b_clipped, bins=bins, alpha=0.6, color='#2c3e50', label='Baseline', density=True)
    ax.hist(c_clipped, bins=bins, alpha=0.6, color='#c0392b', label='Covert', density=True)
    ax.set_title(f'k={k}')
    ax.set_xlabel('Distance (bits)')
    if idx == 0:
        ax.set_ylabel('Density')
    if idx == 4:
        ax.legend(loc='upper right', fontsize=8)

fig.suptitle('Inter-Error Distance Distributions: Baseline vs Covert Channel', y=1.02, fontsize=13)
plt.tight_layout()
plt.savefig(f'{figure_dir}/fig5_inter_error_histograms.svg', bbox_inches='tight')
plt.savefig(f'{figure_dir}/fig5_inter_error_histograms.png', bbox_inches='tight')
plt.close()


# FIGURE 6: Mean Inter-Error Distances bar chart
fig, ax = plt.subplots(figsize=(6, 4))
x = np.arange(len(k_values))
width = 0.35
ax.bar(x - width/2, [np.mean(baseline_inter[k]) for k in k_values], width, label='Baseline', color='#2c3e50', alpha=0.85)
ax.bar(x + width/2, [np.mean(covert_inter[k]) for k in k_values], width, label='Covert', color='#c0392b', alpha=0.85)
ax.set_xlabel('Trigger Length (k)')
ax.set_ylabel('Mean Inter-Error Distance (bits)')
ax.set_title('Mean Inter-Error Distance: Baseline vs Covert')
ax.set_xticks(x)
ax.set_xticklabels(k_values)
ax.legend()
ax.grid(True, alpha=0.2, axis='y')
plt.tight_layout()
plt.savefig(f'{figure_dir}/fig6_mean_inter_error.svg')
plt.savefig(f'{figure_dir}/fig6_mean_inter_error.png')
plt.close()


# Print summary table for paper
print("\n" + "="*100)
print("SUMMARY TABLE FOR PAPER")
print("="*100)
print(f"{'k':<4} {'Baseline QBER':>14} {'Covert QBER':>14} {'Gap':>10} {'QBER p-val':>14} {'Inter-err p-val':>16} {'QBER Det. @':>12}")
print("-"*100)
for i, k in enumerate(k_values):
    threshold = ">1000"
    for j, n in enumerate(session_counts):
        if qber_p_by_k[k][j] < 0.05:
            threshold = str(n)
            break
    print(f"{k:<4} {np.mean(baseline_qbers[k]):>13.4f}% {np.mean(covert_qbers[k]):>13.4f}% {qber_gaps[i]:>9.4f}% {qber_p_1000[k]:>14.6e} {inter_p_1000[k]:>16.6e} {threshold:>12}")

print(f"\nFigures saved to {figure_dir}/")