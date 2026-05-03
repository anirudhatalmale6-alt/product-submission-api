import httpx
from typing import Optional, Dict, Any, List
from base64 import b64encode

from app.config import settings


class EbayClient:
    BASE_URL = "https://api.ebay.com"

    def __init__(self):
        self.app_id = settings.ebay_app_id
        self.cert_id = settings.ebay_cert_id
        self.dev_id = settings.ebay_dev_id
        self.user_token = settings.ebay_user_token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.user_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Content-Language": "en-GB",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, f"{self.BASE_URL}{endpoint}", headers=self._headers(), **kwargs
            )
            return response

    async def create_or_update_inventory_item(self, sku: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or replace an inventory item using the Inventory API."""
        response = await self._request(
            "PUT", f"/sell/inventory/v1/inventory_item/{sku}", json=product_data
        )
        if response.status_code in (200, 201, 204):
            return {"success": True, "status_code": response.status_code, "sku": sku}
        return {"success": False, "status_code": response.status_code, "errors": response.json()}

    async def create_offer(self, offer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create an offer (links inventory item to a listing)."""
        response = await self._request("POST", "/sell/inventory/v1/offer", json=offer_data)
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        return {"success": False, "status_code": response.status_code, "errors": response.json()}

    async def publish_offer(self, offer_id: str) -> Dict[str, Any]:
        """Publish an offer to make it a live eBay listing."""
        response = await self._request("POST", f"/sell/inventory/v1/offer/{offer_id}/publish")
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        return {"success": False, "status_code": response.status_code, "errors": response.json()}

    async def get_inventory_item(self, sku: str) -> Dict[str, Any]:
        """Get an inventory item by SKU."""
        response = await self._request("GET", f"/sell/inventory/v1/inventory_item/{sku}")
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {"success": False, "status_code": response.status_code}

    async def get_offers_by_sku(self, sku: str) -> Dict[str, Any]:
        """Get offers for an inventory item."""
        response = await self._request("GET", f"/sell/inventory/v1/offer?sku={sku}")
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {"success": False, "status_code": response.status_code, "errors": response.json()}

    async def delete_inventory_item(self, sku: str) -> Dict[str, Any]:
        """Delete an inventory item."""
        response = await self._request("DELETE", f"/sell/inventory/v1/inventory_item/{sku}")
        if response.status_code == 204:
            return {"success": True}
        return {"success": False, "status_code": response.status_code}

    async def get_category_suggestions(self, query: str, marketplace: str = "EBAY_GB") -> Dict[str, Any]:
        """Get eBay category suggestions for a product query."""
        response = await self._request(
            "GET",
            f"/commerce/taxonomy/v1/category_tree/3/get_category_suggestions",
            params={"q": query},
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        return {"success": False, "status_code": response.status_code}


ebay_client = EbayClient()
