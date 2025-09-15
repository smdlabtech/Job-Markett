import json
from sklearn.metrics.pairwise import cosine_similarity
from recommender.data_preparation import prepare_offer_data, text_normalization, vectorize_texts, transform_text
from pipelines.transform import PROCESSED_DATA_DIR
from fetch_functions.utils import get_latest_file


def compute_similarity(query_vector, offer_vectors):
    """
    Calcule la similarité cosinus entre le vecteur de la requête et les vecteurs d'offres.
    Renvoie un tableau de scores.
    """
    scores = cosine_similarity(query_vector, offer_vectors)
    return scores.flatten()



def load_processed_offers(file_path: str):
    """
    Charge les offres transformées depuis un fichier JSON.
    """
    with open(file_path, 'r', encoding = 'utf-8') as f:
        processed_offers = json.load(f)
    return processed_offers



def build_recommendation_engine_from_folder(folder_path: str,
                                            weight_title: int = 2,
                                            weight_location: int = 1,
                                            weight_description: int = 1):
    """
    Construit le moteur de recommandation à partir du dernier fichier JSON transformé
    trouvé dans le dossier donné.
    Chaque offre est prétraitée et les champs sont pondérés pour la vectorisation.

    Pour chaque offre, la pondération de la description est ajustée :
      - Si la description est présente, on utilise le poids passé en paramètre.
      - Sinon, on ne prend pas en compte ce champ (poids = 0).
    """
    latest_file = get_latest_file(folder_path)
    processed_offers = load_processed_offers(latest_file)

    combined_text_list = []

    for _offer in processed_offers:
        # Normalisation des données du fichier selon les règles de normalisation présentes dans data_preparation.py :
        data = prepare_offer_data(_offer)

        # Combination des champs pour obtenir une sortie composée de toutes les informations :
        current_weight_description = weight_description if data["description"] else 0
        current_weight_location = weight_location if data["location"] else 0

        combined_text = " ".join(
            [data["title"]] * weight_title +
            [data["location"]] * current_weight_location +
            [data["description"]] * current_weight_description
        )
        combined_text_list.append(combined_text)

    offers_vectorizer, processed_offer_vectors = vectorize_texts(combined_text_list)

    # 4. Sauvegarde des offres normalisées
    #output_filename = os.path.basename(f'{latest_file}_normalized')
    #output_path = os.path.join(NORMALIZED_OFFERS_DIR, output_filename)

    #with open(output_path, "w") as f:
    #    json.dump(normalized_offers, f, indent=2, ensure_ascii=False)

    return processed_offers, offers_vectorizer, processed_offer_vectors, combined_text_list



def recommend_offers(user_input: str, offers_vectorizer, processed_offer_vectors, processed_offers: list, top_n=5, score_threshold: float = 0.3):
    """
    Génère une liste d'offres recommandées à partir d'une requête utilisateur.

    - La requête est vectorisée (TF-IDF) et comparée à l'ensemble des offres via similarité cosinus.
    - Seules les offres dépassant le seuil de similarité sont retenues, triées par score décroissant.

    Args:
        user_input (str): Mot-clé de recherche fourni par l'utilisateur.
        offers_vectorizer: Objet vectorizer (TF-IDF) entraîné sur le corpus d'offres.
        processed_offer_vectors: Matrice sparse des offres vectorisées.
        processed_offers (list): Liste des dictionnaires d'offres.
        top_n (int, optional): Nombre maximum d'offres à retourner. Défaut à 5.
        score_threshold (float, optional): Seuil minimal de similarité cosinus pour considérer une offre.

    Returns:
        list: Liste des offres recommandées (dictionnaires).
    """
    # Pré-traiter l'input utilisateur
    user_input_normalized = text_normalization(user_input)
    query_vector = transform_text(offers_vectorizer, user_input_normalized)
    scores = compute_similarity(query_vector, processed_offer_vectors)

    # On filtre uniquement les offres dont le score de similarité est au moins égal au seuil
    scored_offers = [(i, score) for i, score in enumerate(scores) if score >= score_threshold]

    # Trier par ordre décroissant de score
    scored_offers.sort(key = lambda x: x[1], reverse = True)

    # Extraire les indices pour les top n offres (si elles existent)
    top_indices = [i for i, score in scored_offers][:top_n]

    recommended_offers = [
        processed_offers[i]
        for i in top_indices
        if processed_offers[i].get("location")  # ne garde que celles qui ont location non vide
    ]

    return recommended_offers



if __name__ == "__main__":
    # Utilisation du dossier processed_data défini via PROCESSED_DATA_DIR
    offers, vectorizer, offer_vectors, texts = build_recommendation_engine_from_folder(PROCESSED_DATA_DIR)

    # Requête utilisateur
    user_query = input("Chercher un job par intitulé de poste : \n -> ")
    recommendations = recommend_offers(user_input = user_query,
                                       offers_vectorizer=vectorizer,
                                       processed_offer_vectors = offer_vectors,
                                       processed_offers = offers, top_n = 10)

    print("Offres recommandées :")
    for offer in recommendations:
        print(offer)
