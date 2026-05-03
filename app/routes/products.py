from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Product, User
from app.schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    BulkProductCreate,
    BulkProductResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a single product. Returns 201 on success, 400 on validation error, 409 if SKU exists."""
    result = await db.execute(select(Product).where(Product.sku == product_data.sku))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Product with SKU '{product_data.sku}' already exists")

    product = Product(**product_data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.post("/bulk", response_model=BulkProductResponse, status_code=status.HTTP_201_CREATED)
async def create_products_bulk(
    bulk_data: BulkProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit up to 100 products in a single request. Partial success is possible."""
    successful_products = []
    errors = []

    for idx, product_data in enumerate(bulk_data.products):
        try:
            result = await db.execute(select(Product).where(Product.sku == product_data.sku))
            if result.scalar_one_or_none():
                errors.append({"index": idx, "sku": product_data.sku, "error": "SKU already exists"})
                continue

            product = Product(**product_data.model_dump())
            db.add(product)
            await db.flush()
            successful_products.append(product)
        except Exception as e:
            errors.append({"index": idx, "sku": product_data.sku, "error": str(e)})

    await db.commit()
    for p in successful_products:
        await db.refresh(p)

    return BulkProductResponse(
        successful=len(successful_products),
        failed=len(errors),
        products=successful_products,
        errors=errors,
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing product by ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_data.model_dump(exclude_unset=True)
    if "sku" in update_data and update_data["sku"] != product.sku:
        existing = await db.execute(select(Product).where(Product.sku == update_data["sku"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"SKU '{update_data['sku']}' already in use")

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product


@router.put("/sku/{sku}", response_model=ProductResponse)
async def update_product_by_sku(
    sku: str,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing product by SKU."""
    result = await db.execute(select(Product).where(Product.sku == sku))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with SKU '{sku}' not found")

    update_data = product_data.model_dump(exclude_unset=True)
    if "sku" in update_data and update_data["sku"] != product.sku:
        existing = await db.execute(select(Product).where(Product.sku == update_data["sku"]))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail=f"SKU '{update_data['sku']}' already in use")

    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)
    return product
