import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
import csv
from typing import Dict, List, Optional
from urllib.parse import urljoin


class OfisScraperAsync:
    def __init__(self, max_concurrent: int = 5):
        self.base_url = "https://ofis.az"
        self.max_concurrent = max_concurrent
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'DNT': '1',
            'Accept-Encoding': 'gzip, deflate, br'
        }

    async def get_listings_from_page(self, session: aiohttp.ClientSession, start: int = 0) -> List[Dict]:
        """Fetch listings from a paginated page"""
        url = f"{self.base_url}/homelist/?start={start}"

        headers = {
            **self.headers,
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }

        try:
            async with session.post(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                text = await response.text()

                soup = BeautifulSoup(text, 'html.parser')
                listings = []

                # Parse each listing
                for listing in soup.find_all('div', class_='nobj prod'):
                    listing_data = self._parse_listing_preview(listing)
                    if listing_data:
                        listings.append(listing_data)

                return listings
        except Exception as e:
            print(f"Error fetching page {start}: {e}")
            return []

    def _parse_listing_preview(self, listing_elem) -> Optional[Dict]:
        """Parse a single listing preview from the list page"""
        try:
            link_elem = listing_elem.find('a', href=True)
            if not link_elem:
                return None

            listing_url = urljoin(self.base_url, link_elem['href'])

            # Extract listing ID from URL
            listing_id = listing_url.split('-')[-1].replace('.html', '')

            title_elem = listing_elem.find('b')
            title = title_elem.text.strip() if title_elem else ''

            category_elem = listing_elem.find('small', class_='catshwopen')
            category = category_elem.text.strip().replace('\n', ' ') if category_elem else ''

            price_elem = listing_elem.find('span', class_='sprice')
            price = price_elem.text.strip() if price_elem else ''

            img_elem = listing_elem.find('img')
            image_url = urljoin(self.base_url, img_elem['src']) if img_elem and img_elem.get('src') else ''

            return {
                'listing_id': listing_id,
                'url': listing_url,
                'title': title,
                'category': category,
                'price': price,
                'image_url': image_url
            }
        except Exception as e:
            print(f"Error parsing listing preview: {e}")
            return None

    async def get_listing_details(self, session: aiohttp.ClientSession, listing_url: str) -> Optional[Dict]:
        """Fetch detailed information from individual listing page"""
        try:
            async with session.get(listing_url, headers=self.headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                text = await response.text()

                soup = BeautifulSoup(text, 'html.parser')
                details = {}

                # Get listing ID and code
                code_elem = soup.find('span', class_='open_idshow')
                if code_elem:
                    details['listing_code'] = code_elem.text.strip()

                # Get title
                h1_elem = soup.find('h1')
                if h1_elem:
                    details['full_title'] = h1_elem.text.strip()

                # Get all property details
                article = soup.find('article')
                if article:
                    # Extract all paragraph data
                    for p in article.find_all('p'):
                        text = p.get_text(strip=True)
                        if text:
                            # Parse key-value pairs
                            if p.find('b'):
                                key = p.find('b').text.strip()
                                # Get value after the bold tag
                                value = ''.join([str(c) for c in p.contents if str(c) != str(p.find('b'))]).strip()
                                details[key] = value

                    # Get full description
                    desc_elem = article.find('p', class_='infop100 fullteshow')
                    if desc_elem:
                        details['description'] = desc_elem.text.strip()

                    # Get contact info
                    contact_elem = article.find('div', class_='infocontact')
                    if contact_elem:
                        name_elem = contact_elem.find('span', class_='glyphicon-user')
                        if name_elem and name_elem.next_sibling:
                            details['contact_name'] = name_elem.next_sibling.strip()

                    # Get date
                    date_elem = article.find('span', class_='viewsbb')
                    if date_elem:
                        details['date'] = date_elem.text.strip()

                    # Get images
                    images = []
                    pic_area = soup.find('div', id='picsopen')
                    if pic_area:
                        for img_link in pic_area.find_all('a', rel='slider'):
                            img_url = img_link.get('href')
                            if img_url:
                                images.append(urljoin(self.base_url, img_url))
                    details['images'] = images

                    # Get phone data attributes for AJAX call
                    telshow_elem = soup.find('div', id='telshow')
                    if telshow_elem:
                        details['ajax_data'] = {
                            'id': telshow_elem.get('data-id'),
                            't': telshow_elem.get('data-t'),
                            'h': telshow_elem.get('data-h'),
                            'rf': telshow_elem.get('data-rf')
                        }

                return details
        except Exception as e:
            print(f"Error fetching listing details from {listing_url}: {e}")
            return None

    async def get_phone_number(self, session: aiohttp.ClientSession, listing_id: str, data_t: str, data_h: str, data_rf: str) -> Optional[str]:
        """Fetch phone number via AJAX call"""
        url = f"{self.base_url}/ajax.php"

        headers = {
            **self.headers,
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.base_url,
            'Referer': f'{self.base_url}/',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }

        payload = {
            'act': 'telshow',
            'id': listing_id,
            't': data_t,
            'h': data_h,
            'rf': data_rf
        }

        try:
            async with session.post(url, headers=headers, data=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get('ok') == 1:
                    return data.get('tel')
                else:
                    print(f"Phone fetch failed for listing {listing_id}: {data}")
                    return None
        except Exception as e:
            print(f"Error fetching phone for listing {listing_id}: {e}")
            return None

    async def process_listing(self, session: aiohttp.ClientSession, listing: Dict) -> Optional[Dict]:
        """Process a single listing: get details and phone number"""
        print(f"  Processing listing: {listing['url']}")

        # Get detailed information
        details = await self.get_listing_details(session, listing['url'])

        if details:
            # Merge preview and detail data
            full_data = {**listing, **details}

            # Get phone number if AJAX data available
            if 'ajax_data' in full_data and full_data['ajax_data'].get('id'):
                ajax = full_data['ajax_data']
                phone = await self.get_phone_number(
                    session,
                    ajax['id'],
                    ajax.get('t', 'product'),
                    ajax['h'],
                    ajax.get('rf', '')
                )
                full_data['phone'] = phone
                print(f"    Phone: {phone}")

            return full_data

        return None

    async def scrape_page(self, session: aiohttp.ClientSession, start: int) -> List[Dict]:
        """Scrape a single page and process all its listings"""
        print(f"Scraping page (start={start})...")

        # Get listings from current page
        listings = await self.get_listings_from_page(session, start)

        if not listings:
            print(f"No more listings found at start={start}")
            return []

        print(f"Found {len(listings)} listings on this page")

        # Process listings with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(listing):
            async with semaphore:
                return await self.process_listing(session, listing)

        # Process all listings concurrently
        tasks = [process_with_semaphore(listing) for listing in listings]
        results = await asyncio.gather(*tasks)

        # Filter out None results
        return [r for r in results if r is not None]

    async def scrape_all_listings(self, max_pages: int = 10) -> List[Dict]:
        """Scrape all listings with pagination"""
        all_data = []

        # Create a single session for all requests
        connector = aiohttp.TCPConnector(limit_per_host=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Process pages sequentially (but listings within each page concurrently)
            for page in range(max_pages):
                start = page * 4

                page_data = await self.scrape_page(session, start)

                if not page_data:
                    break

                all_data.extend(page_data)

                # Small delay between pages
                if page < max_pages - 1:
                    await asyncio.sleep(1)

        return all_data

    def save_to_json(self, data: List[Dict], filename: str = 'ofis_listings.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")

    def save_to_csv(self, data: List[Dict], filename: str = 'ofis_listings.csv'):
        """Save scraped data to CSV file"""
        if not data:
            print("No data to save")
            return

        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())

        # Remove complex fields for CSV
        simple_keys = [k for k in all_keys if k not in ['images', 'ajax_data']]

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(simple_keys))
            writer.writeheader()

            for item in data:
                # Create simplified row
                row = {k: v for k, v in item.items() if k in simple_keys}
                writer.writerow(row)

        print(f"Data saved to {filename}")


async def main():
    scraper = OfisScraperAsync(max_concurrent=5)

    # Scrape first 5 pages (start=0, 4, 8, 12, 16)
    # Listings within each page are processed concurrently
    listings = await scraper.scrape_all_listings(max_pages=5)

    print(f"\nTotal listings scraped: {len(listings)}")

    # Save to both JSON and CSV
    scraper.save_to_json(listings)
    scraper.save_to_csv(listings)

    print("\nScraping completed!")


if __name__ == "__main__":
    asyncio.run(main())