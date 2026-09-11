from flask import Flask
from config import Config
from app.extensions import db, migrate, jwt, cors


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)  # allows your React frontend to call this API

    from app.models import Drug, User, Report  # noqa: F401 - registers models with SQLAlchemy

    from app.routes.drugs import drugs_bp
    from app.routes.auth import auth_bp
    from app.routes.reports import reports_bp

    app.register_blueprint(drugs_bp, url_prefix="/api/drugs")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app