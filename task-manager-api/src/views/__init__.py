def register_blueprints(app):
    from src.views.task_routes import task_bp
    from src.views.user_routes import user_bp
    from src.views.report_routes import report_bp
    from src.views.category_routes import category_bp

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)
