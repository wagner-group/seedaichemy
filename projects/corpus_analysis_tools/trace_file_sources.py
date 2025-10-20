#!/usr/bin/env python3
"""
Trace the source of files in the corpus by matching file hashes with original source directories.
Usage: python3 trace_file_sources.py <corpus_dir>
"""

import os
import sys
import hashlib
import argparse
from pathlib import Path
import json
from collections import defaultdict

def hash_file(file_path):
    """Calculate SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def scan_source_directories():
    """Scan all source directories and create a hash map."""
    hash_to_sources = {}  # Changed to track multiple sources per hash
    
    # Define source directories exactly as they appear in combine.py, but with trial-1 subdirectory
    source_dirs = {
        'search_queries': 'search_queries/trial-1/jpg_corpus',
        'search_features': 'search_features/trial-1/jpg_corpus', 
        'github_queries': 'github_queries/trial-1/jpg_corpus',
        'common_crawl': 'common_crawl/trial-1/jpg_corpus',
        'bug_tracker': 'bug_tracker/trial-1/jpg_corpus'  # Note: no matching_files subdirectory found
    }
    
    print("Scanning source directories...")
    
    for tool_name, dir_path in source_dirs.items():
        if os.path.exists(dir_path):
            print(f"  Scanning {tool_name}: {dir_path}")
            file_count = 0
            
            for file_path in Path(dir_path).rglob("*.jpg"):
                if file_path.is_file():
                    try:
                        file_hash = hash_file(file_path)
                        if file_hash not in hash_to_sources:
                            hash_to_sources[file_hash] = []
                        hash_to_sources[file_hash].append(tool_name)
                        file_count += 1
                    except Exception as e:
                        print(f"    Error processing {file_path}: {e}")
            
            print(f"    Found {file_count} files")
        else:
            print(f"  Directory not found: {dir_path}")
    
    print(f"Total hash mappings: {len(hash_to_sources)}")
    return hash_to_sources

def analyze_corpus_sources(corpus_dir, hash_to_sources):
    """Analyze which tools contributed files to the corpus."""
    source_counts = defaultdict(int)
    source_files = defaultdict(list)
    unknown_files = []
    multi_source_files = 0  # Track files from multiple sources
    
    print(f"\nAnalyzing corpus: {corpus_dir}")
    
    for file_path in Path(corpus_dir).rglob("*.jpg"):
        if file_path.is_file():
            try:
                file_hash = hash_file(file_path)
                if file_hash in hash_to_sources:
                    sources = hash_to_sources[file_hash]
                    # Credit all sources for this file
                    for source in sources:
                        source_counts[source] += 1
                        source_files[source].append(file_path.name)
                    
                    # Track multi-source files
                    if len(sources) > 1:
                        multi_source_files += 1
                else:
                    unknown_files.append(file_path.name)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    
    print("\nSource distribution (files can be credited to multiple sources):")
    total_credits = sum(source_counts.values())
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_credits) * 100 if total_credits > 0 else 0
        print(f"  {source}: {count} files ({percentage:.1f}%)")
    
    if unknown_files:
        print(f"  Unknown source: {len(unknown_files)} files")
    
    if multi_source_files > 0:
        print(f"  Files from multiple sources: {multi_source_files}")
    
    return source_counts, source_files, unknown_files, multi_source_files

def check_if_directories_exist():
    """Check which source directories actually exist and have files."""
    source_dirs = {
        'search_queries': 'search_queries/trial-1/jpg_corpus',
        'search_features': 'search_features/trial-1/jpg_corpus', 
        'github_queries': 'github_queries/trial-1/jpg_corpus',
        'common_crawl': 'common_crawl/trial-1/jpg_corpus',
        'bug_tracker': 'bug_tracker/trial-1/jpg_corpus'
    }
    
    print("\nChecking source directory status:")
    for tool_name, dir_path in source_dirs.items():
        if os.path.exists(dir_path):
            file_count = len(list(Path(dir_path).rglob("*.jpg")))
            print(f"  {tool_name}: {dir_path} - {file_count} files")
        else:
            print(f"  {tool_name}: {dir_path} - NOT FOUND")

def main():
    parser = argparse.ArgumentParser(description="Trace file sources in corpus")
    parser.add_argument("corpus_dir", help="Corpus directory to analyze")
    parser.add_argument("--output", help="Output JSON file for results")
    parser.add_argument("--check-dirs", action='store_true', help="Just check which source directories exist")
    
    args = parser.parse_args()
    
    if args.check_dirs:
        check_if_directories_exist()
        return
    
    # Scan source directories
    hash_to_sources = scan_source_directories()
    
    # Analyze corpus
    source_counts, source_files, unknown_files, multi_source_files = analyze_corpus_sources(args.corpus_dir, hash_to_sources)
    
    # Prepare results
    results = {
        'corpus_dir': args.corpus_dir,
        'source_distribution': dict(source_counts),
        'source_files': {k: v[:100] for k, v in source_files.items()},  # Limit to first 100 files per source
        'unknown_files': unknown_files[:100],  # Limit to first 100 unknown files
        'total_files': sum(source_counts.values()) + len(unknown_files),
        'total_known_sources': sum(source_counts.values()),
        'total_unknown_sources': len(unknown_files),
        'multi_source_files': multi_source_files
    }
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {args.output}")
    else:
        print("\nResults:")
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main() 