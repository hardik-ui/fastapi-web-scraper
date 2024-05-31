# FastAPI Web Scraper

This is a web scraping tool built using the FastAPI framework. It scrapes product information from a given e-commerce website and stores the data locally. The tool can scrape product names, prices, and images, and has configurable options for the number of pages to scrape and the use of a proxy server.

## Features

- Scrapes product name, price, and image from each page of the catalog.
- Supports limiting the number of pages to scrape.
- Supports using a proxy server for scraping.
- Stores the scraped data in a local SQLite database and as a JSON file.
- Implements simple authentication using a static token.
- Caches scraping results to avoid redundant updates.
- Notifies the scraping status in the console.

## Requirements

- Python 3.7+
- Redis server

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/hardik-ui/fastapi-web-scraper.git
    cd fastapi-web-scraper
    ```

2. **Create and activate a virtual environment:**

    ```sh
    python -m venv env
    source env/bin/activate  # On Windows use `.\env\Scripts\activate`
    ```

3. **Install dependencies:**

    ```sh
    pip install fastapi uvicorn httpx beautifulsoup4 sqlalchemy pydantic redis
    ```

4. **Set up Redis:**

    Ensure Redis is installed and running on your local machine. If not installed, follow the instructions based on your operating system.

    - **For macOS (using Homebrew):**
      ```sh
      brew install redis
      brew services start redis
      ```

    - **For Ubuntu/Debian:**
      ```sh
      sudo apt update
      sudo apt install redis-server
      sudo systemctl start redis
      ```

    - **For Windows:**
      Download Redis from the official website and follow the installation instructions.

5. **Create necessary directories and files:**

    ```sh
    mkdir images
    touch scraped_data.db
    ```

## Configuration

- **Static Token:** Replace `your_static_token_here` in the code with your actual static token for authentication.

## Running the Application

1. **Start the FastAPI application:**

    ```sh
    uvicorn main:app --reload
    ```

2. **Make a POST request to scrape data:**

    Use `curl`, Postman, or a Python script to send a request to the `/scrape` endpoint.

    ### Example Using `curl`:

    ```sh
    curl -X POST "http://127.0.0.1:8000/scrape?page_limit=5" -H "Authorization: Bearer your_static_token_here" -H "Content-Type: application/json" -d ""
    ```

    Replace `your_static_token_here` with your actual static token.

    ### Example Using Python:

    ```python
    import requests

    url = "http://127.0.0.1:8000/scrape"
    headers = {
        "Authorization": "Bearer your_static_token_here"
    }
    params = {
        "page_limit": 5,
        "proxy": None  # Replace with your proxy if needed
    }

    response = requests.post(url, headers=headers, params=params)
    print(response.json())
    ```

## Code Overview

### `main.py`

This is the main file that contains the FastAPI application, database models, and the web scraper logic.

- **Dependencies:** Import necessary packages.
- **FastAPI Setup:** Initialize the FastAPI application and set up authentication.
- **Redis Setup:** Initialize Redis for caching.
- **Database Setup:** Set up SQLite database using SQLAlchemy.
- **Scraper Class:** Define the scraper class to fetch and parse data from the target website.
- **API Endpoint:** Define the `/scrape` endpoint to trigger the scraping process.

### Additional Notes

- **Ensure Redis is running** before starting the application.
- **Error Handling:** The application includes basic error handling and retries for network requests.
- **Production:** For a production environment, consider deploying the application using a production-grade ASGI server like `uvicorn` or `daphne`.
