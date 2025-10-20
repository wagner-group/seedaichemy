#!/usr/bin/env python3
"""
Safety check script to identify potential issues before running the full test
"""

import os
import sys
import shutil
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_api_keys():
    """Check if required API keys are available"""
    print("🔑 Checking API Keys...")
    
    required_keys = {
        'OPENAI_API_KEY': 'OpenAI API (for query generation)',
        'SERP_API_KEY': 'SerpAPI (for Google search)',
        'GOOGLE_API_KEY': 'Google Custom Search API',
        'SEARCH_ENGINE_ID': 'Google Custom Search Engine ID',
        'GITHUB_API_KEY': 'GitHub API (for repository search)',
        'AWS_ACCESS_KEY_ID': 'AWS (for Common Crawl)',
        'AWS_SECRET_ACCESS_KEY': 'AWS (for Common Crawl)',
        'AWS_REGION_NAME': 'AWS (for Common Crawl)'
    }
    
    missing_keys = []
    available_keys = []
    
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value:
            available_keys.append(f"✅ {key}: {description}")
        else:
            missing_keys.append(f"❌ {key}: {description}")
    
    print("Available keys:")
    for key in available_keys:
        print(f"  {key}")
    
    if missing_keys:
        print("\nMissing keys (these methods will be disabled):")
        for key in missing_keys:
            print(f"  {key}")
    
    return len(missing_keys) == 0

def check_disk_space():
    """Check available disk space"""
    print("\n💾 Checking disk space...")
    
    try:
        # Get current directory disk usage
        stat = shutil.disk_usage('.')
        free_gb = stat.free / (1024**3)
        total_gb = stat.total / (1024**3)
        
        print(f"  Total disk space: {total_gb:.1f} GB")
        print(f"  Available space: {free_gb:.1f} GB")
        
        if free_gb < 1.0:
            print("  ⚠️  WARNING: Less than 1 GB available")
            return False
        elif free_gb < 5.0:
            print("  ⚠️  WARNING: Less than 5 GB available")
            return False
        else:
            print("  ✅ Sufficient disk space available")
            return True
            
    except Exception as e:
        print(f"  ❌ Error checking disk space: {e}")
        return False

def check_network_connectivity():
    """Test basic network connectivity"""
    print("\n🌐 Checking network connectivity...")
    
    test_urls = [
        "https://httpbin.org/get",
        "https://www.google.com",
        "https://api.github.com"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            print(f"  ✅ {url}: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {url}: {e}")
            return False
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n📦 Checking Python dependencies...")
    
    required_packages = [
        ('requests', 'requests'),
        ('beautifulsoup4', 'bs4'),
        ('python-magic', 'magic'),
        ('openai', 'openai'),
        ('google-search-results', 'serpapi'),
        ('gitpython', 'git'),
        ('boto3', 'boto3')
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n  ⚠️  Missing packages: {', '.join(missing_packages)}")
        print("  Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_file_permissions():
    """Check if we can create directories and files"""
    print("\n📁 Checking file permissions...")
    
    test_dir = "test_outputs"
    test_file = os.path.join(test_dir, "test_write.txt")
    
    try:
        # Test directory creation
        os.makedirs(test_dir, exist_ok=True)
        print(f"  ✅ Can create directory: {test_dir}")
        
        # Test file writing
        with open(test_file, 'w') as f:
            f.write("test")
        print(f"  ✅ Can write file: {test_file}")
        
        # Test file reading
        with open(test_file, 'r') as f:
            content = f.read()
        print(f"  ✅ Can read file: {test_file}")
        
        # Clean up
        os.remove(test_file)
        print(f"  ✅ Can delete file: {test_file}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Permission error: {e}")
        return False

def check_subprocess_safety():
    """Test if subprocess execution works safely"""
    print("\n🔧 Checking subprocess execution...")
    
    try:
        # Test simple command
        result = subprocess.run(
            [sys.executable, "-c", "print('test')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✅ Subprocess execution works")
            return True
        else:
            print(f"  ❌ Subprocess failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Subprocess error: {e}")
        return False

def check_magic_detection():
    """Test if magic number detection works"""
    print("\n🔍 Testing magic number detection...")
    
    try:
        from tool.utils import check_magic_num_response
        print("  ✅ Magic detection module imported")
        
        # Test with a simple mock
        from unittest.mock import Mock
        mock_response = Mock()
        mock_response.iter_content.return_value = iter([b'\x89PNG\r\n\x1a\n'])
        
        result = check_magic_num_response(mock_response, file_extension="png")
        print(f"  ✅ Magic detection test: {result}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Magic detection error: {e}")
        return False

def run_mini_test():
    """Run a very small test to verify everything works"""
    print("\n🧪 Running mini test...")
    
    try:
        # Create a minimal test
        test_dir = "test_outputs/mini_test"
        os.makedirs(test_dir, exist_ok=True)
        
        # Test just the search_queries module with minimal parameters
        from search_queries.search_queries import search_queries_main
        
        print("  Testing search_queries with minimal parameters...")
        search_queries_main(test_dir, "png", N_query=1, N_link=1)
        
        print("  ✅ Mini test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Mini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all safety checks"""
    print("🔒 SAFETY CHECKS")
    print("=" * 50)
    
    checks = [
        ("API Keys", check_api_keys),
        ("Disk Space", check_disk_space),
        ("Network", check_network_connectivity),
        ("Dependencies", check_dependencies),
        ("File Permissions", check_file_permissions),
        ("Subprocess", check_subprocess_safety),
        ("Magic Detection", check_magic_detection),
    ]
    
    results = {}
    all_passed = True
    
    for name, check_func in checks:
        try:
            result = check_func()
            results[name] = result
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  ❌ {name} check failed with exception: {e}")
            results[name] = False
            all_passed = False
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    
    for name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name}: {status}")
    
    if all_passed:
        print("\n🎉 All checks passed! Safe to run the full test.")
        
        # Ask user if they want to run mini test
        response = input("\nWould you like to run a mini test first? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if run_mini_test():
                print("\n🎉 Mini test passed! Ready for full test.")
            else:
                print("\n⚠️  Mini test failed. Check issues above.")
    else:
        print("\n⚠️  Some checks failed. Please address issues before running full test.")
        print("\nRecommendations:")
        if not results.get("API Keys", True):
            print("- Set up required API keys in .env file")
        if not results.get("Disk Space", True):
            print("- Free up disk space")
        if not results.get("Network", True):
            print("- Check network connectivity")
        if not results.get("Dependencies", True):
            print("- Install missing Python packages")

if __name__ == "__main__":
    main() 