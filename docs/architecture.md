# 🏗️ Architecture du projet Job Market

Ce document présente l’architecture technique du projet **Job Market**, une plateforme modulaire d'agrégation, de traitement et de recommandation d’offres d’emploi issues de sources externes.

---

## 📐 Vue d’ensemble

![workflow](/docs/assets/jobs_workflow.png)

---

## 🧱 Composants principaux

### 1. **ETL Pipeline**
- **Langage** : Python
- **Orchestration** : Apache Airflow
- **Étapes** :
  - Extraction depuis Adzuna, France Travail et JSearch
  - Transformation et normalisation
  - Chargement en base SQL via fichier JSON transformé

### 2. **Base de données**
- **Type** : PostgreSQL
- **Utilisation** : stockage relationnel, audit, triggers, vues, optimisations
- **Conteneurisée** via Docker Compose

### 3. **API de recherche**
- **Framework** : FastAPI
- **Objectif** : exposer des endpoints REST performants pour rechercher, filtrer et recommander des offres
- **Authentification** : Pas définie

### 4. **Moteur de recommandation**
- **Méthode** : TF-IDF + Similarité Cosinus
- **Données** : vectorisation des descriptions d'offres
- **Chargé en mémoire au lancement de l'API**

### 5. **Interface utilisateur**
- **Technologie** : Streamlit
- **Objectif** : prototyper une UI permettant de tester la recherche d’offres

---

## 🐳 Dockerisation

- Chaque service est isolé dans un conteneur :
  - `api` : FastAPI
  - `streamlit` : Interface utilisateur
  - `postgres` : Base de données
  - `airflow-webserver`, `airflow-scheduler`, etc.
  - `grafana` : Visualisation
  - `prometheus` et `StatsD` pour les métriques airflow

- Gestion complète avec un `docker-compose.yaml`

---

## ☁️ Orchestration avec Airflow

- **DAG principal** : `./airflow/dags/etl.py`
- **Fréquence** : personnalisable (Tous les 16 jours par défaut)
- **Tâches** :
  - Extraction depuis les API externes
  - Transformation avec nettoyage + enrichissement
  - Chargement dans PostgreSQL ou fichier JSON
  - Rechargement de l'API via **/reload**

---

## 📊 Monitoring (optionnel)

- **Stack Prometheus + Grafana**
- Airflow expose des métriques via StatsD (désactivables)
- Logs disponibles dans `/logs/`

---

## 🔐 Sécurité

- Clé Fernet générée
- Clé de signature configurable via `AIRFLOW__API__SECRET_KEY`
- `.env` centralisé pour les clés API, secrets, configs

---

## 🔧 Dossiers importants

| Dossier            | Rôle                                          |
|--------------------|-----------------------------------------------|
| `src/`             | Code source principal (ETL, API, reco, DB)    |
| `data/`            | Données transformées et exportées             |
| `sql/`             | Scripts SQL pour la base PostgreSQL           |
| `logs/`            | Logs d'exécution                              |
| `dags/`            | DAGs Airflow                                  |
| `docs/`            | Documentation technique                       |

