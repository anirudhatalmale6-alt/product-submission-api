from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.database import get_db
from app.models import Product, User
from app.auth import get_current_user
from app.services.cj_client import cj_client
from app.schemas import ProductResponse

router = APIRouter(prefix="/cj", tags=["CJ Dropshipping"])


@router.get("/products/search")
async def search_cj_products(
    keyword: Optional[str] = Query(None, description="Search keyword"),
    category_id: Optional[str] = Query(None, description="CJ category ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=50, description="Results per page"),
    current_user: User = Depends(get_current_user),
):
    """Search CJ Dropshipping product catalog."""
    result = await cj_client.search_products(
        keyword=keyword, category_id=category_id, page_num=page, page_size=page_size
    )
    if not result.get("result"):
        raise HTTPException(status_code=502, detail=f"CJ API error: {result.get('message')}")

    products = result.get("data", {}).get("list", [])
    return {
        "total": result["data"].get("total", 0),
        "page": page,
        "page_size": page_size,
        "products": [
            {
                "cj_pid": p.get("pid"),
                "title": p.get("productNameEn") or p.get("productName"),
                "sku": p.get("productSku"),
                "image": p.get("productImage"),
                "price": p.get("sellPrice"),
                "category": p.get("categoryName"),
                "weight": p.get("productWeight"),
            }
            for p in products
        ],
    }


@router.get("/products/{pid}")
async def get_cj_product_detail(
    pid: str,
    current_user: User = Depends(get_current_user),
):
    """Get full details of a CJ product by its PID."""
    result = await cj_client.get_product_detail(pid)
    if not result.get("result"):
        raise HTTPException(status_code=502, detail=f"CJ API error: {result.get('message')}")
    return result.get("data")


@router.get("/categories")
async def get_cj_categories(
    current_user: User = Depends(get_current_user),
):
    """Get CJ Dropshipping product categories."""
    result = await cj_client.get_categories()
    if not result.get("result"):
        raise HTTPException(status_code=502, detail=f"CJ API error: {result.get('message')}")
    return result.get("data")


@router.post("/products/{pid}/import", response_model=ProductResponse, status_code=201)
async def import_cj_product(
    pid: str,
    price_markup: float = Query(2.0, ge=1.0, description="Price multiplier (e.g. 2.0 = double the CJ price)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import a CJ product into your database. Applies price markup automatically."""
    detail_result = await cj_client.get_product_detail(pid)
    if not detail_result.get("result"):
        raise HTTPException(status_code=502, detail=f"CJ API error: {detail_result.get('message')}")

    cj_product = detail_result.get("data")
    if not cj_product:
        raise HTTPException(status_code=404, detail="Product not found on CJ")

    sku = cj_product.get("productSku", f"CJ-{pid}")

    existing = await db.execute(select(Product).where(Product.sku == sku))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Product with SKU '{sku}' already imported")

    cj_price = float(cj_product.get("sellPrice", 0))
    images = []
    image_set = cj_product.get("productImageSet", [])
    if isinstance(image_set, list):
        for img in image_set:
            if isinstance(img, str) and img.startswith("http"):
                images.append(img)
    if not images and cj_product.get("productImage"):
        images.append(cj_product["productImage"])
    images = images[:24]

    variants = cj_product.get("variants", [])
    item_specifics = {}
    if variants:
        for v in variants[:1]:
            if v.get("variantProperty"):
                for prop in v["variantProperty"]:
                    item_specifics[prop.get("propertyName", "")] = prop.get("propertyValue", "")

    product = Product(
        sku=sku,
        title=cj_product.get("productNameEn") or cj_product.get("productName", ""),
        description=cj_product.get("description", ""),
        price=round(cj_price * price_markup, 2),
        currency="GBP",
        quantity=999,
        images=images,
        category=cj_product.get("categoryName", ""),
        item_specifics=item_specifics,
        condition="New",
        brand=cj_product.get("brandName"),
        weight=None,
    )
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.post("/products/import/bulk")
async def import_cj_products_bulk(
    pids: List[str],
    price_markup: float = Query(2.0, ge=1.0, description="Price multiplier"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import multiple CJ products by their PIDs."""
    results = {"successful": 0, "failed": 0, "products": [], "errors": []}

    for pid in pids[:50]:
        try:
            detail_result = await cj_client.get_product_detail(pid)
            if not detail_result.get("result"):
                results["errors"].append({"pid": pid, "error": detail_result.get("message")})
                results["failed"] += 1
                continue

            cj_product = detail_result.get("data")
            if not cj_product:
                results["errors"].append({"pid": pid, "error": "Not found"})
                results["failed"] += 1
                continue

            sku = cj_product.get("productSku", f"CJ-{pid}")
            existing = await db.execute(select(Product).where(Product.sku == sku))
            if existing.scalar_one_or_none():
                results["errors"].append({"pid": pid, "sku": sku, "error": "Already imported"})
                results["failed"] += 1
                continue

            cj_price = float(cj_product.get("sellPrice", 0))
            images = []
            if cj_product.get("productImage"):
                images.append(cj_product["productImage"])
            if cj_product.get("productImageSet"):
                images.extend(cj_product["productImageSet"][:23])

            product = Product(
                sku=sku,
                title=cj_product.get("productNameEn") or cj_product.get("productName", ""),
                description=cj_product.get("description", ""),
                price=round(cj_price * price_markup, 2),
                currency="GBP",
                quantity=999,
                images=images,
                category=cj_product.get("categoryName", ""),
                item_specifics={},
                condition="New",
            )
            db.add(product)
            await db.flush()
            results["successful"] += 1
            results["products"].append({"pid": pid, "sku": sku, "title": product.title})
        except Exception as e:
            results["errors"].append({"pid": pid, "error": str(e)})
            results["failed"] += 1

    await db.commit()
    return results
