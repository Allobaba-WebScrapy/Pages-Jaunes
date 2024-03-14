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
        # Run the scraper and yield the results
        for result in scraper.run():
            yield f"data: {json.dumps(result)}\n\n"
        # Send a 'done' event when the scraper has finished running
        yield "event: done\ndata: Done\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


#! Server Side Events (SSE) route
# @app.route("/stream1")
# def index():
#     # params = request.get_json()

#     def generate():
#         # Start time
#         start_time = time.time()
#         print("Server is running!")

#         scraper.server_urls = client_urls[:1]

#         # scraper.server_urls = [
#         #     {
#         #         "genre":"B2B",
#         #         "start-limit": "2",
#         #         "end-limit": "2",
#         #         "url": "https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=restaurants&ou=paris-75&&page=2&tri=PERTINENCE-ASC",
#         #     },
#         #     # {
#         #     #     "genre":"B2C",
#         #     #     "start-limit": "2",
#         #     #     "end-limit": "1",
#         #     #     "url": "https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui=agences+immobilieres&ou=strasbourg-67&&tri=PERTINENCE-ASC&page=1",
#         #     # },

#         # ]

#         for item in scraper.run():
#             # Yield the item for SSE (optional)
#             yield f"data:{json.dumps(item)}\n\n"
#         # End of request
#         yield "event: done\ndata: Done\n\n"
#         end_time = time.time()
#         execution_time = end_time - start_time
#         print("Execution time:", execution_time, "seconds")

#     return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3090)
