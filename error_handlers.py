# This file contains the error handlers for the application
# The error handlers are used to render custom error pages when the application encounters an error.
from flask import render_template, request
import logging

def register_error_handlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        logging.error(f'Page not found: {request.url}')
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        logging.error(f'Internal server error: {e}')
        return render_template('500.html'), 500