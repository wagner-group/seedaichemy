import os
import hashlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from collections import defaultdict
import seaborn as sns
import re
import glob
import argparse
from datetime import datetime
import json
from supported_file_types import SUPPORTED_FILE_TYPES

# =========================
# CONFIGURATION
# =========================
CORPUS_BASE_DIR = "../../corpus_output"
OUTPUT_DIR = "reports"
REPORT_NAME = "comprehensive_corpus_report.md"
PLOT_PREFIX = "enhanced_analysis"
LOGS_DIR = "../../logs"

# =========================

def parse_corpus_name(corpus_name):
    """Parse corpus name to extract file type, timestamp, and attempt number"""
    # Handle old format: png_test1, png_test2, etc.
    if "_test" in corpus_name and not "_attempt" in corpus_name:
        file_type = corpus_name.split("_test")[0]
        return file_type, None, None, None, None
    
    # Handle new format: json_20250707_221201_attempt1
    parts = corpus_name.split("_")
    if len(parts) >= 4 and "attempt" in parts[-1]:
        file_type = parts[0]
        timestamp = f"{parts[1]}_{parts[2]}_{parts[3]}"
        attempt = int(parts[-1].replace("attempt", ""))
        # Try to extract timeout and file_size from logs or use defaults
        timeout = None
        file_size = None
        return file_type, timestamp, attempt, timeout, file_size
    
    # Handle other formats
    return None, None, None, None, None

def get_corpus_parameters(corpus_name):
    """Extract parameters from corpus name or logs to determine matching criteria"""
    file_type, timestamp, attempt, timeout, file_size = parse_corpus_name(corpus_name)
    
    # Try to extract timeout and file_size from batch results if available
    batch_results_files = [
        "corpus_results_20250708_114249.json",
        "corpus_results_20250707_221104.json", 
        "corpus_results_20250707_215628.json"
    ]
    
    for results_file in batch_results_files:
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                for result in results:
                    if result.get('output_dir') == f"corpus_output/{corpus_name}":
                        timeout = result.get('timeout')
                        file_size = result.get('file_size')
                        break
            except (json.JSONDecodeError, IOError):
                continue
    
    return {
        'file_type': file_type,
        'timeout': timeout,
        'file_size': file_size,
        'timestamp': timestamp,
        'attempt': attempt
    }

def group_corpora_by_parameters(corpus_groups):
    """Group corpora by identical parameters for fair comparison"""
    parameter_groups = defaultdict(list)
    
    for file_type, corpora in corpus_groups.items():
        for corpus in corpora:
            params = get_corpus_parameters(corpus['name'])
            
            # Create a key based on all parameters
            param_key = (
                params['file_type'],
                params['timeout'], 
                params['file_size']
            )
            
            parameter_groups[param_key].append(corpus)
    
    return parameter_groups

def auto_detect_corpora():
    """Auto-detect available corpora and group them by parameters"""
    if not os.path.exists(CORPUS_BASE_DIR):
        print(f"Error: Corpus base directory {CORPUS_BASE_DIR} not found")
        return {}
    
    corpus_groups = defaultdict(list)
    
    for item in os.listdir(CORPUS_BASE_DIR):
        item_path = os.path.join(CORPUS_BASE_DIR, item)
        if os.path.isdir(item_path):
            file_type, timestamp, attempt, timeout, file_size = parse_corpus_name(item)
            
            # Group by file type for organization
            group_key = file_type if file_type else "unknown"
            corpus_groups[group_key].append({
                'name': item,
                'path': item_path,
                'file_type': file_type,
                'timestamp': timestamp,
                'attempt': attempt,
                'timeout': timeout,
                'file_size': file_size
            })
    
    return corpus_groups

def get_file_hashes(directory):
    """Get SHA256 hashes of all files in directory"""
    hashes = {}
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            try:
                with open(path, 'rb') as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                hashes[path] = file_hash
            except (IOError, OSError):
                print(f"Warning: Could not read file {path}")
    return hashes

def get_file_sizes(directory):
    """Get file sizes and basic statistics"""
    sizes = []
    file_info = []
    for root, _, files in os.walk(directory):
        for fname in files:
            path = os.path.join(root, fname)
            try:
                size = os.path.getsize(path)
                sizes.append(size)
                file_info.append({
                    'path': path,
                    'size': size,
                    'name': fname
                })
            except (IOError, OSError):
                print(f"Warning: Could not get size for file {path}")
    return sizes, file_info

def compare_hashes(hashes1, hashes2):
    """Compare two sets of file hashes"""
    set1 = set(hashes1.values())
    set2 = set(hashes2.values())
    overlap = set1 & set2
    return len(set1), len(set2), len(overlap), overlap

def create_venn_diagram(corpus_names, hash_sets, output_path):
    """Create a Venn diagram showing file overlap"""
    try:
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
        else:
            print(f"Warning: Venn diagram requires 2-3 corpora, got {len(hash_sets)}")
            return
        
        plt.title('File Content Overlap Between Corpora', fontsize=16, pad=20)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    except ImportError:
        print("Warning: matplotlib_venn not available, skipping Venn diagram")
    except Exception as e:
        print(f"Error creating Venn diagram: {e}")

def create_size_distribution_plot(sizes_list, labels, output_path):
    """Create an improved file size distribution plot"""
    try:
        # Create subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Histogram
        for i, (sizes, label) in enumerate(zip(sizes_list, labels)):
            if sizes:  # Only plot if we have data
                ax1.hist(sizes, bins=30, alpha=0.7, label=label, edgecolor='black', linewidth=0.5)
        
        ax1.set_xlabel('File Size (bytes)', fontsize=12)
        ax1.set_ylabel('Count', fontsize=12)
        ax1.set_title('File Size Distribution (Histogram)', fontsize=14)
        ax1.legend(fontsize=11)
        ax1.grid(True, alpha=0.3)
        
        # Box plot
        box_data = [sizes for sizes in sizes_list if sizes]  # Only include non-empty data
        if box_data:
            bp = ax2.boxplot(box_data, tick_labels=[label for label, sizes in zip(labels, sizes_list) if sizes], patch_artist=True)
            
            # Color the boxes
            colors = ['lightblue', 'lightgreen', 'lightcoral', 'lightyellow', 'lightpink']
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
        
        ax2.set_ylabel('File Size (bytes)', fontsize=12)
        ax2.set_title('File Size Distribution (Box Plot)', fontsize=14)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"Error creating size distribution plot: {e}")

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

def find_closest_log_directory(corpus_timestamp):
    """Find the closest log directory within a 10-minute buffer window"""
    # Convert corpus timestamp from YYYYMMDD_HHMMSS to datetime
    try:
        year = int(corpus_timestamp[:4])
        month = int(corpus_timestamp[4:6])
        day = int(corpus_timestamp[6:8])
        hour = int(corpus_timestamp[9:11])
        minute = int(corpus_timestamp[11:13])
        second = int(corpus_timestamp[13:15])
        
        from datetime import datetime, timedelta
        corpus_time = datetime(year, month, day, hour, minute, second)
    except (IndexError, ValueError):
        return None
    
    # Get all log directories
    log_dirs = glob.glob(os.path.join(LOGS_DIR, "*"))
    closest_dir = None
    min_diff = timedelta(minutes=10)  # 10-minute buffer
    
    for log_dir in log_dirs:
        dir_name = os.path.basename(log_dir)
        # Parse log directory name: "2025-07-08 011211"
        try:
            date_part, time_part = dir_name.split(' ')
            year, month, day = map(int, date_part.split('-'))
            hour = int(time_part[:2])
            minute = int(time_part[2:4])
            second = int(time_part[4:6])
            
            log_time = datetime(year, month, day, hour, minute, second)
            time_diff = abs(corpus_time - log_time)
            
            if time_diff <= min_diff:
                min_diff = time_diff
                closest_dir = log_dir
        except (ValueError, IndexError):
            continue
    
    return closest_dir

def extract_subtool_statistics(corpus_name):
    """Extract subtool production statistics from batch results files"""
    stats = {
        'search_queries': {'files': 0, 'keywords': []},
        'search_features': {'files': 0, 'keywords': []},
        'github_queries': {'files': 0, 'keywords': []}
    }
    
    # Look for the corpus in batch results files
    batch_results_files = []
    for file in os.listdir("../../"):
        if file.startswith("corpus_results_") and file.endswith(".json"):
            batch_results_files.append(os.path.join("../../", file))
    
    # Sort by modification time (newest first) to prioritize recent results
    batch_results_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    for results_file in batch_results_files:
        if os.path.exists(results_file):
            try:
                with open(results_file, 'r') as f:
                    results = json.load(f)
                
                for result in results:
                    if result.get('output_dir') == f"corpus_output/{corpus_name}":
                        # Extract file counts from stdout
                        stdout = result.get('stdout', '')
                        
                        # Extract search_queries file count
                        search_match = re.search(r'search_queries generated (\d+) (\w+) files', stdout)
                        if search_match:
                            stats['search_queries']['files'] = int(search_match.group(1))
                        
                        # Extract search_features file count
                        features_match = re.search(r'search_features generated (\d+) (\w+) files', stdout)
                        if features_match:
                            stats['search_features']['files'] = int(features_match.group(1))
                        
                        # Extract github_queries file count
                        github_match = re.search(r'github_queries generated (\d+) (\w+) files', stdout)
                        if github_match:
                            stats['github_queries']['files'] = int(github_match.group(1))
                        
                        # Found the corpus, no need to check other files
                        break
            except (json.JSONDecodeError, IOError):
                continue
    
    # Try to extract keywords from log files if available
    # Parse corpus name to extract timestamp for log directory lookup
    file_type, timestamp, attempt, timeout, file_size = parse_corpus_name(corpus_name)
    
    if timestamp:
        target_log_dir = find_closest_log_directory(timestamp)
        
        if target_log_dir and os.path.exists(target_log_dir):
            # Extract search queries from search_queries.log
            search_log = os.path.join(target_log_dir, 'search_queries.log')
            if os.path.exists(search_log):
                with open(search_log, 'r') as f:
                    content = f.read()
                    # Extract search queries
                    queries = re.findall(r'Search query: (.+)', content)
                    stats['search_queries']['keywords'] = queries
            
            # Extract search keywords from github_queries.log
            github_log = os.path.join(target_log_dir, 'github_queries.log')
            if os.path.exists(github_log):
                with open(github_log, 'r') as f:
                    content = f.read()
                    # Extract search keywords
                    keywords_match = re.search(r'Search keywords obtained: \[(.*?)\]', content)
                    if keywords_match:
                        keywords_str = keywords_match.group(1)
                        keywords = [k.strip().strip("'\"") for k in keywords_str.split(',')]
                        stats['github_queries']['keywords'] = keywords
            # Extract search_features keywords from search_features.log
            features_log = os.path.join(target_log_dir, 'search_features.log')
            if os.path.exists(features_log):
                with open(features_log, 'r') as f:
                    lines = f.readlines()
                    features_keywords = []
                    for line in lines:
                        match = re.search(r'<result>(.*?)</result>', line)
                        if match:
                            features_keywords.append(match.group(1).strip())
                    stats['search_features']['keywords'] = features_keywords
    return stats

def analyze_keyword_overlap(all_stats):
    """Analyze overlap in keywords/queries between corpora and subtools"""
    overlap_analysis = {
        'search_queries_overlap': {},
        'github_queries_overlap': {},
        'search_features_overlap': {},
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
    
    # Analyze search_features overlap
    search_features_sets = {}
    for corpus, stats in all_stats.items():
        if stats and stats['search_features']['keywords']:
            search_features_sets[corpus] = set(stats['search_features']['keywords'])
    
    if len(search_features_sets) >= 2:
        corpora = list(search_features_sets.keys())
        for i in range(len(corpora)):
            for j in range(i+1, len(corpora)):
                set1 = search_features_sets[corpora[i]]
                set2 = search_features_sets[corpora[j]]
                overlap = set1 & set2
                overlap_analysis['search_features_overlap'][f"{corpora[i]}_vs_{corpora[j]}"] = {
                    'overlap_count': len(overlap),
                    'overlap_keywords': list(overlap),
                    'total_unique': len(set1 | set2),
                    'jaccard': len(overlap) / len(set1 | set2) if len(set1 | set2) > 0 else 0
                }
    
    return overlap_analysis

def main():
    parser = argparse.ArgumentParser(description='Enhanced Corpus Analysis Tool')
    parser.add_argument('--file-type', '-f', help='Specific file type to analyze (e.g., png, jpg, json)')
    parser.add_argument('--corpora', '-c', nargs='+', help='Specific corpus names to analyze')
    parser.add_argument('--output-dir', '-o', default=OUTPUT_DIR, help='Output directory for reports')
    parser.add_argument('--list', '-l', action='store_true', help='List available corpora and exit')
    parser.add_argument('--parameter-groups', '-p', action='store_true', help='Show corpora grouped by parameters')
    
    args = parser.parse_args()
    
    # Auto-detect available corpora
    corpus_groups = auto_detect_corpora()
    
    if args.list:
        print("Available corpora by file type:")
        for file_type, corpora in corpus_groups.items():
            print(f"\n{file_type.upper()} files:")
            for corpus in corpora:
                print(f"  - {corpus['name']}")
        return
    
    if args.parameter_groups:
        print("Available corpora grouped by parameters:")
        parameter_groups = group_corpora_by_parameters(corpus_groups)
        for param_key, corpora in parameter_groups.items():
            file_type, timeout, file_size = param_key
            print(f"\nFile Type: {file_type}, Timeout: {timeout}s, File Size: {file_size}KB")
            for corpus in corpora:
                print(f"  - {corpus['name']}")
        return
    
    # Determine which corpora to analyze
    if args.corpora:
        # Use specific corpora provided by user
        existing_corpora = []
        for corpus_name in args.corpora:
            corpus_path = os.path.join(CORPUS_BASE_DIR, corpus_name)
            if os.path.exists(corpus_path):
                existing_corpora.append(corpus_name)
            else:
                print(f"Warning: Corpus '{corpus_name}' not found")
    elif args.file_type:
        # Use all corpora of the specified file type
        if args.file_type in corpus_groups:
            existing_corpora = [corpus['name'] for corpus in corpus_groups[args.file_type]]
        else:
            print(f"Error: No corpora found for file type '{args.file_type}'")
            print(f"Available file types: {list(corpus_groups.keys())}")
            return
    else:
        # Use all available corpora
        existing_corpora = []
        for file_type, corpora in corpus_groups.items():
            existing_corpora.extend([corpus['name'] for corpus in corpora])
    
    if len(existing_corpora) < 2:
        print(f"Error: Need at least 2 existing corpora. Found: {existing_corpora}")
        print("Use --list to see available corpora")
        return
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    print(f"Analyzing {len(existing_corpora)} corpora: {existing_corpora}")
    
    # Group corpora by parameters for fair comparison
    parameter_groups = group_corpora_by_parameters(corpus_groups)
    
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
    # 1. Venn diagram (only for corpora with identical parameters)
    venn_diagrams_created = []
    for param_key, corpora in parameter_groups.items():
        if len(corpora) >= 2 and len(corpora) <= 3:
            file_type, timeout, file_size = param_key
            corpus_names = [corpus['name'] for corpus in corpora]
            
            # Find the indices of these corpora in our analysis list
            indices = [existing_corpora.index(name) for name in corpus_names if name in existing_corpora]
            if len(indices) >= 2:
                hash_sets = [set(all_hashes[i].values()) for i in indices]
                venn_path = os.path.join(args.output_dir, f"{PLOT_PREFIX}_venn_{file_type}_{timeout}s_{file_size}KB.png")
                create_venn_diagram(corpus_names, hash_sets, venn_path)
                venn_diagrams_created.append(venn_path)
    
    # 2. Enhanced size distribution
    size_plot_path = os.path.join(args.output_dir, f"{PLOT_PREFIX}_size_distribution.png")
    create_size_distribution_plot(all_sizes, existing_corpora, size_plot_path)
    
    # Generate comprehensive report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(args.output_dir, f"comprehensive_corpus_report_{timestamp}.md")
    
    with open(report_path, "w") as f:
        f.write("# Comprehensive Corpus Analysis Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Corpora Analyzed**: {', '.join(existing_corpora)}\n\n")
        
        # Category 1: Basic Information
        f.write("## Category 1: Basic Information\n\n")
        f.write("### Overview\n\n")
        f.write("This section provides fundamental statistics about each corpus and subtool production.\n\n")
        
        for i, corpus in enumerate(existing_corpora):
            stats = all_statistics[i]
            f.write(f"#### {corpus}\n\n")
            
            if stats and 'count' in stats and stats['count'] > 0:
                f.write(f"- **Total Files**: {stats['count']:,}\n")
                f.write(f"- **Smallest File**: {format_bytes(stats['min'])} ({stats['min']:,} bytes)\n")
                f.write(f"- **Largest File**: {format_bytes(stats['max'])} ({stats['max']:,} bytes)\n")
                f.write(f"- **Average File Size**: {format_bytes(stats['mean'])} ({stats['mean']:,.0f} bytes)\n")
                f.write(f"- **Median File Size**: {format_bytes(stats['median'])} ({stats['median']:,.0f} bytes)\n")
                f.write(f"- **Standard Deviation**: {format_bytes(stats['std'])} ({stats['std']:,.0f} bytes)\n")
                f.write(f"- **25th Percentile**: {format_bytes(stats['q25'])} ({stats['q25']:,.0f} bytes)\n")
                f.write(f"- **75th Percentile**: {format_bytes(stats['q75'])} ({stats['q75']:,.0f} bytes)\n\n")
            else:
                f.write("- **Total Files**: 0 (Empty corpus)\n\n")
            
            # Add subtool production statistics for every corpus
            if subtool_stats.get(corpus):
                subtool_data = subtool_stats[corpus]
                f.write("**Subtool Production Breakdown:**\n")
                f.write(f"- **search_queries**: {subtool_data['search_queries']['files']:,} files\n")
                f.write(f"- **search_features**: {subtool_data['search_features']['files']:,} files\n")
                f.write(f"- **github_queries**: {subtool_data['github_queries']['files']:,} files\n\n")
                # Add sample queries if available
                if subtool_data['search_queries']['keywords']:
                    f.write("**Sample search_queries:**\n")
                    sample_queries = subtool_data['search_queries']['keywords'][:10]
                    for query in sample_queries:
                        f.write(f"- \"{query}\"\n")
                    if len(subtool_data['search_queries']['keywords']) > 10:
                        f.write(f"- ... and {len(subtool_data['search_queries']['keywords']) - 10} more queries\n")
                    f.write("\n")
                if subtool_data['search_features']['keywords']:
                    f.write("**Sample search_features:**\n")
                    sample_features = subtool_data['search_features']['keywords'][:10]
                    for feature in sample_features:
                        f.write(f"- \"{feature}\"\n")
                    if len(subtool_data['search_features']['keywords']) > 10:
                        f.write(f"- ... and {len(subtool_data['search_features']['keywords']) - 10} more features\n")
                    f.write("\n")
                if subtool_data['github_queries']['keywords']:
                    f.write("**Sample github_queries:**\n")
                    sample_keywords = subtool_data['github_queries']['keywords'][:10]
                    for keyword in sample_keywords:
                        f.write(f"- \"{keyword}\"\n")
                    if len(subtool_data['github_queries']['keywords']) > 10:
                        f.write(f"- ... and {len(subtool_data['github_queries']['keywords']) - 10} more keywords\n")
                    f.write("\n")
        
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
        
        if venn_diagrams_created:
            f.write("### Parameter-Matched Venn Diagrams\n\n")
            f.write("The following Venn diagrams show overlap between corpora with identical parameters:\n\n")
            for venn_path in venn_diagrams_created:
                f.write(f"![Venn Diagram]({os.path.basename(venn_path)})\n\n")
        
        # Category 3: File Size Distribution
        f.write("## Category 3: File Size Distribution Analysis\n\n")
        f.write("### Summary Statistics\n\n")
        
        for i, corpus in enumerate(existing_corpora):
            stats = all_statistics[i]
            f.write(f"#### {corpus}\n\n")
            if stats and 'min' in stats:
                f.write(f"- **Minimum file size**: {format_bytes(stats['min'])} ({stats['min']:,} bytes)\n")
                f.write(f"- **Maximum file size**: {format_bytes(stats['max'])} ({stats['max']:,} bytes)\n")
                f.write(f"- **Average file size**: {format_bytes(stats['mean'])} ({stats['mean']:,.0f} bytes)\n")
                f.write(f"- **Median file size**: {format_bytes(stats['median'])} ({stats['median']:,.0f} bytes)\n\n")
            else:
                f.write("- **No files in this corpus**\n\n")
        
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
        # search_features analysis
        if keyword_overlap['search_features_overlap']:
            f.write("#### Search Features Overlap Analysis\n\n")
            for comparison, data in keyword_overlap['search_features_overlap'].items():
                f.write(f"**{comparison}**:\n")
                f.write(f"- **Overlap count**: {data['overlap_count']} features\n")
                f.write(f"- **Total unique features**: {data['total_unique']}\n")
                f.write(f"- **Jaccard similarity**: {data['jaccard']:.3f}\n")
                if data['overlap_keywords']:
                    f.write(f"- **Overlapping features**: {', '.join(data['overlap_keywords'][:5])}")
                    if len(data['overlap_keywords']) > 5:
                        f.write(f" (and {len(data['overlap_keywords']) - 5} more)")
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
        f.write("The LLM generates diverse queries targeting different aspects of the target file type.\n\n")
        
        f.write("**search_features**: Uses feature-based search strategies to find files. ")
        f.write("Performance varies depending on the file type and available features.\n\n")
        
        f.write("**github_queries**: Uses a comprehensive set of keywords covering multiple domains ")
        f.write("including fuzzing, testing, graphics, AI/ML, cybersecurity, and software development. ")
        f.write("This broad approach helps discover files across various GitHub repositories.\n\n")
        
        # Conclusion
        f.write("## Conclusion\n\n")
        f.write("This analysis provides a comprehensive view of the corpus characteristics, overlap patterns, ")
        f.write("file size distributions, and query strategy effectiveness. The results show:\n\n")
        
        # Dynamic conclusion based on actual data
        total_files = sum(stats.get('count', 0) for stats in all_statistics)
        f.write(f"- **Total files analyzed**: {total_files:,}\n")
        f.write(f"- **Number of corpora compared**: {len(existing_corpora)}\n")
        
        if subtool_stats:
            total_search_queries = sum(stats.get('search_queries', {}).get('files', 0) for stats in subtool_stats.values() if stats)
            total_search_features = sum(stats.get('search_features', {}).get('files', 0) for stats in subtool_stats.values() if stats)
            total_github_queries = sum(stats.get('github_queries', {}).get('files', 0) for stats in subtool_stats.values() if stats)
            
            f.write(f"- **Total files from search_queries**: {total_search_queries:,}\n")
            f.write(f"- **Total files from search_features**: {total_search_features:,}\n")
            f.write(f"- **Total files from github_queries**: {total_github_queries:,}\n")
        
        f.write("- Query diversity varied between runs, with some overlap in search strategies\n")
        f.write("- The combination of different query strategies helps achieve comprehensive corpus coverage\n\n")
        
        # Add Glossary section with all queries
        f.write("## Glossary: Complete Query Lists\n\n")
        f.write("This section contains the complete lists of queries and keywords used by each subtool for each corpus.\n\n")
        for corpus in existing_corpora:
            if subtool_stats.get(corpus):
                subtool_data = subtool_stats[corpus]
                f.write(f"### {corpus}\n\n")
                if subtool_data['search_queries']['keywords']:
                    f.write("**Complete search_queries list:**\n")
                    for query in subtool_data['search_queries']['keywords']:
                        f.write(f"- \"{query}\"\n")
                    f.write("\n")
                if subtool_data['search_features']['keywords']:
                    f.write("**Complete search_features list:**\n")
                    for feature in subtool_data['search_features']['keywords']:
                        f.write(f"- \"{feature}\"\n")
                    f.write("\n")
                if subtool_data['github_queries']['keywords']:
                    f.write("**Complete github_queries list:**\n")
                    for keyword in subtool_data['github_queries']['keywords']:
                        f.write(f"- \"{keyword}\"\n")
                    f.write("\n")
    
    print(f"Comprehensive report written to {report_path}")
    if venn_diagrams_created:
        for venn_path in venn_diagrams_created:
            print(f"Venn diagram saved to {venn_path}")
    print(f"Size distribution plot saved to {size_plot_path}")

if __name__ == "__main__":
    main() 