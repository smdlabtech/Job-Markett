import pickle
import numpy as np
import json

def load_model_data():
    with open("models/vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    with open("models/vectors.npy", "rb") as f:
        vectors = np.load(f)

    with open("data/processed_offers.json", "r") as f:
        offers = json.load(f)

    return vectorizer, vectors, offers
