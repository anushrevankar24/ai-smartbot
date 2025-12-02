import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  type: "user" | "bot";
  content: string | React.ReactNode;
  timestamp?: string;
}

export default function ChatMessage({ type, content, timestamp }: ChatMessageProps) {
  const isUser = type === "user";

  return (
    <div
      className={cn(
        "flex gap-3 mb-4 animate-slide-in",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      
      <div className={cn("flex flex-col", isUser ? "items-end" : "items-start", isUser ? "max-w-[85%]" : "flex-1 min-w-0")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 shadow-card",
            isUser ? "chat-bubble-user rounded-br-sm w-full" : "chat-bubble-bot rounded-bl-sm w-full"
          )}
        >
          <div className={cn("text-base leading-relaxed", isUser ? "text-white" : "text-foreground")}>
            {content}
          </div>
        </div>
        {timestamp && (
          <span className="text-xs text-muted-foreground mt-1 px-2">{timestamp}</span>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 border border-primary/20">
          <User className="w-5 h-5 text-primary" />
        </div>
      )}
    </div>
  );
}
