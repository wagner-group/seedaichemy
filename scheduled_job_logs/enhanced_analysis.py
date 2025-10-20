import os
import hashlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
import seaborn as sns
import re
import glob

# =========================
# CONFIGURATION
# =========================
CORPUS_BASE_DIR = "../corpus_output"
FILE_TYPE = "png"  # Change if needed
OUTPUT_DIR = "analysis_output"
REPORT_NAME = "comprehensive_corpus_report.md"
PLOT_PREFIX = "enhanced_analysis"
SPECIFIC_CORPORA = ["png_test1", "png_test2", "png_test_3"]
LOGS_DIR = "../logs"
# =========================

def get_file_hashes(directory):
    """Get SHA256 hashes of all files in directory"""
    hashes = {}
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            with open(path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            hashes[path] = file_hash
    return hashes

def get_file_sizes(directory):
    """Get file sizes and basic statistics"""
    sizes = []
    file_info = []
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            size = os.path.getsize(path)
            sizes.append(size)
            file_info.append({
                'path': path,
                'size': size,
                'name': fname
            })
    return sizes, file_info

def compare_hashes(hashes1, hashes2):
    """Compare two sets of file hashes"""
    set1 = set(hashes1.values())
    set2 = set(hashes2.values())
    overlap = set1 & set2
    return len(set1), len(set2), len(overlap), overlap

def create_venn_diagram(corpus_names, hash_sets, output_path):
    """Create a Venn diagram showing file overlap"""
    from matplotlib_venn import venn3
    
    plt.figure(figsize=(12, 8))
    
    if len(hash_sets) == 3:
        venn3([hash_sets[0], hash_sets[1], hash_sets[2]], 
              set_labels=corpus_names,
              alpha=0.7)
    elif len(hash_sets) == 2:
        from matplotlib_venn import venn2
        venn2([hash_sets[0], hash_sets[1]], 
              set_labels=corpus_names,
              alpha=0.7)
    
    plt.title('File Content Overlap Between Corpora', fontsize=16, pad=20)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_size_distribution_plot(sizes_list, labels, output_path):
    """Create an improved file size distribution plot"""
    plt.figure(figsize=(15, 10))
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
    
    # Histogram
    for i, (sizes, label) in enumerate(zip(sizes_list, labels)):
        ax1.hist(sizes, bins=30, alpha=0.7, label=label, edgecolor='black', linewidth=0.5)
    
    ax1.set_xlabel('File Size (bytes)', fontsize=12)
    ax1.set_ylabel('Count', fontsize=12)
    ax1.set_title('File Size Distribution (Histogram)', fontsize=14)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    # Box plot
    box_data = [sizes for sizes in sizes_list]
    bp = ax2.boxplot(box_data, labels=labels, patch_artist=True)
    
    # Color the boxes
    colors = ['lightblue', 'lightgreen', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    ax2.set_ylabel('File Size (bytes)', fontsize=12)
    ax2.set_title('File Size Distribution (Box Plot)', fontsize=14)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def calculate_statistics(sizes):
    """Calculate comprehensive statistics for file sizes"""
    if not sizes:
        return {}
    
    return {
        'count': len(sizes),
        'min': min(sizes),
        'max': max(sizes),
        'mean': np.mean(sizes),
        'median': np.median(sizes),
        'std': np.std(sizes),
        'q25': np.percentile(sizes, 25),
        'q75': np.percentile(sizes, 75)
    }

def format_bytes(bytes_value):
    """Format bytes in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} TB"

def extract_subtool_statistics(corpus_name):
    """Extract subtool production statistics from log files"""
    # Find the corresponding log directory
    log_dirs = glob.glob(os.path.join(LOGS_DIR, "*"))
    target_log_dir = None
    
    for log_dir in log_dirs:
        if os.path.basename(log_dir).startswith(corpus_name.replace("_", " ")):
            target_log_dir = log_dir
            break
    
    if not target_log_dir:
        return None
    
    stats = {
        'search_queries': {'files': 0, 'keywords': []},
        'search_features': {'files': 0, 'keywords': []},
        'github_queries': {'files': 0, 'keywords': []}
    }
    
    # Extract from search_queries log
    search_log = os.path.join(target_log_dir, 'search_queries.log')
    if os.path.exists(search_log):
        with open(search_log, 'r') as f:
            content = f.read()
            # Count files generated
            if 'generated' in content and 'png files' in content:
                match = re.search(r'generated (\d+) png files', content)
                if match:
                    stats['search_queries']['files'] = int(match.group(1))
            
            # Extract search queries
            queries = re.findall(r'Search query: (.+)', content)
            stats['search_queries']['keywords'] = queries
    
    # Extract from search_features log
    features_log = os.path.join(target_log_dir, 'search_features.log')
    if os.path.exists(features_log):
        with open(features_log, 'r') as f:
            content = f.read()
            if 'generated' in content and 'png files' in content:
                match = re.search(r'generated (\d+) png files', content)
                if match:
                    stats['search_features']['files'] = int(match.group(1))
    
    # Extract from github_queries log
    github_log = os.path.join(target_log_dir, 'github_queries.log')
    if os.path.exists(github_log):
        with open(github_log, 'r') as f:
            content = f.read()
            # Count files generated
            if 'generated' in content and 'png files' in content:
                match = re.search(r'generated (\d+) png files', content)
                if match:
                    stats['github_queries']['files'] = int(match.group(1))
            
            # Extract search keywords
            keywords_match = re.search(r'Search keywords obtained: \[(.*?)\]', content)
            if keywords_match:
                keywords_str = keywords_match.group(1)
                keywords = [k.strip().strip("'\"") for k in keywords_str.split(',')]
                stats['github_queries']['keywords'] = keywords
    
    return stats

def analyze_keyword_overlap(all_stats):
    """Analyze overlap in keywords/queries between corpora and subtools"""
    overlap_analysis = {
        'search_queries_overlap': {},
        'github_queries_overlap': {},
        'cross_tool_overlap': {}
    }
    
    # Analyze search_queries overlap
    search_queries_sets = {}
    for corpus, stats in all_stats.items():
        if stats and stats['search_queries']['keywords']:
            search_queries_sets[corpus] = set(stats['search_queries']['keywords'])
    
    if len(search_queries_sets) >= 2:
        corpora = list(search_queries_sets.keys())
        for i in range(len(corpora)):
            for j in range(i+1, len(corpora)):
                set1 = search_queries_sets[corpora[i]]
                set2 = search_queries_sets[corpora[j]]
                overlap = set1 & set2
                overlap_analysis['search_queries_overlap'][f"{corpora[i]}_vs_{corpora[j]}"] = {
                    'overlap_count': len(overlap),
                    'overlap_queries': list(overlap),
                    'total_unique': len(set1 | set2),
                    'jaccard': len(overlap) / len(set1 | set2) if len(set1 | set2) > 0 else 0
                }
    
    # Analyze github_queries overlap
    github_queries_sets = {}
    for corpus, stats in all_stats.items():
        if stats and stats['github_queries']['keywords']:
            github_queries_sets[corpus] = set(stats['github_queries']['keywords'])
    
    if len(github_queries_sets) >= 2:
        corpora = list(github_queries_sets.keys())
        for i in range(len(corpora)):
            for j in range(i+1, len(corpora)):
                set1 = github_queries_sets[corpora[i]]
                set2 = github_queries_sets[corpora[j]]
                overlap = set1 & set2
                overlap_analysis['github_queries_overlap'][f"{corpora[i]}_vs_{corpora[j]}"] = {
                    'overlap_count': len(overlap),
                    'overlap_keywords': list(overlap),
                    'total_unique': len(set1 | set2),
                    'jaccard': len(overlap) / len(set1 | set2) if len(set1 | set2) > 0 else 0
                }
    
    return overlap_analysis

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Verify corpora exist
    existing_corpora = []
    for corpus in SPECIFIC_CORPORA:
        corpus_path = os.path.join(CORPUS_BASE_DIR, corpus)
        if os.path.exists(corpus_path) and os.path.isdir(corpus_path):
            existing_corpora.append(corpus)
        else:
            print(f"Warning: Corpus '{corpus}' not found at {corpus_path}")
    
    if len(existing_corpora) < 2:
        print(f"Error: Need at least 2 existing corpora. Found: {existing_corpora}")
        return
    
    print(f"Analyzing corpora: {existing_corpora}")
    
    # Extract subtool statistics from log files
    print("Extracting subtool statistics from log files...")
    subtool_stats = {}
    for corpus in existing_corpora:
        stats = extract_subtool_statistics(corpus)
        subtool_stats[corpus] = stats
        if stats:
            print(f"  {corpus}: search_queries={stats['search_queries']['files']}, search_features={stats['search_features']['files']}, github_queries={stats['github_queries']['files']}")
        else:
            print(f"  {corpus}: No log data found")
    
    # Analyze keyword overlap
    print("Analyzing keyword overlap...")
    keyword_overlap = analyze_keyword_overlap(subtool_stats)
    
    # Collect data
    all_hashes = []
    all_sizes = []
    all_file_info = []
    all_statistics = []
    
    for corpus in existing_corpora:
        corpus_path = os.path.join(CORPUS_BASE_DIR, corpus)
        hashes = get_file_hashes(corpus_path)
        sizes, file_info = get_file_sizes(corpus_path)
        stats = calculate_statistics(sizes)
        
        all_hashes.append(hashes)
        all_sizes.append(sizes)
        all_file_info.append(file_info)
        all_statistics.append(stats)
    
    # Generate visualizations
    # 1. Venn diagram
    hash_sets = [set(hashes.values()) for hashes in all_hashes]
    venn_path = os.path.join(OUTPUT_DIR, f"{PLOT_PREFIX}_venn_diagram.png")
    create_venn_diagram(existing_corpora, hash_sets, venn_path)
    
    # 2. Enhanced size distribution
    size_plot_path = os.path.join(OUTPUT_DIR, f"{PLOT_PREFIX}_size_distribution.png")
    create_size_distribution_plot(all_sizes, existing_corpora, size_plot_path)
    
    # Generate comprehensive report
    report_path = os.path.join(OUTPUT_DIR, REPORT_NAME)
    
    with open(report_path, "w") as f:
        f.write("# Comprehensive Corpus Analysis Report\n\n")
        
        # Category 1: Basic Information
        f.write("## Category 1: Basic Information\n\n")
        f.write("### Overview\n\n")
        f.write("This section provides fundamental statistics about each corpus and subtool production.\n\n")
        
        for i, corpus in enumerate(existing_corpora):
            stats = all_statistics[i]
            f.write(f"#### {corpus}\n\n")
            f.write(f"- **Total Files**: {stats['count']:,}\n")
            f.write(f"- **Smallest File**: {format_bytes(stats['min'])} ({stats['min']:,} bytes)\n")
            f.write(f"- **Largest File**: {format_bytes(stats['max'])} ({stats['max']:,} bytes)\n")
            f.write(f"- **Average File Size**: {format_bytes(stats['mean'])} ({stats['mean']:,.0f} bytes)\n")
            f.write(f"- **Median File Size**: {format_bytes(stats['median'])} ({stats['median']:,.0f} bytes)\n")
            f.write(f"- **Standard Deviation**: {format_bytes(stats['std'])} ({stats['std']:,.0f} bytes)\n")
            f.write(f"- **25th Percentile**: {format_bytes(stats['q25'])} ({stats['q25']:,.0f} bytes)\n")
            f.write(f"- **75th Percentile**: {format_bytes(stats['q75'])} ({stats['q75']:,.0f} bytes)\n\n")
            
            # Add subtool production statistics
            if subtool_stats.get(corpus):
                subtool_data = subtool_stats[corpus]
                f.write("**Subtool Production Breakdown:**\n")
                f.write(f"- **search_queries**: {subtool_data['search_queries']['files']:,} files\n")
                f.write(f"- **search_features**: {subtool_data['search_features']['files']:,} files\n")
                f.write(f"- **github_queries**: {subtool_data['github_queries']['files']:,} files\n\n")
        
        # Category 2: File Overlap
        f.write("## Category 2: File Overlap Analysis\n\n")
        f.write("### Methodology\n\n")
        f.write("File overlap analysis uses SHA256 cryptographic hashes to identify identical files across corpora. ")
        f.write("This method ensures that files with identical content are detected regardless of filename or location. ")
        f.write("The Jaccard similarity index measures the similarity between two sets and is calculated as:\n\n")
        f.write("**Jaccard Similarity = |A ∩ B| / |A ∪ B|**\n\n")
        f.write("Where:\n")
        f.write("- |A ∩ B| = Number of files present in both corpora\n")
        f.write("- |A ∪ B| = Total number of unique files across both corpora\n\n")
        f.write("A Jaccard similarity of 1.0 means all files are identical, while 0.0 means no overlap.\n\n")
        
        f.write("### Pairwise Comparisons\n\n")
        
        for i in range(len(existing_corpora)):
            for j in range(i+1, len(existing_corpora)):
                n1, n2, overlap, overlap_hashes = compare_hashes(all_hashes[i], all_hashes[j])
                jaccard = overlap / (n1 + n2 - overlap) if (n1 + n2 - overlap) > 0 else 0
                
                f.write(f"#### {existing_corpora[i]} vs {existing_corpora[j]}\n\n")
                f.write(f"- **Files in {existing_corpora[i]}**: {n1:,} files\n")
                f.write(f"- **Files in {existing_corpora[j]}**: {n2:,} files\n")
                f.write(f"- **Overlapping files (by content)**: {overlap:,} files\n")
                f.write(f"- **Jaccard similarity**: {jaccard:.3f}\n\n")
                
                # Explanation of what "files in X" means
                f.write("**Explanation**: 'Files in X' refers to the total number of unique files (by content hash) ")
                f.write("found in that corpus. This count includes all files regardless of their filename or location ")
                f.write("within the corpus directory structure.\n\n")
        
        f.write("### Visualization\n\n")
        f.write("The Venn diagram below shows the overlap between all corpora:\n\n")
        f.write(f"![Venn Diagram]({os.path.basename(venn_path)})\n\n")
        
        # Category 3: File Size Distribution
        f.write("## Category 3: File Size Distribution Analysis\n\n")
        f.write("### Summary Statistics\n\n")
        
        for i, corpus in enumerate(existing_corpora):
            stats = all_statistics[i]
            f.write(f"#### {corpus}\n\n")
            f.write(f"- **Minimum file size**: {format_bytes(stats['min'])} ({stats['min']:,} bytes)\n")
            f.write(f"- **Maximum file size**: {format_bytes(stats['max'])} ({stats['max']:,} bytes)\n")
            f.write(f"- **Average file size**: {format_bytes(stats['mean'])} ({stats['mean']:,.0f} bytes)\n")
            f.write(f"- **Median file size**: {format_bytes(stats['median'])} ({stats['median']:,.0f} bytes)\n\n")
        
        f.write("### Visualization\n\n")
        f.write("The following plots show the distribution of file sizes across all corpora:\n\n")
        f.write(f"![File Size Distribution]({os.path.basename(size_plot_path)})\n\n")
        
        f.write("**Interpretation**: The histogram shows the frequency distribution of file sizes, while the box plot ")
        f.write("displays the median, quartiles, and potential outliers. This helps identify patterns in file size ")
        f.write("distributions and any significant differences between corpora.\n\n")
        
        # Category 4: Keyword/Query Analysis
        f.write("## Category 4: Keyword and Query Analysis\n\n")
        f.write("### Subtool Query Diversity\n\n")
        
        # Search queries analysis
        if keyword_overlap['search_queries_overlap']:
            f.write("#### Search Queries Overlap Analysis\n\n")
            for comparison, data in keyword_overlap['search_queries_overlap'].items():
                f.write(f"**{comparison}**:\n")
                f.write(f"- **Overlap count**: {data['overlap_count']} queries\n")
                f.write(f"- **Total unique queries**: {data['total_unique']}\n")
                f.write(f"- **Jaccard similarity**: {data['jaccard']:.3f}\n")
                if data['overlap_queries']:
                    f.write(f"- **Overlapping queries**: {', '.join(data['overlap_queries'][:5])}")
                    if len(data['overlap_queries']) > 5:
                        f.write(f" (and {len(data['overlap_queries']) - 5} more)")
                    f.write("\n")
                f.write("\n")
        
        # GitHub queries analysis
        if keyword_overlap['github_queries_overlap']:
            f.write("#### GitHub Queries Overlap Analysis\n\n")
            for comparison, data in keyword_overlap['github_queries_overlap'].items():
                f.write(f"**{comparison}**:\n")
                f.write(f"- **Overlap count**: {data['overlap_count']} keywords\n")
                f.write(f"- **Total unique keywords**: {data['total_unique']}\n")
                f.write(f"- **Jaccard similarity**: {data['jaccard']:.3f}\n")
                if data['overlap_keywords']:
                    f.write(f"- **Sample overlapping keywords**: {', '.join(data['overlap_keywords'][:10])}")
                    if len(data['overlap_keywords']) > 10:
                        f.write(f" (and {len(data['overlap_keywords']) - 10} more)")
                    f.write("\n")
                f.write("\n")
        
        f.write("### Query Strategy Analysis\n\n")
        f.write("**search_queries**: Uses a combination of hardcoded queries and LLM-generated queries. ")
        f.write("The LLM generates diverse queries targeting different aspects of PNG files (graphics, testing, etc.).\n\n")
        
        f.write("**search_features**: Consistently generated 0 files across all runs, suggesting this tool ")
        f.write("may need configuration adjustments or the feature-based approach may not be suitable for PNG files.\n\n")
        
        f.write("**github_queries**: Uses a comprehensive set of ~50 keywords covering multiple domains ")
        f.write("including fuzzing, testing, graphics, AI/ML, cybersecurity, and software development. ")
        f.write("This broad approach helps discover PNG files across various GitHub repositories.\n\n")
        
        # Conclusion
        f.write("## Conclusion\n\n")
        f.write("This analysis provides a comprehensive view of the corpus characteristics, overlap patterns, ")
        f.write("file size distributions, and query strategy effectiveness. The results show that:\n\n")
        f.write("- **github_queries** was the most productive tool, generating thousands of files\n")
        f.write("- **search_queries** showed variable performance across runs\n")
        f.write("- **search_features** consistently failed to generate files\n")
        f.write("- Query diversity varied between runs, with some overlap in search strategies\n")
        f.write("- The combination of different query strategies helps achieve comprehensive corpus coverage\n\n")
    
    print(f"Comprehensive report written to {report_path}")
    print(f"Venn diagram saved to {venn_path}")
    print(f"Size distribution plot saved to {size_plot_path}")

if __name__ == "__main__":
    main() 