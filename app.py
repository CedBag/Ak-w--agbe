from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from passlib.hash import pbkdf2_sha256
from database import init_db
from datetime import datetime, timedelta
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
import os
import re
import random
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

# Chargement des variables d'environnement depuis .env
load_dotenv()

app = Flask(__name__)

# Clé secrète chargée depuis .env — stable entre les redémarrages
# ⚠️  Ne jamais committer le fichier .env sur Git !
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise RuntimeError(
        "FLASK_SECRET_KEY manquante ! "
        "Créez un fichier .env avec : FLASK_SECRET_KEY=<votre_clé_secrète>"
    )

# Initialisation de la base de données
init_db()

# Activation de la protection CSRF sur toute l'application
csrf = CSRFProtect(app)

# Fonctions pour gérer les mots de passe
def hash_password(password):
    return pbkdf2_sha256.hash(password)

def check_password(hashed_password, password):
    return pbkdf2_sha256.verify(password, hashed_password)

# Validation de l'email
def is_valid_email(email):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

# Validation du mot de passe
def is_valid_password(password):
    return (
        len(password) >= 8 and
        any(c.isupper() for c in password) and
        any(c.islower() for c in password) and
        any(c.isdigit() for c in password) and
        any(c in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for c in password)
    )


# Route pour l'authentification (connexion/inscription)
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form['action']
        with sqlite3.connect('budget.db') as conn:
            cursor = conn.cursor()

            if action == 'login':
                identifier = request.form['identifier']
                password = request.form['password']
                cursor.execute('SELECT id, password FROM users WHERE username = ? OR email = ?', (identifier, identifier))
                user = cursor.fetchone()
                if user and check_password(user[1], password):
                    session['user_id'] = user[0]
                    return redirect(url_for('dashboard'))
                else:
                    flash("Identifiant ou mot de passe incorrect.", "error")
                    return render_template('auth.html')

            elif action == 'register':
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
                confirm_password = request.form['confirm_password']

                if not all([username, email, password, confirm_password]):
                    flash("Tous les champs sont obligatoires.", "error")
                    return render_template('auth.html')

                if not is_valid_email(email):
                    flash("Adresse email invalide.", "error")
                    return render_template('auth.html')

                if not is_valid_password(password):
                    flash("Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial.", "error")
                    return render_template('auth.html')

                if password != confirm_password:
                    flash("Les mots de passe ne correspondent pas.", "error")
                    return render_template('auth.html')

                # Vérification de l'unicité
                cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
                if cursor.fetchone():
                    flash("Ce nom d'utilisateur ou cet email est déjà utilisé.", "error")
                    return render_template('auth.html')

                # Création du compte
                hashed_password = hash_password(password)
                cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
                conn.commit()
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                user_id = cursor.fetchone()[0]
                session['user_id'] = user_id
                session.pop('email_verification_code', None)
                flash("Inscription réussie ! Bienvenue sur AkɔwɛƐyɛ.", "success")
                return redirect(url_for('dashboard'))

    return render_template('auth.html')

# Route pour la page d'accueil
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# Route pour le tableau de bord
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        user_id = session['user_id']
        
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        username = cursor.fetchone()[0]
        
        current_month = datetime.now().strftime('%Y-%m')
        
        # Total des dépenses
        cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ? AND strftime("%Y-%m", date) = ?', (user_id, current_month))
        total_expenses = cursor.fetchone()[0] or 0
        
        # Total des revenus
        cursor.execute('SELECT SUM(amount) FROM revenues WHERE user_id = ? AND strftime("%Y-%m", date) = ?', (user_id, current_month))
        total_revenues = cursor.fetchone()[0] or 0
        
        # Solde net
        net_balance = total_revenues - total_expenses
        
        # Catégories de dépenses
        cursor.execute('SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? AND strftime("%Y-%m", date) = ? GROUP BY category ORDER BY total DESC LIMIT 5', (user_id, current_month))
        expense_categories = cursor.fetchall()
        
        categories_labels = [row[0] for row in expense_categories] if expense_categories else []
        categories_amounts = [row[1] for row in expense_categories] if expense_categories else []
        
        # Dernières transactions (dépenses)
        cursor.execute('SELECT amount, category, date, description, id FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 3', (user_id,))
        last_expenses = cursor.fetchall()
        
        # Générer un conseil basé sur les revenus et le solde net
        advice = ""
        if net_balance > 0:
            advice = "Vous avez un solde positif ce mois-ci ! Pensez à épargner une partie de vos revenus pour des projets futurs."
        elif net_balance < 0:
            advice = "Votre solde est négatif. Réduisez vos dépenses ou augmentez vos revenus pour rééquilibrer votre budget."
        else:
            advice = "Votre budget est équilibré. Continuez à suivre vos revenus et dépenses attentivement !"

    return render_template('dashboard.html', 
                         user_name=username,
                         total_expenses=total_expenses,
                         total_revenues=total_revenues,
                         net_balance=net_balance,
                         categories_data=expense_categories,
                         categories_labels=categories_labels,
                         categories_amounts=categories_amounts,
                         recent_transactions=last_expenses,
                         daily_tip=advice)

# Route pour ajouter une dépense
# Mise à jour de la route /add_expense avec contrôles de cohérence logique
@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            if amount <= 0:
                flash("Le montant de la dépense doit être positif.", "error")
                return redirect(url_for('add_expense'))

            category = request.form['category']
            if category == 'Autres' and 'custom_category' in request.form:
                category = request.form['custom_category']
            date = request.form['date']
            description = request.form.get('description', '')
            user_id = session['user_id']

            with sqlite3.connect('budget.db') as conn:
                cursor = conn.cursor()

                # Vérifier si un revenu existe pour l'utilisateur
                cursor.execute('SELECT MIN(date) FROM revenues WHERE user_id = ?', (user_id,))
                first_revenue_date = cursor.fetchone()[0]

                if not first_revenue_date:
                    flash("Veuillez d'abord enregistrer un revenu avant d'ajouter une dépense.", "error")
                    return redirect(url_for('add_revenue'))

                # Comparer la date de dépense avec celle du premier revenu
                if datetime.strptime(date, '%Y-%m-%d') < datetime.strptime(first_revenue_date, '%Y-%m-%d'):
                    flash("Vous ne pouvez pas ajouter une dépense avant la date de votre premier revenu.", "error")
                    return redirect(url_for('add_expense'))

                # Calcul du solde disponible avant l'ajout de la dépense
                cursor.execute('SELECT SUM(amount) FROM revenues WHERE user_id = ?', (user_id,))
                total_revenue = cursor.fetchone()[0] or 0
                cursor.execute('SELECT SUM(amount) FROM expenses WHERE user_id = ?', (user_id,))
                total_expense = cursor.fetchone()[0] or 0

                current_balance = total_revenue - total_expense

                if amount > current_balance:
                    flash("Le montant de la dépense dépasse votre solde actuel.", "error")
                    return redirect(url_for('add_expense'))

                # Insertion de la dépense si toutes les vérifications sont passées
                cursor.execute('INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
                               (user_id, amount, category, date, description))
                conn.commit()
            return redirect(url_for('dashboard'))

        except ValueError:
            flash("Le montant doit être un nombre valide.", "error")
            return redirect(url_for('add_expense'))

    return render_template('add_expense.html')


# Route pour ajouter un revenu
@app.route('/add_revenue', methods=['GET', 'POST'])
def add_revenue():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    if request.method == 'POST':
        try:
            amount = float(request.form['amount'])
            category = request.form['category']
            if category == 'Autres' and 'custom_category' in request.form:
                category = request.form['custom_category']
            date = request.form['date']
            description = request.form.get('description', '')
            user_id = session['user_id']

            with sqlite3.connect('budget.db') as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO revenues (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)', (user_id, amount, category, date, description))
                conn.commit()
            flash("Revenu ajouté avec succès.", "success")
            return redirect(url_for('dashboard'))
        except ValueError:
            flash("Le montant doit être un nombre valide.", "error")
            return render_template('add_revenue.html')
    return render_template('add_revenue.html')

# Route pour voir les dépenses
@app.route('/view_expenses', methods=['GET'])
def view_expenses():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        user_id = session['user_id']
        
        year = request.args.get('year', 'Toutes')
        month = request.args.get('month', 'Tous')
        day = request.args.get('day', 'Tous')
        
        query = 'SELECT amount, category, date, description, id FROM expenses WHERE user_id = ?'
        params = [user_id]
        
        if year != 'Toutes':
            query += ' AND strftime("%Y", date) = ?'
            params.append(year)
        if month != 'Tous':
            query += ' AND strftime("%m", date) = ?'
            params.append(month)
        if day != 'Tous':
            query += ' AND strftime("%d", date) = ?'
            params.append(day)
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        cursor.execute('SELECT DISTINCT strftime("%Y", date) FROM expenses WHERE user_id = ?', (user_id,))
        years = sorted([row[0] for row in cursor.fetchall()])
        
        months = [
            {"name": "Janvier", "value": "01"}, {"name": "Février", "value": "02"},
            {"name": "Mars", "value": "03"}, {"name": "Avril", "value": "04"},
            {"name": "Mai", "value": "05"}, {"name": "Juin", "value": "06"},
            {"name": "Juillet", "value": "07"}, {"name": "Août", "value": "08"},
            {"name": "Septembre", "value": "09"}, {"name": "Octobre", "value": "10"},
            {"name": "Novembre", "value": "11"}, {"name": "Décembre", "value": "12"}
        ]
        
        cursor.execute('SELECT DISTINCT strftime("%d", date) FROM expenses WHERE user_id = ?', (user_id,))
        days = sorted([row[0] for row in cursor.fetchall()])
    return render_template('view_expenses.html', expenses=expenses, years=years, months=months, days=days,
                           selected_year=year, selected_month=month, selected_day=day)

# Route pour voir les revenus
@app.route('/view_revenues', methods=['GET'])
def view_revenues():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        user_id = session['user_id']
        
        year = request.args.get('year', 'Toutes')
        month = request.args.get('month', 'Tous')
        day = request.args.get('day', 'Tous')
        
        query = 'SELECT amount, category, date, description, id FROM revenues WHERE user_id = ?'
        params = [user_id]
        
        if year != 'Toutes':
            query += ' AND strftime("%Y", date) = ?'
            params.append(year)
        if month != 'Tous':
            query += ' AND strftime("%m", date) = ?'
            params.append(month)
        if day != 'Tous':
            query += ' AND strftime("%d", date) = ?'
            params.append(day)
        
        cursor.execute(query, params)
        revenues = cursor.fetchall()
        
        cursor.execute('SELECT DISTINCT strftime("%Y", date) FROM revenues WHERE user_id = ?', (user_id,))
        years = sorted([row[0] for row in cursor.fetchall()])
        
        months = [
            {"name": "Janvier", "value": "01"}, {"name": "Février", "value": "02"},
            {"name": "Mars", "value": "03"}, {"name": "Avril", "value": "04"},
            {"name": "Mai", "value": "05"}, {"name": "Juin", "value": "06"},
            {"name": "Juillet", "value": "07"}, {"name": "Août", "value": "08"},
            {"name": "Septembre", "value": "09"}, {"name": "Octobre", "value": "10"},
            {"name": "Novembre", "value": "11"}, {"name": "Décembre", "value": "12"}
        ]
        
        cursor.execute('SELECT DISTINCT strftime("%d", date) FROM revenues WHERE user_id = ?', (user_id,))
        days = sorted([row[0] for row in cursor.fetchall()])
    return render_template('view_revenues.html', revenues=revenues, years=years, months=months, days=days,
                           selected_year=year, selected_month=month, selected_day=day)

# Routes pour Supprimer et Éditer Dépenses / Revenus

@app.route('/delete_expense/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (expense_id, session['user_id']))
        conn.commit()
    flash("Dépense supprimée avec succès.", "success")
    return redirect(request.referrer or url_for('view_expenses'))

@app.route('/delete_revenue/<int:revenue_id>', methods=['POST'])
def delete_revenue(revenue_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM revenues WHERE id = ? AND user_id = ?', (revenue_id, session['user_id']))
        conn.commit()
    flash("Revenu supprimé avec succès.", "success")
    return redirect(request.referrer or url_for('view_revenues'))

@app.route('/edit_expense/<int:expense_id>', methods=['GET', 'POST'])
def edit_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            amount = float(request.form['amount'])
            category = request.form['category']
            if category == 'Autres' and 'custom_category' in request.form:
                category = request.form['custom_category']
            date = request.form['date']
            description = request.form.get('description', '')
            
            cursor.execute('''UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? 
                              WHERE id = ? AND user_id = ?''', 
                           (amount, category, date, description, expense_id, session['user_id']))
            conn.commit()
            flash("Dépense modifiée avec succès.", "success")
            return redirect(url_for('view_expenses'))
        
        cursor.execute('SELECT amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?', (expense_id, session['user_id']))
        expense = cursor.fetchone()
        
    if not expense:
        flash("Dépense introuvable.", "error")
        return redirect(url_for('view_expenses'))
        
    return render_template('edit_expense.html', expense=expense, expense_id=expense_id)

@app.route('/edit_revenue/<int:revenue_id>', methods=['GET', 'POST'])
def edit_revenue(revenue_id):
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            amount = float(request.form['amount'])
            category = request.form['category']
            if category == 'Autres' and 'custom_category' in request.form:
                category = request.form['custom_category']
            date = request.form['date']
            description = request.form.get('description', '')
            
            cursor.execute('''UPDATE revenues SET amount = ?, category = ?, date = ?, description = ? 
                              WHERE id = ? AND user_id = ?''', 
                           (amount, category, date, description, revenue_id, session['user_id']))
            conn.commit()
            flash("Revenu modifié avec succès.", "success")
            return redirect(url_for('view_revenues'))
        
        cursor.execute('SELECT amount, category, date, description FROM revenues WHERE id = ? AND user_id = ?', (revenue_id, session['user_id']))
        revenue = cursor.fetchone()
        
    if not revenue:
        flash("Revenu introuvable.", "error")
        return redirect(url_for('view_revenues'))
        
    return render_template('edit_revenue.html', revenue=revenue, revenue_id=revenue_id)

# Route pour la prédiction des dépenses
@app.route('/predict', methods=['GET'])
def predict_expenses():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    user_id = session['user_id']
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()

        # Récupération des dépenses (seulement les dépenses pour le budget prédictif)
        cursor.execute('SELECT date, amount FROM expenses WHERE user_id = ? ORDER BY date', (user_id,))
        expense_data = cursor.fetchall()

        if not expense_data:
            flash("Aucune dépense enregistrée pour le moment. Ajoutez des données pour voir vos prédictions.", "warning")
            return render_template('prediction.html', prediction=None)

        # 1. Conversion en DataFrame et agrégation mensuelle
        expense_df = pd.DataFrame(expense_data, columns=['date', 'amount'])
        expense_df['date'] = pd.to_datetime(expense_df['date'])
        
        # On extrait la période mensuelle (ex: 2025-01, 2025-02)
        expense_df['month'] = expense_df['date'].dt.to_period('M')
        
        # On groupe par mois pour avoir le budget total dépensé chaque mois
        monthly_df = expense_df.groupby('month')['amount'].sum().reset_index()
        
        # On convertit le mois en un index numérique continu défini depuis le premier mois
        first_month = monthly_df['month'].min()
        monthly_df['month_num'] = monthly_df['month'].apply(lambda m: (m.year - first_month.year) * 12 + (m.month - first_month.month))

        num_months = len(monthly_df)
        r2_score = None
        
        # 2. Choix du modèle selon la quantité de données historiques (en mois)
        if num_months < 3:
            # S'il y a 1 ou 2 mois historiques, la régression linéaire sur 2 points est absurde (R²=1 systématique)
            # On utilise une simple moyenne mensuelle (Moyenne Mobile)
            prediction = monthly_df['amount'].mean()
            method = "moyenne"
        else:
            # S'il y a 3 mois ou plus, on a assez de points pour chercher une tendance avec la Régression Linéaire
            X = monthly_df[['month_num']]
            y = monthly_df['amount']

            model = LinearRegression()
            model.fit(X, y)
            r2_score = model.score(X, y)

            # On prédit pour le mois suivant le dernier mois enregistré
            future_month_num = monthly_df['month_num'].max() + 1
            future_X = pd.DataFrame([[future_month_num]], columns=['month_num'])

            prediction = model.predict(future_X)[0]
            
            # Anti-aberration : on redresse vers la moyenne si le modèle prédit un montant négatif
            if prediction < 0:
                prediction = monthly_df['amount'].mean()
                
            method = "regression"

    return render_template(
        'prediction.html',
        prediction=round(prediction, 2),
        r2_score=round(r2_score, 2) if r2_score is not None else None,
        num_data=num_months,
        method=method
    )

# Route pour la déconnexion
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

# Route pour la page de profil/paramètres
@app.route('/profile-settings', methods=['GET', 'POST'])
def profile_settings():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
        
    user_id = session['user_id']
    
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            new_username = request.form.get('username')
            new_email = request.form.get('email')
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # Vérification : vérifier si nom d'utilisateur/email est déjà utilisé
            cursor.execute('SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?', (new_username, new_email, user_id))
            if cursor.fetchone():
                flash("Nom d'utilisateur ou e-mail déjà utilisé.", "error")
            else:
                # Mise à jour des informations de base
                cursor.execute('UPDATE users SET username = ?, email = ? WHERE id = ?', (new_username, new_email, user_id))
                updated = True
                
                # Traitement du changement de mot de passe
                if new_password or current_password:
                    if not current_password or not new_password or not confirm_password:
                        flash("Veuillez remplir tous les champs de mot de passe pour le modifier.", "error")
                        updated = False
                    else:
                        cursor.execute('SELECT password FROM users WHERE id = ?', (user_id,))
                        user_pass = cursor.fetchone()[0]
                        if not check_password(user_pass, current_password):
                            flash("Mot de passe actuel incorrect.", "error")
                            updated = False
                        elif new_password != confirm_password:
                            flash("Les nouveaux mots de passe ne correspondent pas.", "error")
                            updated = False
                        elif len(new_password) < 6:
                            flash("Le nouveau mot de passe doit faire au moins 6 caractères.", "error")
                            updated = False
                        else:
                            hashed_pw = hash_password(new_password)
                            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_pw, user_id))
                            flash("Mot de passe mis à jour avec succès.", "success")
                conn.commit()
                if updated:
                    flash("Vos informations ont été mises à jour.", "success")
            
            return redirect(url_for('profile_settings'))

        cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
    if user:
        username, email = user
        return render_template('profile-settings.html', username=username, email=email)
    else:
        flash('Utilisateur non trouvé.', "error")
        return redirect(url_for('dashboard'))

# Route pour supprimer toutes les données (dépenses et revenus)
@app.route('/delete-data', methods=['POST'])
def delete_data():
    if 'user_id' not in session:
        return redirect(url_for('auth'))
    with sqlite3.connect('budget.db') as conn:
        cursor = conn.cursor()
        user_id = session['user_id']
        cursor.execute('DELETE FROM expenses WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM revenues WHERE user_id = ?', (user_id,))
        conn.commit()
    flash('Vos données de dépenses et de revenus ont été supprimées avec succès.', "success")
    return redirect(url_for('profile_settings'))

if __name__ == '__main__':
    # Le mode debug ne sera actif que s'il est explicitement à 'True' dans le fichier .env
    debug_mode = os.environ.get('FLASK_DEBUG') == 'True'
    app.run(debug=debug_mode)