# Akɔwɛɖagbe 🇧🇯 - Application de Gestion Budgétaire Personnalisée

**Akɔwɛɖagbe** est une application web moderne et responsive conçue pour aider les utilisateurs à suivre leurs finances personnelles au quotidien, particulièrement adaptée aux réalités du Bénin (Tontines, transports Zêm, etc.).

## ✨ Fonctionnalités Principales

*   **Tableau de bord interactif** : Suivi visuel de l'évolution du budget et des transactions récentes.
*   **Gestion des revenus et dépenses** : Catégorisation locale pour le contexte ouest-africain.
*   **Module de Prédiction IA** : Estimation des dépenses futures basée sur l'historique de l'utilisateur (Machine Learning).
*   **Design Moderne & Responsive** : Menu latéral, "Scroll Reveal", et un système de design épuré compatible avec tous les écrans.
*   **Sécurisé** : Authentification requise avec hachage des mots de passe (Passlib) et protection CSRF (Flask-WTF).

## 🛠️ Technologies Utilisées

*   **Backend** : Python 3, Flask, Flask-WTF, sqlite3
*   **Frontend** : HTML5, CSS3 Variables (Design System), Vanilla JavaScript
*   **Data Science / IA** : scikit-learn, pandas, numpy
*   **Icônes** : Phosphor Icons (CDN)
*   **Graphiques** : Chart.js

## 🚀 Installation Locale

1. **Cloner le projet**
```bash
git clone https://github.com/votre-nom/projet_depenses.git
cd projet_depenses
```

2. **Créer et activer l'environnement virtuel**
Sur Windows :
```bash
python -m venv venv
venv\Scripts\activate
```
Sur macOS/Linux :
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de l'environnement**
Dupliquez le fichier d'exemple et renommez-le :
```bash
cp .env.example .env
```
Éditez ensuite le fichier `.env` pour ajouter votre propre `FLASK_SECRET_KEY` (utilisez une chaîne aléatoire générée).

5. **Lancer l'application**
```bash
python app.py
```
Puis ouvrez votre navigateur à l'adresse **http://127.0.0.1:5000** !

## 👤 Auteur

**Cedoque BAGBONON** - Data Analyst (Licence en Informatique Industrielle et Maintenance, spécialité Analyse des Données).

*Projet initialement réalisé en troisième année d'université (Juin-Juillet 2025), et ayant bénéficié d'une mise à jour majeure (Interface, Sécurité, Modèle d'Analyse) en Mars 2026.*
