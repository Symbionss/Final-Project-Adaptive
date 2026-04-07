from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

RYU_API = os.environ.get('RYU_API', 'http://localhost:8080')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/block_ip', methods=['POST'])
def block_ip():
    ip = request.json.get('ip')

    if not ip:
        return jsonify({'status': 'error', 'message': 'IP tidak diberikan'}), 400

    try:
        resp = requests.post(
            f'{RYU_API}/block_ip',
            json={'ip': ip},
            timeout=5
        )

        return jsonify({
            'status': 'success',
            'action': 'block',
            'ip': ip,
            'ryu_response': resp.json()
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Gagal ke Ryu: {str(e)}'
        }), 500


@app.route('/unblock_ip', methods=['POST'])
def unblock_ip():
    ip = request.json.get('ip')

    if not ip:
        return jsonify({'status': 'error', 'message': 'IP tidak diberikan'}), 400

    try:
        resp = requests.post(
            f'{RYU_API}/unblock_ip',
            json={'ip': ip},
            timeout=5
        )

        return jsonify({
            'status': 'success',
            'action': 'unblock',
            'ip': ip,
            'ryu_response': resp.json()
        })

    except requests.exceptions.RequestException as e:
        return jsonify({
            'status': 'error',
            'message': f'Gagal ke Ryu: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)