from flask import Flask, jsonify
from scrape import PageJaunesScraper 
from data import client_urls
import time
import json


scraper = PageJaunesScraper()
app = Flask(__name__)


#! Server Side
from flask import stream_with_context, Response

@app.route("/")
def index():
    def generate():
        # Start time
        start_time = time.time()
        print("Server is running!")
        for url in client_urls[:2]:
            scraper.add_base_url(
                url["url"], params=url.get("params"), limit=url.get("limit")
            )
        # End time
        end_time = time.time()
        execution_time = end_time - start_time
        for item in scraper.run():
            yield f"data:{json.dumps(item)}\n\n"
        print("Execution time:", execution_time, "seconds")

    return Response(stream_with_context(generate()), mimetype='text/event-stream')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3030)