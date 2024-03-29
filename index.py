from flask import Flask, jsonify, request, Response
from flask_cors import CORS  # Import CORS from flask_cors module
from scrape import PageJaunesScraper
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
    data = request.get_json()
    client_urls = [data]
    print(client_urls)
    scraper.server_urls = client_urls
    return jsonify({"status": "Setup complete"})


@app.route("/stream")
def stream():
    def event_stream():
        results = list()
        yield f"event: progress\ndata: {json.dumps({"type":"progress", "message": "Scraping started!"})}\n\n"
        for result in scraper.run():
            if "type" in result and result["type"]=="progress":
                yield f"event: progress\ndata: {json.dumps(result)}\n\n"
            elif "type" in result and result["type"]=='error':
                yield f"errorEvent: error\ndata: {json.dumps(result)}\n\n"
            else:
                results.append(result)
                yield f"data: {json.dumps(result)}\n\n"
        if not results:
            yield f"event: errorEvent\ndata: {json.dumps({"type":"error", "message":"Bybass verification failed No result!"})}\n\n"
            return
        else:
            # save_to_csv(result, f"static/{scraper.fileName}.csv")
            yield f"event: done\ndata: done\n\n"

    return Response(event_stream(), mimetype="text/event-stream")

    
#! Server Side Events (SSE) route For Test
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
            if "type" in result and result["type"]=="progress":
                yield f"event: progress\ndata: {json.dumps(result)}\n\n"
            elif "type" in result and result["type"]=="error":
                yield f"errorEvent: error\ndata: {json.dumps(result)}\n\n"
            else:
                yield f"data: {json.dumps(result)}\n\n"
        if not results:
            yield "event: errorEvent\ndata: Verification failed Not result\n\n"
            return
        else:
            yield f"event: done\ndata: done\n\n"

        end_time = time.time()
        execution_time = end_time - start_time
        print("Execution time:", execution_time, "seconds")

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
