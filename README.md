# 🤖 AI Smartbot - ERP Business Assistant

An intelligent, AI-powered business assistant that connects to your ERP/Tally data through natural language. Built with OpenAI GPT-4o, FastAPI, React, and Supabase.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![React](https://img.shields.io/badge/React-18.3-61dafb.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178c6.svg)
![License](https://img.shields.io/badge/License-Proprietary-red.svg)

## ✨ Features

- **Natural Language Queries**: Ask questions about your business data in plain English
- **Multi-Tenant Architecture**: Secure tenant isolation with automatic context injection
- **Real-Time Data Access**: Query vouchers, ledgers, stock items, godowns, and more
- **Rich Data Tables**: Interactive tables with pagination, sorting, and export capabilities
- **Business Insights**: AI-generated summaries and analytics from your data
- **Secure by Design**: LLM never sees sensitive tenant identifiers or raw SQL

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│   OpenAI        │
│   (Port 8080)   │     │   (Port 8000)   │     │   GPT-4o        │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Supabase      │
                        │   PostgreSQL    │
                        │   (Port 6543)   │
                        └─────────────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | React + TypeScript + Tailwind | Modern chat interface with data tables |
| Backend API | FastAPI + Python | REST API server with session management |
| AI Agent | OpenAI Agents SDK + GPT-4o | Natural language understanding & tool execution |
| Database | Supabase (PostgreSQL) | ERP data storage with connection pooling |

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **Supabase** account with database setup
- **OpenAI API Key** (GPT-4o access)

### 1. Clone the Repository

```bash
git clone git@github.com:anushrevankar24/ai-smartbot.git
cd ai-smartbot
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd chatbot-ui
npm install
cd ..
```

### 4. Environment Configuration

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual credentials
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `SQL_DATABASE_URL` | Supabase Transaction Pooler connection string (port 6543) |
| `COMPANY_ID` | UUID of the company to access |
| `DIVISION_ID` | UUID of the division to access |

### 5. Run the Application

**Option A: Use start scripts (Recommended)**

```bash
# Terminal 1 - Backend
./start-backend.sh

# Terminal 2 - Frontend
./start-frontend.sh
```

**Option B: Manual start**

```bash
# Terminal 1 - Backend
source .venv/bin/activate
uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Frontend
cd chatbot-ui
npm run dev
```

### 6. Access the Application

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:8080 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |

## 💬 Usage Examples

Once running, you can ask natural language questions:

### Voucher Queries
- *"Show me all sales vouchers from last month"*
- *"Find payments above ₹50,000"*
- *"List transactions for ABC Company"*

### Ledger Queries
- *"Show all ledgers with outstanding balance"*
- *"Find sundry debtors with dues above ₹1 lakh"*
- *"List ledgers in the Cash group"*

### Stock Queries
- *"Show all stock items"*
- *"Find items with HSN code 8471"*
- *"List low stock items"*

### Warehouse Queries
- *"Show all godowns"*
- *"Find warehouses in Mumbai"*
- *"List warehouse capacity details"*

## 🛠️ Available Tools

The AI agent has access to these tools for querying your ERP data:

| Tool | Description |
|------|-------------|
| `list_master` | Retrieve master data (Groups, VoucherTypes, Units, etc.) |
| `search_vouchers` | Search transactions with filters (date, type, party, amount) |
| `search_ledgers` | Search ledger accounts with balance filters |
| `search_stockitem` | Search stock items by name, group, HSN code |
| `search_godown` | Search warehouses by name, location |

## 📁 Project Structure

```
ai-smartbot/
├── api.py                 # FastAPI backend server
├── agent.py               # OpenAI agent orchestration
├── tools.py               # Tool definitions and implementations
├── sql_queries.py         # SQL query templates
├── requirements.txt       # Python dependencies
│
├── chatbot-ui/            # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── VoucherTable.tsx
│   │   │   └── ui/        # shadcn/ui components
│   │   ├── pages/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── start-backend.sh       # Backend start script
├── start-frontend.sh      # Frontend start script
├── stop.sh                # Stop all services
├── restart.sh             # Restart services
│
├── .env.example           # Environment template
├── .gitignore
└── README.md
```

## 🔒 Security Features

- **Tenant Isolation**: `company_id` and `division_id` are injected server-side, never exposed to LLM
- **Read-Only Operations**: All tools perform read-only database queries
- **No Schema Exposure**: LLM never sees database schema or raw SQL
- **Connection Pooling**: Uses Supabase Transaction Pooler for secure, scalable connections
- **Environment Variables**: All secrets stored in `.env` (never committed)

## 🧪 Testing Database Connection

```bash
# Activate virtual environment
source .venv/bin/activate

# Test database connectivity
python test_db_connection.py
```

## 🐛 Troubleshooting

### Connection Timeout Errors
- Verify `SQL_DATABASE_URL` uses port **6543** (Transaction Pooler)
- Check if Supabase project is paused
- Verify network connectivity

### Backend Won't Start
- Check Python dependencies: `pip install -r requirements.txt`
- Verify `.env` file exists with all required variables
- Check if port 8000 is available: `lsof -ti:8000`

### Frontend Won't Start
- Install dependencies: `cd chatbot-ui && npm install`
- Check if port 8080 is available: `lsof -ti:8080`
- Clear npm cache if issues persist: `npm cache clean --force`

### Agent Not Using Tools
- Verify `OPENAI_API_KEY` is valid
- Check API key has GPT-4o access
- Review agent logs for errors

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This is a proprietary ERP integration system. All rights reserved.

## 🙏 Acknowledgments

- [OpenAI](https://openai.com/) - GPT-4o and Agents SDK
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - Frontend library
- [Supabase](https://supabase.com/) - Backend-as-a-Service
- [shadcn/ui](https://ui.shadcn.com/) - UI components
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS

---

**Built with ❤️ for smarter business operations**
