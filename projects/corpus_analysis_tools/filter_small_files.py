#!/usr/bin/env python3
"""
Filter small files from corpus and create different sized sub-corpora for testing.
Usage: python3 filter_small_files.py <corpus_dir> <output_base_dir>
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
import json
from collections import defaultdict

def get_file_size_mb(file_path):
    """Get file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)

def analyze_corpus(corpus_dir):
    """Analyze the corpus and return file information."""
    files_info = []
    total_files = 0
    
    print(f"Analyzing corpus: {corpus_dir}")
    
    for file_path in Path(corpus_dir).rglob("*.jpg"):
        if file_path.is_file():
            size_mb = get_file_size_mb(file_path)
            files_info.append({
                'path': str(file_path),
                'name': file_path.name,
                'size_mb': size_mb,
                'size_bytes': os.path.getsize(file_path)
            })
            total_files += 1
    
    print(f"Total files found: {total_files}")
    return files_info

def filter_small_files(files_info, max_size_mb=1.0):
    """Filter files by size (smaller than max_size_mb)."""
    small_files = [f for f in files_info if f['size_mb'] <= max_size_mb]
    print(f"Files <= {max_size_mb}MB: {len(small_files)}")
    return small_files

def create_sub_corpus(files_info, output_dir, target_count, corpus_name):
    """Create a sub-corpus with the specified number of smallest files."""
    # Sort by size (smallest first)
    sorted_files = sorted(files_info, key=lambda x: x['size_bytes'])
    
    # Take the smallest N files
    selected_files = sorted_files[:target_count]
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy files
    copied_count = 0
    total_size_mb = 0
    
    for file_info in selected_files:
        src_path = file_info['path']
        dst_path = os.path.join(output_dir, file_info['name'])
        
        try:
            shutil.copy2(src_path, dst_path)
            copied_count += 1
            total_size_mb += file_info['size_mb']
        except Exception as e:
            print(f"Error copying {src_path}: {e}")
    
    print(f"{corpus_name}: {copied_count} files, {total_size_mb:.2f}MB total")
    
    # Save metadata
    metadata = {
        'corpus_name': corpus_name,
        'file_count': copied_count,
        'total_size_mb': total_size_mb,
        'max_file_size_mb': max([f['size_mb'] for f in selected_files]),
        'min_file_size_mb': min([f['size_mb'] for f in selected_files]),
        'files': [{'name': f['name'], 'size_mb': f['size_mb']} for f in selected_files]
    }
    
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def analyze_source_distribution(files_info, corpus_dir):
    """Analyze which tools contributed files by looking at source directories."""
    source_counts = defaultdict(int)
    
    for file_info in files_info:
        file_path = Path(file_info['path'])
        # Try to determine source by looking at parent directories
        relative_path = file_path.relative_to(Path(corpus_dir))
        if len(relative_path.parts) > 1:
            source = relative_path.parts[0]  # First directory level
            source_counts[source] += 1
    
    print("\nSource distribution:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} files")
    
    return source_counts

def main():
    parser = argparse.ArgumentParser(description="Filter small files and create sub-corpora")
    parser.add_argument("corpus_dir", help="Input corpus directory")
    parser.add_argument("output_base_dir", help="Base output directory for sub-corpora")
    parser.add_argument("--max-size", type=float, default=1.0, help="Maximum file size in MB (default: 1.0)")
    parser.add_argument("--sizes", nargs='+', type=int, default=[10000, 40000, 70000], 
                       help="Target file counts for sub-corpora (default: 10000 40000 70000)")
    
    args = parser.parse_args()
    
    # Analyze corpus
    files_info = analyze_corpus(args.corpus_dir)
    
    if not files_info:
        print("No files found in corpus!")
        return
    
    # Filter small files
    small_files = filter_small_files(files_info, args.max_size)
    
    if not small_files:
        print(f"No files <= {args.max_size}MB found!")
        return
    
    # Analyze source distribution
    source_counts = analyze_source_distribution(small_files, args.corpus_dir)
    
    # Create sub-corpora
    print(f"\nCreating sub-corpora with sizes: {args.sizes}")
    
    for target_count in args.sizes:
        if target_count > len(small_files):
            print(f"Warning: Requested {target_count} files but only {len(small_files)} small files available")
            target_count = len(small_files)
        
        corpus_name = f"corpus_{target_count//1000}k"
        output_dir = os.path.join(args.output_base_dir, corpus_name)
        
        metadata = create_sub_corpus(small_files, output_dir, target_count, corpus_name)
        
        # Save source distribution for this sub-corpus
        sub_corpus_files = small_files[:target_count]
        sub_source_counts = analyze_source_distribution(sub_corpus_files, args.corpus_dir)
        
        metadata['source_distribution'] = dict(sub_source_counts)
        
        with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
    
    print(f"\nSub-corpora created in: {args.output_base_dir}")

if __name__ == "__main__":
    main() 
