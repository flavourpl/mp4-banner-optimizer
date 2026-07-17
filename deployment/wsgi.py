"""
WSGI entry point for production deployment with Gunicorn.
"""

from web_app_prod import app

if __name__ == "__main__":
    app.run()