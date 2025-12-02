import { useState, useEffect } from "react";
import Sidebar from "@/components/Sidebar";
import ChatInterface from "@/components/ChatInterface";
import { useIsMobile } from "@/hooks/use-mobile";

const Index = () => {
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  
  // Update sidebar state when mobile state changes
  useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);

  return (
    <div className="flex h-screen w-full bg-background overflow-hidden relative">
      <Sidebar 
        collapsed={!sidebarOpen}
        onToggleCollapse={toggleSidebar}
        isMobile={isMobile}
      />
      
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <ChatInterface 
        sidebarCollapsed={!sidebarOpen}
        onToggleSidebar={toggleSidebar}
      />
    </div>
  );
};

export default Index;
