from datetime import datetime
import json
from db_connector import get_db_connection



def parse_google_books_data(raw_api_data):
    """
    Extracts required fields (title, authors, year, publisher) from the 
    raw Google Books API JSON response.
    """
    try:
        volume_info = raw_api_data.get('volumeInfo', {})
        
        # Extract core book details
        book_details = {
            'title': volume_info.get('title'),
            'publisher': volume_info.get('publisher'),
            'publication_year': None,
            'authors': volume_info.get('authors', []) # Get list of authors
        }
        
        # Safely extract the publication year(the date format many vary)
        published_date = volume_info.get('publishedDate', '')
        if published_date:
            # Assumes the date format starts with the year (e.g., "2023-10-15" or "1998")
            book_details['publication_year'] = published_date.split('-')[0]

        # Basic validation
        if not book_details['title'] or not book_details['authors']:
            print("ERROR: Missing critical data (Title or Author) in API response.")
            return None
        
        return book_details
        
    except Exception as e:
        print(f"Error parsing API data: {e}")
        return None

import requests
import json
from typing import Optional, Dict, Any

def get_book_data_from_api(isbn: str) -> Optional[Dict[str, Any]]:
    """
    Fetches raw book data from the Google Books API using ISBN.

    Args:
        isbn: The 10 or 13 digit ISBN string of the book to look up.

    Returns:
        A dictionary containing the raw JSON data item from the API, 
        or None if the request fails or the book is not found.
    """
    
    # The base URL for the Google Books API volumes endpoint
    base_url = "https://www.googleapis.com/books/v1/volumes"
    
    # Parameters for the API call: We query using the ISBN
    params = {'q': f'isbn:{isbn}'}
    
    print(f"DEBUG: Calling API for ISBN: {isbn}")
    
    try:
        # 1. Make the HTTP GET request
        response = requests.get(base_url, params=params)
        
        # 2. Check for HTTP errors (4xx or 5xx status codes)
        response.raise_for_status() 
        
        # 3. Convert the response text into a Python dictionary
        data = response.json()

        # 4. Check if the API returned any results
        # totalItems > 0 indicates success
        if data.get('totalItems', 0) > 0 and 'items' in data:
            # The API returns a list of items. We only need the first one.
            print(f"DEBUG: Book data found successfully.")
            return data['items'][0] 
        else:
            print(f"INFO: No book found on Google Books API for ISBN: {isbn}. Total items: 0")
            return None
#--------except conditions---------------
    except requests.exceptions.HTTPError as http_err:
        print(f"API Request Error (HTTP): {http_err} for ISBN {isbn}")
        return None
    except requests.RequestException as req_err:
        print(f"API Request Error (Connection/Timeout): {req_err} for ISBN {isbn}")
        return None
    except json.JSONDecodeError as json_err:
        print(f"API Response Error: Could not parse JSON response for ISBN {isbn}. Error: {json_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during API call: {e}")
        return None

# --- Example Usage (Place in your main testing file) ---
if __name__ == '__main__':
    # Test with a known book (e.g., The Martian by Andy Weir)
    test_isbn = '9780804139024'
    raw_book_data = get_book_data_from_api(test_isbn)
    
    if raw_book_data:
        # Display key information to confirm success
        title = raw_book_data.get('volumeInfo', {}).get('title', 'N/A')
        authors = raw_book_data.get('volumeInfo', {}).get('authors', [])
        print("\n--- Test Results ---")
        print(f"ISBN: {test_isbn}")
        print(f"Title: {title}")
        print(f"Authors: {', '.join(authors)}")
        print("--------------------")
    else:
        print(f"\nFailed to retrieve data for ISBN {test_isbn}")
