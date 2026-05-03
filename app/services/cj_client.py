import httpx
from typing import Optional, Dict, Any

from app.config import settings


class CJClient:
    BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"

    def __init__(self):
        self.api_key = settings.cj_api_key
        self.access_token: Optional[str] = None

    async def _get_access_token(self) -> str:
        if self.access_token:
            return self.access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.BASE_URL}/authentication/getAccessToken",
                json={"apiKey": self.api_key},
            )
            data = response.json()
            if data.get("result"):
                self.access_token = data["data"]["accessToken"]
                return self.access_token
            raise Exception(f"Failed to get CJ access token: {data.get('message')}")

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        token = await self._get_access_token()
        headers = {"CJ-Access-Token": token, "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method, f"{self.BASE_URL}{endpoint}", headers=headers, **kwargs
            )
            data = response.json()

            if data.get("code") == 1600001:
                self.access_token = None
                token = await self._get_access_token()
                headers["CJ-Access-Token"] = token
                response = await client.request(
                    method, f"{self.BASE_URL}{endpoint}", headers=headers, **kwargs
                )
                data = response.json()

            return data

    async def search_products(
        self,
        keyword: Optional[str] = None,
        category_id: Optional[str] = None,
        page_num: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        params = {"pageNum": page_num, "pageSize": page_size}
        if keyword:
            params["productNameEn"] = keyword
        if category_id:
            params["categoryId"] = category_id
        return await self._request("GET", "/product/list", params=params)

    async def get_product_detail(self, pid: str) -> Dict[str, Any]:
        return await self._request("GET", f"/product/query", params={"pid": pid})

    async def get_product_variants(self, pid: str) -> Dict[str, Any]:
        return await self._request("GET", f"/product/variant/query", params={"pid": pid})

    async def get_categories(self) -> Dict[str, Any]:
        return await self._request("GET", "/product/getCategory")


cj_client = CJClient()
