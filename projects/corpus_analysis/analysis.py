import os
import hashlib
import matplotlib.pyplot as plt

# =========================
# CONFIGURATION
# =========================
CORPUS_BASE_DIR = "../../corpus_output"
FILE_TYPE = "png"  # Change if needed
OUTPUT_DIR = "reports"
REPORT_NAME = "corpus_analysis_report.md"
PLOT_PREFIX = "file_size_dist"

# SPECIFIC CORPUS SELECTION
# Set to True to manually specify which corpora to analyze
USE_SPECIFIC_CORPORA = True
SPECIFIC_CORPORA = ["png_test1", "png_test2", "png_test_3"]  # Add your corpus names here
# =========================

def list_runs(base_dir, file_type):
    runs = []
    for d in os.listdir(base_dir):
        if file_type in d and os.path.isdir(os.path.join(base_dir, d)):
            runs.append(d)
    return sorted(runs)

def get_file_hashes(directory):
    hashes = {}
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            with open(path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            hashes[path] = file_hash
    return hashes

def compare_hashes(hashes1, hashes2):
    set1 = set(hashes1.values())
    set2 = set(hashes2.values())
    overlap = set1 & set2
    return len(set1), len(set2), len(overlap), overlap

def get_file_sizes(directory):
    sizes = []
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            sizes.append(os.path.getsize(path))
    return sizes

def plot_size_distribution(sizes_list, labels, output_path):
    plt.figure(figsize=(10,6))
    for sizes, label in zip(sizes_list, labels):
        plt.hist(sizes, bins=50, alpha=0.7, label=label)
    plt.xlabel('File size (bytes)')
    plt.ylabel('Count')
    plt.legend()
    plt.title('File Size Distribution')
    plt.savefig(output_path)
    plt.close()

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if USE_SPECIFIC_CORPORA:
        # Use manually specified corpora
        runs = SPECIFIC_CORPORA
        # Verify that the specified corpora exist
        existing_runs = []
        for run in runs:
            run_path = os.path.join(CORPUS_BASE_DIR, run)
            if os.path.exists(run_path) and os.path.isdir(run_path):
                existing_runs.append(run)
            else:
                print(f"Warning: Corpus '{run}' not found at {run_path}")
        
        if len(existing_runs) < 2:
            print(f"Error: Need at least 2 existing corpora. Found: {existing_runs}")
            return
        
        runs = existing_runs
        print(f"Using specified corpora: {runs}")
    else:
        # Auto-discover runs (original behavior)
        runs = list_runs(CORPUS_BASE_DIR, FILE_TYPE)
        if not runs:
            print("No runs found!")
            return

        print("Available runs:")
        for i, run in enumerate(runs):
            print(f"{i}: {run}")
        idxs = input("Enter the indices of runs to compare (comma separated, e.g. 0,1): ")
        idxs = [int(x.strip()) for x in idxs.split(",") if x.strip().isdigit()]
        if len(idxs) < 2:
            print("Please select at least two runs.")
            return

        selected_runs = [runs[i] for i in idxs]
        print(f"Selected runs: {selected_runs}")
        runs = selected_runs

    hashes = [get_file_hashes(os.path.join(CORPUS_BASE_DIR, run)) for run in runs]
    sizes = [get_file_sizes(os.path.join(CORPUS_BASE_DIR, run)) for run in runs]

    # Pairwise comparison
    report_lines = []
    for i in range(len(runs)):
        for j in range(i+1, len(runs)):
            n1, n2, overlap, overlap_hashes = compare_hashes(hashes[i], hashes[j])
            report_lines.append(
                f"Comparison: {runs[i]} vs {runs[j]}\n"
                f"  Files in {runs[i]}: {n1}\n"
                f"  Files in {runs[j]}: {n2}\n"
                f"  Overlapping files (by content): {overlap}\n"
                f"  Jaccard similarity: {overlap / (n1 + n2 - overlap):.3f}\n"
            )
            print(report_lines[-1])

    # Plot file size distributions
    plot_path = os.path.join(OUTPUT_DIR, f"{PLOT_PREFIX}_{'_'.join(runs)}.png")
    plot_size_distribution(sizes, runs, plot_path)
    print(f"File size distribution plot saved to {plot_path}")

    # Write report
    report_path = os.path.join(OUTPUT_DIR, REPORT_NAME)
    with open(report_path, "w") as f:
        f.write("# Corpus Analysis Report\n\n")
        for line in report_lines:
            f.write(line + "\n")
        f.write(f"\n![File Size Distribution]({plot_path})\n")
    print(f"Report written to {report_path}")

if __name__ == "__main__":
    main()

# Example usage:
# hashes1 = get_file_hashes('corpus_output/png_run1')
# hashes2 = get_file_hashes('corpus_output/png_run2')
# n1, n2, overlap, overlap_hashes = compare_hashes(hashes1, hashes2)
# sizes1 = get_file_sizes('corpus_output/png_run1')
# sizes2 = get_file_sizes('corpus_output/png_run2')
# plot_size_distribution(sizes1, 'Run 1')
# plot_size_distribution(sizes2, 'Run 2')
# plt.show()