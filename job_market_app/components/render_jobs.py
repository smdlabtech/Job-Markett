# render_jobs.py
import streamlit as st

def render_jobs(results, query):
    # 1) Structure HTML
    html = (
        '<div class="jobs-container">'
        f'  <div class="result-header">{len(results)} offres recommendées {query}</div>'
    )

    for o in results:
        tag_location = (
            f'<span class="tag1">📍 {o["location"]} - {o["code_postal"]}</span>'
        )

        # Affichage conditionnel du salaire
        salary_min = o.get("salary_min")
        salary_max = o.get("salary_max")

        if salary_min is not None:
            unit = "€/mois" if salary_min <= 10000 else "€/an"
            salary_range = f"{salary_min}"
            if salary_max:
                salary_range += f" - {salary_max}"
            tag_salary = f'<span class="tag2">💶 {salary_range} {unit}</span>'
        else:
            tag_salary = ""

        html += (
            '<div class="job-card">'
            '  <div class="job-content">'
            '    <div class="job-top">'
            f'      <h3 class="job-title">{o["title"]}</h3>'
            f'      <div class="job-company">{o["company"]}</div>'
            '    </div>'
            '    <div class="job-tags">'
            f'      {tag_location}'
            f'      {tag_salary}'
            '    </div>'
            '    <div class="job-bottom">'
            f'      <a href="{o["url"]}" target="_blank" class="view-btn">Voir l’offre</a>'
            '    </div>'
            '  </div>'
            '</div>'
        )

    html += '</div>'

    # 2) Ne PAS utiliser components.html : on injecte directement
    st.markdown(html, unsafe_allow_html=True)