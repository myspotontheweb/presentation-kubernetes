from flask import Flask
import math

app = Flask(__name__)

#
# Landing page
#
@app.route('/')
def index():
    return 'Hello World this is a demo'

#
# A request that will generate high CPU usage
#
@app.route("/stress")
def stress():
    for x in range(0,1000000):
        math.sqrt(x)
    return "Phew! Done"

#
# Main program
#
app.run(host='0.0.0.0', port=8080)
