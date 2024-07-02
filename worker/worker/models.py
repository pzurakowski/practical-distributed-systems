from pydantic import BaseModel
from typing import Literal

class ProductInfo(BaseModel):
    product_id: int
    brand_id: str
    category_id: str
    price: int

class UserTag(BaseModel):
    time: str
    cookie: str
    country: str
    device: Literal["PC", "MOBILE", "TV"]
    action: Literal["VIEW", "BUY"]
    origin: str
    product_info: ProductInfo