"""
ERP AI Assistant - Tools Module

This module contains all tool definitions and implementations for the agent.
All tools use direct database queries via Supabase Transaction Pooler.
"""

import json
import os
from typing import Optional, Dict, Any

# Load environment variables (in case this module is imported before load_dotenv is called)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, will rely on system environment variables

# Import SQL queries for rapid prototyping mode
try:
    from sql_queries import (
        get_search_vouchers_query, 
        get_search_ledgers_query,
        get_list_master_query,
        get_search_stockitem_query,
        get_search_godown_query
    )
    SQL_QUERIES_AVAILABLE = True
except ImportError:
    SQL_QUERIES_AVAILABLE = False

# Try to import psycopg2 for direct SQL execution
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


# Tool functions will receive these from agent.py
COMPANY_ID: str = None
DIVISION_ID: str = None

# Store voucher records for UI display (keyed by a unique identifier)
_voucher_records_cache: Dict[str, Any] = {}

def check_database_connection() -> tuple:
    """
    Check if database connection is working.
    Returns (success: bool, error_message: str)
    
    This function tests connectivity to Supabase's Transaction Pooler (PgBouncer).
    """
    if not PSYCOPG2_AVAILABLE:
        return False, "psycopg2-binary is not installed. Run: pip install psycopg2-binary"
    
    # Get SQL_DATABASE_URL (must point to Transaction Pooler at port 6543)
    database_url = os.getenv("SQL_DATABASE_URL")
    if not database_url:
        return False, (
            "SQL_DATABASE_URL not set in .env file.\n"
            "Must point to Supabase Transaction Pooler (port 6543).\n"
            "Format: postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres\n"
            "Example: postgresql://postgres.ppfwlhfehwelinfprviw:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres\n"
            "\n"
            "Note: Port 6543 is required for Transaction Pooler mode."
        )
    
    # Validate that URL contains port 6543 (Transaction Pooler)
    if ":6543/" not in database_url and not database_url.endswith(":6543"):
        return False, (
            "SQL_DATABASE_URL must use port 6543 (Supabase Transaction Pooler).\n"
            "Current URL does not contain :6543\n"
            "\n"
            "Update your .env file to use the Transaction Pooler connection string.\n"
            "You can find this in Supabase Dashboard → Project Settings → Database → Connection Pooling"
        )
    
    # Test connection using Transaction Pooler
    try:
        # Open short-lived connection
        conn = psycopg2.connect(database_url, connect_timeout=5)
        
        # Set autocommit for PgBouncer transaction mode
        conn.autocommit = True
        
        # Test with simple query
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        
        # Close immediately
        conn.close()
        
        return True, ""
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "password authentication failed" in error_msg:
            return False, "Database password authentication failed. Check your password in SQL_DATABASE_URL"
        elif "timeout" in error_msg.lower() or "timeout expired" in error_msg.lower():
            return False, (
                "Database connection timeout\n"
                "Possible causes:\n"
                "  1. Network connectivity issues\n"
                "  2. Incorrect SQL_DATABASE_URL\n"
                "  3. Supabase project is paused\n"
                "  4. Firewall blocking port 6543"
            )
        elif "connection refused" in error_msg.lower() or "could not connect" in error_msg.lower():
            return False, (
                "Could not connect to database\n"
                "Make sure you're using the Transaction Pooler connection string (port 6543) from Supabase Dashboard"
            )
        else:
            return False, f"Database connection error: {error_msg}"
    except Exception as e:
        return False, f"Database connection failed: {str(e)}"


def initialize_tools(company_id: str, division_id: str):
    """
    Initialize the tools module with tenant context.
    Must be called before using any tools.
    
    Validates database connection before proceeding.
    """
    global COMPANY_ID, DIVISION_ID
    COMPANY_ID = company_id
    DIVISION_ID = division_id
    
    # Print initialization information
    print("\n" + "="*80)
    print(f"TOOLS INITIALIZATION")
    print("="*80)
    print(f"Company ID: {company_id}")
    print(f"Division ID: {division_id}")
    print("="*80 + "\n")
    
    # Check database connection
    success, error_msg = check_database_connection()
    if not success:
        print("\n" + "="*80)
        print("ERROR: DATABASE CONNECTION FAILED")
        print("="*80)
        print(error_msg)
        print("\n" + "="*80)
        print("To fix:")
        print("  Update SQL_DATABASE_URL in .env to use Transaction Pooler (port 6543)")
        print("  Example: postgresql://postgres.PROJECT:PASS@aws-0-REGION.pooler.supabase.com:6543/postgres")
        print("="*80 + "\n")
        raise ConnectionError("Database connection failed. Cannot start server.")


def execute_sql_query(query: str, params: dict) -> dict:
    """
    Execute SQL query using Supabase Transaction Pooler (PgBouncer).
    
    Connection Pattern:
    1. Open short-lived connection from SQL_DATABASE_URL
    2. Set autocommit = True (required for PgBouncer transaction mode)
    3. Execute single query/transaction
    4. Close connection immediately
    
    This pattern allows PgBouncer to efficiently pool connections and scale
    to 100+ concurrent users without connection exhaustion.
    
    Args:
        query: SQL query string with %(param_name)s placeholders
        params: Dictionary of parameters for the query
    
    Returns:
        Dictionary containing the query result
    
    Raises:
        ImportError: If psycopg2 is not installed
        ValueError: If SQL_DATABASE_URL is not set
        ConnectionError: If connection fails
        Exception: If query execution fails
    """
    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2-binary is required. Install: pip install psycopg2-binary")
    
    # Get Transaction Pooler URL (port 6543)
    database_url = os.getenv("SQL_DATABASE_URL")
    if not database_url:
        raise ValueError(
            "SQL_DATABASE_URL not set in .env\n"
            "Must point to Supabase Transaction Pooler (port 6543)"
        )
    
    conn = None
    try:
        # STEP 1: Open short-lived connection to Transaction Pooler
        conn = psycopg2.connect(
            database_url,
            connect_timeout=10  # 10 second timeout for pooler
        )
        
        # STEP 2: Set autocommit (required for PgBouncer transaction mode)
        conn.autocommit = True
        
        # STEP 3: Execute single transaction/query
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            result = cur.fetchone()
            
            if result and 'result' in result:
                return result['result']
            elif result:
                return dict(result)
            else:
                return {}
                
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower() or "timeout expired" in error_msg.lower():
            raise ConnectionError(
                "Database connection timeout. The query took too long to execute.\n"
                "This usually indicates:\n"
                "  1. Complex query that needs optimization\n"
                "  2. Missing database indexes\n"
                "  3. Network issues\n"
                "  4. Database overload"
            )
        else:
            raise ConnectionError(f"Database connection error: {error_msg}")
    except psycopg2.Error as e:
        raise Exception(f"Database query failed: {str(e)}")
    finally:
        # STEP 4: Always close connection immediately
        if conn:
            conn.close()


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

def list_master_tool(collection: str) -> str:
    """
    Retrieve master data from the ERP system.
    
    Args:
        collection: The type of master data to retrieve. Must be one of:
            Group, Ledger, VoucherType, Unit, Godown, StockGroup, StockItem,
            CostCentre, CostCategory, AttendanceType, Company, Currency, GSTIN,
            GSTClassification
    
    Returns:
        JSON string containing the list of master records
    """
    # Print tool call arguments (what LLM requested)
    args_dict = {"collection": collection}
    print(f"TOOL: list_master | Args: {json.dumps(args_dict, indent=2)}")
    
    try:
        # Collections supported via SQL queries
        sql_collections = ['group', 'vouchertype', 'unit', 'godown', 'stockgroup']
        v_collection = collection.strip().lower() if collection else ''
        
        if v_collection in sql_collections:
            if not SQL_QUERIES_AVAILABLE:
                raise ImportError("sql_queries module not found. Make sure sql_queries.py exists.")
            
            # Get SQL query and parameters
            query, sql_params = get_list_master_query(
                company_id=COMPANY_ID,
                division_id=DIVISION_ID,
                collection=collection
            )
            
            # Execute SQL query
            result_data = execute_sql_query(query, sql_params)
            
            # Result from SQL is a JSONB array
            if isinstance(result_data, str):
                result_data = json.loads(result_data)
            elif hasattr(result_data, '__iter__') and not isinstance(result_data, dict):
                # If it's already a list, use it directly
                pass
            else:
                # Try to extract result from dict if needed
                if isinstance(result_data, dict) and 'result' in result_data:
                    result_data = result_data['result']
            
            # Check for empty results
            if not result_data or (isinstance(result_data, list) and len(result_data) == 0):
                print(f"WARNING: list_master returned empty results for collection: {collection}")
                return json.dumps([])
            
            return json.dumps(result_data, indent=2)
        else:
            # Unsupported collection
            error_msg = f"Collection '{collection}' is not supported. Supported collections: {', '.join(sql_collections)}"
            print(f"WARNING: {error_msg}")
            return json.dumps({
                "error": "Unsupported collection",
                "message": error_msg,
                "supported_collections": sql_collections
            })
    
    except Exception as e:
        error_msg = f"Failed to retrieve data: {str(e)}"
        print(f"ERROR: list_master failed - {error_msg}")
        return json.dumps({"error": error_msg})


def search_vouchers_tool(
    voucher_type: Optional[str] = None,
    voucher_number: Optional[str] = None,
    reference: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    party_name: Optional[str] = None
) -> str:
    """
    Search for vouchers/transactions in the ERP system with various filters.
    
    Args:
        voucher_type: Filter by voucher type (e.g., 'Sales', 'Purchase', 'Payment')
        voucher_number: Filter by voucher number
        reference: Filter by reference number
        date_from: Start date filter (YYYY-MM-DD format)
        date_to: End date filter (YYYY-MM-DD format)
        min_amount: Minimum voucher amount
        max_amount: Maximum voucher amount
        party_name: Filter by party/customer/vendor name (supports partial matching)
    
    Returns:
        JSON string containing only insights (for LLM consumption)
        Records with actions are stored in _voucher_records_cache for UI display
    """
    import time
    import hashlib
    
    # Print tool call arguments (what LLM requested)
    args_dict = {
        "voucher_type": voucher_type,
        "voucher_number": voucher_number,
        "reference": reference,
        "date_from": date_from,
        "date_to": date_to,
        "min_amount": min_amount,
        "max_amount": max_amount,
        "party_name": party_name
    }
    # Remove None values for cleaner output
    args_dict = {k: v for k, v in args_dict.items() if v is not None}
    print(f"TOOL: search_vouchers | Args: {json.dumps(args_dict, indent=2)}")
    
    try:
        if not SQL_QUERIES_AVAILABLE:
            raise ImportError("sql_queries module not found. Make sure sql_queries.py exists.")
        
        # Get SQL query and parameters
        query, sql_params = get_search_vouchers_query(
            company_id=COMPANY_ID,
            division_id=DIVISION_ID,
            voucher_type=voucher_type,
            voucher_number=voucher_number,
            reference=reference,
            date_from=date_from,
            date_to=date_to,
            min_amount=min_amount,
            max_amount=max_amount,
            party_name=party_name
        )
        
        # Execute SQL query
        result_data = execute_sql_query(query, sql_params)
        
        # Result from SQL is already a dict with the expected structure
        if not isinstance(result_data, dict):
            result_data = json.loads(result_data) if isinstance(result_data, str) else {}
        
        # Parse the result to check for errors
        if result_data and isinstance(result_data, dict):
            if result_data.get('error'):
                error_msg = result_data.get('message', result_data.get('error'))
                print(f"ERROR: search_vouchers failed - {error_msg}")
                # Return error to LLM
                return json.dumps({"error": result_data.get('error'), "message": error_msg})
            
            # Extract insights and records from the response format
            insights = result_data.get('insights', {})
            records = result_data.get('records', [])
            
            # Check for empty results
            total_matches = insights.get('total_matches', 0)
            if total_matches == 0 or not records:
                print(f"WARNING: search_vouchers returned no results")
            
            # Add actions column to each record
            records_with_actions = []
            for record in records:
                record_copy = record.copy()
                record_copy['actions'] = {
                    'view_voucher': f"https://vyaapari360.com/vouchers/{record.get('id')}"
                }
                records_with_actions.append(record_copy)
            
            # Generate a unique cache key for this search
            cache_params = {
                'company_id': COMPANY_ID,
                'division_id': DIVISION_ID,
                'voucher_type': voucher_type,
                'voucher_number': voucher_number,
                'reference': reference,
                'date_from': date_from,
                'date_to': date_to,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'party_name': party_name
            }
            cache_key = hashlib.md5(
                json.dumps(cache_params, sort_keys=True).encode()
            ).hexdigest()
            
            # Store records with actions for UI display
            global _voucher_records_cache
            _voucher_records_cache[cache_key] = {
                'records': records_with_actions,
                'total_count': total_matches,
                'timestamp': time.time()
            }
            
            # Return ONLY insights to LLM (no records, no IDs, no debit/credit values, no URLs)
            llm_response = {
                "insights": insights
            }
            
            return json.dumps(llm_response, indent=2)
        else:
            print(f"WARNING: search_vouchers returned empty or invalid result")
            return json.dumps({"insights": {}})
    
    except Exception as e:
        error_msg = f"Failed to search vouchers: {str(e)}"
        print(f"ERROR: search_vouchers failed - {error_msg}")
        return json.dumps({"error": error_msg})


def search_ledgers_tool(
    ledger_name: Optional[str] = None,
    group_name: Optional[str] = None,
    gstin: Optional[str] = None,
    min_opening_balance: Optional[float] = None,
    max_opening_balance: Optional[float] = None,
    min_closing_balance: Optional[float] = None,
    max_closing_balance: Optional[float] = None
) -> str:
    """
    Search for ledgers in the ERP system with various filters.
    
    Args:
        ledger_name: Filter by ledger name (supports partial matching)
        group_name: Filter by group name (supports partial matching)
        gstin: Filter by GSTIN (supports partial matching)
        min_opening_balance: Minimum opening balance
        max_opening_balance: Maximum opening balance
        min_closing_balance: Minimum closing balance
        max_closing_balance: Maximum closing balance
    
    Returns:
        JSON string containing only insights (for LLM consumption)
        Records are stored in _ledger_records_cache for UI display
    """
    import time
    import hashlib
    
    # Print tool call arguments
    args_dict = {
        "ledger_name": ledger_name,
        "group_name": group_name,
        "gstin": gstin,
        "min_opening_balance": min_opening_balance,
        "max_opening_balance": max_opening_balance,
        "min_closing_balance": min_closing_balance,
        "max_closing_balance": max_closing_balance
    }
    args_dict = {k: v for k, v in args_dict.items() if v is not None}
    print(f"TOOL: search_ledgers | Args: {json.dumps(args_dict, indent=2)}")
    
    try:
        if not SQL_QUERIES_AVAILABLE:
            raise ImportError("sql_queries module not found. Make sure sql_queries.py exists.")
        
        # Get SQL query and parameters
        query, sql_params = get_search_ledgers_query(
            company_id=COMPANY_ID,
            division_id=DIVISION_ID,
            ledger_name=ledger_name,
            group_name=group_name,
            gstin=gstin,
            min_opening_balance=min_opening_balance,
            max_opening_balance=max_opening_balance,
            min_closing_balance=min_closing_balance,
            max_closing_balance=max_closing_balance
        )
        
        # Execute SQL query
        result_data = execute_sql_query(query, sql_params)
        
        if not isinstance(result_data, dict):
            result_data = json.loads(result_data) if isinstance(result_data, str) else {}
        
        # Parse the result
        if result_data and isinstance(result_data, dict):
            if result_data.get('error'):
                error_msg = result_data.get('message', result_data.get('error'))
                print(f"ERROR: search_ledgers failed - {error_msg}")
                return json.dumps({"error": result_data.get('error'), "message": error_msg})
            
            insights = result_data.get('insights', {})
            records = result_data.get('records', [])
            
            total_matches = insights.get('total_matches', 0)
            if total_matches == 0 or not records:
                print(f"WARNING: search_ledgers returned no results")
            
            # Generate cache key
            cache_params = {
                'company_id': COMPANY_ID,
                'division_id': DIVISION_ID,
                'ledger_name': ledger_name,
                'group_name': group_name,
                'gstin': gstin,
                'min_opening_balance': min_opening_balance,
                'max_opening_balance': max_opening_balance,
                'min_closing_balance': min_closing_balance,
                'max_closing_balance': max_closing_balance
            }
            cache_key = hashlib.md5(
                json.dumps(cache_params, sort_keys=True).encode()
            ).hexdigest()
            
            # Add actions (view_url) to each record for UI display
            records_with_actions = []
            for record in records:
                record_copy = record.copy()
                record_copy['actions'] = {
                    'view_ledger': f"https://vyaapari360.com/ledgers/{record.get('id')}"
                }
                records_with_actions.append(record_copy)
            
            # Store records for UI display (using voucher cache for now, could create separate)
            global _voucher_records_cache
            _voucher_records_cache[f"ledgers_{cache_key}"] = {
                'records': records_with_actions,
                'total_count': total_matches,
                'timestamp': time.time(),
                'type': 'ledgers'
            }
            
            # Return ONLY insights to LLM
            llm_response = {
                "insights": insights
            }
            
            return json.dumps(llm_response, indent=2)
        else:
            print(f"WARNING: search_ledgers returned empty or invalid result")
            return json.dumps({"insights": {}})
    
    except Exception as e:
        error_msg = f"Failed to search ledgers: {str(e)}"
        print(f"ERROR: search_ledgers failed - {error_msg}")
        return json.dumps({"error": error_msg})


def search_stockitem_tool(
    item_name: Optional[str] = None,
    item_code: Optional[str] = None,
    stock_group: Optional[str] = None,
    gst_hsn_code: Optional[str] = None
) -> str:
    """
    Search for stock items in the ERP system with various filters.
    
    Args:
        item_name: Filter by item name (supports partial matching)
        item_code: Filter by item code (supports partial matching)
        stock_group: Filter by stock group name (supports partial matching)
        gst_hsn_code: Filter by GST HSN code (supports partial matching)
    
    Returns:
        JSON string containing only insights (for LLM consumption)
        Records are stored in cache for UI display
    """
    import time
    import hashlib
    
    # Print tool call arguments
    args_dict = {
        "item_name": item_name,
        "item_code": item_code,
        "stock_group": stock_group,
        "gst_hsn_code": gst_hsn_code
    }
    args_dict = {k: v for k, v in args_dict.items() if v is not None}
    print(f"TOOL: search_stockitem | Args: {json.dumps(args_dict, indent=2)}")
    
    try:
        if not SQL_QUERIES_AVAILABLE:
            raise ImportError("sql_queries module not found. Make sure sql_queries.py exists.")
        
        # Get SQL query and parameters
        query, sql_params = get_search_stockitem_query(
            company_id=COMPANY_ID,
            division_id=DIVISION_ID,
            item_name=item_name,
            item_code=item_code,
            stock_group=stock_group,
            gst_hsn_code=gst_hsn_code
        )
        
        # Execute SQL query
        result_data = execute_sql_query(query, sql_params)
        
        if not isinstance(result_data, dict):
            result_data = json.loads(result_data) if isinstance(result_data, str) else {}
        
        # Parse the result
        if result_data and isinstance(result_data, dict):
            if result_data.get('error'):
                error_msg = result_data.get('message', result_data.get('error'))
                print(f"ERROR: search_stockitem failed - {error_msg}")
                return json.dumps({"error": result_data.get('error'), "message": error_msg})
            
            insights = result_data.get('insights', {})
            records = result_data.get('records', [])
            
            total_matches = insights.get('total_matches', 0)
            if total_matches == 0 or not records:
                print(f"WARNING: search_stockitem returned no results")
            
            # Generate cache key
            cache_params = {
                'company_id': COMPANY_ID,
                'division_id': DIVISION_ID,
                'item_name': item_name,
                'item_code': item_code,
                'stock_group': stock_group,
                'gst_hsn_code': gst_hsn_code
            }
            cache_key = hashlib.md5(
                json.dumps(cache_params, sort_keys=True).encode()
            ).hexdigest()
            
            # Add actions to each record for UI display
            records_with_actions = []
            for record in records:
                record_copy = record.copy()
                record_copy['actions'] = {
                    'view_stockitem': f"https://vyaapari360.com/stockitems/{record.get('id')}"
                }
                records_with_actions.append(record_copy)
            
            # Store records for UI display
            global _voucher_records_cache
            _voucher_records_cache[f"stockitems_{cache_key}"] = {
                'records': records_with_actions,
                'total_count': total_matches,
                'timestamp': time.time(),
                'type': 'stockitems'
            }
            
            # Return ONLY insights to LLM
            llm_response = {
                "insights": insights
            }
            
            return json.dumps(llm_response, indent=2)
        else:
            print(f"WARNING: search_stockitem returned empty or invalid result")
            return json.dumps({"insights": {}})
    
    except Exception as e:
        error_msg = f"Failed to search stock items: {str(e)}"
        print(f"ERROR: search_stockitem failed - {error_msg}")
        return json.dumps({"error": error_msg})


def search_godown_tool(
    godown_name: Optional[str] = None,
    godown_code: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """
    Search for godowns (warehouses) in the ERP system with various filters.
    
    Args:
        godown_name: Filter by godown name (supports partial matching)
        godown_code: Filter by godown code (supports partial matching)
        location: Filter by location/address (supports partial matching)
    
    Returns:
        JSON string containing only insights (for LLM consumption)
        Records are stored in cache for UI display
    """
    import time
    import hashlib
    
    # Print tool call arguments
    args_dict = {
        "godown_name": godown_name,
        "godown_code": godown_code,
        "location": location
    }
    args_dict = {k: v for k, v in args_dict.items() if v is not None}
    print(f"TOOL: search_godown | Args: {json.dumps(args_dict, indent=2)}")
    
    try:
        if not SQL_QUERIES_AVAILABLE:
            raise ImportError("sql_queries module not found. Make sure sql_queries.py exists.")
        
        # Get SQL query and parameters
        query, sql_params = get_search_godown_query(
            company_id=COMPANY_ID,
            division_id=DIVISION_ID,
            godown_name=godown_name,
            godown_code=godown_code,
            location=location
        )
        
        # Execute SQL query
        result_data = execute_sql_query(query, sql_params)
        
        if not isinstance(result_data, dict):
            result_data = json.loads(result_data) if isinstance(result_data, str) else {}
        
        # Parse the result
        if result_data and isinstance(result_data, dict):
            if result_data.get('error'):
                error_msg = result_data.get('message', result_data.get('error'))
                print(f"ERROR: search_godown failed - {error_msg}")
                return json.dumps({"error": result_data.get('error'), "message": error_msg})
            
            insights = result_data.get('insights', {})
            records = result_data.get('records', [])
            
            total_matches = insights.get('total_matches', 0)
            if total_matches == 0 or not records:
                print(f"WARNING: search_godown returned no results")
            
            # Generate cache key
            cache_params = {
                'company_id': COMPANY_ID,
                'division_id': DIVISION_ID,
                'godown_name': godown_name,
                'godown_code': godown_code,
                'location': location
            }
            cache_key = hashlib.md5(
                json.dumps(cache_params, sort_keys=True).encode()
            ).hexdigest()
            
            # Add actions to each record for UI display
            records_with_actions = []
            for record in records:
                record_copy = record.copy()
                record_copy['actions'] = {
                    'view_godown': f"https://vyaapari360.com/godowns/{record.get('id')}"
                }
                records_with_actions.append(record_copy)
            
            # Store records for UI display
            global _voucher_records_cache
            _voucher_records_cache[f"godowns_{cache_key}"] = {
                'records': records_with_actions,
                'total_count': total_matches,
                'timestamp': time.time(),
                'type': 'godowns'
            }
            
            # Return ONLY insights to LLM
            llm_response = {
                "insights": insights
            }
            
            return json.dumps(llm_response, indent=2)
        else:
            print(f"WARNING: search_godown returned empty or invalid result")
            return json.dumps({"insights": {}})
    
    except Exception as e:
        error_msg = f"Failed to search godowns: {str(e)}"
        print(f"ERROR: search_godown failed - {error_msg}")
        return json.dumps({"error": error_msg})


def get_voucher_records_for_display(cache_key: str = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve stored voucher records for UI display.
    If cache_key is None, returns the most recent search results.
    
    Args:
        cache_key: Optional cache key to retrieve specific search results
    
    Returns:
        Dictionary with records and metadata, or None if not found
    """
    global _voucher_records_cache
    
    if cache_key:
        return _voucher_records_cache.get(cache_key)
    
    # Return most recent entry
    if _voucher_records_cache:
        most_recent = max(_voucher_records_cache.items(), key=lambda x: x[1].get('timestamp', 0))
        return most_recent[1]
    
    return None


# ============================================================================
# TOOL DEFINITIONS FOR OPENAI
# ============================================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "list_master",
            "description": """Retrieve master data from the ERP system. This function returns lists of business entities 
            such as ledgers, stock items, voucher types, etc. The data is automatically filtered to the current 
            company and division context. Use this when the user asks about available options, lists, or master data.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "collection": {
                        "type": "string",
                        "enum": [
                            "Group", "Ledger", "VoucherType", "Unit", "Godown",
                            "StockGroup", "StockItem", "CostCentre", "CostCategory",
                            "AttendanceType", "Company", "Currency", "GSTIN",
                            "GSTClassification"
                        ],
                        "description": "The type of master data to retrieve"
                    }
                },
                "required": ["collection"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_vouchers",
            "description": """Search for vouchers and transactions in the ERP system. Use this when users ask about:
            - Specific transactions, invoices, bills, payments, receipts
            - Transactions for a specific party/customer/vendor
            - Transactions in a date range
            - Transactions of a specific type (Sales, Purchase, Payment, etc.)
            - Transactions within an amount range
            - Finding vouchers by number or reference
            
            Returns business insights including: total vouchers and amount, highest value voucher details,
            most common voucher type, most frequent party, top parties by value, date range, and 
            comprehensive summary by voucher type (Sales/Purchase/Payment totals).""",
            "parameters": {
                "type": "object",
                "properties": {
                    "voucher_type": {
                        "type": "string",
                        "description": "Filter by voucher type (e.g., 'Sales', 'Purchase', 'Payment', 'Receipt', 'Journal'). Case-insensitive, supports partial matching."
                    },
                    "voucher_number": {
                        "type": "string",
                        "description": "Filter by voucher number. Supports partial matching."
                    },
                    "reference": {
                        "type": "string",
                        "description": "Filter by reference number or PO number. Supports partial matching."
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date for filtering (format: YYYY-MM-DD). Returns vouchers from this date onwards."
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date for filtering (format: YYYY-MM-DD). Returns vouchers up to this date."
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "Minimum voucher amount. Returns vouchers with amount >= this value."
                    },
                    "max_amount": {
                        "type": "number",
                        "description": "Maximum voucher amount. Returns vouchers with amount <= this value."
                    },
                    "party_name": {
                        "type": "string",
                        "description": "Filter by party/customer/vendor name. Supports fuzzy matching and partial names (e.g., 'ABC' will match 'ABC Corporation')."
                    },
                },
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_ledgers",
            "description": """Search for ledgers (accounts) in the ERP system. Use this when users ask about:
            - Finding specific ledgers or accounts
            - Ledgers in a specific group
            - Ledgers with specific balance ranges
            - Ledgers by GSTIN
            - Account balances and financial information
            - Outstanding receivables and payables
            - Party dues and credit analysis
            
            Returns business insights including: total ledgers, total receivables and payables,
            net outstanding, largest opening/closing balances, top parties with dues, and 
            group-wise summary (especially Sundry Debtors vs Creditors).""",
            "parameters": {
                "type": "object",
                "properties": {
                    "ledger_name": {
                        "type": "string",
                        "description": "Filter by ledger name. Supports partial matching (e.g., 'Cash' will match 'Cash Account')."
                    },
                    "group_name": {
                        "type": "string",
                        "description": "Filter by group name. Supports partial matching (e.g., 'Assets' will match 'Current Assets')."
                    },
                    "gstin": {
                        "type": "string",
                        "description": "Filter by GSTIN (GST Identification Number). Supports partial matching."
                    },
                    "min_opening_balance": {
                        "type": "number",
                        "description": "Minimum opening balance. Returns ledgers with opening balance >= this value."
                    },
                    "max_opening_balance": {
                        "type": "number",
                        "description": "Maximum opening balance. Returns ledgers with opening balance <= this value."
                    },
                    "min_closing_balance": {
                        "type": "number",
                        "description": "Minimum closing balance. Returns ledgers with closing balance >= this value."
                    },
                    "max_closing_balance": {
                        "type": "number",
                        "description": "Maximum closing balance. Returns ledgers with closing balance <= this value."
                    },
                },
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_stockitem",
            "description": """Search for stock items in the ERP system. Use this when users ask about:
            - Finding specific stock items or products
            - Stock items in a specific stock group
            - Stock items by HSN code
            - Product inventory and stock information
            - Items by name or code
            - Stock valuation and inventory worth
            - Items with low stock or missing GST details
            
            Returns business insights about stock items including valuation, highest value items, 
            stock by group, GST compliance, and low stock alerts.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "Filter by item name. Supports partial matching (e.g., 'Widget' will match 'Widget A')."
                    },
                    "item_code": {
                        "type": "string",
                        "description": "Filter by item code. Supports partial matching."
                    },
                    "stock_group": {
                        "type": "string",
                        "description": "Filter by stock group name. Supports partial matching (e.g., 'Electronics' will match 'Electronics - Components')."
                    },
                    "gst_hsn_code": {
                        "type": "string",
                        "description": "Filter by GST HSN code. Supports partial matching."
                    },
                },
                "required": [],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_godown",
            "description": """Search for godowns (warehouses) in the ERP system. Use this when users ask about:
            - Finding specific godowns or warehouses
            - Godowns by location or address
            - Warehouse capacity and details
            - Storage locations and facility information
            
            Returns business insights including: total warehouses, total storage capacity, 
            largest warehouse details, location-wise distribution, and warehouses missing 
            contact information.""",
            "parameters": {
                "type": "object",
                "properties": {
                    "godown_name": {
                        "type": "string",
                        "description": "Filter by godown name. Supports partial matching (e.g., 'Main' will match 'Main Warehouse')."
                    },
                    "godown_code": {
                        "type": "string",
                        "description": "Filter by godown code. Supports partial matching."
                    },
                    "location": {
                        "type": "string",
                        "description": "Filter by location or address. Supports partial matching (e.g., 'Mumbai' will match godowns in Mumbai)."
                    },
                },
                "required": [],
                "additionalProperties": False
            }
        }
    }
]


# ============================================================================
# FUNCTION REGISTRY
# ============================================================================

# Map function names to actual Python functions
available_functions = {
    "list_master": list_master_tool,
    "search_vouchers": search_vouchers_tool,
    "search_ledgers": search_ledgers_tool,
    "search_stockitem": search_stockitem_tool,
    "search_godown": search_godown_tool
}

