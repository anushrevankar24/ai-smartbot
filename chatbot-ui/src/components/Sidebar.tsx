import { Edit, ChevronLeft, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";

interface SidebarProps {
  collapsed: boolean;
  onToggleCollapse: () => void;
  isMobile?: boolean;
}

const chatHistory = [
  {
    category: "Today",
    items: [
      { id: 1, name: "Finance Overview", isFolder: false },
      { id: 2, name: "Q3 Sales Report", isFolder: false },
    ]
  },
  {
    category: "Yesterday",
    items: [
      { id: 3, name: "Compliance Report", isFolder: false },
      { id: 4, name: "Inventory Status", isFolder: false },
      { id: 5, name: "Pending Invoices", isFolder: false },
    ]
  },
  {
    category: "Previous 7 Days",
    items: [
      { id: 6, name: "Sales Forecast", isFolder: false },
      { id: 7, name: "Top Customers", isFolder: false },
      { id: 8, name: "Expense Analysis", isFolder: false },
      { id: 9, name: "Tax Summary", isFolder: false },
    ]
  }
];

export default function Sidebar({ collapsed, onToggleCollapse, isMobile }: SidebarProps) {
  const sidebarClasses = isMobile
    ? `fixed inset-y-0 left-0 z-50 w-72 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-300 ${collapsed ? '-translate-x-full' : 'translate-x-0'}`
    : `bg-sidebar border-r border-sidebar-border flex flex-col transition-all duration-300 relative ${collapsed ? 'w-0 overflow-hidden' : 'w-72'}`;

  return (
    <aside className={sidebarClasses}>
      {/* Header with Logo */}
      <div className="p-4 border-b border-sidebar-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            {/* Logo removed */}
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            onClick={onToggleCollapse}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <Button
          variant="ghost"
          className="w-full justify-start text-sidebar-foreground hover:bg-sidebar-accent"
        >
          <Edit className="w-4 h-4 mr-3" />
          <span className="text-base font-medium">New chat</span>
        </Button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto px-3 space-y-4 thin-scrollbar">
        {chatHistory.map((section) => (
          <div key={section.category}>
            <h3 className="text-sidebar-foreground/50 text-xs font-medium uppercase tracking-wider mb-2 px-2">
              {section.category}
            </h3>
            <div className="space-y-1">
              {section.items.map((item) => (
                <Button
                  key={item.id}
                  variant="ghost"
                  className="w-full justify-start text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent text-base py-2 h-auto"
                >
                  <MessageSquare className="w-4 h-4 mr-2 flex-shrink-0" />
                  <span className="flex-1 text-left truncate">{item.name}</span>
                </Button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
