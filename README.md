# Order-to-Delivery Backend 

A FastAPI-based backend service for managing orders and inventory in an order-to-delivery system.

## Features

- **Order Management**: Create and track orders with status updates
- **Inventory Management**: Manage product inventory with stock tracking
- **RESTful API**: Built with FastAPI for high performance and async support
- **Database**: MongoDB (Atlas) using PyMongo
- **Logging**: Centralized logging with Loguru
- **Environment-based Configuration**: Using Pydantic settings

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB Atlas
- **Driver**: PyMongo
- **Logging**: Loguru
- **Environment Management**: python-dotenv

## Prerequisites

- Python 3.8+
- pip (Python package manager)

## Getting Started

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Order-to-delivery/backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   # or
   source venv/bin/activate  # On Unix or MacOS
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```env
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority&appName=<appName>
   MONGODB_DB=order_to_delivery
   LOG_LEVEL=INFO
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Orders
- `POST /orders/` - Create a new order
- `GET /orders/{order_id}` - Get order details

### Inventory
- `GET /inventory/` - List all inventory items
- `PATCH /inventory/{sku}` - Update stock for a SKU

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application setup
│   ├── mongo.py          # MongoDB client helpers
│   ├── schemas.py        # Pydantic schemas
│   └── routers/          # API route handlers
│       ├── __init__.py
│       ├── orders.py     # Order-related endpoints
│       └── inventory.py  # Inventory-related endpoints
├── tests/                # Test files
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Development

### Running Tests
```bash
pytest
```

## Deployment (Render)

1. Create a **Web Service** on Render from this GitHub repo.
2. Set **Build Command**:
   ```bash
   pip install -r requirements.txt
   ```
3. Set **Start Command**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Add environment variables on Render:
   - `MONGODB_URI`
   - `MONGODB_DB` (e.g. `order_to_delivery`)
   - `CORS_ORIGINS` (JSON list string)
5. Set health check path to `/health`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.# Order-to-DeliveryBackend
