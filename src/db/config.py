"""
Ce fichier est nécessaire pour établir une connexion avec la base de données.

!!! Une base de données **PostgresSQL** est strictement nécessaire !!!
La modélisation ainsi que la partie d'ingestion des données sont strictement propre à Postgres.
Le dictionnaire de configuration est établie grâce à la documentation postgresql avec les mots clés
reconnus : https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS

Les variables d'environnement sont définies dans le fichier .env.
Adapter les variables d'environnement pour votre environnement.
Se référer à la documentation pour plus de détails.
"""

import os
from dotenv import load_dotenv

load_dotenv()


DB_CONFIG = {
    "dbname": os.getenv("JOBS_POSTGRES_DB"),
    "user": os.getenv("JOBS_POSTGRES_USER"),
    "password": os.getenv("JOBS_POSTGRES_PASSWORD"),
    "host": os.getenv("JOBS_POSTGRES_HOST"),
    "port": os.getenv("JOBS_POSTGRES_PORT")
}