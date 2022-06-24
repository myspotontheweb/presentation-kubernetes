from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello World this is a demo'

app.run(host='0.0.0.0', port=8080)
