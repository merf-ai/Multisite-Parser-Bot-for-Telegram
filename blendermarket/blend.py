import asyncio
from asyncio import Semaphore
from bs4 import BeautifulSoup
import httpx
import json

FORBIDDEN_SYMBOLS = ('\\', '/', ':', '*', '?', '"', '<', '>', '|', ' ')
BASE_URL = "https://blendermarket.com/products"

async def page_count(client: httpx.AsyncClient) -> int:
    '''Count page number'''

    responce = await client.get('https://blendermarket.com/products')

    soup = BeautifulSoup(responce.text, 'html.parser')

    page_count = soup.find('nav', class_='pagy-bootstrap-nav').find_all('li')[-2].get_text()

    return int(page_count) 


def replace_forbidden_symbols_for_file_name(string: str, symbol: str) -> str:
    '''Replace FORBIDDEN_SYMBOLS in file on symbol'''
    new_str = ''
    for symbol in string:
        new_str += '_' if symbol in FORBIDDEN_SYMBOLS else symbol
    return new_str

async def load_data(client: httpx.AsyncClient, semaphore: Semaphore, file, page_number: int) -> None:
    '''Load data from site'''

    await semaphore.acquire()
    # Load the link as a JSON object

    # Send a GET request to the URL with the page number
    response = await client.get(f"{BASE_URL}?page={page_number}")

    # Parse the HTML contents
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the blocks with the posts
    post_blocks = soup.find_all(
    'a', class_='text-nounderline text-nocolor')

    # Iterate through the post blocks
    for block in post_blocks:
        link = block['href']
        # Find the link to the product page
        link = f'https://blendermarket.com/{link}'
        response = await client.get(link)
        # Parse the HTML contents
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the section with the images 
        image_section = soup.find_all('img', class_='img-fluid')

        name_of_tools = replace_forbidden_symbols_for_file_name(
            soup.find('title').get_text(strip=True), '_')

        url_on_image = image_section[0]['src'] if len(image_section) > 0 else None

        file.write(json.dumps({
            'off_link': link,
            'name_of_tools': name_of_tools,
            'url_on_image': url_on_image,
            }) + '\n' )

    semaphore.release()

async def main() -> None:
    '''Create tasks and async load data'''
    semaphore = Semaphore(10)
    client = httpx.AsyncClient()
    number_of_page = page_count(client)

    # Iterate through the links
    with open('blendermarket\\json\\blend.json', 'w') as file:

        tasks = [asyncio.create_task(load_data(client, semaphore, file, num_page)) for num_page in range(1, number_of_page+1)]
        await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())

'''
Documentation:

This code is a web scraper that scrapes information from the Blender Market website. 
It uses the asyncio and httpx libraries to make concurrent HTTP requests and 
parse the HTML data.

The main function of the code is main(), which creates a semaphore with a limit 
of 10 concurrent tasks and an HTTP client. It then calls the page_count() function 
to get the number of pages to be scraped, and creates tasks to scrape each page 
using the load_data() function. The tasks are run concurrently using the asyncio.gather() function.

The page_count() function sends a GET request to the base URL of the website and 
parses the HTML data using BeautifulSoup. It then finds the navigation menu and 
extracts the page count from the menu.

The load_data() function is responsible for loading data from each page of the website. 
It sends a GET request to the URL of the page, and uses BeautifulSoup to parse the HTML data. 
It then extracts the data for each product on the page, including the link to the 
product page, the name of the product, and the URL of the product image. 
The extracted data is then written to a file in JSON format.

The replace_forbidden_symbols_for_file_name() function is a helper function that 
replaces forbidden characters in a file name with an underscore symbol. 
This is done to ensure that the file name is valid and can be saved on the filesystem.

'''