from flask import Flask
from config import Config
from extensions import db, login_manager
from models import User

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import redirect, url_for
        return redirect(url_for('auth.login'))
    
    # Root route
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.items import items_bp
    from routes.inventory import inventory_bp
    from routes.purchase_orders import po_bp
    from routes.receipts import receipts_bp
    from routes.shipments import shipments_bp
    from routes.external_processes import external_processes_bp
    from routes.clients import clients_bp
    from routes.reports import reports_bp
    from routes.scraps import scraps_bp
    from routes.bom import bom_bp
    from routes.stock_movements import stock_movements_bp
    from routes.batches import batches_bp
    from routes.production_orders import production_orders_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(items_bp, url_prefix='/items')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(po_bp, url_prefix='/purchase-orders')
    app.register_blueprint(receipts_bp, url_prefix='/receipts')
    app.register_blueprint(shipments_bp, url_prefix='/shipments')
    app.register_blueprint(external_processes_bp, url_prefix='/external-processes')
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(scraps_bp, url_prefix='/scraps')
    app.register_blueprint(bom_bp, url_prefix='/bom')
    app.register_blueprint(stock_movements_bp, url_prefix='/stock-movements')
    app.register_blueprint(batches_bp, url_prefix='/batches')
    app.register_blueprint(production_orders_bp, url_prefix='/production-orders')
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@inventory.com',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    
    return app

# Create app instance for gunicorn
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
