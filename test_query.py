#!/usr/bin/env python3
"""
Test SQL queries using Supabase Transaction Pooler (PgBouncer)

This script tests the database connection and query execution through
Supabase's built-in Transaction Pooler at port 6543.

Connection Pattern:
1. Open short-lived connection
2. Set autocommit = True (required for PgBouncer)
3. Execute query
4. Close immediately
"""

import os
import time
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()

# Get Transaction Pooler URL (port 6543)
database_url = os.getenv("SQL_DATABASE_URL")

if not database_url:
    print("ERROR: SQL_DATABASE_URL not set in .env")
    print("Must point to Supabase Transaction Pooler (port 6543)")
    print("Example: postgresql://postgres.PROJECT:PASS@aws-0-REGION.pooler.supabase.com:6543/postgres")
    exit(1)

if ":6543" not in database_url:
    print("WARNING: SQL_DATABASE_URL does not contain port 6543")
    print("Transaction Pooler should use port 6543")
    print("Current URL:", database_url)
    print()

print("="*80)
print("TESTING SUPABASE TRANSACTION POOLER CONNECTION")
print("="*80)
print(f"Using: SQL_DATABASE_URL (Transaction Pooler)")
print(f"Port: {'6543 (Transaction Mode)' if ':6543' in database_url else 'Unknown - check your URL'}")

# Import the actual query
from sql_queries import get_search_vouchers_query

# Test with the same parameters as the tool call
company_id = os.getenv("COMPANY_ID")
division_id = os.getenv("DIVISION_ID")
party_name = "Maha Engineering"

print(f"\nQuery parameters:")
print(f"  Company ID: {company_id}")
print(f"  Division ID: {division_id}")
print(f"  Party Name: {party_name}")

# Get the query
query, params = get_search_vouchers_query(
    company_id=company_id,
    division_id=division_id,
    party_name=party_name
)

print(f"\nQuery length: {len(query)} characters")
print(f"Parameters: {params}")

# Connect and execute using Transaction Pooler pattern
conn = None
try:
    start_time = time.time()
    
    # STEP 1: Open short-lived connection to Transaction Pooler
    print("\n[1/4] Opening connection to Transaction Pooler...")
    conn = psycopg2.connect(database_url, connect_timeout=10)
    
    connect_time = time.time() - start_time
    print(f"[OK] Connection established in {connect_time:.2f}s")
    
    # STEP 2: Set autocommit (required for PgBouncer transaction mode)
    print("\n[2/4] Setting autocommit = True...")
    conn.autocommit = True
    print(f"[OK] Autocommit enabled")
    
    # STEP 3: Execute query
    print("\n[3/4] Executing query...")
    query_start = time.time()
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        result = cur.fetchone()
    
    query_time = time.time() - query_start
    total_time = time.time() - start_time
    
    print(f"[OK] Query executed in {query_time:.2f}s")
    print(f"[OK] Total time: {total_time:.2f}s")
    
    if result and 'result' in result:
        result_data = result['result']
        if isinstance(result_data, dict):
            insights = result_data.get('insights', {})
            records = result_data.get('records', [])
            
            print(f"\n[OK] Query successful!")
            print(f"  Total matches: {insights.get('total_matches', 0)}")
            print(f"  Records returned: {len(records) if records else 0}")
            
            if records:
                print(f"\n  First record:")
                print(f"    {records[0]}")
        else:
            print(f"\n[OK] Query returned: {type(result_data)}")
    else:
        print(f"\nSUCCESS: Query returned: {result}")
    
except psycopg2.OperationalError as e:
    error_msg = str(e)
    elapsed = time.time() - start_time
    print(f"\nERROR: Query failed after {elapsed:.2f}s")
    print(f"Error: {error_msg}")
    
    if "timeout" in error_msg.lower():
        print("\nDIAGNOSIS: Query execution timeout")
        print("The query itself is taking too long to execute.")
        print("Possible causes:")
        print("  1. Query is too complex")
        print("  2. Missing database indexes")
        print("  3. Large dataset being processed")
        print("  4. Database server is slow/overloaded")
        
except Exception as e:
    elapsed = time.time() - start_time
    print(f"\nERROR: Error after {elapsed:.2f}s: {e}")
    import traceback
    traceback.print_exc()

finally:
    # STEP 4: Always close connection immediately
    if conn:
        print("\n[4/4] Closing connection...")
        conn.close()
        print("[OK] Connection closed")

print("\n" + "="*80)

