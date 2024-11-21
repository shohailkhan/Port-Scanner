from flask import Flask, request, jsonify, render_template
import socket
import threading
import queue

app = Flask(__name__)


port_states = {}


def scan_port(target_host, port, result):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result_code = sock.connect_ex((target_host, port))
        if result_code == 0:
            result[port] = 'open'
        else:
            result[port] = 'closed'
        sock.close()
    except Exception as e:
        result[port] = 'error'


def perform_scan(target_host, start_port, end_port):
    result = {}
    port_queue = queue.Queue()

    def worker():
        while True:
            port = port_queue.get()
            scan_port(target_host, port, result)
            port_queue.task_done()

   
    for _ in range(100):
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()

   
    for port in range(start_port, end_port + 1):
        port_queue.put(port)

   
    port_queue.join()

    return result


@app.route('/scan', methods=['POST'])
def scan():
    data = request.get_json()
    target_host = data.get('host')
    start_port = int(data.get('start_port'))
    end_port = int(data.get('end_port'))

    if not target_host or not start_port or not end_port:
        return jsonify({'error': 'Missing required parameters'}), 400

   
    result = perform_scan(target_host, start_port, end_port)
    return jsonify(result)


@app.route('/open_port', methods=['POST'])
def open_port():
    data = request.get_json()
    port = data.get('port')

    if port not in port_states:
        port_states[port] = 'open'
        return jsonify({'message': f'Port {port} opened.'}), 200
    else:
        return jsonify({'message': f'Port {port} is already open.'}), 400


@app.route('/close_port', methods=['POST'])
def close_port():
    data = request.get_json()
    port = data.get('port')

    if port in port_states:
        del port_states[port]
        return jsonify({'message': f'Port {port} closed.'}), 200
    else:
        return jsonify({'message': f'Port {port} was not open.'}), 400


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
