import os
from app import create_app
from config import Config

app = create_app(Config)
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True) 