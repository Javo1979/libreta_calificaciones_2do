"""Importa las notas directas de Segundo I; no publica los datos privados."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import unicodedata
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent
SUBJECTS = [
    ('biologia', 'Biología', '🧬', 'BIOLOGÍA'),
    ('eca', 'Educación Cultural y Artística', '🎨', 'EDUCACION CULTURAL ARTISTICA'),
    ('educacion-fisica', 'Educación Física', '⚽', 'EDUCACIÓN FISICA'),
    ('ciudadania', 'Educación para la Ciudadanía', '🤝', 'EDUCACIÓN PARA LA CIUDADANIA'),
    ('emprendimiento', 'Emprendimiento y Gestión', '🚀', 'EMPRENDIMINETO Y GESTIÓN'),
    ('filosofia', 'Filosofía', '💡', 'FILOSOFÍA'),
    ('fisica', 'Física', '⚛️', 'FÍSICA'),
    ('historia', 'Historia y Ciencias Sociales', '🏛️', 'HISTORIA Y CIENCIAS SOCIALES'),
    ('ingles', 'Inglés', '🌎', 'INGLES'),
    ('lengua', 'Lengua y Literatura', '📚', 'LENGUA Y LITERATURA'),
    ('matematica', 'Matemática', '📐', 'MATEMATICA'),
    ('quimica', 'Química', '🧪', 'QUIMICA'),
    ('civica', 'Cívica y Acompañamiento en el Aula', '🇪🇨', 'CÍVICA Y ACOMPAÑAMIENTO EN EL AULA'),
]

def normalized(value):
    plain = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode()
    return ' '.join(re.findall(r'[A-Z0-9]+', plain.upper()))

def importar(resumen, registro, output=ROOT / 'datos'):
    roster_book = load_workbook(registro, data_only=True)
    roster = {}
    ids = set()
    for row in roster_book['2do I Matemática'].iter_rows(min_row=7, values_only=True):
        if not isinstance(row[0], (int, float)) or not row[1]:
            continue
        key = normalized(row[1])
        if key in roster:
            raise ValueError('Nombre duplicado en el padrón.')
        cedula = row[3]
        if cedula is not None and str(cedula).strip():
            if isinstance(cedula, float) and cedula.is_integer():
                cedula = int(cedula)
            cedula = str(cedula).strip().zfill(10)
            if not re.fullmatch(r'[0-9]{10}', cedula) or cedula in ids:
                raise ValueError('Cédula inválida o duplicada: revisar el padrón.')
            ids.add(cedula)
        else:
            cedula = None
        roster[key] = {'cedula': cedula, 'nombre': ' '.join(str(row[1]).split()), 'notas': {}}
    sheet = load_workbook(resumen, data_only=True)['I ETAPA']
    for col, (_, _, _, expected) in enumerate(SUBJECTS, start=3):
        if normalized(sheet.cell(7, col).value) != normalized(expected):
            raise ValueError(f'La asignatura de la columna {col} cambió; revisar antes de importar.')
    seen = set()
    for row in sheet.iter_rows(min_row=8, values_only=True):
        if not isinstance(row[0], (int, float)) or not row[1]:
            continue
        key = normalized(row[1])
        if key not in roster or key in seen:
            raise ValueError('Nombre sin correspondencia o duplicado en el resumen.')
        seen.add(key)
        for col, (sid, _, _, _) in enumerate(SUBJECTS, start=2):
            value = row[col]
            if value is None or value == '' or (isinstance(value, str) and value.strip().upper() in {'SN', 'S/N', 'SIN NOTA'}):
                grade = None
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and 0 <= value <= 10:
                grade = round(value, 2)
            else:
                raise ValueError(f'Nota inválida en fila {row[0]}, columna {col+1}.')
            roster[key]['notas'][sid] = grade
    if seen != set(roster):
        raise ValueError('Las nóminas no contienen los mismos estudiantes; revisar los archivos.')
    pending = [s for s in roster.values() if s['cedula'] is None]
    data = {
        'actualizado': datetime.now(timezone.utc).isoformat(),
        'periodo': '2026–2027 · Ciclo 1 · I etapa',
        'curso': '2.º de Bachillerato «I»',
        'asignaturas': [{'id': sid, 'nombre': label, 'emoji': emoji} for sid, label, emoji, _ in SUBJECTS],
        'estudiantes': {s['cedula']: s for s in roster.values() if s['cedula'] is not None},
    }
    audit = {
        'total_estudiantes': len(roster), 'habilitados_para_consulta': len(data['estudiantes']),
        'pendientes_de_cedula': len(pending), 'asignaturas': len(SUBJECTS),
        'hoja_origen': 'I ETAPA', 'columnas_notas': 'C:O',
        'notas_registradas': {sid: sum(s['notas'][sid] is not None for s in roster.values()) for sid, _, _, _ in SUBJECTS},
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name, payload in [('calificaciones.json', data), ('pendientes_identificacion.json', pending), ('informe_importacion.json', audit)]:
        (output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return audit

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resumen', type=Path, required=True)
    parser.add_argument('--registro', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(importar(args.resumen, args.registro), ensure_ascii=False, indent=2))
