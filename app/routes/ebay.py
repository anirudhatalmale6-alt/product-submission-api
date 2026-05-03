import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Product, User
from app.auth import get_current_user
from app.services.ebay_client import ebay_client
from app.schemas import ProductResponse

router = APIRouter(prefix="/ebay", tags=["eBay Listing"])


class EbayListingConfig(BaseModel):
    marketplace_id: str = Field("EBAY_GB", description="eBay marketplace (EBAY_GB, EBAY_US, EBAY_AU, etc.)")
    category_id: str = Field(..., description="eBay category ID for the listing")
    currency: str = Field("GBP", description="Currency code")
    fulfillment_policy_id: Optional[str] = Field(None, description="Fulfillment (shipping) policy ID")
    payment_policy_id: Optional[str] = Field(None, description="Payment policy ID")
    return_policy_id: Optional[str] = Field(None, description="Return policy ID")
    listing_format: str = Field("FIXED_PRICE", description="FIXED_PRICE or AUCTION")
    condition: str = Field("NEW", description="Item condition (NEW, USED_EXCELLENT, etc.)")
    merchant_location_key: str = Field("uk-warehouse", description="Merchant location key for ship-from location")


class BulkListConfig(BaseModel):
    product_ids: List[int] = Field(..., description="List of product IDs to list on eBay")
    marketplace_id: str = Field("EBAY_GB")
    category_id: str = Field(..., description="eBay category ID")
    currency: str = Field("GBP")
    fulfillment_policy_id: Optional[str] = None
    payment_policy_id: Optional[str] = None
    return_policy_id: Optional[str] = None
    condition: str = Field("NEW")
    merchant_location_key: str = Field("uk-warehouse")


@router.get("/category-suggestions")
async def get_category_suggestions(
    query: str = Query(..., description="Product name/keywords to get category suggestions"),
    current_user: User = Depends(get_current_user),
):
    """Get eBay category suggestions for a product. Use the returned category_id when listing."""
    result = await ebay_client.get_category_suggestions(query)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail="Failed to get eBay categories")

    suggestions = result["data"].get("categorySuggestions", [])
    return {
        "suggestions": [
            {
                "category_id": s["category"]["categoryId"],
                "category_name": s["category"]["categoryName"],
                "category_path": " > ".join(
                    [a["categoryName"] for a in s.get("categoryTreeNodeAncestors", [])]
                ),
            }
            for s in suggestions[:10]
        ]
    }


@router.post("/list/{product_id}")
async def list_product_on_ebay(
    product_id: int,
    config: EbayListingConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Push a product from your database to eBay as a live listing."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in database")

    aspects = {}
    if product.item_specifics:
        for key, value in product.item_specifics.items():
            aspects[key] = [str(value)] if not isinstance(value, list) else value
    if product.brand:
        aspects["Brand"] = [product.brand]

    inventory_data = {
        "product": {
            "title": product.title[:80],
            "description": product.description or product.title,
            "aspects": aspects,
            "imageUrls": product.images[:12] if product.images else [],
        },
        "condition": config.condition,
        "availability": {
            "shipToLocationAvailability": {
                "quantity": product.quantity,
            }
        },
    }

    if product.ean:
        inventory_data["product"]["ean"] = [product.ean]
    if product.mpn:
        inventory_data["product"]["mpn"] = product.mpn

    inv_result = await ebay_client.create_or_update_inventory_item(product.sku, inventory_data)
    if not inv_result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=f"Failed to create eBay inventory item: {inv_result.get('errors')}",
        )

    offer_data = {
        "sku": product.sku,
        "marketplaceId": config.marketplace_id,
        "format": config.listing_format,
        "categoryId": config.category_id,
        "merchantLocationKey": config.merchant_location_key,
        "listingPolicies": {},
        "pricingSummary": {
            "price": {
                "value": str(product.price),
                "currency": config.currency,
            }
        },
    }

    if config.fulfillment_policy_id:
        offer_data["listingPolicies"]["fulfillmentPolicyId"] = config.fulfillment_policy_id
    if config.payment_policy_id:
        offer_data["listingPolicies"]["paymentPolicyId"] = config.payment_policy_id
    if config.return_policy_id:
        offer_data["listingPolicies"]["returnPolicyId"] = config.return_policy_id

    offer_result = await ebay_client.create_offer(offer_data)
    if not offer_result.get("success"):
        return {
            "status": "inventory_created",
            "message": "Inventory item created on eBay but offer creation failed. You may need to set up business policies on eBay first.",
            "sku": product.sku,
            "inventory_status": "success",
            "offer_error": offer_result.get("errors"),
        }

    offer_id = offer_result["data"].get("offerId")

    publish_result = await ebay_client.publish_offer(offer_id)
    if not publish_result.get("success"):
        return {
            "status": "offer_created",
            "message": "Offer created but publish failed. May need seller verification.",
            "sku": product.sku,
            "offer_id": offer_id,
            "publish_error": publish_result.get("errors"),
        }

    return {
        "status": "listed",
        "message": "Product successfully listed on eBay!",
        "sku": product.sku,
        "offer_id": offer_id,
        "listing_id": publish_result["data"].get("listingId"),
        "ebay_url": f"https://www.ebay.co.uk/itm/{publish_result['data'].get('listingId')}",
    }


@router.post("/list/bulk")
async def bulk_list_on_ebay(
    config: BulkListConfig,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List multiple products on eBay at once."""
    results = {"successful": 0, "failed": 0, "listings": [], "errors": []}

    for product_id in config.product_ids[:20]:
        result = await db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            results["errors"].append({"product_id": product_id, "error": "Not found"})
            results["failed"] += 1
            continue

        try:
            aspects = {}
            if product.item_specifics:
                for key, value in product.item_specifics.items():
                    aspects[key] = [str(value)] if not isinstance(value, list) else value

            inventory_data = {
                "product": {
                    "title": product.title[:80],
                    "description": product.description or product.title,
                    "aspects": aspects,
                    "imageUrls": product.images[:12] if product.images else [],
                },
                "condition": config.condition,
                "availability": {
                    "shipToLocationAvailability": {"quantity": product.quantity}
                },
            }

            inv_result = await ebay_client.create_or_update_inventory_item(product.sku, inventory_data)
            if not inv_result.get("success"):
                results["errors"].append({"product_id": product_id, "sku": product.sku, "error": str(inv_result.get("errors"))})
                results["failed"] += 1
                continue

            offer_data = {
                "sku": product.sku,
                "marketplaceId": config.marketplace_id,
                "format": "FIXED_PRICE",
                "categoryId": config.category_id,
                "merchantLocationKey": config.merchant_location_key,
                "listingPolicies": {},
                "pricingSummary": {
                    "price": {"value": str(product.price), "currency": config.currency}
                },
            }
            if config.fulfillment_policy_id:
                offer_data["listingPolicies"]["fulfillmentPolicyId"] = config.fulfillment_policy_id
            if config.payment_policy_id:
                offer_data["listingPolicies"]["paymentPolicyId"] = config.payment_policy_id
            if config.return_policy_id:
                offer_data["listingPolicies"]["returnPolicyId"] = config.return_policy_id

            offer_result = await ebay_client.create_offer(offer_data)
            if not offer_result.get("success"):
                results["errors"].append({"product_id": product_id, "sku": product.sku, "error": "Offer creation failed", "details": offer_result.get("errors")})
                results["failed"] += 1
                continue

            offer_id = offer_result["data"].get("offerId")
            publish_result = await ebay_client.publish_offer(offer_id)

            if publish_result.get("success"):
                results["successful"] += 1
                results["listings"].append({
                    "product_id": product_id,
                    "sku": product.sku,
                    "listing_id": publish_result["data"].get("listingId"),
                })
            else:
                results["errors"].append({"product_id": product_id, "sku": product.sku, "error": "Publish failed", "details": publish_result.get("errors")})
                results["failed"] += 1

        except Exception as e:
            results["errors"].append({"product_id": product_id, "error": str(e)})
            results["failed"] += 1

    return results


@router.get("/inventory/{sku}")
async def get_ebay_inventory_item(
    sku: str,
    current_user: User = Depends(get_current_user),
):
    """Check if a product exists in eBay inventory."""
    result = await ebay_client.get_inventory_item(sku)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=f"SKU '{sku}' not found in eBay inventory")
    return result["data"]


@router.delete("/inventory/{sku}")
async def delete_ebay_inventory_item(
    sku: str,
    current_user: User = Depends(get_current_user),
):
    """Remove a product from eBay inventory."""
    result = await ebay_client.delete_inventory_item(sku)
    if not result.get("success"):
        raise HTTPException(status_code=502, detail="Failed to delete eBay inventory item")
    return {"message": f"SKU '{sku}' removed from eBay inventory"}


@router.get("/policies")
async def get_ebay_policies(
    current_user: User = Depends(get_current_user),
):
    """Get your eBay business policies (fulfillment, payment, return). Needed for listing."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {ebay_client.user_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        fulfillment = await client.get(
            f"{ebay_client.BASE_URL}/sell/account/v1/fulfillment_policy?marketplace_id=EBAY_GB",
            headers=headers,
        )
        payment = await client.get(
            f"{ebay_client.BASE_URL}/sell/account/v1/payment_policy?marketplace_id=EBAY_GB",
            headers=headers,
        )
        return_pol = await client.get(
            f"{ebay_client.BASE_URL}/sell/account/v1/return_policy?marketplace_id=EBAY_GB",
            headers=headers,
        )

    return {
        "fulfillment_policies": fulfillment.json() if fulfillment.status_code == 200 else {"error": fulfillment.status_code},
        "payment_policies": payment.json() if payment.status_code == 200 else {"error": payment.status_code},
        "return_policies": return_pol.json() if return_pol.status_code == 200 else {"error": return_pol.status_code},
    }
