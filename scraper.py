import requests
from bs4 import BeautifulSoup
import json
import time
import csv
from typing import Dict, List, Optional
from urllib.parse import urljoin

class OfisScraper:
    def __init__(self):
        self.base_url = "https://ofis.az"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8,ru;q=0.7,az;q=0.6',
            'DNT': '1',
            'Accept-Encoding': 'gzip, deflate, br, zstd'
        })

    def get_listings_from_page(self, start: int = 0) -> List[Dict]:
        """Fetch listings from a paginated page"""
        url = f"{self.base_url}/homelist/?start={start}"

        headers = {
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
            response = self.session.post(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
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

    def get_listing_details(self, listing_url: str) -> Optional[Dict]:
        """Fetch detailed information from individual listing page"""
        try:
            response = self.session.get(listing_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
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

    def get_phone_number(self, listing_id: str, data_t: str, data_h: str, data_rf: str) -> Optional[str]:
        """Fetch phone number via AJAX call"""
        url = f"{self.base_url}/ajax.php"

        headers = {
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
            response = self.session.post(url, headers=headers, data=payload, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get('ok') == 1:
                return data.get('tel')
            else:
                print(f"Phone fetch failed for listing {listing_id}: {data}")
                return None
        except Exception as e:
            print(f"Error fetching phone for listing {listing_id}: {e}")
            return None

    def scrape_all_listings(self, max_pages: int = 10, delay: float = 2.0) -> List[Dict]:
        """Scrape all listings with pagination"""
        all_data = []
        start = 0

        for page in range(max_pages):
            print(f"Scraping page {page + 1} (start={start})...")

            # Get listings from current page
            listings = self.get_listings_from_page(start)

            if not listings:
                print(f"No more listings found at start={start}")
                break

            print(f"Found {len(listings)} listings on this page")

            # Get details for each listing
            for i, listing in enumerate(listings, 1):
                print(f"  Processing listing {i}/{len(listings)}: {listing['url']}")

                # Get detailed information
                details = self.get_listing_details(listing['url'])

                if details:
                    # Merge preview and detail data
                    full_data = {**listing, **details}

                    # Get phone number if AJAX data available
                    if 'ajax_data' in full_data and full_data['ajax_data'].get('id'):
                        ajax = full_data['ajax_data']
                        phone = self.get_phone_number(
                            ajax['id'],
                            ajax.get('t', 'product'),
                            ajax['h'],
                            ajax.get('rf', '')
                        )
                        full_data['phone'] = phone
                        print(f"    Phone: {phone}")

                    all_data.append(full_data)

                # Delay between requests
                time.sleep(delay)

            # Move to next page
            start += 4

            # Delay between pages
            time.sleep(delay)

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


def main():
    scraper = OfisScraper()

    # Scrape first 5 pages (start=0, 4, 8, 12, 16)
    # Each page returns different listings
    listings = scraper.scrape_all_listings(max_pages=5, delay=2.0)

    print(f"\nTotal listings scraped: {len(listings)}")

    # Save to both JSON and CSV
    scraper.save_to_json(listings)
    scraper.save_to_csv(listings)

    print("\nScraping completed!")


if __name__ == "__main__":
    main()