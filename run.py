from flask import Flask, redirect, send_from_directory
from api.routes import auth, positions, funds, wallets, dashboard
from api.docs import bp as docs_bp
from config import Config

# initialize flask application
app = Flask(__name__, static_folder='assets')

# load configuration from environment
flask_config = Config.get_flask_config()
app.config['SECRET_KEY'] = flask_config['secret_key']
app.config['DEBUG'] = flask_config['debug']
app.config['MYSQL_PORT'] = flask_config.get('port', 3306)

# setup cors with security settings for cross-origin requests
from flask_cors import CORS
CORS(app, 
     resources={r"/api/*": {
         "origins": ["http://localhost:5001", "https://aegis.smartswap.com"],
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

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/')
def index():
    return redirect('/api/', code=302)

if __name__ == '__main__':
    app.run(port=flask_config['port'])