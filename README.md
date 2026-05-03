# Product Submission API

REST API for submitting product data into a PostgreSQL database. Built with FastAPI, designed for eBay-compatible product fields including item specifics, images, SKU, etc.

## Features

- **POST /products** — Submit a single product (returns 201)
- **POST /products/bulk** — Submit up to 100 products at once
- **PUT /products/{id}** — Update product by ID
- **PUT /products/sku/{sku}** — Update product by SKU
- **JWT Authentication** — Register/login to get a Bearer token
- **Rate Limiting** — 100 requests/minute per IP (configurable)
- **CORS** — Configurable allowed origins
- **Swagger Docs** — Auto-generated at `/docs`
- **ReDoc** — Alternative docs at `/redoc`

## Product Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| sku | string | Yes | Unique product identifier |
| title | string | Yes | Product title (max 500 chars) |
| description | string | No | HTML description |
| price | float | Yes | Price (must be > 0) |
| currency | string | No | Currency code (default: GBP) |
| quantity | int | No | Stock level (default: 0) |
| images | array | No | Up to 24 image URLs |
| category | string | No | Product category path |
| item_specifics | object | No | eBay item specifics (key-value pairs) |
| condition | string | No | Item condition (default: New) |
| brand | string | No | Brand name |
| mpn | string | No | Manufacturer Part Number |
| ean | string | No | EAN/barcode |
| weight | float | No | Weight in kg |

## Quick Start

### Option 1: Docker Compose (recommended)

```bash
docker-compose up --build
```

API will be available at `http://localhost:8000`

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables (copy .env.example to .env and edit)
cp .env.example .env

# Run the API
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_URL | postgresql+asyncpg://postgres:password@localhost:5432/products_api | PostgreSQL connection string |
| SECRET_KEY | change-this-in-production | JWT signing key |
| ALGORITHM | HS256 | JWT algorithm |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | Token expiry |
| RATE_LIMIT | 100/minute | Rate limit per IP |
| CORS_ORIGINS | ["http://localhost:3000"] | Allowed CORS origins |

## Usage

### 1. Register / Login

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "myuser", "password": "mypassword123"}'

# Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

### 2. Submit a Product

```bash
curl -X POST http://localhost:8000/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "sku": "EBAY-001",
    "title": "Vintage Leather Jacket",
    "price": 149.99,
    "quantity": 5,
    "images": ["https://example.com/img1.jpg"],
    "item_specifics": {"Brand": "Levis", "Size": "L", "Color": "Brown"}
  }'
```

### 3. Bulk Upload

```bash
curl -X POST http://localhost:8000/products/bulk \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"products": [{"sku": "SKU-1", "title": "Item 1", "price": 10}, {"sku": "SKU-2", "title": "Item 2", "price": 20}]}'
```

## Running Tests

```bash
pip install aiosqlite  # needed for test SQLite backend
pytest tests/ -v
```

## Deployment

### Production with Docker

```bash
docker-compose -f docker-compose.yml up -d
```

### Production with systemd

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json
