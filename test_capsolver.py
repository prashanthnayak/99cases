#!/usr/bin/env python3
"""
Test CapSolver API Key and Balance
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY")

def check_balance():
    """Check CapSolver account balance"""
    print("🔍 Checking CapSolver API key and balance...")
    
    if not CAPSOLVER_API_KEY:
        print("❌ CAPSOLVER_API_KEY not found in .env file")
        return
    
    print(f"✅ API Key found: {CAPSOLVER_API_KEY[:15]}...")
    
    url = "https://api.capsolver.com/getBalance"
    payload = {
        "clientKey": CAPSOLVER_API_KEY
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        result = response.json()
        
        print(f"\n📊 CapSolver Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {result}")
        
        if result.get("errorId") == 0:
            balance = result.get("balance", 0)
            print(f"\n✅ API Key is valid!")
            print(f"💰 Account Balance: ${balance}")
            
            if balance <= 0:
                print("⚠️ WARNING: Your balance is $0. Please top up your account!")
                print("   Visit: https://dashboard.capsolver.com/dashboard/overview")
            else:
                print("✅ You have sufficient balance to solve CAPTCHAs")
        else:
            error_code = result.get("errorId")
            error_msg = result.get("errorDescription", "Unknown error")
            print(f"\n❌ Error {error_code}: {error_msg}")
            
            if error_code == 1:
                print("   This usually means invalid API key")
    
    except Exception as e:
        print(f"\n❌ Error connecting to CapSolver: {e}")

if __name__ == "__main__":
    check_balance()


