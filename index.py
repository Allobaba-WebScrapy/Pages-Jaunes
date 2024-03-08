from flask import Flask, jsonify
from scrape import PageJaunesScraper 
from data import client_urls
import time


scraper = PageJaunesScraper()
app = Flask(__name__)


#! Server Side
@app.route("/")
def index():
    # Start time
    start_time = time.time()
    print("Server is running!")
    for url in client_urls[:1]:
        scraper.add_base_url(
            url["url"], params=url.get("params"), limit=url.get("limit")
        )
    # End time
    end_time = time.time()
    execution_time = end_time - start_time
    formated_data = jsonify(scraper.start_app())
    print("Execution time:", execution_time, "seconds")
    return formated_data


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030)