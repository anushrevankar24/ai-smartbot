"""
ERP AI Assistant - FastAPI Backend

This is the main FastAPI application that provides a REST API
for the ERP business assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
from agent import run_agent
from tools import get_voucher_records_for_display

# Initialize FastAPI app
app = FastAPI(title="ERP AI Assistant API", version="1.0.0")

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory conversation history storage
# Key: conversation_id (str), Value: conversation_history (List[Dict])
conversations: Dict[str, List[Dict[str, str]]] = {}


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class TableColumn(BaseModel):
    key: str
    header: str
    className: Optional[str] = None
    headerClassName: Optional[str] = None

class TableData(BaseModel):
    columns: List[TableColumn]
    rows: List[Dict[str, Any]]
    total_count: Optional[int] = None
    page_size: Optional[int] = 20
    current_page: Optional[int] = 1
    title: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    table_data: Optional[TableData] = None
    # Keep voucher_records for backward compatibility
    voucher_records: Optional[Dict[str, Any]] = None


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ERP AI Assistant API"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message and return the assistant's response.
    
    Args:
        request: ChatRequest containing message and optional conversation_id
    
    Returns:
        ChatResponse with response, conversation_id, and optional voucher_records
    """
    try:
        # Get or create conversation_id
        conversation_id = request.conversation_id
        if not conversation_id or conversation_id not in conversations:
            conversation_id = str(uuid.uuid4())
            conversations[conversation_id] = []
        
        # Get conversation history
        conversation_history = conversations[conversation_id]
        
        # Run the agent
        result = run_agent(request.message, conversation_history)
        
        # Update conversation history
        conversations[conversation_id] = result["conversation_history"]
        
        # Check if any search tool was called
        voucher_records_data = None
        ledger_records_data = None
        stockitem_records_data = None
        godown_records_data = None
        
        if result.get("tool_calls_made"):
            from tools import _voucher_records_cache
            for tool_call in result["tool_calls_made"]:
                if tool_call['name'] == 'search_vouchers':
                    # Retrieve voucher records for display
                    voucher_records_data = get_voucher_records_for_display()
                elif tool_call['name'] == 'search_ledgers':
                    # Retrieve ledger records for display
                    ledger_records_data = get_voucher_records_for_display()
                    # Check if it's a ledger type record
                    if ledger_records_data and ledger_records_data.get('type') == 'ledgers':
                        pass  # Already have ledger data
                    else:
                        # Try to find ledger records in cache
                        ledger_records_data = None
                        for key, value in _voucher_records_cache.items():
                            if key.startswith('ledgers_') and value.get('type') == 'ledgers':
                                ledger_records_data = value
                                break
                elif tool_call['name'] == 'search_stockitem':
                    # Retrieve stock item records for display
                    stockitem_records_data = get_voucher_records_for_display()
                    if stockitem_records_data and stockitem_records_data.get('type') == 'stockitems':
                        pass  # Already have stockitem data
                    else:
                        # Try to find stockitem records in cache
                        stockitem_records_data = None
                        for key, value in _voucher_records_cache.items():
                            if key.startswith('stockitems_') and value.get('type') == 'stockitems':
                                stockitem_records_data = value
                                break
                elif tool_call['name'] == 'search_godown':
                    # Retrieve godown records for display
                    godown_records_data = get_voucher_records_for_display()
                    if godown_records_data and godown_records_data.get('type') == 'godowns':
                        pass  # Already have godown data
                    else:
                        # Try to find godown records in cache
                        godown_records_data = None
                        for key, value in _voucher_records_cache.items():
                            if key.startswith('godowns_') and value.get('type') == 'godowns':
                                godown_records_data = value
                                break
        
        # Format table data for frontend if present
        table_data = None
        formatted_voucher_records = None
        
        if voucher_records_data and voucher_records_data.get('records'):
            records = voucher_records_data['records']
            total_count = voucher_records_data.get('total_count', len(records))
            
            # Create table data structure
            columns = [
                TableColumn(key="index", header="#", className="w-12"),
                TableColumn(key="voucher_number", header="Voucher Number"),
                TableColumn(key="type", header="Type"),
                TableColumn(key="date", header="Date"),
                TableColumn(key="party", header="Party"),
                TableColumn(key="debit", header="Debit", className="text-right", headerClassName="text-right"),
                TableColumn(key="credit", header="Credit", className="text-right", headerClassName="text-right"),
                TableColumn(key="balanced", header="Balanced", className="text-center", headerClassName="text-center"),
                TableColumn(key="actions", header="Actions", className="text-center", headerClassName="text-center"),
            ]
            
            # Format rows for table
            table_rows = []
            for idx, record in enumerate(records):
                view_url = record.get('actions', {}).get('view_voucher', '')
                party_name = record.get('party_ledger_name') or ''
                
                table_rows.append({
                    'index': idx + 1,
                    'voucher_number': record.get('voucher_number', ''),
                    'type': record.get('voucher_type', ''),
                    'date': record.get('voucher_date', ''),
                    'party': party_name,
                    'debit': record.get('total_debit', 0),
                    'credit': record.get('total_credit', 0),
                    'balanced': record.get('is_balanced', False),
                    'actions': view_url,
                })
            
            table_data = TableData(
                columns=[col.dict() for col in columns],
                rows=table_rows,
                total_count=total_count,
                page_size=5,
                current_page=1,
                title="Vouchers"
            )
            
            # Also create backward-compatible format
            display_records = []
            for idx, record in enumerate(records):
                view_url = record.get('actions', {}).get('view_voucher', '')
                voucher_number = record.get('voucher_number', '')
                party_name = record.get('party_ledger_name') or ''
                
                display_record = {
                    'index': idx + 1,
                    'voucher_number': voucher_number,
                    'type': record.get('voucher_type', ''),
                    'date': record.get('voucher_date', ''),
                    'party': party_name[:50] + '...' if len(party_name) > 50 else party_name,
                    'debit': f"₹{record.get('total_debit', 0):,.2f}" if record.get('total_debit') else '₹0.00',
                    'credit': f"₹{record.get('total_credit', 0):,.2f}" if record.get('total_credit') else '₹0.00',
                    'balanced': 'Yes' if record.get('is_balanced') else 'No',
                    'actions': view_url
                }
                display_records.append(display_record)
            
            formatted_voucher_records = {
                'records': display_records,
                'total_count': total_count,
                'page_size': 5
            }
        
        # Handle ledger records if present
        if ledger_records_data and ledger_records_data.get('records'):
            records = ledger_records_data['records']
            total_count = ledger_records_data.get('total_count', len(records))
            
            # Create table data structure for ledgers
            ledger_columns = [
                TableColumn(key="index", header="#", className="w-12"),
                TableColumn(key="name", header="Ledger Name"),
                TableColumn(key="group_name", header="Group"),
                TableColumn(key="opening_balance", header="Opening Balance", className="text-right", headerClassName="text-right"),
                TableColumn(key="closing_balance", header="Closing Balance", className="text-right", headerClassName="text-right"),
                TableColumn(key="gstin", header="GSTIN"),
                TableColumn(key="actions", header="Actions", className="text-center", headerClassName="text-center"),
            ]
            
            # Format rows for ledger table
            ledger_table_rows = []
            for idx, record in enumerate(records):
                view_url = record.get('actions', {}).get('view_ledger', '')
                ledger_table_rows.append({
                    'index': idx + 1,
                    'name': record.get('name', ''),
                    'group_name': record.get('group_name', ''),
                    'opening_balance': record.get('opening_balance', 0),
                    'closing_balance': record.get('closing_balance', 0),
                    'gstin': record.get('gstin', '') or '-',
                    'actions': view_url,
                })
            
            # Override table_data with ledger data
            table_data = TableData(
                columns=[col.dict() for col in ledger_columns],
                rows=ledger_table_rows,
                total_count=total_count,
                page_size=5,
                current_page=1,
                title="Ledgers"
            )
        
        # Handle stock item records if present
        if stockitem_records_data and stockitem_records_data.get('records'):
            records = stockitem_records_data['records']
            total_count = stockitem_records_data.get('total_count', len(records))
            
            # Create table data structure for stock items
            stockitem_columns = [
                TableColumn(key="index", header="#", className="w-12"),
                TableColumn(key="name", header="Item Name"),
                TableColumn(key="code", header="Code"),
                TableColumn(key="stock_group", header="Stock Group"),
                TableColumn(key="gst_hsn_code", header="HSN Code"),
                TableColumn(key="gst_rate", header="GST %", className="text-center", headerClassName="text-center"),
                TableColumn(key="opening_balance_quantity", header="Qty", className="text-right", headerClassName="text-right"),
                TableColumn(key="opening_balance_value", header="Value", className="text-right", headerClassName="text-right"),
                TableColumn(key="actions", header="Actions", className="text-center", headerClassName="text-center"),
            ]
            
            # Format rows for stock item table
            stockitem_table_rows = []
            for idx, record in enumerate(records):
                view_url = record.get('actions', {}).get('view_stockitem', '')
                stockitem_table_rows.append({
                    'index': idx + 1,
                    'name': record.get('name', ''),
                    'code': record.get('code', ''),
                    'stock_group': record.get('stock_group', '') or '-',
                    'gst_hsn_code': record.get('gst_hsn_code', '') or '-',
                    'gst_rate': record.get('gst_rate', 0),
                    'opening_balance_quantity': record.get('opening_balance_quantity', 0),
                    'opening_balance_value': record.get('opening_balance_value', 0),
                    'actions': view_url,
                })
            
            # Override table_data with stock item data
            table_data = TableData(
                columns=[col.dict() for col in stockitem_columns],
                rows=stockitem_table_rows,
                total_count=total_count,
                page_size=5,
                current_page=1,
                title="Stock Items"
            )
        
        # Handle godown records if present
        if godown_records_data and godown_records_data.get('records'):
            records = godown_records_data['records']
            total_count = godown_records_data.get('total_count', len(records))
            
            # Create table data structure for godowns
            godown_columns = [
                TableColumn(key="index", header="#", className="w-12"),
                TableColumn(key="name", header="Warehouse Name"),
                TableColumn(key="location_details", header="Location"),
                TableColumn(key="address", header="Address"),
                TableColumn(key="contact_person", header="Contact Person"),
                TableColumn(key="phone", header="Phone"),
                TableColumn(key="capacity", header="Capacity", className="text-right", headerClassName="text-right"),
                TableColumn(key="actions", header="Actions", className="text-center", headerClassName="text-center"),
            ]
            
            # Format rows for godown table
            godown_table_rows = []
            for idx, record in enumerate(records):
                view_url = record.get('actions', {}).get('view_godown', '')
                capacity_display = f"{record.get('capacity', 0)} {record.get('capacity_unit', '')}" if record.get('capacity') else '-'
                godown_table_rows.append({
                    'index': idx + 1,
                    'name': record.get('name', ''),
                    'location_details': record.get('location_details', '') or '-',
                    'address': record.get('address', '') or '-',
                    'contact_person': record.get('contact_person', '') or '-',
                    'phone': record.get('phone', '') or '-',
                    'capacity': capacity_display,
                    'actions': view_url,
                })
            
            # Override table_data with godown data
            table_data = TableData(
                columns=[col.dict() for col in godown_columns],
                rows=godown_table_rows,
                total_count=total_count,
                page_size=5,
                current_page=1,
                title="Warehouses"
            )
        
        return ChatResponse(
            response=result["response"],
            conversation_id=conversation_id,
            table_data=table_data.dict() if table_data else None,
            voucher_records=formatted_voucher_records
        )
        
    except ConnectionError as e:
        # Database connection errors
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Connection Timeout Error",
                    "message": error_msg,
                    "suggestions": [
                        "Check your network connection",
                        "Verify SQL_DATABASE_URL points to Transaction Pooler (port 6543) in .env",
                        "Check if Supabase project is paused"
                    ]
                }
            )
        else:
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "Database Connection Error",
                    "message": error_msg
                }
            )
    except Exception as e:
        # Other errors
        import traceback
        error_trace = traceback.format_exc()
        
        # Print full error to terminal for debugging
        print(f"\nERROR in api.py:")
        print(f"   Error: {str(e)}")
        print(f"   Traceback:\n{error_trace}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

