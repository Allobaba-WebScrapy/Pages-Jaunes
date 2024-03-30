from flask import Flask, jsonify, request, Response
from flask_cors import CORS  # Import CORS from flask_cors module
from scrape import PageJaunesScraper
import json

app = Flask(__name__)

CORS(app)  

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
        yield f"event: progress\ndata: {json.dumps({'type':'progress', 'message': 'Scraping started 👍'})}\n\n"
        for result in scraper.run():
            if "type" in result and result["type"] == "progress":
                yield f"event: progress\ndata: {json.dumps(result)}\n\n"
            elif "type" in result and result["type"] == "error":
                print(result)
                yield f"event: errorEvent\ndata: {json.dumps(result)}\n\n"
            else:
                results.append(result)
                yield f"data: {json.dumps(result)}\n\n"
        if not results:
            yield f"event: errorEvent\ndata: {json.dumps({'type':'error', 'message':'Bybass verification failed No result 😢'})}\n\n"
            return
        else:
            # save_to_csv(result, f"static/{scraper.fileName}.csv")
            yield f"event: done\ndata: done\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
