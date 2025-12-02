import { useState, useRef, useEffect } from "react";
import { Send, ChevronRight, Bot, Plus, Mic, ArrowUp, FileText, Users, Box, TrendingUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import ChatMessage from "./ChatMessage";
import { toast } from "sonner";
import VoucherTable from "./VoucherTable";
import MarkdownRenderer from "./MarkdownRenderer";
import DataTable, { ColumnDefinition, createLinkColumn, createCurrencyColumn } from "./DataTable";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  type: "user" | "bot";
  content: string | React.ReactNode;
  timestamp: string;
  actions?: string[];
}

interface VoucherRecord {
  index: number;
  voucher_number: string;
  type: string;
  date: string;
  party: string;
  debit: string;
  credit: string;
  balanced: string;
  actions: string;
}

interface VoucherRecordsData {
  records: VoucherRecord[];
  total_count: number;
  page_size: number;
}

interface TableColumn {
  key: string;
  header: string;
  className?: string;
  headerClassName?: string;
}

interface TableData {
  columns: TableColumn[];
  rows: any[];
  total_count?: number;
  page_size?: number;
  current_page?: number;
  title?: string;
}

interface ChatInterfaceProps {
  onQuerySubmit?: (query: string) => void;
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export default function ChatInterface({ onQuerySubmit, sidebarCollapsed, onToggleSidebar }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  
  // Prevent body scroll issues on mobile by ensuring max width
  useEffect(() => {
    document.body.style.overflowX = "hidden";
    return () => {
      document.body.style.overflowX = "auto";
    };
  }, []);
  const [isThinking, setIsThinking] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  // Helper function to render table from API table_data
  const renderTableFromData = (tableData: TableData): React.ReactNode => {
    // Convert API columns to DataTable column definitions
    const columns: ColumnDefinition[] = tableData.columns.map(col => {
      const columnDef: ColumnDefinition = {
        key: col.key,
        header: col.header,
        className: col.className,
        headerClassName: col.headerClassName,
      };

      // Special handling for specific column types
      if (col.key === 'actions') {
        return createLinkColumn(
          'actions',
          col.header || 'Actions',
          (row: any) => row.actions,
          'View'
        );
      }
      
      if (col.key === 'debit' || col.key === 'credit' || col.key === 'opening_balance' || col.key === 'closing_balance' || col.key === 'opening_balance_value') {
        return createCurrencyColumn(
          col.key,
          col.header,
          '₹',
          col.className
        );
      }

      if (col.key === 'party') {
        return {
          ...columnDef,
          render: (value, row) => (
            <span className="truncate block max-w-[200px]" title={String(value || '')}>
              {String(value || '-')}
            </span>
          ),
        };
      }

      if (col.key === 'balanced') {
        return {
          ...columnDef,
          render: (value) => (
            <span className="text-center">
              {value ? 'Yes' : 'No'}
            </span>
          ),
        };
      }

      return columnDef;
    });

    return (
      <DataTable
        data={tableData.rows}
        columns={columns}
        totalCount={tableData.total_count}
        title={tableData.title}
      />
    );
  };

  const sendMessageToAPI = async (message: string): Promise<{ response: string; conversation_id: string; voucher_records?: VoucherRecordsData; table_data?: TableData }> => {
    const response = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: message,
        conversation_id: conversationId,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: { message: "Unknown error" } }));
      throw new Error(errorData.detail?.message || `HTTP error! status: ${response.status}`);
    }

    return await response.json();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isThinking || isStreaming) return;

    const userMessage: Message = {
      id: `user-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      type: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMessage]);
    const userInput = input;
    setInput("");
    
    // Set processing state immediately to prevent duplicate submissions
    setIsThinking(true);
    setIsStreaming(true);
    
    // Create message ID for the response
    const botMessageId = `bot-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    try {
      // Call API
      const apiResponse = await sendMessageToAPI(userInput);
      
      // Update conversation ID
      if (apiResponse.conversation_id) {
        setConversationId(apiResponse.conversation_id);
      }
      
      // Build response content with markdown rendering and table integrated
      const responseContent = (
        <div>
          <MarkdownRenderer content={apiResponse.response} />
          {apiResponse.table_data && apiResponse.table_data.rows.length > 0 && (
            <div className="mt-3 -mx-1">
              {renderTableFromData(apiResponse.table_data)}
            </div>
          )}
        </div>
      );
      
      // Add bot response message with integrated table
      const botMessage: Message = {
        id: botMessageId,
        type: "bot",
        content: responseContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, botMessage]);
      
    } catch (error) {
      // Show error message
      const errorMessage: Message = {
        id: botMessageId,
        type: "bot",
        content: <MarkdownRenderer content={`**Error**\n\nSorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}\n\nPlease check your configuration and try again.`} />,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prev => [...prev, errorMessage]);
      toast.error("Failed to get response from server");
    } finally {
      setIsThinking(false);
      setIsStreaming(false);
      onQuerySubmit?.(userInput);
    }
  };

  return (
    <div className="flex-1 flex flex-col bg-background overflow-hidden w-full">
      {/* Header with toggle button */}
      <header className="border-b border-border px-4 py-4 flex items-center gap-3 bg-card shadow-sm">
        {sidebarCollapsed && onToggleSidebar && (
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9"
            onClick={onToggleSidebar}
          >
            <ChevronRight className="h-5 w-5" />
          </Button>
        )}
        <div>
          <h2 className="font-heading font-bold text-xl text-foreground">Saarthi AI</h2>
          <p className="text-xs text-muted-foreground">Your intelligent business assistant</p>
        </div>
      </header>

      {/* Chat Messages Area - centered like ChatGPT */}
      <div className="flex-1 overflow-y-auto thin-scrollbar">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full px-4">
            <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center mb-6 shadow-lg">
              <Bot className="w-7 h-7 text-white" />
            </div>
            <h2 className="text-2xl font-bold mb-8 text-center">What can I help with?</h2>
            
            <div className="grid grid-cols-2 gap-3 max-w-2xl w-full">
              <Button 
                variant="outline" 
                className="h-auto p-2 md:p-3 justify-start text-left hover:bg-primary/5 dark:hover:bg-primary/10 border-muted transition-all group"
                onClick={() => setInput("Show me the Balance Sheet")}
              >
                <div className="bg-primary/10 p-1.5 md:p-2 rounded-lg mr-2 md:mr-3 group-hover:bg-primary/20 transition-colors">
                  <FileText className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">Balance Sheet</span>
                  <span className="text-[10px] md:text-xs text-muted-foreground font-normal">View financial statement</span>
                </div>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-auto p-2 md:p-3 justify-start text-left hover:bg-primary/5 dark:hover:bg-primary/10 border-muted transition-all group"
                onClick={() => setInput("List top 5 debtors")}
              >
                <div className="bg-primary/10 p-1.5 md:p-2 rounded-lg mr-2 md:mr-3 group-hover:bg-primary/20 transition-colors">
                  <Users className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">Top Debtors</span>
                  <span className="text-[10px] md:text-xs text-muted-foreground font-normal">List outstanding parties</span>
                </div>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-auto p-2 md:p-3 justify-start text-left hover:bg-primary/5 dark:hover:bg-primary/10 border-muted transition-all group"
                onClick={() => setInput("Show stock summary")}
              >
                <div className="bg-primary/10 p-1.5 md:p-2 rounded-lg mr-2 md:mr-3 group-hover:bg-primary/20 transition-colors">
                  <Box className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">Stock Summary</span>
                  <span className="text-[10px] md:text-xs text-muted-foreground font-normal">Check inventory status</span>
                </div>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-auto p-2 md:p-3 justify-start text-left hover:bg-primary/5 dark:hover:bg-primary/10 border-muted transition-all group"
                onClick={() => setInput("Analyze cash flow")}
              >
                <div className="bg-primary/10 p-1.5 md:p-2 rounded-lg mr-2 md:mr-3 group-hover:bg-primary/20 transition-colors">
                  <TrendingUp className="h-3.5 w-3.5 md:h-4 md:w-4 text-primary" />
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm text-foreground group-hover:text-primary transition-colors">Cash Flow</span>
                  <span className="text-[10px] md:text-xs text-muted-foreground font-normal">Analyze cash movement</span>
                </div>
              </Button>
            </div>
          </div>
        ) : (
          <div className="max-w-5xl mx-auto px-2 py-6 space-y-4 min-w-0">
            {messages.map((message) => (
              <ChatMessage
                key={message.id}
                type={message.type}
                content={message.content}
                timestamp={message.timestamp}
              />
            ))}
            
            {isThinking && (
              <div className="flex items-start gap-3 animate-slide-in">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                  <Bot className="w-5 h-5 text-white" />
                </div>
                <div className="chat-bubble-bot rounded-2xl px-4 py-3 max-w-[80%]">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                    <span className="text-sm text-muted-foreground">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Input Area - ChatGPT style */}
      <div className="p-2 md:p-4 pb-4 md:pb-6">
        <form onSubmit={handleSubmit} className="max-w-5xl mx-auto px-2">
          <div className="relative flex items-center gap-2 bg-[#f4f4f4] dark:bg-secondary/20 border border-border/50 rounded-[26px] px-4 py-2.5 shadow-sm focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/20 focus-within:bg-background focus-within:shadow-md transition-all">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full flex-shrink-0 text-muted-foreground hover:bg-background/50"
            >
              <Plus className="h-5 w-5" />
            </Button>
            
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask anything"
              className="flex-1 bg-transparent border-none outline-none text-base placeholder:text-muted-foreground min-h-[44px]"
              disabled={isThinking || isStreaming}
            />
            
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-full flex-shrink-0 text-muted-foreground hover:bg-background/50"
              >
                <Mic className="h-5 w-5" />
              </Button>
              
              <Button
                type="submit"
                size="icon"
                className={cn(
                  "h-9 w-9 rounded-full flex-shrink-0 transition-all",
                  input.trim() ? "bg-primary text-primary-foreground hover:bg-primary/90 shadow-md" : "bg-[#e5e5e5] text-[#b4b4b4] hover:bg-[#e5e5e5] cursor-not-allowed"
                )}
                disabled={isThinking || isStreaming || !input.trim()}
              >
                <ArrowUp className="h-5 w-5" />
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
