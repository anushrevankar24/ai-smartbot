import { useState } from "react";
import { Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface ActionButtonsProps {
  actions?: string[];
  onActionComplete?: (action: string, message: string) => void;
}

export default function ActionButtons({
  actions = [],
  onActionComplete
}: ActionButtonsProps) {
  const [completedActions, setCompletedActions] = useState<Set<string>>(new Set());
  const [processingAction, setProcessingAction] = useState<string | null>(null);
  
  // Map action names to success messages
  const actionMessages: Record<string, string> = {
    "Confirm Order": "Order Confirmed Successfully\nPO ID: #PO-4821\nItem: 50 × MacBook Air (M3, 13\")\nVendor: Apple Distribution Pvt Ltd\nEstimated Delivery: 14 days\nStatus: Processing\n\nThe order has been recorded in the procurement system, and notifications have been dispatched to inventory and finance for order alignment.",
    "Notify Procurement": "Procurement department has been officially notified regarding the MacBook Air restock.\nA task entry PRQ-1473 has been created under \"Active Purchase Requests.\"\nThe team will verify vendor lead times and initiate the payment workflow within the next business day.",
    "Add to Vendor Tracker": "Entry added to Vendor Tracker Dashboard.\nYou can now monitor:\n• Order fulfillment status\n• Shipment tracking\n• Payment milestones\n\nVendor Tracker auto-syncs updates every 6 hours.",
    "Notify Procurement Head": "A detailed vendor audit summary for Epson Supplies Ltd. has been sent to the Procurement Head.\nIncludes 6-month SLA trend, delivery scorecards, and corrective action logs.\nFollow-up scheduled for the upcoming procurement sync.",
    "Request SLA Review": "SLA Review initiated for Epson vendor account.\nProcurement Compliance will re-evaluate:\n• Delivery punctuality\n• Product quality deviation\n• Support responsiveness\n\nExpected completion by Oct 15, 2025. Results will be auto-pushed to the Vendor Dashboard.",
    "Find Alternative Vendors": "Found high-performing alternative suppliers:\n• Canon Supply Co. — 94% on-time, 4.6/5 quality\n• Brother Distributors Ltd. — 91% efficiency\n• HP Trade Partners — 89% customer satisfaction\n\nVendor comparison file generated and stored under /Procurement/VendorAlternatives.xlsx.",
    "Generate Plan": "Q4 Improvement Plan Generated\nIncludes 4 strategic initiatives with KPIs, owners, and impact metrics.\nFile: /Business/Improvement_Plan_Q4_2025.pdf\nImplementation starts next cycle under Business Excellence Review.",
    "Notify Department Heads": "Department heads across Sales, Marketing, and Operations have been notified.\nThe communication includes assigned KPIs and actionable timelines for performance enhancement.\nTracking begins automatically in the Performance Insights dashboard.",
    "Schedule Review": "Business Improvement Review locked for Oct 12, 2025 – 11:00 AM.\nMeeting details synced with the corporate calendar and linked to the \"Q4 Improvement Initiative\" workspace.",
    "Create Campaign": "Campaign Draft Created: \"Inspire with Inspiron\"\nFeatures:\n• 5% regional discount\n• Localized social media strategy\n• Performance-based sales incentives\n\nCampaign file logged in /Marketing/Campaigns/Q4_Growth_Inspiron.pdf.",
    "Increase Stock": "Stock increment initiated for Dell Inspiron Laptops (+80 units).\nVendor: Dell Global Trade\nDelivery ETA: Oct 20, 2025\nStock ledger auto-updated in ERP Inventory.",
    "Notify Sales Head": "The Sales Head has been briefed on the new growth initiative.\nThe briefing includes regional projections, discount models, and revised sales targets.\nVisible under \"Q3 Growth Briefs.\"",
    "Alert CFO": "CFO alert raised for Marketing Overspend (+33%).\nExpense note filed in the Finance Audit Log.\nAn internal review meeting has been queued in next week's finance calendar.",
    "Review Campaign ROI": "Campaign ROI Analysis Report:\n• Facebook Ads: 2.3× ROI\n• Influencer Deals: 1.4× ROI\n• Search Marketing: 3.1× ROI\n\nInsight: Influencer contracts underperforming by −27% vs benchmarks.\nOptimization recommendations attached in /Finance/Campaign_ROI_Review.pdf.",
    "Export Report": "Report exported successfully to the appropriate directory with complete data analysis and actionable insights.",
    "Plan Discount Campaign": "Overstock Clearance Campaign Prepared\nProducts & Discounts:\n• HP Toner Cartridges: −15%\n• Cisco Routers XR500: −10%\n• Lenovo ThinkPads: −12%\n\nCampaign tagged for weekend execution (Oct 11–13) in Marketing Ops.",
    "Notify Marketing": "Marketing team has received the overstock clearance report.\nThe campaign strategy is now under review in the \"Inventory Optimization\" board.\nStatus auto-updates daily.",
    "Hold New Orders": "Purchase orders for slow-moving items are now on temporary hold.\nInventory restock scheduling will resume post next cycle audit on Oct 25, 2025.",
    "Place Orders": "Auto Reorder Executed\n• Dell Inspiron: 80 units\n• HP Toner: 100 units\n• Epson Projectors: 30 units\n\nRequisition numbers generated and synced to Procurement Tracker.\nVendor confirmations pending approval.",
    "Export Excel": "Weekly reorder data exported to /Inventory/Reorder_Week40.xlsx.\nIncludes SKU, supplier, lead time, and cost breakdown.",
    "Notify Vendors": "Reorder notifications sent to all three vendors.\nCurrent status:\n• Dell: Confirmed\n• HP: Confirmed\n• Epson: Awaiting Acknowledgment\n\nVendor dashboard updated accordingly.",
    "Notify HR": "HR notified about Sophia Carter's 16% performance decline.\nCase logged as #HRR-9283, and review checklist uploaded under HR Performance Tracker.",
    "Assign Mentor": "Mentorship Assigned: Liam Patel (Senior Account Manager)\nStart Date: Oct 8, 2025\nDuration: 4 weeks\nProgress monitored under the HR Mentorship Module.",
    "Review Workload": "Workload redistribution complete.\nSophia's client load reduced by 20%.\nReassignment reflected in the Team Resource Dashboard.",
    "Notify Logistics": "Logistics team notified of delivery delay issues in West Coast.\nDelivery SLA recalibration task created and logged in Operations Control.",
    "Launch Feedback Campaign": "\"Customer Pulse Q4\" survey campaign activated.\n1,000 targeted customers added to outreach sequence.\nFeedback dashboard goes live next week.",
    "Review SLA": "SLA review initiated for regional logistics vendors.\nMetrics under analysis: Delivery timeliness, escalation rates, customer satisfaction.\nCompletion deadline: Oct 16, 2025.",
    "Plan B2B Strategy": "Draft B2B Strategy Q4 created focusing on hybrid workspace and IT infrastructure sectors.\nTargets: 12% growth in enterprise accounts, 5% improvement in cross-region partnerships.",
    "Alert Sales Head": "Sales Head briefed with complete electronics market overview.\nBriefing includes actionable insights for pricing, regional focus, and product mix.",
    "Create Proposal": "Automation Proposal: SmartOps 2025 generated.\nDetails process feasibility, savings potential, and impact areas.\nProposal ID: #AUT-778\nDocument stored under /Operations/Automation/SmartOps2025.pdf.",
    "Notify IT Team": "IT Operations Team notified of automation roadmap.\nKickoff scheduled for Oct 15, 2025 in the SmartOps workspace.",
    "Estimate ROI": "ROI Estimate Completed\nProjected Savings: $320K annually\nEfficiency Uplift: +18%\nCost Recovery: 2.3 months\nReport stored under /Finance/ROI_Automation2025.pdf.",
    "Share with CEO": "Summary shared with CEO via internal workspace.\nDelivery logged and confirmation received in Executive Board Channel.",
    "Set Performance Alerts": "Real-time alerts configured for critical business metrics:\n• Vendor Efficiency <85%\n• Sales Growth <5%\n• Returns >6%\n\nMonitoring now active under the Performance Control Panel."
  };

  const handleActionClick = async (action: string) => {
    if (completedActions.has(action) || processingAction) return;
    
    setProcessingAction(action);
    
    const message = actionMessages[action] || `${action} completed`;
    if (onActionComplete) {
      await onActionComplete(action, message);
    }
    
    setCompletedActions(prev => new Set(prev).add(action));
    setProcessingAction(null);
  };

  if (!actions || actions.length === 0) return null;

  return (
    <Card className="p-5 bg-card border-2 border-border shadow-card mt-4">
      <p className="text-xs font-semibold text-secondary mb-4 uppercase tracking-wider">Suggested Actions</p>
      <div className="flex flex-wrap gap-3">
        {actions.map((action) => {
          const isCompleted = completedActions.has(action);
          const isProcessing = processingAction === action;
          
          return (
            <Button
              key={action}
              size="sm"
              className={
                isCompleted 
                  ? "bg-accent/20 text-accent border-2 border-accent/30 cursor-default pointer-events-none font-medium" 
                  : isProcessing
                  ? "bg-primary text-primary-foreground border-2 border-primary cursor-wait font-medium"
                  : "bg-secondary text-secondary-foreground hover:bg-accent hover:border-accent font-medium border-2 border-secondary transition-all duration-300"
              }
              onClick={() => handleActionClick(action)}
              disabled={isCompleted || isProcessing || !!processingAction}
            >
              {isCompleted && <Check className="w-3.5 h-3.5 mr-1.5" />}
              {isProcessing && <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />}
              {action}
            </Button>
          );
        })}
      </div>
    </Card>
  );
}
