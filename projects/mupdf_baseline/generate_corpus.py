#!/usr/bin/env python3
"""
This script creates multiple low-effort corpora for fuzzing, by randomly sampling files
from a MuPDF seed corpus. It accepts command-line arguments to specify the source directory,
destination directory, number of samples per corpus, and the number of corpora to generate.
After generating the corpora, it writes a text file (corpus_paths.txt) in the destination
directory listing the full paths of each generated corpus folder.
"""

import os
import sys
import argparse
import random
import shutil

def parse_arguments():
    # Set up the argument parser with required options.
    parser = argparse.ArgumentParser(
        description="Generate multiple sampled corpora for fuzzing from MuPDF seed files."
    )
    parser.add_argument("--source", "-s", required=True,
                        help="Path to the source directory containing the MuPDF seed files.")
    parser.add_argument("--destination", "-d", required=True,
                        help="Path to the output directory where the sampled corpora will be copied.")
    parser.add_argument("--samples", "-n", type=int, default=5,
                        help="Number of files to randomly sample for each corpus (default: 5)")
    parser.add_argument("--corpus-count", "-c", type=int, required=True,
                        help="Number of separate sample corpora to generate.")

    return parser.parse_args()

def verify_source_directory(source_dir):
    # Check that the source directory exists.
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)
    # List files from source directory (filter to files only).
    files = [f for f in os.listdir(source_dir)
             if os.path.isfile(os.path.join(source_dir, f))]
    if not files:
        print(f"Error: No files found in source directory '{source_dir}'.")
        sys.exit(1)
    return files

def create_directory(directory):
    # Create the destination directory if it does not exist.
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"Error creating directory '{directory}': {e}")
        sys.exit(1)

def generate_corpora(source_dir, dest_dir, files, samples, corpus_count):
    generated_paths = []  # To store full paths of each corpus folder generated

    # For each corpus we want to create, sample the specified number of files
    for i in range(1, corpus_count + 1):
        corpus_folder = os.path.join(dest_dir, f"corpus_{i}")
        create_directory(corpus_folder)
        
        # Check if there are enough files to sample without replacement, if not use replacement.
        if len(files) < samples:
            sampled_files = random.choices(files, k=samples)
        else:
            sampled_files = random.sample(files, samples)

        for file_name in sampled_files:
            src_file = os.path.join(source_dir, file_name)
            dest_file = os.path.join(corpus_folder, file_name)
            try:
                shutil.copy2(src_file, dest_file)
            except Exception as e:
                print(f"Error copying '{src_file}' to '{dest_file}': {e}")

        generated_paths.append(os.path.abspath(corpus_folder))
        print(f"Generated corpus: {os.path.abspath(corpus_folder)}")
    return generated_paths

def write_corpus_paths(dest_dir, corpus_paths):
    # Write all generated corpus folder full paths into corpus_paths.txt in the destination dir.
    output_file = os.path.join(dest_dir, "corpus_paths.txt")
    try:
        with open(output_file, "w") as f:
            for path in corpus_paths:
                f.write(path + "\n")
        print(f"Corpus paths written to '{output_file}'")
    except Exception as e:
        print(f"Error writing corpus paths to '{output_file}': {e}")

def main():
    args = parse_arguments()

    # Verify source directory and build list of files.
    files = verify_source_directory(args.source)
    print(f"Found {len(files)} files in source directory '{args.source}'.")

    # Create destination directory if it does not exist.
    create_directory(args.destination)
    
    # Generate corpora by sampling files.
    corpus_paths = generate_corpora(args.source, args.destination, files, args.samples, args.corpus_count)

    # Write the corpus paths to a text file.
    write_corpus_paths(args.destination, corpus_paths)

if __name__ == "__main__":
    main()