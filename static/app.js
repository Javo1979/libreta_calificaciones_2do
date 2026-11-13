const form = document.querySelector('#lookup-form');
const input = document.querySelector('#cedula');
const error = document.querySelector('#form-error');
const button = document.querySelector('#search-button');
const results = document.querySelector('#results');
const welcome = document.querySelector('#welcome');
const grid = document.querySelector('#grades-grid');
let pending = false;
const number = new Intl.NumberFormat('es-EC', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function hideResults() {
  results.hidden = true;
  welcome.hidden = false;
  grid.replaceChildren();
  document.querySelector('#student-name').textContent = '';
  document.querySelector('#student-id').textContent = '';
}
function showError(message) {
  error.textContent = message;
  error.hidden = false;
  input.setAttribute('aria-invalid', 'true');
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function gradeRow(subject, index) {
  const grade = subject.nota;
  const state = grade === null ? 'pending' : grade >= 9 ? 'excellent' : grade >= 7 ? 'good' : 'improve';
  const message = grade === null ? 'Consulta con tu docente.'
    : grade >= 9.5 ? '¡Excelente, sigue brillando!'
    : grade >= 9 ? '¡Gran trabajo, sigue así!'
    : grade >= 8 ? '¡Buen avance, sigue practicando!'
    : grade >= 7 ? '¡Sigue así, puedes mejorar!'
    : grade >= 5 ? 'Refuerza los temas con tu docente.'
    : 'Pide apoyo y practica cada día.';
  const row = element('li', `grade-row ${state} subject-color-${index % 7}`);
  const icon = element('span', 'row-icon', subject.emoji);
  icon.setAttribute('aria-hidden', 'true');
  const detail = element('div', 'row-detail');
  detail.append(element('h3', 'row-subject', subject.nombre));
  const recommendation = element('p', 'row-message', message);
  const symbol = element('span', 'message-symbol', grade === null ? '◷ ' : grade >= 9 ? '★ ' : grade >= 7 ? '✦ ' : '↗ ');
  symbol.setAttribute('aria-hidden', 'true');
  recommendation.prepend(symbol);
  detail.append(recommendation);
  const value = element('div', 'final-grade', grade === null ? 'Sin nota' : number.format(grade));
  value.setAttribute('aria-label', grade === null ? 'Sin nota final' : `Promedio final: ${number.format(grade)} sobre 10`);
  if (grade !== null) value.append(element('span', 'grade-scale', '/ 10'));
  row.append(icon, detail, value);
  return row;
}

input.addEventListener('input', () => {
  error.hidden = true;
  input.removeAttribute('aria-invalid');
  hideResults();
});
form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (pending) return;
  hideResults();
  error.hidden = true;
  input.removeAttribute('aria-invalid');
  const cedula = input.value.trim();
  if (!/^[0-9]{10}$/.test(cedula)) {
    showError('Ingresa los 10 dígitos de tu cédula, sin espacios ni guiones.');
    input.focus();
    return;
  }
  pending = true;
  button.disabled = true;
  input.readOnly = true;
  form.setAttribute('aria-busy', 'true');
  button.textContent = 'Consultando…';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('/api/consulta', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cedula }), signal: controller.signal, cache: 'no-store',
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo realizar la consulta. Inténtalo nuevamente.');
    document.querySelector('#student-name').textContent = data.nombre;
    document.querySelector('#student-id').textContent = `Cédula ${data.cedula}`;
    document.querySelector('#period-label').textContent = data.periodo;
    grid.replaceChildren(...data.asignaturas.map(gradeRow));
    input.value = '';
    results.hidden = false;
    welcome.hidden = true;
    results.focus({ preventScroll: true });
    results.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'start' });
  } catch (exception) {
    showError(exception.name === 'AbortError' ? 'La consulta tardó demasiado. Inténtalo otra vez.' : exception instanceof TypeError ? 'No se pudo conectar. Revisa tu conexión e inténtalo nuevamente.' : exception.message);
  } finally {
    clearTimeout(timeout);
    pending = false;
    button.disabled = false;
    input.readOnly = false;
    form.removeAttribute('aria-busy');
    button.replaceChildren(document.createTextNode('Consultar calificaciones '), element('span', '', '→'));
  }
});
document.querySelector('#clear-button').addEventListener('click', () => {
  hideResults();
  form.reset();
  error.hidden = true;
  input.removeAttribute('aria-invalid');
  input.focus();
});
document.querySelector('#print-button').addEventListener('click', () => {
  if (!results.hidden && grid.children.length > 0 && !pending) window.print();
});
// No conservar el reporte al volver desde otra página mediante el historial.
window.addEventListener('pageshow', (event) => { if (event.persisted) { hideResults(); form.reset(); } });
