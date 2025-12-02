import { CheckCircle2, FileText, Calendar, Package, TrendingUp, AlertCircle, Users, BarChart3 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ActionCompletionMessageProps {
  message: string;
  actionType: string;
}

const getActionIcon = (actionType: string) => {
  if (actionType.includes("Order") || actionType.includes("Stock")) return Package;
  if (actionType.includes("Report") || actionType.includes("Export")) return FileText;
  if (actionType.includes("Schedule") || actionType.includes("Review")) return Calendar;
  if (actionType.includes("Notify") || actionType.includes("Alert")) return Users;
  if (actionType.includes("Campaign") || actionType.includes("Strategy")) return TrendingUp;
  if (actionType.includes("ROI") || actionType.includes("Analysis")) return BarChart3;
  return CheckCircle2;
};

const parseMessage = (message: string) => {
  const lines = message.split('\n').filter(line => line.trim());
  const title = lines[0];
  const details: string[] = [];
  const highlights: { label: string; value: string }[] = [];
  let currentSection = '';

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Check if it's a key-value pair (contains a colon)
    if (line.includes(':') && !line.startsWith('•')) {
      const [label, ...valueParts] = line.split(':');
      const value = valueParts.join(':').trim();
      if (label.length < 40 && value) {
        highlights.push({ label: label.trim(), value });
      } else {
        details.push(line);
      }
    } else if (line.startsWith('•')) {
      details.push(line);
    } else if (line.length > 0) {
      details.push(line);
    }
  }

  return { title, highlights, details };
};

export default function ActionCompletionMessage({ message, actionType }: ActionCompletionMessageProps) {
  const { title, highlights, details } = parseMessage(message);
  const Icon = getActionIcon(actionType);

  return (
    <Card className="p-4 bg-gradient-to-br from-accent/5 to-accent/10 border-2 border-accent/20 shadow-lg">
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-accent/20 flex items-center justify-center flex-shrink-0">
          <Icon className="w-5 h-5 text-accent" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="w-4 h-4 text-accent" />
            <Badge variant="secondary" className="bg-accent/10 text-accent border-accent/30 text-xs">
              Completed
            </Badge>
          </div>
          <h4 className="font-semibold text-base text-foreground leading-tight">{title}</h4>
        </div>
      </div>

      {/* Highlights - Key-Value Pairs */}
      {highlights.length > 0 && (
        <div className="grid grid-cols-1 gap-2 mb-3 pb-3 border-b border-border/50">
          {highlights.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <span className="text-xs font-medium text-muted-foreground min-w-[120px]">
                {item.label}:
              </span>
              <span className="text-sm text-foreground font-medium flex-1">
                {item.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Details */}
      {details.length > 0 && (
        <div className="space-y-2">
          {details.map((detail, idx) => (
            <p key={idx} className="text-sm text-muted-foreground leading-relaxed">
              {detail}
            </p>
          ))}
        </div>
      )}
    </Card>
  );
}
