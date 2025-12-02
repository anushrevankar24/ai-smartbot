"""
ERP AI Assistant Agent
Built with OpenAI Agents SDK

This module defines the agent and orchestrates tool execution.
"""

import os
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI
from tools import tools, available_functions, initialize_tools

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COMPANY_ID = os.getenv("COMPANY_ID")
DIVISION_ID = os.getenv("DIVISION_ID")

# Validate required environment variables
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
if not COMPANY_ID:
    raise ValueError("COMPANY_ID not found in environment variables")
if not DIVISION_ID:
    raise ValueError("DIVISION_ID not found in environment variables")

# Initialize clients
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize tools with tenant context
try:
    initialize_tools(COMPANY_ID, DIVISION_ID)
except Exception as e:
    print("\n" + "="*80)
    print("ERROR: INITIALIZATION FAILED")
    print("="*80)
    print(f"Error: {str(e)}")
    print("\nPlease fix the error above and restart the server.")
    print("="*80 + "\n")
    import sys
    sys.exit(1)


def run_agent(message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Run the agent with a user message and return the response.
    
    Args:
        message: The user's message
        conversation_history: List of previous messages in the conversation
    
    Returns:
        Dictionary containing the assistant's response and updated conversation history
    """
    if conversation_history is None:
        conversation_history = []
    
    # Track tool calls for debugging
    tool_calls_debug = []
    
    # Add user message to history
    messages = conversation_history + [{"role": "user", "content": message}]
    
    # Get current date for context
    from datetime import datetime
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_date_readable = datetime.now().strftime("%B %d, %Y")
    
    # System prompt that defines the agent's behavior
    system_message = {
        "role": "system",
        "content": f"""You are an intelligent ERP business assistant. You help users interact with their ERP system 
        through natural language. You can retrieve master data such as ledgers, stock items, voucher types, and more.
        
        Current date: {current_date_readable} ({current_date})
        
        When users ask about available data or lists, use the list_master tool to fetch the information.
        Always provide clear, concise responses and format data in a readable way for the user.
        
        When users mention relative time periods (like "this month", "last month", "this year", etc.), 
        calculate the correct dates based on the current date provided above.
        
        Important: You are working within a specific company and division context. The system automatically 
        handles this context - you never need to ask users for company or division IDs."""
    }
    
    # Prepend system message
    full_messages = [system_message] + messages
    
    print(f"\nUSER MESSAGE: {message}")
    
    # Initial API call
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=full_messages,
        tools=tools,
        tool_choice="auto"
    )
    
    assistant_message = response.choices[0].message
    
    # Handle tool calls if any
    if assistant_message.tool_calls:
        print(f"\nAGENT DECIDED TO CALL {len(assistant_message.tool_calls)} TOOL(S)\n")
        # Add assistant message with tool calls to history
        messages.append({
            "role": "assistant",
            "content": assistant_message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in assistant_message.tool_calls
            ]
        })
        
        # Execute each tool call
        for tool_call in assistant_message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Execute the function
            if function_name in available_functions:
                function_response = available_functions[function_name](**function_args)
                
                # Parse response for debugging
                try:
                    response_data = json.loads(function_response)
                    records_count = len(response_data) if isinstance(response_data, list) else 0
                    sample_record = json.dumps(response_data[0], indent=2) if isinstance(response_data, list) and len(response_data) > 0 else None
                    
                    tool_calls_debug.append({
                        "name": function_name,
                        "arguments": json.dumps(function_args, indent=2),
                        "records_count": records_count,
                        "sample_record": sample_record
                    })
                except:
                    tool_calls_debug.append({
                        "name": function_name,
                        "arguments": json.dumps(function_args, indent=2),
                        "records_count": 0,
                        "sample_record": None
                    })
                
                # Add function response to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": function_response
                })
        
        # Get final response with function results
        final_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[system_message] + messages,
        )
        
        final_message = final_response.choices[0].message
        messages.append({"role": "assistant", "content": final_message.content or ""})
        
        print(f"\nAGENT FINAL RESPONSE GENERATED\n")
        
        return {
            "response": final_message.content,
            "conversation_history": messages,
            "tool_calls_made": tool_calls_debug
        }
    
    # No tool calls - just add the response
    messages.append({"role": "assistant", "content": assistant_message.content or ""})
    
    print(f"\nAGENT RESPONDED WITHOUT TOOLS\n")
    
    return {
        "response": assistant_message.content,
        "conversation_history": messages,
        "tool_calls_made": []
    }
