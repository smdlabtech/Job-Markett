import os
import pathlib
import streamlit as st
import requests
from components.render_jobs import render_jobs

st.set_page_config(
    page_title="JobMarket Recommendation App",
    layout="wide",
    page_icon="👾"

)

path = pathlib.Path(__file__).parent

# Image de fond
st.image(
    image=path/"content"/"park-troopers-RAtKWVlfdf4-unsplash-cropped.jpg",
    use_container_width=True,
    output_format = "JPEG"

)


# --- Injection CSS globale ---
st.markdown("""
<style>
  /* Applique Inter var au titre h1 */
  h1 {
    font-family: "Inter var",sans-serif !important;
    font-weight: 700 !important;
  }
  
  /* Container centré et largeur max */
  .jobs-container {
    max-width: 1200px;
    margin: 32px auto;
  }

  /* Bannière de résultats en vert */
  .result-header {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 24px;
    background-color: #c8fca7;
    color: #000;
    padding: 12px 16px;
    border-radius: 8px;
    text-align: center;
  }

  /* Cartes arrondies + hover */
  .job-card {
    display: flex;
    background: #fff;
    border: 1px solid #eee;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .job-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  }

  .job-content {
    flex: 1;
    padding: 16px;
    display: flex;
    flex-direction: column;
  }

  /* Titre et compagnie */
  .job-top {
    margin-bottom: 16px;
  }
  .job-title {
    font-size: 16px;
    font-weight: 600;
    margin: 0 0 8px 0;
  }
  .job-company {
    font-size: 14px;
    color: #555;
    margin: 0;
  }

  /* Tags (localisation + salaire) */
  .job-tags {
    display: flex;
    gap: 15px;
    margin-top: 12px;
  }
  .job-tags .tag1 {
    background: #94fdff;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 14px;
    font-weight: 600;
    color: #000;
  }
  .job-tags .tag2 {
    background: #b9fcb8;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 14px;
    font-weight: 600;
    color: #000;
  }

  /* Bouton Voir l’offre */
  .job-bottom {
    text-align: right;
    margin-top: 12px;
  }
  .view-btn {
    display: inline-block;
    border: 2px solid #333;
    border-radius: 25px;
    padding: 8px 16px;
    text-decoration: none !important;
    color: #333 !important;
    transition: background 0.2s, color 0.2s;
    cursor: pointer;
  }
  .view-btn:hover {
    background: #000;
    color: #fff !important;
  }
  
""", unsafe_allow_html=True)



# --- Titre centré ---
st.markdown(
    '<h1 style="text-align:center;">Recommandation d\'offres High Tech</h1>',
    unsafe_allow_html=True
)

# --- Recherche (Quoi / Où / Bouton) ---
with st.form("search_form", clear_on_submit=False, enter_to_submit = False):
    col1, col2 = st.columns([5, 5])
    with col1:
        quoi = st.text_input("Quoi ?", placeholder="Data Engineer, Product Owner…")
    with col2:
        ou = st.text_input("Où ?", placeholder="Ville: Bordeaux, Paris... ",
                           help = "Il est possible d'ajouter plusieurs villes séparées par un espace")

    search = st.form_submit_button("Rechercher", icon="🔍")



# --- Appel API & rendu ---
if search and (quoi or ou):
    if not quoi:
        q = f'à "{ou}"'.strip()
    elif not ou:
        q = f'pour "{quoi}"'.strip()
    else:
        q = f'pour "{quoi} à {ou}"'.strip()
    try:
        with st.spinner("Recherche en cours…"):
            host = os.getenv("STREAMLIT_API_HOST")
            resp = requests.get(
                f"{host}",
                params={"query": q},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                results = data["results"]
            else:
                results = data
    except Exception as e:
        st.error(f"Erreur API : {e}")
        st.stop()

    if not results:
        st.warning("Aucune offre trouvée.")
    else:
        render_jobs(results, q)
elif quoi or ou:
    st.info("Cliquez sur « Rechercher » pour lancer la recherche.")