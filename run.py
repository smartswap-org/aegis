import os
from flask import Flask, redirect, send_from_directory
from api.routes import auth, positions, funds, wallets, dashboard
from api.docs import bp as docs_bp
from dotenv import load_dotenv

load_dotenv()

# initialize flask application
app = Flask(__name__, static_folder='assets')

# initialize flask configuration directly from environment variables
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'smartswap')
app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))

# setup cors with security settings for cross-origin requests
from flask_cors import CORS
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5001,https://aegis.smartswap.com').split(',')
CORS(app, 
     resources={r"/api/*": {
         "origins": cors_origins,
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "expose_headers": ["Content-Range", "X-Content-Range"],
         "supports_credentials": True,
         "max_age": 600,
         "allow_private_network": False
     }}
)

# register all api blueprints
app.register_blueprint(auth.bp)
app.register_blueprint(positions.bp)
app.register_blueprint(funds.bp)
app.register_blueprint(wallets.bp)
app.register_blueprint(dashboard.bp)
app.register_blueprint(docs_bp)

# serve static assets
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# redirect root to api documentation
@app.route('/')
def index():
    return redirect('/api/', code=302)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001))) 