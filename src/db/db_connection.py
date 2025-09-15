import psycopg
from db.config import DB_CONFIG
from logger.logger import error


def connect_db() -> psycopg.connection:
    """
    Etablit une connexion à une base de données PostgreSQL en utilisant la configuration fournie.

    Cette fonction tente de se connecter à une base de données PostgreSQL à l'aide de détails de
    prédéfinis. Si la connexion réussit, elle renvoie l'objet de connexion.
    Si une erreur survient au cours du processus de connexion, elle est enregistrée et la fonction
    renvoie None.

    :return : Un objet de connexion psycopg2 si la connexion est réussie, None dans le cas contraire.
    :rtype : Psycopg.connection ou None
    """
    try:
        conn = psycopg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        error(f" Erreur de connexion : {e}")
        return None

if __name__ == "__main__":
    connect_db()
