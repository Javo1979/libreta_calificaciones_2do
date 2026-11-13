from pathlib import Path
from collections import defaultdict, deque
import json
import os
import re
import threading
import time
from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

ROOT = Path(__file__).resolve().parent
app = Flask(__name__)
if os.environ.get('TRUST_PROXY') == '1':
    # Activar solo detrás del proxy de confianza del alojamiento.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
app.config['MAX_CONTENT_LENGTH'] = 2048
attempts = defaultdict(deque)
lock = threading.Lock()

@app.after_request
def secure(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
    return response

@app.get('/')
def index():
    return render_template('index.html')

@app.post('/api/consulta')
def consulta():
    if request.headers.get('Sec-Fetch-Site') == 'cross-site':
        return jsonify(error='Consulta no permitida.'), 403
    with lock:
        now = time.monotonic()
        # Acotar memoria y no conservar direcciones más allá de la ventana.
        for ip in list(attempts):
            while attempts[ip] and now - attempts[ip][0] > 60:
                attempts[ip].popleft()
            if not attempts[ip]:
                del attempts[ip]
        queue = attempts[request.remote_addr]
        if len(queue) >= 12:
            response = jsonify(error='Has realizado varias consultas. Espera un minuto e inténtalo de nuevo.')
            response.headers['Retry-After'] = '60'
            return response, 429
        queue.append(now)
    body = request.get_json(silent=True)
    cedula = body.get('cedula', '') if isinstance(body, dict) else ''
    if not isinstance(cedula, str) or not re.fullmatch(r'[0-9]{10}', cedula):
        return jsonify(error='Ingresa los 10 dígitos de tu cédula, sin espacios ni guiones.'), 400
    try:
        data_path = Path(os.environ.get('CALIFICACIONES_PATH', str(ROOT / 'datos' / 'calificaciones.json')))
        data = json.loads(data_path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return jsonify(error='El registro no está disponible. Comunícate con la institución.'), 503
    student = data['estudiantes'].get(cedula)
    if student is None:
        return jsonify(error='No encontramos un registro con esa cédula. Revisa los dígitos o consulta con Secretaría.'), 404
    return jsonify(
        nombre=student['nombre'], cedula='••••••' + cedula[-4:],
        periodo=data['periodo'],
        asignaturas=[dict(s, nota=student['notas'].get(s['id'])) for s in data['asignaturas']],
    )

if __name__ == '__main__':
    from waitress import serve
    print('Portal de calificaciones de Segundo I: http://127.0.0.1:5001', flush=True)
    serve(app, host='127.0.0.1', port=5001)
