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


@app.route("/setup", methods=["POST"])
def setup():
    client_urls = request.get_json()
    # Add the URLs to the scraper
    scraper.server_urls = client_urls
    return jsonify({"status": "Setup complete"})


@app.route("/stream")
def stream():
    def event_stream():
        results = list()
        for result in scraper.run():
            results.append(result)
            yield f"data: {json.dumps(result)}\n\n"
        if not results:
            yield f"event: failedVerification\ndata: {json.dumps({'error':'Verification failed'})}\n\n"
            return

    return Response(event_stream(), mimetype="text/event-stream")


#! Server Side Events (SSE) route
@app.route("/s")
def index():
    # params = request.get_json()

    def generate():
        # Start time
        start_time = time.time()
        print("Server is running!")

        scraper.server_urls = client_urls[:1]

        results = list()
        for result in scraper.run():
            results.append(result)
            yield f"data: {json.dumps(result)}\n\n"
        if not results:
            yield "event: error\ndata: Verification failed\n\n"
            return

        end_time = time.time()
        execution_time = end_time - start_time
        print("Execution time:", execution_time, "seconds")

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3090)
