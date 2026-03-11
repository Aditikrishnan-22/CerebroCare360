from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_mail import Mail

db           = SQLAlchemy()
login_manager= LoginManager()
bcrypt       = Bcrypt()
migrate      = Migrate()
mail         = Mail() 

login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'