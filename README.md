# Ofis.az Web Scraper

A Python web scraper for extracting real estate listings from ofis.az, including property details and contact phone numbers.

## Features

- **Pagination Support**: Scrapes multiple pages using the `start` parameter
- **Detailed Property Data**: Extracts comprehensive information including:
  - Title, category, price
  - Location (city, region, metro station)
  - Property details (rooms, area, floor)
  - Full description
  - Multiple images
  - Contact information
- **AJAX Phone Fetching**: Retrieves hidden phone numbers via AJAX calls
- **Multiple Export Formats**: Saves data to both JSON and CSV

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage (Synchronous)

Run the synchronous scraper with default settings (5 pages):
```bash
python scraper.py
```

### Async Usage (Faster - Recommended)

Run the async scraper with concurrent processing:
```bash
python scraper_async.py
```

The async version processes multiple listings concurrently (default: 5 concurrent requests), making it significantly faster than the synchronous version.

### Custom Usage (Synchronous)

```python
from scraper import OfisScraper

scraper = OfisScraper()

# Scrape 10 pages with 3 second delay between requests
listings = scraper.scrape_all_listings(max_pages=10, delay=3.0)

# Save to JSON
scraper.save_to_json(listings, 'my_listings.json')

# Save to CSV
scraper.save_to_csv(listings, 'my_listings.csv')
```

### Custom Usage (Async)

```python
import asyncio
from scraper_async import OfisScraperAsync

async def run():
    # Create scraper with max 10 concurrent requests
    scraper = OfisScraperAsync(max_concurrent=10)

    # Scrape 10 pages
    listings = await scraper.scrape_all_listings(max_pages=10)

    # Save to JSON
    scraper.save_to_json(listings, 'my_listings.json')

    # Save to CSV
    scraper.save_to_csv(listings, 'my_listings.csv')

asyncio.run(run())
```

### Scrape Single Listing (Async)

```python
import asyncio
import aiohttp
from scraper_async import OfisScraperAsync

async def scrape_single():
    scraper = OfisScraperAsync()

    async with aiohttp.ClientSession() as session:
        # Get details from specific URL
        details = await scraper.get_listing_details(
            session,
            'https://ofis.az/hezi-aslanov-kiraye-ev-211360.html'
        )

        # Get phone number
        if details and 'ajax_data' in details:
            ajax = details['ajax_data']
            phone = await scraper.get_phone_number(
                session,
                ajax['id'],
                ajax['t'],
                ajax['h'],
                ajax['rf']
            )
            print(f"Phone: {phone}")

asyncio.run(scrape_single())
```

## Data Structure

### Extracted Fields

- `listing_id`: Unique identifier
- `url`: Full URL to listing
- `title`: Short title
- `full_title`: Complete title with all details
- `category`: Property category and type
- `price`: Price information
- `listing_code`: Official listing code
- `Kateqoriya`: Property type (New building, Old building, etc.)
- `Şəhər`: City
- `Otaq Sayı`: Number of rooms
- `Mərtəbə`: Floor number
- `Mərtəbə sayı`: Total floors
- `Sahə`: Area in m²
- `Ünvan`: Address
- `Qiymət`: Price
- `description`: Full property description
- `contact_name`: Contact person name
- `phone`: Phone number (fetched via AJAX)
- `images`: List of all image URLs
- `date`: Listing date

## Output Files

- `ofis_listings.json`: Complete data in JSON format (includes images array)
- `ofis_listings.csv`: Simplified data in CSV format (excludes complex fields)

## Configuration

### Adjust Concurrency (Async Version)

Control how many requests run simultaneously:

```python
scraper = OfisScraperAsync(max_concurrent=5)  # Max 5 concurrent requests
```

### Adjust Delay Between Requests (Sync Version)

To be respectful to the server, adjust the delay parameter:

```python
listings = scraper.scrape_all_listings(max_pages=5, delay=2.0)  # 2 seconds between requests
```

### Adjust Number of Pages

The pagination uses `start` parameter incremented by 4:
- Page 1: start=0
- Page 2: start=4
- Page 3: start=8
- etc.

```python
listings = scraper.scrape_all_listings(max_pages=20, delay=2.0)  # Scrape 20 pages
```

## Important Notes

1. **Performance**:
   - **Async version** (recommended): Uses `asyncio` and `aiohttp` for concurrent requests, significantly faster
   - **Sync version**: Traditional sequential processing with delays
2. **Rate Limiting**:
   - Async version uses semaphore to limit concurrent requests (default: 5)
   - Sync version includes delays between requests
3. **Headers**: Proper headers are set to mimic a real browser
4. **Error Handling**: Includes try-catch blocks for robust operation
5. **Phone Numbers**: Fetched via separate AJAX calls using the listing's unique hash
6. **Images**: Full-size image URLs are extracted from the slider

## Example Output

```json
{
  "listing_id": "211360",
  "url": "https://ofis.az/hezi-aslanov-kiraye-ev-211360.html",
  "title": "Xətai r., Həzi Aslanov m.",
  "category": "Yeni tikili, Kirayə Verilir, 1 otaq, 55 m²",
  "price": "550 Azn/ Ay",
  "full_title": "Yeni tikili Kirayə Verilir , Xətai r., Həzi Aslanov m., 1 otaq, 55 m²",
  "listing_code": "Elan kodu: 211360",
  "phone": "0515810068",
  "description": "Gence Prospekti Serhed Qosunlarinin yaxinliginda 1 otaqli metbex studiya ev...",
  "contact_name": "Hesen",
  "images": [
    "https://ofis.az/uploads/news/ofis_1759088300507668d98eac959f5.jpeg",
    "https://ofis.az/uploads/news/ofis_1759088300104268d98eac7639d.jpeg"
  ]
}
```

## License

This scraper is for educational purposes only. Please respect ofis.az's terms of service and robots.txt.