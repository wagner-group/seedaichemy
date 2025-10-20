#!/usr/bin/env python3
"""
Benchmark script to measure the performance impact of magic number detection
"""

import time
import requests
from io import BytesIO
from tool.utils import check_magic_num_response

def benchmark_extension_only(url):
    """Benchmark extension-only checking (fast path)"""
    start_time = time.time()
    
    # Simulate extension check
    if any(url.lower().endswith(ext) for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.zip', '.tar', '.gz', '.rar', '.7z', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.csv', '.json', '.xml', '.html', '.htm', '.css', '.js', '.py', '.java', '.cpp', '.c', '.h', '.hpp', '.md', '.rst', '.tex', '.log', '.out', '.err']):
        is_valid = True
    else:
        is_valid = False
    
    end_time = time.time()
    return end_time - start_time, is_valid

def benchmark_magic_check(url, file_extension):
    """Benchmark magic number checking (slow path)"""
    start_time = time.time()
    
    try:
        # Simulate the magic check process
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
        
        # Use the magic detection function with file_extension
        is_valid = check_magic_num_response(response, file_extension=file_extension)
        response.close()
        
    except Exception as e:
        print(f"Error checking {url}: {e}")
        is_valid = False
    
    end_time = time.time()
    return end_time - start_time, is_valid

def main():
    # Test URLs - mix of valid and invalid files
    test_cases = [
        ("https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", "pdf"),  # Valid PDF
        ("https://httpbin.org/image/png", "png"),  # Valid PNG
        ("https://httpbin.org/html", "pdf"),  # HTML (should be invalid for PDF)
        ("https://httpbin.org/json", "pdf"),  # JSON (should be invalid for PDF)
        ("https://httpbin.org/robots.txt", "pdf"),  # Text (should be invalid for PDF)
    ]
    
    print("Benchmarking Magic Number Detection Performance")
    print("=" * 50)
    
    total_extension_time = 0
    total_magic_time = 0
    extension_valid_count = 0
    magic_valid_count = 0
    
    for i, (url, file_extension) in enumerate(test_cases, 1):
        print(f"\nTest {i}: {url}")
        
        # Extension-only benchmark
        ext_time, ext_valid = benchmark_extension_only(url)
        total_extension_time += ext_time
        if ext_valid:
            extension_valid_count += 1
        print(f"  Extension check: {ext_time:.4f}s, Valid: {ext_valid}")
        
        # Magic number benchmark
        magic_time, magic_valid = benchmark_magic_check(url, file_extension)
        total_magic_time += magic_time
        if magic_valid:
            magic_valid_count += 1
        print(f"  Magic check: {magic_time:.4f}s, Valid: {magic_valid}")
        
        # Calculate slowdown
        if ext_time > 0:
            slowdown = magic_time / ext_time
            print(f"  Slowdown: {slowdown:.1f}x")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Extension-only total time: {total_extension_time:.4f}s")
    print(f"Magic detection total time: {total_magic_time:.4f}s")
    print(f"Average extension time: {total_extension_time/len(test_cases):.4f}s")
    print(f"Average magic time: {total_magic_time/len(test_cases):.4f}s")
    
    if total_extension_time > 0:
        overall_slowdown = total_magic_time / total_extension_time
        print(f"Overall slowdown: {overall_slowdown:.1f}x")
    
    print(f"Extension valid files: {extension_valid_count}/{len(test_cases)}")
    print(f"Magic valid files: {magic_valid_count}/{len(test_cases)}")

if __name__ == "__main__":
    main() 