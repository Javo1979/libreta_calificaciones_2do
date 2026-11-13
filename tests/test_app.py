import json
import unittest
from unittest.mock import patch
from app import app, attempts

FIXTURE = {
    'periodo': 'Agosto 2026 – Enero 2027',
    'asignaturas': [
        {'id': 'mat', 'nombre': 'Matemática', 'emoji': '📐'},
        {'id': 'fis', 'nombre': 'Física', 'emoji': '⚛️'},
        {'id': 'len', 'nombre': 'Lengua', 'emoji': '📚'},
    ],
    'estudiantes': {
        '0123456789': {'nombre': 'Estudiante de prueba', 'notas': {'mat': 9.86, 'fis': None, 'len': 0}},
        '0000000001': {'nombre': 'Otro estudiante', 'notas': {}},
    },
}

class PortalTests(unittest.TestCase):
    def setUp(self):
        attempts.clear()
        self.client = app.test_client()
        self.mock = patch('pathlib.Path.read_text', return_value=json.dumps(FIXTURE))
        self.mock.start()

    def tearDown(self):
        self.mock.stop()

    def test_page_and_assets(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        for path in ['/static/app.js', '/static/styles.css', '/static/libreta.css', '/static/print.css', '/static/sello.png']:
            result = self.client.get(path)
            self.assertEqual(result.status_code, 200)
            result.close()

    def test_individual_report_and_zero_vs_missing(self):
        response = self.client.post('/api/consulta', json={'cedula': '0123456789'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['cedula'], '••••••6789')
        self.assertEqual([s['nota'] for s in data['asignaturas']], [9.86, None, 0])
        self.assertNotIn('0123456789', response.get_data(as_text=True))
        self.assertNotIn('Otro estudiante', response.get_data(as_text=True))

    def test_leading_zero_and_missing_subjects(self):
        result = self.client.post('/api/consulta', json={'cedula': '0000000001'})
        self.assertEqual(result.status_code, 200)
        self.assertTrue(all(s['nota'] is None for s in result.json['asignaturas']))

    def test_invalid_inputs(self):
        for body in ({}, [], {'cedula': 1234567890}, {'cedula': '123'}, {'cedula': 'abcdefghij'}, {'cedula': '<script>x<'}, {'cedula': '０１２３４５６７８９'}):
            self.assertEqual(self.client.post('/api/consulta', json=body).status_code, 400)

    def test_unknown_and_private_files(self):
        self.assertEqual(self.client.post('/api/consulta', json={'cedula': '9999999999'}).status_code, 404)
        for path in ['/datos/calificaciones.json', '/importar_notas.py', '/static/../datos/calificaciones.json']:
            self.assertEqual(self.client.get(path).status_code, 404)
        self.assertEqual(self.client.get('/api/consulta').status_code, 405)

    def test_cross_site_blocked(self):
        result = self.client.post('/api/consulta', json={'cedula': '0123456789'}, headers={'Sec-Fetch-Site': 'cross-site'})
        self.assertEqual(result.status_code, 403)

    def test_rate_limit(self):
        for _ in range(12):
            self.assertEqual(self.client.post('/api/consulta', json={'cedula': '0123456789'}).status_code, 200)
        self.assertEqual(self.client.post('/api/consulta', json={'cedula': '0123456789'}).status_code, 429)

    def test_security_headers(self):
        response = self.client.get('/')
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertEqual(response.headers['X-Frame-Options'], 'DENY')
        self.assertIn("script-src 'self'", response.headers['Content-Security-Policy'])

    def test_unavailable_data(self):
        with patch('pathlib.Path.read_text', side_effect=OSError):
            self.assertEqual(self.client.post('/api/consulta', json={'cedula': '0123456789'}).status_code, 503)

if __name__ == '__main__':
    unittest.main()
