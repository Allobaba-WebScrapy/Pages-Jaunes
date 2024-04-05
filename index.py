from flask import Flask, jsonify, request, Response
from flask_cors import CORS  # Import CORS from flask_cors module
from scrape import PageJaunesScraper
import json

app = Flask(__name__)

CORS(app)  


@app.route("/pagesjaunes", methods=["GET"])
@app.route("/", methods=["GET"])
def home():
    return jsonify({"Flask": "Welcome to the PageJaunes Scraper API!"})


@app.route("/pagesjaunes/stream", methods=["POST"])
@app.route("/stream", methods=["POST"])
def stream():
    # Get the data from the client
    data = request.get_json()
    client_url = data
    print(client_url)
    # Start the scraping process
    def event_stream():
        results = list()
        yield "data: {}\n\n".format(json.dumps({'type':'progress', 'message': 'Scraping started 👍'})).encode()
        for result in PageJaunesScraper(client_url).run():
            if "type" in result and result["type"] == "progress":
                yield "data: {}\n\n".format(json.dumps(result)).encode()
            elif "type" in result and result["type"] == "error":
                print(result)
                yield "data: {}\n\n".format(json.dumps(result)).encode()
            else:
                results.append(result)
                yield "data: {}\n\n".format(json.dumps(result)).encode()
        if results:
            yield "data: {}\n\n".format(json.dumps({"type":"done","message":"Scraping is done 🥳"})).encode()
        else:
            yield "data: {}\n\n".format(json.dumps({"type":"error","message":"Verification failed no result found 😥"})).encode()
        yield "\n\n".encode()  # Add two newline characters at the end
    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4080)
