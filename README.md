# Order-to-Delivery Backend 

A FastAPI-based backend service for managing orders and inventory in an order-to-delivery system.

## Features

- **Order Management**: Create and track orders with status updates
- **Inventory Management**: Manage product inventory with stock tracking
- **RESTful API**: Built with FastAPI for high performance and async support
- **Database**: SQLite with SQLAlchemy ORM
- **Migrations**: Alembic for database migrations
- **Logging**: Centralized logging with Loguru
- **Environment-based Configuration**: Using Pydantic settings

## Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite
- **ORM**: SQLAlchemy 2.0+
- **Migrations**: Alembic
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
   DATABASE_URL=sqlite:///./orders.db
   LOG_LEVEL=INFO
   ```

5. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Orders
- `POST /orders/` - Create a new order
- `GET /orders/{order_id}` - Get order details

### Inventory
- `GET /inventory/` - List all inventory items
- `GET /inventory/{sku}` - Get inventory item by SKU
- `POST /inventory/` - Add new inventory item
- `PUT /inventory/{sku}` - Update inventory item

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application setup
│   ├── config.py         # Configuration settings
│   ├── database.py       # Database connection and session management
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   └── routers/          # API route handlers
│       ├── __init__.py
│       ├── orders.py     # Order-related endpoints
│       └── inventory.py  # Inventory-related endpoints
├── tests/                # Test files
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore file
├── alembic.ini           # Alembic configuration
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
- Create a new migration:
  ```bash
  alembic revision --autogenerate -m "description of changes"
  ```
- Apply migrations:
  ```bash
  alembic upgrade head
  ```

### Linting
```bash
flake8 .
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.# Order-to-DeliveryBackend
