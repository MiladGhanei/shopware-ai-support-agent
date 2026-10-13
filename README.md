# Shopware AI Support Agent

An AI-powered customer support assistant for Shopware 6.

Customers can ask questions about their orders in natural language. The AI agent understands the request, uses tool calling to retrieve real-time order data from Shopware, verifies the customer, and responds with the actual order information.

## Demo

<table>
  <tr>
    <td width="68%" align="center">
      <strong>Customer Interface</strong>
    </td>
    <td width="32%" align="center">
      <strong>Configuration</strong>
    </td>
  </tr>
  <tr>
    <td align="center" valign="top">
      <img
        src="screenshots/chat.png"
        alt="Shopware AI Support Agent customer interface"
        width="100%"
      />
    </td>
    <td align="center" valign="top">
      <img
        src="screenshots/settings.png"
        alt="Shopware AI Support Agent configuration"
        width="100%"
      />
    </td>
  </tr>
</table>

> The screenshots above show the original prototype interface. The project is currently being migrated to a dedicated Next.js customer frontend and FastAPI backend.

## How it works

```text
Customer
   ↓
Next.js Customer Interface
   ↓
FastAPI Backend
   ↓
LLM Agent
   ↓
Tool Calling
   ↓
Shopware 6 Admin API
   ↓
Verified Order Data
   ↓
Customer Response
```

The language model does not access Shopware directly.

Instead, it decides when order information is required and requests the appropriate backend tool. The Python backend executes the Shopware API request and returns only the relevant data to the agent.

## Current Features

- Natural-language customer support chat
- LLM tool calling
- Real-time Shopware 6 order lookup
- Order number and shipping ZIP verification
- Order status
- Payment status
- Delivery status
- Tracking codes
- Expected shipping period
- Conversation context
- Automatic expiration of inactive conversations
- Graceful handling of Shopware connection errors
- Graceful handling of LLM rate limits
- Server-side credential management
- Separate customer frontend and AI backend

## Tech Stack

### Backend

- Python
- FastAPI
- OpenRouter
- OpenAI-compatible API
- Shopware 6 Admin API
- Requests

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

## Project Structure

```text
shopware-ai-support-agent/
├── backend/
│   ├── agent.py
│   ├── config.py
│   └── main.py
├── frontend/
│   ├── src/
│   └── package.json
├── legacy/
│   ├── app.py
│   └── ui.py
├── screenshots/
├── .env.example
├── requirements.txt
└── README.md
```

The `legacy/` directory contains the original Streamlit prototype.

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/MiladGhanei/shopware-ai-support-agent.git
cd shopware-ai-support-agent
```

### 2. Create the Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure the backend

Copy the example environment file:

```bash
cp .env.example .env
```

Configure:

```text
OPENROUTER_API_KEY=your_openrouter_api_key
SHOPWARE_URL=https://your-shopware-shop.example
SHOPWARE_ACCESS_ID=your_shopware_access_id
SHOPWARE_SECRET_ACCESS_KEY=your_shopware_secret_access_key
```

Credentials are stored on the backend and are never sent to the customer frontend.

### 4. Start the backend

From the project root:

```bash
uvicorn backend.main:app --reload
```

The API runs locally at:

```text
http://localhost:8000
```

You can check it with:

```text
http://localhost:8000/health
```

### 5. Install the frontend

Open another terminal:

```bash
cd frontend
npm install
```

### 6. Start the frontend

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

## Security

Shopware and LLM credentials remain exclusively on the backend.

Customers never receive:

- Shopware API credentials
- OpenRouter API keys
- Internal tool results
- Shipping ZIP data returned by Shopware

Before order information is returned, the backend verifies the supplied order number against the shipping ZIP code.

The current verification mechanism is intended for the prototype/product validation stage. A production deployment should use stronger customer authentication and appropriate rate limiting.

## Current Product Goal

The first product checkpoint is:

> A Shopware merchant can connect one shop, provide customers with a public support-chat URL, and customers can securely ask about their orders.

The next planned checkpoint is an embeddable Shopware storefront chat widget.