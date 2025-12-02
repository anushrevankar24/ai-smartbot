# DataTable Component Usage Guide

The `DataTable` component is a flexible, reusable table component that can display any tabular data with pagination support.

## Basic Usage

```tsx
import DataTable, { ColumnDefinition } from "./DataTable";

const columns: ColumnDefinition[] = [
  { key: "id", header: "ID" },
  { key: "name", header: "Name" },
  { key: "email", header: "Email" },
];

const data = [
  { id: 1, name: "John Doe", email: "john@example.com" },
  { id: 2, name: "Jane Smith", email: "jane@example.com" },
];

<DataTable
  data={data}
  columns={columns}
  title="Users"
/>
```

## With Pagination

```tsx
<DataTable
  data={data}
  columns={columns}
  totalCount={100}
  pageSize={20}
  currentPage={1}
  onPageChange={(page) => setCurrentPage(page)}
/>
```

## Helper Functions

### Currency Column
```tsx
import { createCurrencyColumn } from "./DataTable";

const columns = [
  { key: "name", header: "Name" },
  createCurrencyColumn("amount", "Amount", "₹"),
];
```

### Link Column
```tsx
import { createLinkColumn } from "./DataTable";

const columns = [
  { key: "name", header: "Name" },
  createLinkColumn(
    "view_url",
    "View",
    (row) => row.view_url,
    "Open"
  ),
];
```

### Date Column
```tsx
import { createDateColumn } from "./DataTable";

const columns = [
  createDateColumn("date", "Date", (date) => {
    return new Date(date).toLocaleDateString();
  }),
];
```

### Text Column (with truncation)
```tsx
import { createTextColumn } from "./DataTable";

const columns = [
  createTextColumn("description", "Description", 200),
];
```

## Custom Rendering

```tsx
const columns: ColumnDefinition[] = [
  {
    key: "status",
    header: "Status",
    render: (value, row) => (
      <span className={value === "active" ? "text-green-500" : "text-red-500"}>
        {value}
      </span>
    ),
  },
];
```

## Backend API Format

When returning table data from your API, use this format:

```python
table_data = {
    "columns": [
        {"key": "id", "header": "ID", "className": "w-12"},
        {"key": "name", "header": "Name"},
    ],
    "rows": [
        {"id": 1, "name": "John"},
        {"id": 2, "name": "Jane"},
    ],
    "total_count": 100,
    "page_size": 20,
    "current_page": 1,
    "title": "Users"
}
```

## Features

- ✅ Automatic pagination
- ✅ Custom column rendering
- ✅ Responsive design
- ✅ Empty state handling
- ✅ Flexible styling
- ✅ Type-safe with TypeScript
- ✅ Server-side and client-side pagination support

