import json
from pathlib import Path
import tempfile
import unittest
from openpyxl import Workbook
from importar_notas import SUBJECTS, importar

class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root = Path(self.temp.name)
        self.resumen = self.root / 'resumen.xlsx'
        self.registro = self.root / 'registro.xlsx'
        self.output = self.root / 'datos'
        roster = Workbook()
        sheet = roster.active
        sheet.title = '2do I Matemática'
        for row, name, cedula in [(7, 'Alumno De Prueba', '0123456789'), (8, 'Alumno Sin Cedula', None)]:
            sheet.cell(row, 1, row-6)
            sheet.cell(row, 2, name)
            if cedula:
                sheet.cell(row, 4, cedula)
        roster.save(self.registro)
        self.book = Workbook()
        sheet = self.book.active
        sheet.title = 'I ETAPA'
        for col, (_, _, _, header) in enumerate(SUBJECTS, start=3):
            sheet.cell(7, col, header)
        sheet.cell(8, 1, 1)
        sheet.cell(8, 2, 'ALUMNO  DE PRUEBA')
        sheet.cell(8, 3, 9.73)
        sheet.cell(8, 4, 0)
        sheet.cell(9, 1, 2)
        sheet.cell(9, 2, 'ALUMNO SIN CEDULA')
        sheet.cell(9, 3, 8.46)
        self.book.save(self.resumen)

    def tearDown(self):
        self.temp.cleanup()

    def test_direct_grades_zero_missing_and_pending_id(self):
        audit = importar(self.resumen, self.registro, self.output)
        self.assertEqual(audit['total_estudiantes'], 2)
        self.assertEqual(audit['habilitados_para_consulta'], 1)
        self.assertEqual(audit['pendientes_de_cedula'], 1)
        data = json.loads((self.output / 'calificaciones.json').read_text(encoding='utf-8'))
        grades = data['estudiantes']['0123456789']['notas']
        self.assertEqual(grades['biologia'], 9.73)
        self.assertEqual(grades['eca'], 0)
        self.assertIsNone(grades['fisica'])
        self.assertEqual(len(grades), 13)
        pending = json.loads((self.output / 'pendientes_identificacion.json').read_text(encoding='utf-8'))
        self.assertEqual(pending[0]['notas']['biologia'], 8.46)

    def test_header_change_is_not_silently_imported(self):
        self.book.active.cell(7, 3, 'OTRA ASIGNATURA')
        self.book.save(self.resumen)
        with self.assertRaises(ValueError):
            importar(self.resumen, self.registro, self.output)

    def test_unknown_student_is_not_guessed(self):
        self.book.active.cell(8, 2, 'OTRA PERSONA')
        self.book.save(self.resumen)
        with self.assertRaises(ValueError):
            importar(self.resumen, self.registro, self.output)

    def test_invalid_grade_is_rejected(self):
        self.book.active.cell(8, 3, 100)
        self.book.save(self.resumen)
        with self.assertRaises(ValueError):
            importar(self.resumen, self.registro, self.output)
