from flask import Flask
from threading import Thread
import time
app = Flask(__name__)


@app.route('/')
def index():
    return "Bot is Running"


def run():
    app.run(host='0.0.0.0', port=8080)

def auto_update(update):
    update()

def keep_alive(update):
    t = Thread(target=run)
    auto_update(update)
    t.start()

# howto keepalive
