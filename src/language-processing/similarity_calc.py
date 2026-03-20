# file for similarity calculations and similar helper functions
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Helper to match_name
def edit_distance(source: str, target: str):
    D = np.zeros((len(source) + 1, len(target) + 1))
    for i in range(len(source) + 1):
        D[i, 0] = i
    for j in range(len(target) + 1):
        D[0, j] = j
    D[0,0] = 0

    for i in range(1, len(source) + 1):
        for j in range(1, len(target) + 1):
            deletion = D[i-1, j] + 1
            insertion = D[i, j-1] + 1

            if target[j - 1] == source[i - 1]:
                substitution = D[i-1, j-1] + 0
            else: 
                substitution = D[i-1,j-1] + 2
            D[i,j] = min(deletion, insertion, substitution)
    return D[len(source), len(target)]




# Helper: turn txt file into list[str] with each element representing a line
def file_to_list_stripped(file_path: str) -> list[str]:
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f]


# Function 1: Match name using edit distance
# 	- Need to know user if trying to search a name, and i don't think
# 	there's a clean way to determine unless we make a checkbox saying:
# 	"Search for character"
# 	- Input example: "Loofy"
# 	- Output example: "Luffy"
def match_name(input_name: str, character_list: list[str]):
    best_edit_distance = 1000000
    best_match = ""
    for character in character_list:
        char_edit_dist = edit_distance(input_name, character)
        if char_edit_dist < best_edit_distance:
            best_match = character
            best_edit_distance = char_edit_dist
    return best_match;
    

# character_list = file_to_list_stripped("data/character_names.txt")
# print(match_name("Monkey D Luffy", character_list))
# print(match_name("Nami", character_list))
# print(match_name("Bentha", character_list))

# Current problem: Some characters have aliases. Should we use the aliases for later searching documents?
# Should we add aliases to the current list? Would be hard to do in a systematic way...



# Function 1.5: Create tf-idf matrix from docs
def create_tfidf_matrix(filepath: str):
    df = pd.read_csv(filepath)

    df["text"] = df["text"].fillna("").astype(str)

    docs = df["text"].tolist()
    ids = df["id"].tolist()

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(docs)
    return (ids, vectorizer, tfidf_matrix, docs)
    


# Function 2: Return k most relevant documents for query
# 	- Assume "Search for character" checkbox is not checked. Then:
# 	- Input example: "Most useless in Whole Cake arc"
# 	- Output: Ranked comments based off cosine similarity
def retrieve_k_docs(query, td_matrix, k, vectorizer, ids, docs):
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, td_matrix).flatten()

    # get just top k indeces
    top_indices = similarities.argsort()[::-1][:k]

    rankings = []
    for i in top_indices:
        rankings.append({
            "id": ids[i],
            "score": similarities[i],
            "text": docs[i]
        })
    
    return rankings

csv_path = "data/piratefolk_comments.csv"
query = "usopp bum"
ids, vectorizer, tfidf_matrix, docs = create_tfidf_matrix(csv_path)
rankings = retrieve_k_docs(query, tfidf_matrix, 10, vectorizer, ids, docs)

for ranking in rankings:
    print(ranking["text"])





# Function 3: Return character rating
# 	- Input: Character name (exact match)
# 	- Output: Score of character
# 	- Use similarity with good / bad document





