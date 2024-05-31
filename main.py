from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
from bs4 import BeautifulSoup
import json
import os
from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
import time

# FastAPI setup
app = FastAPI()

# Authentication setup
security = HTTPBearer()
STATIC_TOKEN = "your_static_token_here"

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != STATIC_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

# Redis setup
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Database setup
DATABASE_URL = "sqlite:///./scraped_data.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    price = Column(Float)
    image_path = Column(String)

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class ScrapedProduct(BaseModel):
    product_title: str
    product_price: float
    path_to_image: str

class Scraper:
    def __init__(self, base_url: str, page_limit: Optional[int] = None, proxy: Optional[str] = None):
        self.base_url = base_url
        self.page_limit = page_limit
        self.proxy = proxy
        self.session = httpx.Client(proxies={"http": proxy, "https": proxy} if proxy else None)

    def fetch_page(self, page_number: int):
        url = f"{self.base_url}?page={page_number}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            print(f"Failed to fetch page {page_number}: {e}")
            time.sleep(5)  # Retry after 5 seconds
            return self.fetch_page(page_number)

    def scrape_page(self, page_content: str) -> List[ScrapedProduct]:
        soup = BeautifulSoup(page_content, "html.parser")
        products = []
        for product_div in soup.find_all("div", class_="product-inner"):
            title = product_div.find("h2", class_="woo-loop-product__title").text
            price_str = product_div.find("span", class_="woocommerce-Price-amount").text
            price = self.convert_price_to_float(price_str)
            image_url = product_div.find("img", class_="attachment-woocommerce_thumbnail")["src"]
            image_path = self.download_image(image_url)
            products.append(ScrapedProduct(product_title=title, product_price=price, path_to_image=image_path))
        return products
    
    def convert_price_to_float(self, price_str: str) -> float:
        cleaned_price_str = price_str.replace('₹', '').replace(',', '').strip()
        return float(cleaned_price_str)

    def download_image(self, url: str) -> str:
        response = self.session.get(url)
        image_name = url.split("/")[-1]
        image_path = os.path.join("images", image_name)
        with open(image_path, "wb") as file:
            file.write(response.content)
        return image_path

    def scrape(self) -> List[ScrapedProduct]:
        all_products = []
        for page in range(1, self.page_limit + 1):
            page_content = self.fetch_page(page)
            products = self.scrape_page(page_content)
            all_products.extend(products)
        return all_products

# Initialize and use the scraper
@app.post("/scrape", dependencies=[Depends(get_current_user)])
def scrape_data(page_limit: Optional[int] = Query(None), proxy: Optional[str] = Query(None)):
    scraper = Scraper("https://dentalstall.com/shop/", page_limit=page_limit, proxy=proxy)
    products = scraper.scrape()

    db = SessionLocal()
    new_products_count = 0

    for product in products:
        # Check cache for existing product details
        cached_product = redis_client.get(product.product_title)
        
        if cached_product:
            cached_product = json.loads(cached_product)
            if cached_product["product_price"] == product.product_price:
                # If the price hasn't changed, skip updating this product
                continue

        # Update or add the product in the database
        db_product = db.query(Product).filter_by(title=product.product_title).first()
        if db_product:
            db_product.price = product.product_price
            db_product.image_path = product.path_to_image
        else:
            db_product = Product(
                title=product.product_title,
                price=product.product_price,
                image_path=product.path_to_image,
            )
            db.add(db_product)
            new_products_count += 1

        # Update cache with new product details
        redis_client.set(product.product_title, json.dumps(product.dict()))

    db.commit()
    db.close()

    # Store in JSON file
    with open("scraped_data.json", "w") as file:
        json.dump([product.dict() for product in products], file)

    # Notify via console
    print(f"Scraped and updated {new_products_count} new products")

    return {"status": "success", "products_scraped": new_products_count}
