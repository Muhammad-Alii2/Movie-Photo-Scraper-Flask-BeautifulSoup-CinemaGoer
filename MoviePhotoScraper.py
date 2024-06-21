from flask import Flask, jsonify
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor
from imdb import Cinemagoer

app = Flask(__name__)
session = requests.Session()

@app.route('/get_image_urls/<movie_name>', methods=['GET'])
def get_image_urls(movie_name):
    gallery_url = get_gallery_url(movie_name)
    img_urls = get_gallery_info(gallery_url)
    return jsonify({'image_urls': img_urls, 'num_images': len(img_urls)})

def get_gallery_url(movie):
    try:
        movies = Cinemagoer().search_movie(movie)
        if movies:
            movie = movies[0]
            movie_id = movie.getID()
            gallery_url = f"https://www.imdb.com/title/tt{movie_id}/mediaindex"
            return gallery_url
    except Exception as e:
        print("Movie not found.", e)
        gallery_url = None
        return gallery_url

def get_image_urls_from_page(page_url):
    response = session.get(page_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        images = soup.find('div', class_='media_index_thumb_list').find_all("img")
        img_urls = [image.get('src').split('._V1_', 1)[0] for image in images]
        return img_urls
    except Exception as e:
        print(f"Error processing page {page_url}: {e}")
        return []

def get_gallery_info(gallery_url):
    response = session.get(gallery_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    try:
        pages = soup.find('span', class_='page_list').find_all("a")
        page_urls = [gallery_url] + [f'https://www.imdb.com{page.get("href")}' for page in pages]

        result_img_urls = []

        with ThreadPoolExecutor() as executor:
            img_urls_list = list(executor.map(get_image_urls_from_page, page_urls))

        for img_urls in img_urls_list:
            result_img_urls.extend(img_urls)

        return result_img_urls
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == '__main__':
    app.run()
