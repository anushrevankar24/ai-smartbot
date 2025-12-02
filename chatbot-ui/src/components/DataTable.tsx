import { useState, useMemo, useEffect } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, ExternalLink, ChevronsLeft, ChevronsRight, Download } from "lucide-react";
import { cn } from "@/lib/utils";
import * as XLSX from "xlsx";

export interface ColumnDefinition<T = any> {
  key: string;
  header: string;
  accessor?: (row: T, index: number) => React.ReactNode;
  className?: string;
  headerClassName?: string;
  render?: (value: any, row: T, index: number) => React.ReactNode;
  sortable?: boolean;
}

export interface DataTableProps<T = any> {
  data: T[];
  columns: ColumnDefinition<T>[];
  totalCount?: number;
  pageSize?: number;
  currentPage?: number;
  onPageChange?: (page: number) => void;
  title?: string;
  emptyMessage?: string;
  className?: string;
  showPagination?: boolean;
  keyExtractor?: (row: T, index: number) => string | number;
}

export default function DataTable<T = any>({
  data,
  columns,
  totalCount,
  pageSize: propPageSize,
  currentPage: controlledPage,
  onPageChange,
  title,
  emptyMessage = "No data available",
  className,
  showPagination = true,
  keyExtractor,
}: DataTableProps<T>) {
  const [internalPage, setInternalPage] = useState(1);
  
  // Hardcode page size to 5 for voucher tables
  const pageSize = 5;
  
  // Use controlled page if provided, otherwise use internal state
  const currentPage = controlledPage !== undefined ? controlledPage : internalPage;
  const setCurrentPage = onPageChange || setInternalPage;
  
  // Calculate total count - use provided totalCount or data length
  const effectiveTotalCount = totalCount !== undefined ? totalCount : data.length;
  
  const totalPages = useMemo(() => {
    return Math.ceil(effectiveTotalCount / pageSize);
  }, [effectiveTotalCount, pageSize]);

  // Reset to page 1 when data changes (only if using internal state)
  useEffect(() => {
    if (controlledPage === undefined) {
      // Reset to page 1 when data changes significantly
      setInternalPage(1);
    }
  }, [data.length, controlledPage]);

  // Always do client-side pagination - slice the data array
  const paginatedData = useMemo(() => {
    if (!showPagination) {
      return data;
    }
    // Always paginate client-side by slicing the data
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return data.slice(startIndex, endIndex);
  }, [data, currentPage, pageSize, showPagination]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
    }
  };

  const getRowKey = (row: T, index: number): string | number => {
    if (keyExtractor) {
      return keyExtractor(row, index);
    }
    // Try to find an 'id' or 'index' field
    if (typeof row === 'object' && row !== null) {
      const obj = row as any;
      if (obj.id !== undefined) return obj.id;
      if (obj.index !== undefined) return obj.index;
      if (obj.key !== undefined) return obj.key;
    }
    return index;
  };

  const getCellValue = (row: T, column: ColumnDefinition<T>, index: number): React.ReactNode => {
    if (column.render) {
      return column.render((row as any)[column.key], row, index);
    }
    if (column.accessor) {
      return column.accessor(row, index);
    }
    // Default: try to access the key from the row
    const value = (row as any)[column.key];
    if (value === null || value === undefined) {
      return <span className="text-muted-foreground">-</span>;
    }
    return String(value);
  };

  if (data.length === 0) {
    return (
      <div className={cn("border border-border rounded-lg p-8 text-center", className)}>
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  // Calculate display counts
  const displayCount = effectiveTotalCount;
  const showingFrom = (currentPage - 1) * pageSize + 1;
  const showingTo = Math.min(currentPage * pageSize, effectiveTotalCount);

  // Export to Excel function
  const handleExportToExcel = () => {
    try {
      // Prepare data for export - use all data, not just paginated
      // Exclude actions column and get raw values from row data
      const exportColumns = columns.filter(col => col.key !== 'actions');
      
      const exportData = data.map((row, index) => {
        const rowData: any = {};
        exportColumns.forEach((column) => {
          // Get raw value from row data, not from rendered component
          let cellValue: any = (row as any)[column.key];
          
          // Handle special cases
          if (cellValue === null || cellValue === undefined) {
            cellValue = '';
          } else if (typeof cellValue === 'object') {
            // Handle objects - try to extract meaningful value
            if (Array.isArray(cellValue)) {
              cellValue = cellValue.join(', ');
            } else if (cellValue.toString && cellValue.toString() !== '[object Object]') {
              cellValue = cellValue.toString();
            } else {
              // Try to get a common property
              cellValue = cellValue.name || cellValue.value || cellValue.label || '';
            }
          } else if (column.key === 'balanced') {
            // Convert boolean to Yes/No
            cellValue = cellValue ? 'Yes' : 'No';
          } else if (typeof cellValue === 'boolean') {
            cellValue = cellValue ? 'Yes' : 'No';
          } else if (typeof cellValue === 'number') {
            // Keep numbers as-is (currency formatting will be handled by Excel)
            cellValue = cellValue;
          } else {
            // Convert to string for other types
            cellValue = String(cellValue);
          }
          
          rowData[column.header] = cellValue;
        });
        return rowData;
      });

      // Create workbook and worksheet
      const ws = XLSX.utils.json_to_sheet(exportData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, title || "Data");

      // Generate filename with timestamp
      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
      const filename = `${title || "export"}_${timestamp}.xlsx`;

      // Write file
      XLSX.writeFile(wb, filename);
    } catch (error) {
      console.error("Error exporting to Excel:", error);
      alert("Failed to export data. Please try again.");
    }
  };

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between pt-2 pb-1 flex-wrap gap-2">
        {title && (
          <div className="flex items-center gap-3">
            <h3 className="text-sm font-semibold text-foreground">{title}</h3>
            <span className="text-xs text-muted-foreground font-normal">
              {showingFrom}-{showingTo} of {displayCount}
            </span>
          </div>
        )}
        {!title && (
          <span className="text-xs text-muted-foreground font-normal">
            {showingFrom}-{showingTo} of {displayCount}
          </span>
        )}
        <Button
          variant="outline"
          size="sm"
          onClick={handleExportToExcel}
          className="flex items-center gap-1.5 h-7 px-3 text-xs bg-accent text-accent-foreground hover:bg-accent/90 border-accent shadow-sm"
        >
          <Download className="h-3.5 w-3.5" />
          Export to Excel
        </Button>
      </div>
      
      <div className="border border-border/50 rounded-md overflow-hidden bg-background/50 shadow-sm">
        <div className="overflow-x-auto thin-scrollbar">
          <Table>
            <TableHeader>
              <TableRow className="bg-primary/90 hover:bg-primary/90">
                {columns.map((column) => (
                  <TableHead
                    key={column.key}
                    className={cn(
                      "text-white font-semibold",
                      column.headerClassName,
                      column.className
                    )}
                  >
                    {column.header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedData.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns.length} className="text-center py-8">
                    <p className="text-muted-foreground">{emptyMessage}</p>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedData.map((row, index) => (
                  <TableRow 
                    key={getRowKey(row, index)}
                    className={index % 2 === 0 ? "bg-background" : "bg-primary/2"}
                  >
                    {columns.map((column) => (
                      <TableCell
                        key={column.key}
                        className={cn(column.className)}
                      >
                        {getCellValue(row, column, index)}
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>

      {showPagination && totalPages > 1 && (
        <div className="flex items-center justify-between pt-1">
          <div className="text-xs text-muted-foreground font-normal">
            Page {currentPage} of {totalPages}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(1)}
              disabled={currentPage === 1}
              className="h-7 w-7 p-0"
            >
              <ChevronsLeft className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="h-7 w-7 p-0"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
            </Button>
            <span className="text-xs px-2 font-medium">
              {currentPage} / {totalPages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="h-7 w-7 p-0"
            >
              <ChevronRight className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handlePageChange(totalPages)}
              disabled={currentPage === totalPages}
              className="h-7 w-7 p-0"
            >
              <ChevronsRight className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

// Helper function to create a link column
export function createLinkColumn<T = any>(
  key: string,
  header: string,
  urlAccessor: (row: T) => string | undefined,
  label?: string | ((row: T) => string)
): ColumnDefinition<T> {
  return {
    key,
    header,
    className: "text-center",
    render: (value, row) => {
      const url = urlAccessor(row);
      if (!url) {
        return <span className="text-muted-foreground">-</span>;
      }
      const linkLabel = typeof label === 'function' ? label(row) : (label || 'View');
      return (
        <Button
          variant="ghost"
          size="sm"
          asChild
          className="h-8"
        >
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1"
          >
            <ExternalLink className="h-3 w-3" />
            {linkLabel}
          </a>
        </Button>
      );
    },
  };
}

// Helper function to create a formatted number/currency column
export function createCurrencyColumn<T = any>(
  key: string,
  header: string,
  currency: string = "₹",
  className?: string
): ColumnDefinition<T> {
  return {
    key,
    header,
    className: cn("text-right", className),
    headerClassName: "text-right",
    render: (value) => {
      if (value === null || value === undefined || value === '') {
        return <span className="text-muted-foreground">-</span>;
      }
      const numValue = typeof value === 'string' 
        ? parseFloat(value.replace(/[₹,]/g, '')) 
        : Number(value);
      if (isNaN(numValue)) return String(value);
      return `${currency}${numValue.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    },
  };
}

// Helper function to create a date column
export function createDateColumn<T = any>(
  key: string,
  header: string,
  format?: (date: string) => string
): ColumnDefinition<T> {
  return {
    key,
    header,
    render: (value) => {
      if (!value) return <span className="text-muted-foreground">-</span>;
      if (format) {
        return format(String(value));
      }
      return String(value);
    },
  };
}

// Helper function to create a truncated text column
export function createTextColumn<T = any>(
  key: string,
  header: string,
  maxWidth: number = 200,
  className?: string
): ColumnDefinition<T> {
  return {
    key,
    header,
    className: cn("max-w-[200px]", className),
    render: (value, row) => {
      const text = String(value || '');
      return (
        <span className="truncate block" title={text}>
          {text}
        </span>
      );
    },
  };
}

