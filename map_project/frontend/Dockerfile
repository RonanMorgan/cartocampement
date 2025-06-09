# Utiliser une image Node.js officielle (une version LTS est un bon choix)
FROM node:18-alpine

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier package.json et package-lock.json (ou npm-shrinkwrap.json)
# et installer les dépendances en premier pour profiter du cache Docker
COPY package*.json ./
RUN npm install

# Copier tout le code du frontend dans le répertoire de travail
# (Cela inclura .env.local s'il est présent à la racine de frontend/ et non dans .dockerignore)
COPY . .

# Next.js écoute sur le port 3000 par défaut en développement
EXPOSE 3000

# Commande pour lancer le serveur de développement Next.js
# npm run dev expose par défaut sur 0.0.0.0 donc accessible depuis l'extérieur du conteneur
CMD ["npm", "run", "dev"]
