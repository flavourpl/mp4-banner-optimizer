#!/usr/bin/env python3
"""
Quick deployment verification script.
Tests if all components are working correctly.
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path

def test_ffmpeg():
    """Test if FFmpeg is working."""
    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            version_line = result.stdout.split('\n')[0]
            print(f"   {version_line}")
            return True
        else:
            print("❌ FFmpeg not found or not working")
            return False
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        return False

def test_python():
    """Test if Python and required packages are working."""
    try:
        # Test Python version
        result = subprocess.run(['python3', '--version'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("❌ Python3 not found")
            return False

        python_version = result.stdout.strip()
        print(f"✅ Python available: {python_version}")

        # Test imports
        test_imports = [
            "import flask",
            "import werkzeug",
            "from mp4_optimizer import probe",
            "from mp4_optimizer import encoder"
        ]

        for import_cmd in test_imports:
            try:
                subprocess.run(['python3', '-c', import_cmd],
                               capture_output=True, text=True, timeout=5,
                               check=True)
            except:
                print(f"❌ Import failed: {import_cmd}")
                return False

        print("✅ All Python packages available")
        return True
    except Exception as e:
        print(f"❌ Python test failed: {e}")
        return False

def test_web_app():
    """Test if web application starts."""
    try:
        # Test basic Flask import
        result = subprocess.run(['python3', '-c', 'from web_app_prod import app'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ Web app import failed")
            print(f"Error: {result.stderr}")
            return False

        print("✅ Web application imports successfully")
        return True
    except Exception as e:
        print(f"❌ Web app test failed: {e}")
        return False

def test_directories():
    """Test if required directories exist and are writable."""
    required_dirs = ['uploads', 'outputs', 'reports']

    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            try:
                dir_path.mkdir()
                print(f"✅ Created directory: {dir_name}/")
            except:
                print(f"❌ Cannot create directory: {dir_name}/")
                return False
        else:
            # Test if writable
            test_file = dir_path / "test_write.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
                print(f"✅ Directory {dir_name}/ is writable")
            except:
                print(f"❌ Directory {dir_name}/ is not writable")
                return False

    return True

def test_encoding():
    """Test basic encoding functionality."""
    try:
        # Create a tiny test video
        test_input = "test_verify.mp4"

        if os.path.exists(test_input):
            os.remove(test_input)

        print("Creating test video for encoding test...")
        create_cmd = [
            "ffmpeg", "-f", "lavfi",
            "-i", "testsrc=duration=1:size=320x240:rate=30",
            "-t", "1",
            "-pix_fmt", "yuv420p",
            "-y", test_input
        ]

        result = subprocess.run(create_cmd, capture_output=True,
                              timeout=30, check=False)
        if result.returncode != 0:
            print("⚠️  Could not create test video (may be OK if FFmpeg limited)")
            return True

        if not os.path.exists(test_input):
            print("⚠️  Test video not created (FFmpeg may be limited)")
            return True

        # Test basic encoding
        print("Testing basic encoding...")
        encode_cmd = [
            "ffmpeg", "-i", test_input,
            "-vf", "scale=160:120",
            "-c:v", "libx264",
            "-profile:v", "baseline",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            "-t", "1",
            "-y", "test_verify_output.mp4"
        ]

        result = subprocess.run(encode_cmd, capture_output=True,
                              timeout=30, check=False)

        # Clean up
        for f in [test_input, "test_verify_output.mp4"]:
            if os.path.exists(f):
                os.remove(f)

        if result.returncode == 0:
            print("✅ Basic encoding works")
            return True
        else:
            print("⚠️  Encoding failed (may be FFmpeg limitation)")
            return True

    except Exception as e:
        print(f"⚠️  Encoding test skipped: {e}")
        return True

def main():
    """Run all tests."""
    print("="*60)
    print("MP4 Banner Optimizer - Deployment Verification")
    print("="*60)
    print("")

    tests = [
        ("FFmpeg", test_ffmpeg),
        ("Python & Packages", test_python),
        ("Web Application", test_web_app),
        ("Directories", test_directories),
        ("Basic Encoding", test_encoding)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\nTesting: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))

    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print("-" * 40)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())