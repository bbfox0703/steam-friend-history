from flask import Flask, render_template
import utils.steam_api as steam_api
import utils.backup as backup
from datetime import datetime

app = Flask(__name__)

@app.template_filter('datetimeformat')
def datetimeformat(value):
    if not value:
        return ""
    try:
        return datetime.utcfromtimestamp(int(value)).strftime('%Y-%m-%d')
    except Exception:
        return value

@app.route('/')
def index():
    data = steam_api.get_friend_data()
    return render_template('index.html', data=data)

@app.route('/update')
def update():
    result = steam_api.update_friend_list()
    backup.backup_today()
    return {'status': 'ok', 'updated': result}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
