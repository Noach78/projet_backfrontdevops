# Projet BackFrontDevOps

## Authors :

- Noa (https://github.com/Nolan-30)
- Nolan (https://github.com/Noach78)
- Maxence (https://github.com/maxenceb91)

## Lancer le projet en local

Le front React et l'API FastAPI sont deux serveurs distincts : il faut lancer les
deux pour pouvoir créer un compte.

1. Dans un premier terminal, démarrer l'API depuis le dossier `back` :

   ```powershell
   cd back
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

   L'API est alors disponible sur `http://localhost:8000`.

2. Dans un deuxième terminal, démarrer le front depuis le dossier `front` :

   ```powershell
   cd front
   npm install
   npm run dev
   ```

   Ouvrir l'adresse indiquée par Vite, généralement `http://localhost:5173`.

Le front envoie les requêtes d'inscription à `http://localhost:8000/create_user` (ou `/auth/register`) et les requêtes de connexion à `http://localhost:8000/login_user` (ou `/auth/login`).
Si l'API ne démarre pas, vérifier que les dépendances Python du projet sont
installées dans `.venv` (avec `pip install -r back/requirements.txt`).

