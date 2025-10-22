from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)

    @app.route('/')
    def index():
        return jsonify({"message": "Hello from Flask!"}), 200

    @app.route('/health')
    def health():
        return jsonify({"status": "ok"}), 200

    return app

if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=5000, debug=True)
