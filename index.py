from flask import Flask, jsonify, stream_with_context, request, Response
from flask_cors import CORS  # Import CORS from flask_cors module
from scrape import PageJaunesScraper
from data import client_urls
import requests
import json
import time


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes in the Flask app
scraper = PageJaunesScraper()


@app.route("/", methods=["GET"])
def home():
    return jsonify({"Flask": "Welcome to the PageJaunes Scraper API!"})


#! Server Side Events (SSE) route
@app.route("/stream", methods=["POST"])
def index():
    # params = request.get_json()

    def generate():
        # Start time
        start_time = time.time()
        print("Server is running!")

        for url in client_urls[:3]:
            scraper.add_base_url(
                url["url"], params=url.get("params"), limit=url.get("limit")
            )
        # for url in params:
        #     scraper.add_base_url(
        #         url["url"], params=url.get("params"), limit=url.get("limit")
        # )

        # End time
        end_time = time.time()
        execution_time = end_time - start_time

        for item in scraper.run():
            # Send each item as a POST request to localhost:3000/data
            # requests.post("http://localhost:3000/data", json=item)

            # Yield the item for SSE (optional)
            yield f"data:{json.dumps(item)}\n\n"

        print("Execution time:", execution_time, "seconds")

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3050)
