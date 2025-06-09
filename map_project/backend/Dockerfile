# Utiliser une image Python officielle
FROM python:3.9-slim

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier le fichier des dépendances et l'installer en premier pour profiter du cache Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code du backend dans le répertoire de travail
COPY . .

# Exposer le port sur lequel Uvicorn va tourner (celui que Uvicorn écoute DANS le conteneur)
# Le port 8001 a été utilisé précédemment pour éviter les conflits.
EXPOSE 8001

# Commande pour lancer l'application avec Uvicorn en mode développement
# --host 0.0.0.0 pour être accessible depuis l'extérieur du conteneur
# --port 8001 pour correspondre au port EXPOSE et à la configuration attendue
# --reload pour le rechargement à chaud (nécessite que le code source soit monté en volume dans docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
