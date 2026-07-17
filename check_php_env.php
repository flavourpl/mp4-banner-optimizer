#!/usr/bin/env python3
"""
Environment Check Script - Verify PHP Bridge prerequisites
"""

import subprocess
import sys
import os

def check_command(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1

print("🔍 Checking PHP Bridge prerequisites...")
print("=" * 60)

# 1. Check PHP availability
print("1. PHP Availability:")
php_version, code = check_command("php -v")
if code == 0:
    print(f"   ✅ PHP installed: {php_version.split()[1]}")
else:
    print(f"   ❌ PHP not found")

# 2. Check PHP modules
print("\n2. PHP Modules:")
modules = ["curl", "json", "mbstring"]
for module in modules:
    result, code = check_command(f"php -m | grep {module}")
    if code == 0:
        print(f"   ✅ {module}: available")
    else:
        print(f"   ⚠️  {module}: not found")

# 3. Check current Flask app
print("\n3. Flask App Status:")
result, code = check_command("ps aux | grep web_app_prod | grep -v grep")
if code == 0 or result:
    print(f"   ✅ Flask app running")
else:
    print(f"   ⚠️  Flask app not running")

# 4. Check Flask app accessibility
print("\n4. Flask App Local Access:")
result, code = check_command("curl -s http://127.0.0.1:5000/api/presets")
if code == 0 and result:
    print(f"   ✅ Flask app responding on 127.0.0.1:5000")
    print(f"   📦 Sample response: {result[:100]}...")
else:
    print(f"   ❌ Flask app not accessible on 127.0.0.1:5000")

# 5. Check port availability
print("\n5. Port Status:")
for port in [5000, 443, 444, 445]:
    result, code = check_command(f"netstat -tln | grep {port}")
    if code == 0:
        print(f"   📡 Port {port}: in use")
    else:
        print(f"   📭 Port {port}: available")

print("\n" + "=" * 60)
print("Architecture Verification:")
print("Browser → https://vid.flavour.pl → PHP → http://127.0.0.1:5000 → Flask")
print("")
print("✅ If all checks pass: PHP Bridge should work")
print("❌ If PHP missing: Need alternative solution")
print("⚠️  If 127.0.0.1:5000 not accessible: Need to fix Flask app")