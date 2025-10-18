# crowdBuilding

**Plateforme de Financement Participatif dans l'Immobilier pour le Burkina Faso**

crowdBuilding est une plateforme web innovante qui connecte les promoteurs immobiliers locaux avec les investisseurs, notamment ceux de la diaspora burkinabè, pour financer des projets immobiliers au Burkina Faso.

## 🎯 Objectifs

- Connecter les promoteurs immobiliers locaux avec les investisseurs
- Permettre à la diaspora burkinabè d'investir dans leur pays d'origine
- Stimuler le secteur immobilier burkinabè
- Offrir une solution digitale, transparente et sécurisée
- Fournir des rendements attractifs aux investisseurs

## 🛠️ Stack Technique

### Backend
- **Framework** : Django 4.2+
- **Langage** : Python 3.8+
- **Base de données** : MySQL
- **ORM** : Django ORM

### Frontend
- **Templates** : Django Templates (Jinja2)
- **HTML5 / CSS3**
- **Framework CSS** : Bootstrap 5
- **JavaScript** : Vanilla JS et jQuery

### Architecture
- **Pattern** : MVT (Model-View-Template)
- **Structure** : Applications Django modulaires
- **Organisation** : Chaque application possède ses propres templates et fichiers statiques

## 📊 Modèle de Données

Le système repose sur plusieurs entités clés :
- **Utilisateur** : Gestion des comptes et rôles
- **Rôle** : Investisseur, Promoteur, Administrateur
- **Projet** : Projets immobiliers à financer
- **Investissement** : Investissements dans les projets
- **Transaction** : Transactions financières
- **Document** : Gestion des documents et pièces justificatives
- **Notification** : Système de notifications
- **Étape** : Étapes de réalisation des projets
- **Compte Rendu** : Rapports d'avancement

## 🏗️ Structure du Projet

```
crowdBuilding/
│
├── crowdBuilding/                  # Configuration principale du projet Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/                           # Applications Django principales
│   ├── accounts/                   # Gestion des utilisateurs et rôles
│   ├── projects/                   # Gestion des projets immobiliers
│   ├── investments/                # Gestion des investissements et transactions
│   ├── documents/                  # Gestion des documents (upload, validation)
│   ├── notifications/              # Système de notifications
│   └── core/                       # Fonctions partagées (auth, sécurité, utilitaires)
│
├── templates/                      # Templates globaux
├── static/                         # Fichiers statiques globaux
├── media/                          # Fichiers uploadés
├── .env                            # Variables d'environnement
├── requirements.txt
└── manage.py
```

## 🧱 Fonctionnalités Principales

### 🧍‍♂️ Module Utilisateurs (Accounts)
- **Inscription** : Choix entre Investisseur et Promoteur
- **Connexion** : Authentification sécurisée
- **Profil** : Gestion des informations personnelles
- **Dashboard** : Tableau de bord personnalisé selon le rôle

### 🏗️ Module Promoteur (Projects)
- Soumission de projets immobiliers
- Validation administrative obligatoire
- Gestion des étapes et comptes rendus
- Suivi du taux de financement

### 💰 Module Investisseur (Investments)
- Validation administrative avant investissement
- Consultation des projets disponibles
- Gestion du portefeuille d'investissements
- Calcul des rendements

### 📂 Module Documents (Documents)
- Téléversement sécurisé des pièces justificatives
- Validation administrative
- Gestion des différents types de documents

### 🔔 Module Notifications (Notifications)
- Notifications en temps réel
- Envoi automatique et manuel (email + tableau de bord)

### ⚙️ Module Administrateur (Administration)
- Validation des comptes utilisateurs
- Validation des projets
- Supervision globale de la plateforme
- Gestion des documents et transactions

## 🎨 Design et UI/UX

- **Interface responsive** (Bootstrap 5)
- **Palette de couleurs** :
  - Primaire : #2C3E50 (Bleu foncé)
  - Secondaire : #3498DB (Bleu clair)
  - Accent : #E74C3C (Rouge)
  - Succès : #27AE60 (Vert)
- **Expérience utilisateur** simple, intuitive et adaptée au contexte local burkinabè

## 🚀 Installation et Configuration

### Prérequis
- Python 3.8+
- MySQL 5.7+
- Node.js (optionnel, pour les outils de développement)

### Installation

1. **Cloner le projet**
```bash
git clone <repository-url>
cd crowdBuilding
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration de la base de données**
   - Créer une base de données MySQL nommée `crowdbuilding`
   - Copier `env.example` vers `.env` et configurer les variables

5. **Migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

7. **Collecter les fichiers statiques**
```bash
python manage.py collectstatic
```

8. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

### Configuration de l'environnement

Copiez `env.example` vers `.env` et configurez les variables suivantes :

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=crowdbuilding
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
```

## 📱 Utilisation

### Pour les Investisseurs
1. S'inscrire et choisir le rôle "Investisseur"
2. Uploader les documents requis (pièce d'identité, justificatifs de revenus)
3. Attendre la validation administrative
4. Explorer et investir dans les projets disponibles
5. Suivre les rendements et l'avancement des projets

### Pour les Promoteurs
1. S'inscrire et choisir le rôle "Promoteur"
2. Uploader les documents requis
3. Soumettre un projet immobilier
4. Attendre la validation du projet
5. Gérer les étapes et publier des comptes rendus

### Pour les Administrateurs
1. Accéder au panneau d'administration Django
2. Valider les comptes utilisateurs
3. Valider les projets soumis
4. Superviser les transactions et documents

## 🔐 Règles Métier

- L'email est l'identifiant unique
- Les mots de passe sont hachés via PBKDF2
- La validation administrative est obligatoire avant toute action sensible
- Un projet soumis devient non modifiable jusqu'à sa validation
- Les investisseurs non validés ne peuvent pas investir
- Les promoteurs ne peuvent soumettre qu'un projet à la fois avant validation

## 🧪 Tests

```bash
# Lancer tous les tests
python manage.py test

# Tests avec coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 📚 Documentation

La documentation complète est disponible dans le dossier `docs/` :
- Guide d'installation
- Guide d'utilisation
- API Documentation
- Architecture technique

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👥 Équipe

- **Développement** : Équipe crowdBuilding
- **Design** : Spécialistes UI/UX
- **Conseil** : Experts immobiliers burkinabè

## 📞 Contact

- **Email** : contact@crowdbuilding.bf
- **Téléphone** : +226 XX XX XX XX
- **Adresse** : Ouagadougou, Burkina Faso

## 🎓 Objectifs Pédagogiques

Ce projet démontre :
- La conception d'un système complet Django basé sur le pattern MVT
- La gestion conditionnelle des rôles et des validations administratives
- L'architecture modulaire et sécurisée d'un projet professionnel
- L'intégration d'une expérience utilisateur claire et localisée pour le Burkina Faso et sa diaspora

---

**Développé avec ❤️ pour le Burkina Faso**
