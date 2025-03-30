import os
from app import create_app

# Get environment configuration
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    # Only enable debug mode in development
    debug = env == 'development'
    app.run(debug=debug, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))


