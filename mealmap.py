import numpy as np

name_similarity_map = {}


def cosine_similarity_score(name_vec_map, sample_dish_vector):
    global name_similarity_map
    name_similarity_map = {}

    np_sample = np.array(sample_dish_vector, dtype=float)
    norm_sample = np.linalg.norm(np_sample)

    if norm_sample == 0:
        for name in name_vec_map:
            name_similarity_map[name] = 0.0
        return

    for name, vec in name_vec_map.items():
        np_dish = np.array(vec, dtype=float)
        norm_dish = np.linalg.norm(np_dish)

        if norm_dish == 0:
            name_similarity_map[name] = 0.0
        else:
            name_similarity_map[name] = float(np.dot(np_sample, np_dish) / (norm_sample * norm_dish))


if __name__ == "__main__":
    name_vector_map = {
        "chicken burrito bowl": [1, 1, 1, 1, 1, 0],
        "grilled chicken salad": [1, 0, 0, 0, 1, 1],
        "cheese quesadilla": [0, 0, 0, 1, 0, 0],
        "rice and beans": [0, 1, 1, 0, 0, 0],
    }

    sample_dish_vector = [1, 1, 1, 0, 1, 0]

    cosine_similarity_score(name_vector_map, sample_dish_vector)

    ranked = sorted(name_similarity_map.items(), key=lambda x: x[1], reverse=True)
    for name, score in ranked:
        print(f"{name}: {score:.4f}")
