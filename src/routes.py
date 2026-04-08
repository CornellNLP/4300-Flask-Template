"""
Routes: home page and episode search.

To enable AI chat, set USE_LLM = True below. See llm_routes.py for LLM specific routes.
"""
import json
from flask import render_template, request
from models import db, Episode, Review
import joblib
from sklearn.metrics.pairwise import cosine_similarity
from language_processing import similarity_calc
from pathlib import Path

# ── AI toggle ──
USE_LLM = False
# USE_LLM = True
# ───────────────

_root_dir = Path(__file__).parent.parent
data = joblib.load(_root_dir / "data/model.pkl")
tfidf_matrix = data["matrix"]
vectorizer = data["vectorizer"]
characters = data["characters"]

character_data = joblib.load(_root_dir / "data/character_data.pkl")

# calculates similarity between query and character docs, returns best match's name
def query_character(query):
    query_vec = vectorizer.transform([query])
    sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
    return characters[sims.argmax()]
def json_search(query):
   
    # only retrieve top 10 relevant documents
    matches = similarity_calc.retrieve_k_docs(query, similarity_calc.tfidf_matrix, 10, similarity_calc.vectorizer, similarity_calc.ids, similarity_calc.docs)
    return json.dumps({
        "name": "Search Results",
        "summary": "",
        "retrieved": matches,            
        "rating": 0,
        "mentions": 0,
        "consensus": "",
        "trend": [],
        "trend_dates": []
        })



def register_routes(app):
    @app.route("/")
    def home():
        return render_template('character-search.html')
    
    @app.route("/search")
    def search():
        query = request.args.get("q", "")
        
        if not query.strip():
            return json.dumps({"error": "empty query"})
        
        # calculate the similarity of the query with the character "docs" and 
        # return the most similar character
        result = similarity_calc.query_character(query, 
            similarity_calc.vectorizer,
            similarity_calc.tfidf_matrix,
            similarity_calc.characters)
        
        print(f"Received search query: '{query}' -> matched character: '{result}'")
        return json.dumps({
            "character": result
        })
    
    @app.route("/csearch")
    def csearch():
        name = request.args.get("q", "")
        print(f"Received Csearch query: '{name}'")
        if not name:
            return json.dumps({})
        if name in character_data.keys():
            print(f"Exact match found for {name}")
            return json.dumps(character_data[name])
        print(f"{name} is not a character name")

    # fallback (nothing found)
        return json.dumps({})

    if USE_LLM:
        from llm_routes import register_chat_route
        register_chat_route(app, json_search)
