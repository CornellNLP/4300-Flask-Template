import os

from flask import Flask, jsonify, render_template
from routes import register_routes, ensure_models_loaded


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["JSON_SORT_KEYS"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = False

    register_routes(app)

    # Load data/models once at startup instead of during the first live request.
    # This avoids request-time worker timeouts on /mealmap/meta and /mealmap/matches.
    try:
        print("MealMap: preloading models...", flush=True)
        ensure_models_loaded()
        print("MealMap: models loaded successfully.", flush=True)
    except Exception as exc:
        # Let the app fail loudly in logs if startup loading breaks.
        print(f"MealMap startup error while loading models: {exc}", flush=True)
        raise

    @app.get("/")
    def home():
        return render_template("base.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "app": "MealMap"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5001)),
        debug=False,
    )