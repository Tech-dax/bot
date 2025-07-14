from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Table d'association plusieurs-à-plusieurs entre User et Page
user_page = db.Table('user_page', 
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('page_id', db.String(50), db.ForeignKey('page.id'), primary_key=True)  # ID en string
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

    # Relation plusieurs-à-plusieurs avec les pages
    pages = db.relationship('Page', secondary=user_page, back_populates='users')

class Page(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # CHANGÉ en String pour supporter les IDs Facebook
    name = db.Column(db.String(100))
    token = db.Column(db.String(1024))  # large pour éviter d'autres erreurs


    # Relation inverse avec les utilisateurs
    users = db.relationship('User', secondary=user_page, back_populates='pages')

    # Une page a plusieurs réponses automatiques
    responses = db.relationship('ResponseModel', backref='page', cascade="all, delete-orphan")

class ResponseModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    page_id = db.Column(db.String(50), db.ForeignKey('page.id'))  # CHANGÉ en String
    keyword = db.Column(db.String(100))  # Ajouté pour prendre en charge les mots-clés
    content = db.Column(db.String(500))

class AccessCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True)
    valid = db.Column(db.Boolean, default=True)
