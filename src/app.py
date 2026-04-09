from flask import Flask, jsonify, render_template
from routes import register_routes


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["JSON_SORT_KEYS"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

    register_routes(app)

    @app.get("/")
    def home():
        return render_template("base.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "app": "MealMap"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
