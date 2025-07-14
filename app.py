from functools import wraps
import os
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv
from model import db, User, Page, ResponseModel
from module.fb_messenger import MessengerBot
from module.fb_oauth import FacebookOAuth


load_dotenv(dotenv_path=".env")


client_id = os.getenv("APP_ID")
client_secret = os.getenv("APP_SECRET")
redirect_uri = os.getenv('REDIRECT_URI')


app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY', 'dev_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_bot'))  # ou la page de connexion que tu veux
        return f(*args, **kwargs)
    return decorated_function


FB_OAUTH = FacebookOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri
)

# Création de la base au démarrage
with app.app_context():
    db.create_all()



@app.route("/")
@login_required
def index():
    return render_template('index.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        valide = request.form.get("code") == "dax"
        if valide:
            return redirect('/connect-facebook')
    return render_template('register.html', error='')



@app.route('/connect-facebook')
def connect_facebook():
    url = FB_OAUTH.get_authorize_url(scopes=[
        'pages_manage_metadata',
        'pages_messaging',
        'pages_read_engagement'
    ])
    print(f'url : {url}')
    return redirect(url)


@app.route('/oauth-callback')
def oauth_callback():
    code = request.args.get('code')
    if not code:
        return 'Code manquant', 400

    access_token = FB_OAUTH.get_access_token(code)
    session['fb_token'] = access_token

    pages = FB_OAUTH.get_user_pages(access_token)
    user_id = session.get("user_id")
    if not user_id:
        return redirect('/login-bot')  # sécurité

    user = User.query.get(user_id)
    # Vérifie si cette page existe déjà
    for page_data in pages:
        
        page_id = str(page_data['id'])  # converti en string
        page = Page.query.filter_by(id=page_id).first()
        if not page:
            page = Page(
                id=page_id,
                name=page_data['name'],
                token=page_data['access_token']
            )
            db.session.add(page)
        if page not in user.pages:
            user.pages.append(page)

    db.session.commit()
    return redirect('/')

@app.route("/manage")
@login_required
def manage():
    user_id = session.get("user_id")
    #user = User.query.get(user_id)

    #return render_template("manage.html", user=user, pages=user.pages)
    user = User.query.get(user_id)
    pages = [
        {'id': page.id, 'name': page.name}
        for page in user.pages
    ]
    return render_template('manage.html', pages=pages)

@app.route('/login-bot', methods=['GET', 'POST'])
def login_bot():
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect('/manage')
        flash("Identifiants incorrects", "danger")

    return render_template('login_bot.html')


@app.route('/registre-bot', methods=['POST', 'GET'])
def create_account():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            return "Email déjà utilisé", 400
        user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['user_name'] = user.name
        return redirect('/')
    return render_template('create_account.html')



@app.route('/api/pages/<int:page_id>/responses')
def get_responses(page_id):
    page = Page.query.get_or_404(str(page_id))


    return jsonify([{"id": r.id, "content": r.content} for r in page.responses])

@app.route('/api/responses', methods=['POST'])
def add_response():
    data = request.get_json()
    page_id = data.get('page_id')
    keyword = data.get('keyword')
    content = data.get('content')

    if not all([page_id, keyword, content]):
        return jsonify({'error': 'Champs manquants'}), 400

    response = ResponseModel(page_id=str(page_id), keyword=keyword, content=content)

    db.session.add(response)
    db.session.commit()

    return jsonify({
        'id': response.id,
        'keyword': response.keyword,
        'content': response.content
    })



@app.route('/api/responses/<int:response_id>', methods=['DELETE'])
def delete_response(response_id):
    response = ResponseModel.query.get_or_404(response_id)
    db.session.delete(response)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()  # Vide toute la session (user_id, fb_token, etc.)
    flash("Vous avez été déconnecté.", "info")
    return redirect(url_for('login_bot'))

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Vérification du webhook (ajoute ceci dans tes paramètres Meta)
        verify_token = os.getenv("VERIFY_TOKEN", "dax")
        if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == verify_token:
            return request.args.get("hub.challenge")
        return "Invalid verification token", 403

    if request.method == "POST":
        data = request.get_json()
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                page_id = entry["id"]
                message_text = messaging_event.get("message", {}).get("text")

                if message_text:
                    page = Page.query.filter_by(id=page_id).first()
                    if page:
                        bot = MessengerBot(page.token)

                        # Recherche de la réponse par mot-clé
                        
                        response = ResponseModel.query.filter_by(page_id=page.id).all()
                        for r in response:
                            if r.keyword.lower() in message_text.lower():
                                bot.send_text(sender_id, r.content)
                                break  # Une seule réponse suffit

        return "OK", 200



if __name__ == "__main__":
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

