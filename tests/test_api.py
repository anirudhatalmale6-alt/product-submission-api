import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_token(client):
    response = await client.post("/auth/register", json={
        "username": "testuser",
        "password": "testpassword123"
    })
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_register(client):
    response = await client.post("/auth/register", json={
        "username": "newuser",
        "password": "securepass123"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/register", json={
        "username": "loginuser",
        "password": "securepass123"
    })
    response = await client.post("/auth/login", json={
        "username": "loginuser",
        "password": "securepass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_create_product(client, auth_token):
    response = await client.post(
        "/products",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "sku": "TEST-001",
            "title": "Test Product",
            "price": 29.99,
            "quantity": 10,
            "images": ["https://example.com/img1.jpg"],
            "item_specifics": {"Color": "Red", "Size": "Large"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["title"] == "Test Product"
    assert data["price"] == 29.99
    assert data["item_specifics"]["Color"] == "Red"


@pytest.mark.asyncio
async def test_create_product_duplicate_sku(client, auth_token):
    product = {
        "sku": "DUP-001",
        "title": "First Product",
        "price": 19.99,
    }
    await client.post("/products", headers={"Authorization": f"Bearer {auth_token}"}, json=product)
    response = await client.post("/products", headers={"Authorization": f"Bearer {auth_token}"}, json=product)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_product_validation_error(client, auth_token):
    response = await client.post(
        "/products",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "No SKU or price"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_product_unauthorized(client):
    response = await client.post("/products", json={
        "sku": "UNAUTH-001",
        "title": "Unauthorized",
        "price": 9.99,
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bulk_create(client, auth_token):
    products = [
        {"sku": f"BULK-{i:03d}", "title": f"Bulk Product {i}", "price": 10.0 + i}
        for i in range(5)
    ]
    response = await client.post(
        "/products/bulk",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"products": products},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["successful"] == 5
    assert data["failed"] == 0


@pytest.mark.asyncio
async def test_update_product(client, auth_token):
    create_resp = await client.post(
        "/products",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"sku": "UPD-001", "title": "Original", "price": 50.0},
    )
    product_id = create_resp.json()["id"]

    response = await client.put(
        f"/products/{product_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"title": "Updated Title", "price": 75.0},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    assert response.json()["price"] == 75.0
