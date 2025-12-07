"""
SQL Query Templates for Rapid Prototyping

These queries can be executed directly during development.
Once finalized, they can be converted to RPC functions in Supabase.

This allows for rapid iteration without needing to update database functions.
"""

from typing import Tuple, Dict, Optional


def get_search_vouchers_query(
    company_id: str,
    division_id: str,
    voucher_type: Optional[str] = None,
    voucher_number: Optional[str] = None,
    reference: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    party_name: Optional[str] = None
) -> Tuple[str, Dict]:
    """
    Returns the SQL query and parameters for searching vouchers.
    This matches the RPC function logic but can be executed directly.
    
    Returns:
        tuple: (query_string, parameters_dict)
    """
    # Build WHERE clause filters dynamically
    filters = [
        "v.company_id = %(company_id)s",
        "v.division_id = %(division_id)s"
    ]
    
    params = {
        'company_id': company_id,
        'division_id': division_id
    }
    
    # Add optional filters
    if voucher_type:
        filters.append("v.voucher_type ILIKE %(voucher_type)s")
        params['voucher_type'] = f'%{voucher_type}%'
    
    if voucher_number:
        filters.append("v.voucher_number ILIKE %(voucher_number)s")
        params['voucher_number'] = f'%{voucher_number}%'
    
    if reference:
        filters.append("v.reference ILIKE %(reference)s")
        params['reference'] = f'%{reference}%'
    
    if date_from:
        filters.append("COALESCE(v.voucher_date, v.date) >= %(date_from)s")
        params['date_from'] = date_from
    
    if date_to:
        filters.append("COALESCE(v.voucher_date, v.date) <= %(date_to)s")
        params['date_to'] = date_to
    
    if min_amount is not None:
        filters.append("v.total_debit >= %(min_amount)s")
        params['min_amount'] = min_amount
    
    if max_amount is not None:
        filters.append("v.total_debit <= %(max_amount)s")
        params['max_amount'] = max_amount
    
    # Always set party search params for ORDER BY clause (even if None)
    # This allows us to sort by relevance when party_name is provided
    if party_name:
        # Support fuzzy matching with pg_trgm if available
        filters.append("""
            (v.party_ledger_name ILIKE %(party_name)s
             OR v.party_ledger_name ILIKE %(party_name_prefix)s
             OR v.party_ledger_name ILIKE %(party_name_wildcard)s
             OR (EXISTS (SELECT 1 FROM pg_extension WHERE extname='pg_trgm') 
                 AND similarity(v.party_ledger_name, %(party_name_exact)s) > 0.55))
        """)
        params['party_name'] = party_name
        params['party_name_prefix'] = f'{party_name}%'
        params['party_name_wildcard'] = f'%{party_name}%'
        params['party_name_exact'] = party_name
    else:
        # Set to None for ORDER BY clause to work
        params['party_name'] = None
        params['party_name_prefix'] = None
        params['party_name_wildcard'] = None
        params['party_name_exact'] = None
    
    where_clause = " AND ".join(filters)
    
    query = f"""
    WITH base AS (
        SELECT
            v.id,
            v.voucher_number,
            v.voucher_type,
            COALESCE(v.voucher_date, v.date) AS voucher_date,
            v.party_ledger_name,
            v.is_balanced,
            v.balance_difference,
            v.reference,
            -- Calculate TOTAL DEBIT from voucher entries ONLY
            COALESCE(
                (SELECT SUM(tve.debit_amount) 
                 FROM public.tally_voucher_entries tve 
                 WHERE tve.voucher_id = v.id),
                0
            ) AS total_debit,
            -- Calculate TOTAL CREDIT from voucher entries ONLY
            COALESCE(
                (SELECT SUM(tve.credit_amount) 
                 FROM public.tally_voucher_entries tve 
                 WHERE tve.voucher_id = v.id),
                0
            ) AS total_credit
        FROM public.tally_vouchers v
        WHERE {where_clause}
    ),
    aggregates AS (
        SELECT
            COUNT(*)::bigint AS total_count,
            COALESCE(SUM(total_debit), 0) AS total_amount,
            MIN(voucher_date) AS earliest_date,
            MAX(voucher_date) AS latest_date
        FROM base
    ),
    -- Find highest value voucher with all details
    highest_voucher AS (
        SELECT 
            voucher_number,
            party_ledger_name,
            total_debit,
            to_char(voucher_date, 'DD Mon YYYY') AS date,
            voucher_type
        FROM base
        ORDER BY total_debit DESC NULLS LAST
        LIMIT 1
    ),
    -- Most common voucher type
    most_common_type AS (
        SELECT
            voucher_type,
            COUNT(*) AS count
        FROM base
        GROUP BY voucher_type
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ),
    -- Most common party
    most_common_party AS (
        SELECT
            COALESCE(party_ledger_name, 'UNKNOWN') AS party_name,
            COUNT(*) AS transaction_count
        FROM base
        WHERE party_ledger_name IS NOT NULL AND party_ledger_name != ''
        GROUP BY party_ledger_name
        ORDER BY COUNT(*) DESC
        LIMIT 1
    ),
    -- Top 3 parties by value
    top_parties AS (
        SELECT
            COALESCE(party_ledger_name, 'UNKNOWN') AS party_name,
            COALESCE(SUM(total_debit), 0) AS total_value,
            COUNT(*) AS transaction_count
        FROM base
        WHERE party_ledger_name IS NOT NULL AND party_ledger_name != ''
        GROUP BY party_ledger_name
        ORDER BY SUM(total_debit) DESC
        LIMIT 3
    ),
    top_parties_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'party_name', party_name,
            'total_value', total_value,
            'transaction_count', transaction_count
        )), '[]'::jsonb) AS data
        FROM top_parties
    ),
    -- Summary by voucher type (Sales, Purchase, Payment, etc.)
    type_summary AS (
        SELECT
            voucher_type,
            COUNT(*) AS count,
            COALESCE(SUM(total_debit), 0) AS total_amount
        FROM base
        GROUP BY voucher_type
        ORDER BY SUM(total_debit) DESC
    ),
    type_summary_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'type', voucher_type,
            'count', count,
            'total_amount', total_amount
        )), '[]'::jsonb) AS data
        FROM type_summary
    ),
    ui_records AS (
        SELECT 
            jsonb_build_object(
                'id', id,
                'voucher_number', voucher_number,
                'voucher_type', voucher_type,
                'voucher_date', to_char(voucher_date, 'YYYY-MM-DD'),
                'party_ledger_name', party_ledger_name,
                'is_balanced', is_balanced,
                'balance_difference', balance_difference,
                'total_debit', total_debit,
                'total_credit', total_credit
            ) AS rec,
            -- Add relevance score for sorting when party search is active
            CASE 
                WHEN %(party_name_exact)s IS NOT NULL THEN
                    CASE
                        WHEN party_ledger_name = %(party_name_exact)s THEN 1  -- Exact match
                        WHEN party_ledger_name ILIKE %(party_name_prefix)s THEN 2  -- Starts with
                        WHEN party_ledger_name ILIKE %(party_name_wildcard)s THEN 3  -- Contains
                        ELSE 4
                    END
                ELSE 999  -- No party search, don't prioritize by name
            END AS relevance_score,
            voucher_date
        FROM base
        ORDER BY 
            relevance_score,  -- Prioritize relevant parties first
            voucher_date DESC NULLS LAST,  -- Then by date
            id DESC  -- Then by ID for consistency
    )
    SELECT jsonb_build_object(
        'error', NULL,
        'message', NULL,
        'insights', jsonb_build_object(
            'summary', CASE
                WHEN (SELECT total_count FROM aggregates) = 0 THEN 'No vouchers found matching your criteria.'
                WHEN (SELECT total_count FROM aggregates) = 1 THEN 
                    'Found 1 voucher worth ₹' || to_char((SELECT total_amount FROM aggregates), 'FM999,999,999.00')
                ELSE
                    'Found ' || (SELECT total_count FROM aggregates) || ' vouchers worth ₹' || 
                    to_char((SELECT total_amount FROM aggregates), 'FM999,999,999.00')
            END,
            'total_matches', (SELECT total_count FROM aggregates),
            'total_amount', (SELECT total_amount FROM aggregates),
            'period', CASE
                WHEN (SELECT total_count FROM aggregates) = 0 THEN NULL
                WHEN (SELECT earliest_date FROM aggregates) = (SELECT latest_date FROM aggregates) THEN
                    'Date: ' || to_char((SELECT earliest_date FROM aggregates), 'DD Mon YYYY')
                ELSE
                    'From ' || to_char((SELECT earliest_date FROM aggregates), 'DD Mon YYYY') || 
                    ' to ' || to_char((SELECT latest_date FROM aggregates), 'DD Mon YYYY')
            END,
            'highest_voucher', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'voucher_number', voucher_number,
                        'party', party_ledger_name,
                        'amount', total_debit,
                        'date', date,
                        'type', voucher_type,
                        'description', 'Highest: ' || voucher_type || ' #' || voucher_number || 
                                     ' to ' || COALESCE(party_ledger_name, 'N/A') || 
                                     ' for ₹' || to_char(total_debit, 'FM999,999,999.00') || 
                                     ' on ' || date
                    ) FROM highest_voucher)
                ELSE NULL
            END,
            'most_common_type', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'type', voucher_type,
                        'count', count,
                        'description', voucher_type || ' (' || count || ' vouchers)'
                    ) FROM most_common_type)
                ELSE NULL
            END,
            'most_common_party', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'party_name', party_name,
                        'transaction_count', transaction_count,
                        'description', party_name || ' with ' || transaction_count || ' transactions'
                    ) FROM most_common_party)
                ELSE NULL
            END,
            'top_parties_by_value', (SELECT data FROM top_parties_json),
            'voucher_type_summary', (SELECT data FROM type_summary_json)
        ),
        'records', COALESCE((SELECT jsonb_agg(rec) FROM ui_records), '[]'::jsonb)
    ) AS result;
    """
    
    return query, params


def get_search_ledgers_query(
    company_id: str,
    division_id: str,
    ledger_name: Optional[str] = None,
    group_name: Optional[str] = None,
    gstin: Optional[str] = None,
    min_opening_balance: Optional[float] = None,
    max_opening_balance: Optional[float] = None,
    min_closing_balance: Optional[float] = None,
    max_closing_balance: Optional[float] = None
) -> Tuple[str, Dict]:
    """
    Returns the SQL query and parameters for searching ledgers.
    
    Returns:
        tuple: (query_string, parameters_dict)
    """
    # Build WHERE clause filters dynamically
    # Note: tally_ledgers table doesn't have company_id/division_id columns
    filters = []
    
    params = {}
    
    # Add optional filters
    if ledger_name:
        filters.append("l.name ILIKE %(ledger_name)s")
        params['ledger_name'] = f'%{ledger_name}%'
    
    if group_name:
        filters.append("l.group_name ILIKE %(group_name)s")
        params['group_name'] = f'%{group_name}%'
    
    if gstin:
        filters.append("l.gstin ILIKE %(gstin)s")
        params['gstin'] = f'%{gstin}%'
    
    if min_opening_balance is not None:
        filters.append("l.opening_balance >= %(min_opening_balance)s")
        params['min_opening_balance'] = min_opening_balance
    
    if max_opening_balance is not None:
        filters.append("l.opening_balance <= %(max_opening_balance)s")
        params['max_opening_balance'] = max_opening_balance
    
    if min_closing_balance is not None:
        filters.append("l.closing_balance >= %(min_closing_balance)s")
        params['min_closing_balance'] = min_closing_balance
    
    if max_closing_balance is not None:
        filters.append("l.closing_balance <= %(max_closing_balance)s")
        params['max_closing_balance'] = max_closing_balance
    
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    query = f"""
    WITH base AS (
        SELECT
            l.id,
            l.name,
            l.group_name,
            l.opening_balance,
            l.closing_balance,
            l.gstin,
            -- Calculate net movement
            (l.closing_balance - l.opening_balance) AS net_movement
        FROM public.tally_ledgers l
        WHERE {where_clause}
    ),
    aggregates AS (
        SELECT
            COUNT(*)::bigint AS total_count,
            COALESCE(SUM(opening_balance), 0) AS total_opening,
            COALESCE(SUM(closing_balance), 0) AS total_closing,
            COALESCE(SUM(CASE WHEN closing_balance > 0 THEN closing_balance ELSE 0 END), 0) AS total_debit_balance,
            COALESCE(SUM(CASE WHEN closing_balance < 0 THEN ABS(closing_balance) ELSE 0 END), 0) AS total_credit_balance,
            COALESCE(SUM(ABS(closing_balance - opening_balance)), 0) AS total_movement
        FROM base
    ),
    -- Largest opening balance ledger
    largest_opening AS (
        SELECT
            name,
            opening_balance,
            group_name
        FROM base
        ORDER BY ABS(opening_balance) DESC
        LIMIT 1
    ),
    -- Largest closing balance ledger
    largest_closing AS (
        SELECT
            name,
            closing_balance,
            group_name
        FROM base
        ORDER BY ABS(closing_balance) DESC
        LIMIT 1
    ),
    -- Top 5 parties with highest dues (positive closing balance = receivable)
    top_dues AS (
        SELECT
            name,
            closing_balance,
            group_name
        FROM base
        WHERE closing_balance > 0
        ORDER BY closing_balance DESC
        LIMIT 5
    ),
    top_dues_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'name', name,
            'due_amount', closing_balance,
            'group', group_name,
            'description', name || ' owes ₹' || to_char(closing_balance, 'FM999,999,999.00')
        )), '[]'::jsonb) AS data
        FROM top_dues
    ),
    -- Group-wise summary (especially Sundry Debtors vs Sundry Creditors)
    group_summary AS (
        SELECT
            group_name,
            COUNT(*) AS ledger_count,
            COALESCE(SUM(opening_balance), 0) AS total_opening,
            COALESCE(SUM(closing_balance), 0) AS total_closing,
            CASE 
                WHEN SUM(closing_balance) > 0 THEN 'Receivable'
                WHEN SUM(closing_balance) < 0 THEN 'Payable'
                ELSE 'Balanced'
            END AS balance_type
        FROM base
        GROUP BY group_name
        ORDER BY ABS(SUM(closing_balance)) DESC
    ),
    group_summary_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'group_name', group_name,
            'ledger_count', ledger_count,
            'total_closing', total_closing,
            'balance_type', balance_type,
            'description', group_name || ': ' || ledger_count || ' ledgers, ' || 
                         balance_type || ' ₹' || to_char(ABS(total_closing), 'FM999,999,999.00')
        )), '[]'::jsonb) AS data
        FROM group_summary
    ),
    ui_records AS (
        SELECT jsonb_build_object(
            'id', id,
            'name', name,
            'group_name', group_name,
            'opening_balance', opening_balance,
            'closing_balance', closing_balance,
            'gstin', gstin
        ) AS rec
        FROM base
        ORDER BY name ASC
    )
    SELECT jsonb_build_object(
        'error', NULL,
        'message', NULL,
        'insights', jsonb_build_object(
            'summary', CASE
                WHEN (SELECT total_count FROM aggregates) = 0 THEN 'No ledgers found matching your criteria.'
                WHEN (SELECT total_count FROM aggregates) = 1 THEN 'Found 1 ledger account.'
                ELSE 'Found ' || (SELECT total_count FROM aggregates) || ' ledger accounts.'
            END,
            'total_matches', (SELECT total_count FROM aggregates),
            'total_debit_balance', (SELECT total_debit_balance FROM aggregates),
            'total_credit_balance', (SELECT total_credit_balance FROM aggregates),
            'net_outstanding', (SELECT (total_debit_balance - total_credit_balance) FROM aggregates),
            'outstanding_summary', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    'Total Receivables: ₹' || to_char((SELECT total_debit_balance FROM aggregates), 'FM999,999,999.00') || 
                    ', Total Payables: ₹' || to_char((SELECT total_credit_balance FROM aggregates), 'FM999,999,999.00')
                ELSE NULL
            END,
            'largest_opening_balance', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'ledger_name', name,
                        'opening_balance', opening_balance,
                        'group', group_name,
                        'description', name || ' (' || group_name || ') had opening balance of ₹' || 
                                     to_char(ABS(opening_balance), 'FM999,999,999.00')
                    ) FROM largest_opening)
                ELSE NULL
            END,
            'largest_closing_balance', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'ledger_name', name,
                        'closing_balance', closing_balance,
                        'group', group_name,
                        'description', name || ' (' || group_name || ') has closing balance of ₹' || 
                                     to_char(ABS(closing_balance), 'FM999,999,999.00')
                    ) FROM largest_closing)
                ELSE NULL
            END,
            'top_parties_with_dues', (SELECT data FROM top_dues_json),
            'group_summary', (SELECT data FROM group_summary_json)
        ),
        'records', COALESCE((SELECT jsonb_agg(rec) FROM ui_records), '[]'::jsonb)
    ) AS result;
    """
    
    return query, params


def get_list_master_query(
    company_id: str,
    division_id: str,
    collection: str
) -> Tuple[str, Dict]:
    """
    Returns the SQL query and parameters for listing master data.
    Supports: group, vouchertype, unit, godown, stockgroup
    
    Returns:
        tuple: (query_string, parameters_dict)
    """
    v_collection = collection.strip().lower() if collection else ''
    
    params = {
        'company_id': company_id,
        'division_id': division_id
    }
    
    # Return empty array if invalid collection
    if not company_id or not division_id or not v_collection or v_collection == '':
        query = "SELECT '[]'::jsonb AS result;"
        return query, params
    
    # Build query based on collection type
    if v_collection == 'group':
        query = """
        SELECT coalesce(jsonb_agg(obj), '[]'::jsonb) AS result
        FROM (
            SELECT
                id::text AS id,
                coalesce(group_code, '') AS code,
                coalesce(group_name, '') AS name,
                jsonb_build_object(
                    'group_type', group_type,
                    'level', level
                ) AS attrs
            FROM public.tally_groups
            WHERE company_id = %(company_id)s
                AND division_id = %(division_id)s
            ORDER BY group_name
        ) obj;
        """
    elif v_collection == 'vouchertype':
        query = """
        SELECT coalesce(jsonb_agg(obj), '[]'::jsonb) AS result
        FROM (
            SELECT
                id::text AS id,
                coalesce(voucher_type_code, '') AS code,
                coalesce(voucher_type_name, '') AS name,
                jsonb_build_object(
                    'parent_type', parent_type
                ) AS attrs
            FROM public.tally_voucher_types
            WHERE company_id = %(company_id)s
                AND division_id = %(division_id)s
            ORDER BY voucher_type_name
        ) obj;
        """
    elif v_collection == 'unit':
        query = """
        SELECT coalesce(jsonb_agg(obj), '[]'::jsonb) AS result
        FROM (
            SELECT
                id::text AS id,
                coalesce(unit_code, '') AS code,
                coalesce(unit_name, '') AS name,
                jsonb_build_object(
                    'symbol', symbol,
                    'formal_name', formal_name,
                    'unit_type', unit_type,
                    'number_of_decimal_places', number_of_decimal_places,
                    'conversion_factor', conversion_factor
                ) AS attrs
            FROM public.tally_units
            WHERE company_id = %(company_id)s
                AND division_id = %(division_id)s
            ORDER BY unit_name
        ) obj;
        """
    elif v_collection == 'godown':
        query = """
        SELECT coalesce(jsonb_agg(obj), '[]'::jsonb) AS result
        FROM (
            SELECT
                id::text AS id,
                coalesce(tally_guid, '') AS code,
                coalesce(godown_name, '') AS name,
                jsonb_build_object(
                    'godown_code', godown_code,
                    'address', address,
                    'contact_person', contact_person,
                    'phone', phone,
                    'email', email,
                    'capacity', capacity,
                    'capacity_unit', capacity_unit,
                    'location_details', location_details
                ) AS attrs
            FROM public.tally_godowns
            WHERE company_id = %(company_id)s
                AND division_id = %(division_id)s
            ORDER BY godown_name
        ) obj;
        """
    elif v_collection == 'stockgroup':
        query = """
        SELECT coalesce(jsonb_agg(obj), '[]'::jsonb) AS result
        FROM (
            SELECT
                id::text AS id,
                coalesce(group_code, '') AS code,
                coalesce(group_name, '') AS name,
                jsonb_build_object(
                    'hsn_sac', hsn_sac,
                    'gst_rate', gst_rate
                ) AS attrs
            FROM public.tally_stock_groups
            WHERE company_id = %(company_id)s
                AND division_id = %(division_id)s
            ORDER BY group_name
        ) obj;
        """
    else:
        # Return empty array for unsupported collections
        query = "SELECT '[]'::jsonb AS result;"
    
    return query, params


def get_search_stockitem_query(
    company_id: str,
    division_id: str,
    item_name: Optional[str] = None,
    item_code: Optional[str] = None,
    stock_group: Optional[str] = None,
    gst_hsn_code: Optional[str] = None
) -> Tuple[str, Dict]:
    """
    Returns the SQL query and parameters for searching stock items.
    
    Returns:
        tuple: (query_string, parameters_dict)
    """
    filters = [
        "company_id = %(company_id)s",
        "division_id = %(division_id)s"
    ]
    
    params = {
        'company_id': company_id,
        'division_id': division_id
    }
    
    # Add optional filters
    if item_name:
        filters.append("item_name ILIKE %(item_name)s")
        params['item_name'] = f'%{item_name}%'
    
    if item_code:
        filters.append("(item_code ILIKE %(item_code)s OR tally_guid ILIKE %(item_code)s)")
        params['item_code'] = f'%{item_code}%'
    
    if stock_group:
        filters.append("stock_group_name ILIKE %(stock_group)s")
        params['stock_group'] = f'%{stock_group}%'
    
    if gst_hsn_code:
        filters.append("gst_hsn_code ILIKE %(gst_hsn_code)s")
        params['gst_hsn_code'] = f'%{gst_hsn_code}%'
    
    where_clause = " AND ".join(filters)
    
    query = f"""
    WITH base AS (
        SELECT
            id,
            coalesce(item_code, tally_guid, '') AS code,
            coalesce(item_name, '') AS name,
            stock_group_name,
            gst_applicability,
            gst_hsn_code,
            gst_taxability,
            gst_rate,
            opening_balance_quantity,
            opening_balance_rate_per,
            opening_balance_value,
            CASE 
                WHEN gst_hsn_code IS NULL OR gst_hsn_code = '' THEN true
                ELSE false
            END AS missing_hsn
        FROM public.tally_stock_items
        WHERE {where_clause}
    ),
    aggregates AS (
        SELECT
            COUNT(*)::bigint AS total_count,
            COUNT(DISTINCT stock_group_name) AS group_count,
            COALESCE(SUM(opening_balance_value), 0) AS total_valuation,
            COUNT(CASE WHEN missing_hsn THEN 1 END) AS items_without_hsn
        FROM base
    ),
    -- Highest value item by opening stock value
    highest_value_item AS (
        SELECT
            name,
            opening_balance_value,
            opening_balance_quantity,
            stock_group_name,
            gst_hsn_code
        FROM base
        WHERE opening_balance_value IS NOT NULL
        ORDER BY opening_balance_value DESC
        LIMIT 1
    ),
    -- Items below minimum level (assuming items with zero or very low stock)
    low_stock_items AS (
        SELECT
            name,
            opening_balance_quantity,
            stock_group_name
        FROM base
        WHERE opening_balance_quantity IS NOT NULL 
          AND opening_balance_quantity <= 10  -- Assuming 10 as threshold
        ORDER BY opening_balance_quantity ASC
        LIMIT 5
    ),
    low_stock_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'item_name', name,
            'quantity', opening_balance_quantity,
            'group', stock_group_name,
            'description', name || ' has only ' || COALESCE(opening_balance_quantity, 0) || ' units in stock'
        )), '[]'::jsonb) AS data
        FROM low_stock_items
    ),
    -- Stock summary by group
    group_summary AS (
        SELECT
            stock_group_name,
            COUNT(*) AS item_count,
            COALESCE(SUM(opening_balance_value), 0) AS total_value,
            COALESCE(SUM(opening_balance_quantity), 0) AS total_quantity
        FROM base
        WHERE stock_group_name IS NOT NULL
        GROUP BY stock_group_name
        ORDER BY SUM(opening_balance_value) DESC
        LIMIT 10
    ),
    group_summary_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'group_name', stock_group_name,
            'item_count', item_count,
            'total_value', total_value,
            'total_quantity', total_quantity,
            'description', stock_group_name || ': ' || item_count || ' items worth ₹' || 
                         to_char(total_value, 'FM999,999,999.00')
        )), '[]'::jsonb) AS data
        FROM group_summary
    ),
    -- Items without GST classification
    missing_gst AS (
        SELECT COUNT(*) AS count
        FROM base
        WHERE missing_hsn = true
    ),
    -- HSN summary (top HSN codes by item count)
    hsn_summary AS (
        SELECT
            gst_hsn_code,
            COUNT(*) AS item_count,
            COALESCE(SUM(opening_balance_value), 0) AS total_value
        FROM base
        WHERE gst_hsn_code IS NOT NULL AND gst_hsn_code != ''
        GROUP BY gst_hsn_code
        ORDER BY COUNT(*) DESC
        LIMIT 10
    ),
    hsn_summary_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'hsn_code', gst_hsn_code,
            'item_count', item_count,
            'total_value', total_value,
            'description', 'HSN ' || gst_hsn_code || ': ' || item_count || ' items'
        )), '[]'::jsonb) AS data
        FROM hsn_summary
    ),
    -- GST rate wise summary
    gst_rate_summary AS (
        SELECT
            COALESCE(gst_rate, 0) AS gst_rate,
            COUNT(*) AS item_count,
            COALESCE(SUM(opening_balance_value), 0) AS total_value
        FROM base
        GROUP BY gst_rate
        ORDER BY gst_rate DESC
    ),
    gst_rate_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'gst_rate', gst_rate,
            'item_count', item_count,
            'total_value', total_value,
            'description', item_count || ' items at ' || gst_rate || '% GST'
        )), '[]'::jsonb) AS data
        FROM gst_rate_summary
    ),
    ui_records AS (
        SELECT jsonb_build_object(
            'id', id::text,
            'code', code,
            'name', name,
            'stock_group', stock_group_name,
            'gst_hsn_code', gst_hsn_code,
            'gst_rate', gst_rate,
            'opening_balance_quantity', opening_balance_quantity,
            'opening_balance_value', opening_balance_value
        ) AS rec
        FROM base
        ORDER BY name ASC
    )
    SELECT jsonb_build_object(
        'error', NULL,
        'message', NULL,
        'insights', jsonb_build_object(
            'summary', CASE
                WHEN (SELECT total_count FROM aggregates) = 0 THEN 'No stock items found matching your criteria.'
                WHEN (SELECT total_count FROM aggregates) = 1 THEN 
                    'Found 1 stock item with valuation of ₹' || 
                    to_char((SELECT total_valuation FROM aggregates), 'FM999,999,999.00')
                ELSE
                    'Found ' || (SELECT total_count FROM aggregates) || ' stock items with total valuation of ₹' || 
                    to_char((SELECT total_valuation FROM aggregates), 'FM999,999,999.00')
            END,
            'total_matches', (SELECT total_count FROM aggregates),
            'stock_valuation', (SELECT total_valuation FROM aggregates),
            'total_groups', (SELECT group_count FROM aggregates),
            'items_without_gst', (SELECT items_without_hsn FROM aggregates),
            'highest_value_item', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'item_name', name,
                        'value', opening_balance_value,
                        'quantity', opening_balance_quantity,
                        'group', stock_group_name,
                        'hsn', gst_hsn_code,
                        'description', name || ' is the highest valued item at ₹' || 
                                     to_char(opening_balance_value, 'FM999,999,999.00') || 
                                     ' (' || COALESCE(opening_balance_quantity, 0) || ' units)'
                    ) FROM highest_value_item)
                ELSE NULL
            END,
            'low_stock_items', (SELECT data FROM low_stock_json),
            'stock_by_group', (SELECT data FROM group_summary_json),
            'hsn_summary', (SELECT data FROM hsn_summary_json),
            'gst_rate_summary', (SELECT data FROM gst_rate_json),
            'gst_compliance_note', CASE
                WHEN (SELECT items_without_hsn FROM aggregates) > 0 THEN
                    (SELECT items_without_hsn FROM aggregates) || ' items are missing HSN/SAC codes'
                ELSE
                    'All items have GST classification'
            END
        ),
        'records', COALESCE((SELECT jsonb_agg(rec) FROM ui_records), '[]'::jsonb)
    ) AS result;
    """
    
    return query, params


def get_search_godown_query(
    company_id: str,
    division_id: str,
    godown_name: Optional[str] = None,
    godown_code: Optional[str] = None,
    location: Optional[str] = None
) -> Tuple[str, Dict]:
    """
    Returns the SQL query and parameters for searching godowns.
    
    Returns:
        tuple: (query_string, parameters_dict)
    """
    filters = [
        "company_id = %(company_id)s",
        "division_id = %(division_id)s"
    ]
    
    params = {
        'company_id': company_id,
        'division_id': division_id
    }
    
    # Add optional filters
    if godown_name:
        filters.append("godown_name ILIKE %(godown_name)s")
        params['godown_name'] = f'%{godown_name}%'
    
    if godown_code:
        filters.append("(godown_code ILIKE %(godown_code)s OR tally_guid ILIKE %(godown_code)s)")
        params['godown_code'] = f'%{godown_code}%'
    
    if location:
        filters.append("(location_details ILIKE %(location)s OR address ILIKE %(location)s)")
        params['location'] = f'%{location}%'
    
    where_clause = " AND ".join(filters)
    
    query = f"""
    WITH base AS (
        SELECT
            id,
            coalesce(tally_guid, '') AS code,
            coalesce(godown_name, '') AS name,
            godown_code,
            address,
            contact_person,
            phone,
            email,
            capacity,
            capacity_unit,
            location_details,
            CASE 
                WHEN contact_person IS NULL OR contact_person = '' THEN true
                ELSE false
            END AS missing_contact
        FROM public.tally_godowns
        WHERE {where_clause}
    ),
    aggregates AS (
        SELECT
            COUNT(*)::bigint AS total_count,
            COALESCE(SUM(capacity), 0) AS total_capacity,
            COUNT(CASE WHEN missing_contact THEN 1 END) AS godowns_without_contact,
            COUNT(DISTINCT location_details) AS unique_locations
        FROM base
    ),
    -- Largest godown by capacity
    largest_godown AS (
        SELECT
            name,
            capacity,
            capacity_unit,
            location_details,
            contact_person
        FROM base
        WHERE capacity IS NOT NULL
        ORDER BY capacity DESC
        LIMIT 1
    ),
    -- Godowns by location
    location_summary AS (
        SELECT
            COALESCE(location_details, 'Unknown Location') AS location,
            COUNT(*) AS godown_count,
            COALESCE(SUM(capacity), 0) AS total_capacity
        FROM base
        GROUP BY location_details
        ORDER BY COUNT(*) DESC
    ),
    location_json AS (
        SELECT COALESCE(jsonb_agg(jsonb_build_object(
            'location', location,
            'godown_count', godown_count,
            'total_capacity', total_capacity,
            'description', location || ': ' || godown_count || ' warehouse(s)'
        )), '[]'::jsonb) AS data
        FROM location_summary
    ),
    ui_records AS (
        SELECT jsonb_build_object(
            'id', id::text,
            'code', code,
            'name', name,
            'godown_code', godown_code,
            'address', address,
            'contact_person', contact_person,
            'phone', phone,
            'email', email,
            'capacity', capacity,
            'capacity_unit', capacity_unit,
            'location_details', location_details
        ) AS rec
        FROM base
        ORDER BY name ASC
    )
    SELECT jsonb_build_object(
        'error', NULL,
        'message', NULL,
        'insights', jsonb_build_object(
            'summary', CASE
                WHEN (SELECT total_count FROM aggregates) = 0 THEN 'No warehouses found matching your criteria.'
                WHEN (SELECT total_count FROM aggregates) = 1 THEN 'Found 1 warehouse.'
                ELSE 'Found ' || (SELECT total_count FROM aggregates) || ' warehouses.'
            END,
            'total_matches', (SELECT total_count FROM aggregates),
            'total_capacity', (SELECT total_capacity FROM aggregates),
            'unique_locations', (SELECT unique_locations FROM aggregates),
            'capacity_info', CASE
                WHEN (SELECT total_capacity FROM aggregates) > 0 THEN
                    'Total storage capacity: ' || 
                    to_char((SELECT total_capacity FROM aggregates), 'FM999,999,999.00') || ' units'
                ELSE
                    'No capacity information available'
            END,
            'largest_warehouse', CASE
                WHEN (SELECT total_count FROM aggregates) > 0 THEN
                    (SELECT jsonb_build_object(
                        'name', name,
                        'capacity', capacity,
                        'capacity_unit', capacity_unit,
                        'location', location_details,
                        'contact', contact_person,
                        'description', name || ' is the largest warehouse with capacity of ' || 
                                     COALESCE(capacity, 0) || ' ' || COALESCE(capacity_unit, 'units') ||
                                     CASE WHEN location_details IS NOT NULL 
                                          THEN ' at ' || location_details 
                                          ELSE '' END
                    ) FROM largest_godown)
                ELSE NULL
            END,
            'location_summary', (SELECT data FROM location_json),
            'missing_contacts', CASE
                WHEN (SELECT godowns_without_contact FROM aggregates) > 0 THEN
                    (SELECT godowns_without_contact FROM aggregates) || ' warehouse(s) are missing contact person details'
                ELSE
                    'All warehouses have contact information'
            END
        ),
        'records', COALESCE((SELECT jsonb_agg(rec) FROM ui_records), '[]'::jsonb)
    ) AS result;
    """
    
    return query, params

