#!/usr/bin/env python3
"""
Database Connection Test - Supabase Transaction Pooler

Simple script to test database connectivity via Supabase's Transaction Pooler.
Reports any connection issues with detailed error messages.
"""

import os
import sys
from dotenv import load_dotenv

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

# Load environment variables
load_dotenv()

print("\n" + "="*80)
print("DATABASE CONNECTION TEST - SUPABASE TRANSACTION POOLER")
print("="*80 + "\n")

# Check if SQL_DATABASE_URL is set
sql_database_url = os.getenv("SQL_DATABASE_URL")
if not sql_database_url:
    print(f"{RED}❌ ERROR: SQL_DATABASE_URL is not set{RESET}")
    print(f"\nAdd to your .env file:")
    print(f"SQL_DATABASE_URL=postgresql://postgres.PROJECT:PASS@aws-0-region.pooler.supabase.com:6543/postgres")
    print("\n" + "="*80 + "\n")
    sys.exit(1)

print(f"{GREEN}✓{RESET} SQL_DATABASE_URL found")

# Check port
if ":6543" in sql_database_url:
    print(f"{GREEN}✓{RESET} Port 6543 detected (Transaction Pooler)")
elif ":5432" in sql_database_url:
    print(f"{YELLOW}⚠{RESET}  Port 5432 detected - should use 6543 for Transaction Pooler")
else:
    print(f"{YELLOW}⚠{RESET}  Port not detected in URL")

print(f"\nTesting connection...")

# Test database connection
try:
    import psycopg2
    
    # Connect to database
    conn = psycopg2.connect(sql_database_url, connect_timeout=10)
    conn.autocommit = True
    
    # Test with simple query
    with conn.cursor() as cur:
        cur.execute("SELECT 1 as test")
        result = cur.fetchone()
        if result and result[0] == 1:
            print(f"{GREEN}✓{RESET} Connection successful")
            print(f"{GREEN}✓{RESET} Query execution successful")
        else:
            print(f"{RED}❌ ERROR: Unexpected query result{RESET}")
            conn.close()
            sys.exit(1)
    
    # Close connection
    conn.close()
    print(f"{GREEN}✓{RESET} Connection closed properly")
    
    print("\n" + "="*80)
    print(f"{GREEN}SUCCESS: Database connection is working!{RESET}")
    print("="*80 + "\n")
    sys.exit(0)
    
except ImportError:
    print(f"{RED}❌ ERROR: psycopg2 not installed{RESET}")
    print(f"\nInstall it with:")
    print(f"pip install psycopg2-binary")
    print("\n" + "="*80 + "\n")
    sys.exit(1)
    
except psycopg2.OperationalError as e:
    error_msg = str(e)
    print(f"{RED}❌ CONNECTION FAILED{RESET}")
    print(f"\nError: {error_msg}\n")
    
    # Provide specific guidance based on error
    if "password authentication failed" in error_msg:
        print("Issue: Password authentication failed")
        print("Solution: Check your password in SQL_DATABASE_URL")
    elif "timeout" in error_msg.lower():
        print("Issue: Connection timeout")
        print("Possible causes:")
        print("  - Network connectivity issues")
        print("  - Supabase project is paused")
        print("  - Incorrect URL")
        print("  - Firewall blocking port 6543")
    elif "could not connect" in error_msg.lower():
        print("Issue: Could not connect to server")
        print("Solution: Verify SQL_DATABASE_URL points to Transaction Pooler (port 6543)")
    else:
        print("Check your SQL_DATABASE_URL configuration")
    
    print("\n" + "="*80 + "\n")
    sys.exit(1)
    
except Exception as e:
    print(f"{RED}❌ UNEXPECTED ERROR{RESET}")
    print(f"\nError: {str(e)}")
    print(f"Type: {type(e).__name__}")
    print("\n" + "="*80 + "\n")
    sys.exit(1)

