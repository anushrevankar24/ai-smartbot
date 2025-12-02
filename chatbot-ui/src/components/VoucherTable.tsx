import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ExternalLink } from "lucide-react";

interface VoucherRecord {
  index: number;
  voucher_number: string;
  type: string;
  date: string;
  party: string;
  debit: string;
  credit: string;
  balanced: string;
  view_url: string;
}

interface VoucherTableProps {
  records: VoucherRecord[];
  totalCount: number;
  pageSize?: number;
}

export default function VoucherTable({ records, totalCount, pageSize = 20 }: VoucherTableProps) {
  const displayRecords = records.slice(0, pageSize);
  const hasMore = records.length > pageSize;

  return (
    <div className="mt-4 space-y-3">
      <p className="text-sm font-semibold">
        Found {totalCount} voucher(s)
        {hasMore && ` - Showing first ${pageSize} of ${totalCount}`}
      </p>
      
      <div className="border border-border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-12">#</TableHead>
              <TableHead>Voucher Number</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Party</TableHead>
              <TableHead className="text-right">Debit</TableHead>
              <TableHead className="text-right">Credit</TableHead>
              <TableHead className="text-center">Balanced</TableHead>
              <TableHead className="text-center">View</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {displayRecords.map((record) => (
              <TableRow key={record.index}>
                <TableCell className="font-medium">{record.index}</TableCell>
                <TableCell>{record.voucher_number}</TableCell>
                <TableCell>{record.type}</TableCell>
                <TableCell>{record.date}</TableCell>
                <TableCell className="max-w-[200px] truncate" title={record.party}>
                  {record.party}
                </TableCell>
                <TableCell className="text-right">{record.debit}</TableCell>
                <TableCell className="text-right">{record.credit}</TableCell>
                <TableCell className="text-center">{record.balanced}</TableCell>
                <TableCell className="text-center">
                  {record.view_url ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      asChild
                      className="h-8"
                    >
                      <a
                        href={record.view_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        View
                      </a>
                    </Button>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      
      {hasMore && (
        <p className="text-xs text-muted-foreground">
          Note: Showing first {pageSize} vouchers. Total: {totalCount} vouchers found.
        </p>
      )}
    </div>
  );
}

