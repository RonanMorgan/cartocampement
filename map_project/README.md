# Projet Cartographie Associations

Ce projet contient une application de cartographie destinée aux associations et à leurs bénévoles. Il est composé d'un backend en FastAPI et d'un frontend en Next.js.

## Structure du Projet

*   `backend/`: Contient le code source de l'API backend (FastAPI). Voir `backend/README.md` pour plus de détails spécifiques au backend.
*   `frontend/`: Contient le code source de l'application frontend (Next.js).
*   `docker-compose.yml`: Fichier pour orchestrer le lancement des services backend et frontend avec Docker Compose.

## Prérequis

*   Docker
*   Docker Compose (généralement inclus avec Docker Desktop, sinon installez [Docker Compose V2](https://docs.docker.com/compose/install/))

## Démarrage Rapide avec Docker Compose (Recommandé pour le développement local)

Cette méthode lancera le backend FastAPI et le frontend Next.js dans des conteneurs Docker, avec rechargement à chaud pour le développement.

1.  **Clonez le dépôt (si ce n'est pas déjà fait):**
    ```bash
    # git clone <url_du_depot>
    # cd map_project
    ```

2.  **Lancez les services avec Docker Compose:**
    À la racine du projet (`map_project`), exécutez :
    ```bash
    docker-compose up --build
    ```
    *   L'option `--build` reconstruit les images Docker si des modifications ont été apportées aux `Dockerfile` ou au code source copié dans les images. Pour les lancements suivants, `docker-compose up` peut suffire si les images n'ont pas besoin d'être reconstruites.
    *   Les services seront lancés et les logs s'afficheront dans le terminal. Pour lancer en mode détaché (en arrière-plan), utilisez `docker-compose up --build -d`.

3.  **Accès aux applications:**
    *   **Frontend (Next.js):** Ouvrez votre navigateur et allez à `http://localhost:3000`
    *   **Backend (FastAPI API):** L'API est accessible à `http://localhost:8001`
        *   Documentation Swagger UI de l'API : `http://localhost:8001/docs`
        *   Documentation ReDoc de l'API : `http://localhost:8001/redoc`

    Le frontend est configuré pour communiquer avec le backend via `http://api:8001` à l'intérieur du réseau Docker, ce qui est mappé vers `http://localhost:8001` pour votre accès local.

4.  **Arrêter les services:**
    *   Si les services tournent en avant-plan, appuyez sur `Ctrl+C` dans le terminal où `docker-compose up` a été exécuté.
    *   Si les services tournent en mode détaché (avec `-d`), ou pour s'assurer d'un arrêt propre depuis un autre terminal :
        ```bash
        docker-compose down
        ```
    *   Pour supprimer également les volumes (si vous avez des volumes nommés, par exemple pour une base de données) :
        ```bash
        docker-compose down --volumes
        ```

## Développement

### Backend
Consultez le fichier `backend/README.md` pour des instructions détaillées sur la configuration et le lancement du backend en dehors de Docker, ainsi que pour des exemples d'utilisation de l'API.

### Frontend
Le frontend est une application Next.js. Les commandes de développement standard (`npm run dev`, `npm run build`, `npm start`) peuvent être exécutées depuis le répertoire `frontend/` si vous souhaitez le développer en dehors de Docker, mais assurez-vous que la variable d'environnement `NEXT_PUBLIC_API_URL` pointe correctement vers votre backend (par exemple, `http://localhost:8001`).

## Tests

### Backend
Les tests du backend peuvent être exécutés avec `pytest` depuis le répertoire `backend/`. Voir `backend/README.md`.
Pour exécuter les tests du backend à l'intérieur du conteneur Docker (si le service `api` est en cours d'exécution) :
```bash
docker-compose exec api pytest
```

### Frontend
(Instructions de test pour le frontend à ajouter si des tests spécifiques sont mis en place)
