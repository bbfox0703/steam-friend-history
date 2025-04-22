from flask import Flask, render_template
import utils.steam_api as steam_api
import utils.backup as backup

app = Flask(__name__)

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
