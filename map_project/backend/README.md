# Projet Cartographie Associations - Backend FastAPI

Ce répertoire contient le backend de l'application de cartographie pour associations, développé avec FastAPI.

## Prérequis

*   Python 3.8+
*   Pip (gestionnaire de paquets Python)
*   Optionnel : Un outil pour gérer les environnements virtuels (comme `venv` ou `conda`)

## Installation

1.  **Clonez le dépôt (si ce n'est pas déjà fait):**
    ```bash
    # git clone <url_du_depot>
    # cd <repertoire_du_projet>/backend
    ```

2.  **Créez et activez un environnement virtuel (recommandé):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Sur Windows: venv\Scripts\activate
    ```

3.  **Installez les dépendances:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### Base de données

Par défaut, l'application utilise une base de données SQLite nommée `sql_app.db` (ou `test.db` pour les tests) qui sera créée automatiquement dans le répertoire `backend`.

Pour utiliser une autre base de données (par exemple, PostgreSQL), vous pouvez définir la variable d'environnement `DATABASE_URL`.

**Exemple pour PostgreSQL:**
```bash
export DATABASE_URL="postgresql://user:password@host:port/dbname"
```
Assurez-vous d'avoir le driver Python approprié installé (par exemple, `psycopg2-binary` pour PostgreSQL, qui est déjà dans `requirements.txt`).

## Lancement de l'application

Pour démarrer le serveur de développement FastAPI avec Uvicorn :

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera alors accessible à l'adresse `http://localhost:8000`.
La documentation interactive (Swagger UI) sera disponible à `http://localhost:8000/docs` et ReDoc à `http://localhost:8000/redoc`.

L'application a été testée sur le port 8001 lors de certains développements pour éviter les conflits. Si vous rencontrez des problèmes avec le port 8000, vous pouvez essayer :
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## Exécution des tests

Les tests fonctionnels sont écrits avec `pytest`. Pour les exécuter :

1.  Assurez-vous d'être dans le répertoire `backend` et que votre environnement virtuel est activé.
2.  Lancez `pytest` :
    ```bash
    pytest
    ```
    Cela exécutera tous les tests définis dans le répertoire `tests/`. Une base de données de test `test.db` sera créée et utilisée pour ces tests.

## Exemples d'utilisation de l'API (avec `curl`)

Voici quelques exemples pour interagir avec l'API. Remplacez les valeurs entre `< >` par vos propres données.

1.  **Créer un nouvel utilisateur (association):**
    ```bash
    curl -X POST "http://localhost:8000/users/" -H "Content-Type: application/json" -d '{
      "name": "<nom_association>",
      "password": "<mot_de_passe>"
    }'
    ```

2.  **Obtenir un token d'authentification (login):**
    ```bash
    curl -X POST "http://localhost:8000/auth/token" \
         -H "Content-Type: application/x-www-form-urlencoded" \
         -d "username=<nom_association>&password=<mot_de_passe>"
    ```
    (Note: Le retour est un JSON, vous pouvez utiliser `jq` pour extraire l'access_token: `... | jq -r .access_token`)

3.  **Créer un questionnaire (nécessite un token):**
    Supposons que votre token est `MY_ACCESS_TOKEN`.
    ```bash
    curl -X POST "http://localhost:8000/questionnaires/" \
         -H "Authorization: Bearer MY_ACCESS_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{
           "title": "Relevé des déchets Plage Nord",
           "description": "Questionnaire pour les déchets sur la plage Nord",
           "password": "securepassword123",
           "elements": [
             {
               "field_type": "text",
               "label": "Type de déchet principal"
             },
             {
               "field_type": "number",
               "label": "Quantité approximative (en kg)"
             },
             {
               "field_type": "coordinates_lat",
               "label": "Latitude"
             },
             {
               "field_type": "coordinates_lon",
               "label": "Longitude"
             }
           ]
         }'
    ```
