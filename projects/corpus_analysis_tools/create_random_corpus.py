#!/usr/bin/env python3
"""
Create a random corpus by sampling files from the original corpus.
Usage: python3 create_random_corpus.py <corpus_dir> <output_dir> <sample_size>
"""

import os
import sys
import shutil
import argparse
import random
from pathlib import Path
import json
from collections import defaultdict

def get_all_files(corpus_dir):
    """Get all JPEG files from the corpus."""
    files = []
    for file_path in Path(corpus_dir).rglob("*.jpg"):
        if file_path.is_file():
            files.append({
                'path': str(file_path),
                'name': file_path.name,
                'size_bytes': os.path.getsize(file_path),
                'size_mb': os.path.getsize(file_path) / (1024 * 1024)
            })
    return files

def create_random_corpus(files, output_dir, sample_size):
    """Create a random corpus by sampling files."""
    if sample_size > len(files):
        print(f"Warning: Requested {sample_size} files but only {len(files)} available")
        sample_size = len(files)
    
    # Randomly sample files
    selected_files = random.sample(files, sample_size)
    
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
    
    print(f"Random corpus: {copied_count} files, {total_size_mb:.2f}MB total")
    
    # Save metadata
    metadata = {
        'corpus_name': f'random_{sample_size}',
        'file_count': copied_count,
        'total_size_mb': total_size_mb,
        'max_file_size_mb': max([f['size_mb'] for f in selected_files]),
        'min_file_size_mb': min([f['size_mb'] for f in selected_files]),
        'average_file_size_mb': sum([f['size_mb'] for f in selected_files]) / len(selected_files),
        'files': [{'name': f['name'], 'size_mb': f['size_mb']} for f in selected_files]
    }
    
    with open(os.path.join(output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata, selected_files

def analyze_source_distribution(files, corpus_dir):
    """Analyze which tools contributed files by looking at source directories."""
    source_counts = defaultdict(int)
    source_files = defaultdict(list)
    
    for file_info in files:
        file_path = Path(file_info['path'])
        # Try to determine source by looking at parent directories
        relative_path = file_path.relative_to(Path(corpus_dir))
        if len(relative_path.parts) > 1:
            source = relative_path.parts[0]  # First directory level
            source_counts[source] += 1
            source_files[source].append(file_info['name'])
    
    print("\nSource distribution:")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count} files")
    
    return source_counts, source_files

def main():
    parser = argparse.ArgumentParser(description="Create random corpus by sampling files")
    parser.add_argument("corpus_dir", help="Input corpus directory")
    parser.add_argument("output_dir", help="Output directory for random corpus")
    parser.add_argument("sample_size", type=int, help="Number of files to sample")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    
    args = parser.parse_args()
    
    if args.seed:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")
    
    # Get all files
    print(f"Scanning corpus: {args.corpus_dir}")
    files = get_all_files(args.corpus_dir)
    print(f"Total files found: {len(files)}")
    
    if not files:
        print("No files found in corpus!")
        return
    
    # Create random corpus
    metadata, selected_files = create_random_corpus(files, args.output_dir, args.sample_size)
    
    # Analyze source distribution
    source_counts, source_files = analyze_source_distribution(selected_files, args.corpus_dir)
    
    # Add source distribution to metadata
    metadata['source_distribution'] = dict(source_counts)
    metadata['source_files'] = dict(source_files)
    
    with open(os.path.join(args.output_dir, 'metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nRandom corpus created in: {args.output_dir}")

if __name__ == "__main__":
    main() 