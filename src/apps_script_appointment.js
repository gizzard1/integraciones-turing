const HOJA_CITAS = 'citas';
const CALENDAR_ID = 'primary';
const COL_FECHA = 1;
const COL_TITULO = 2;
const COL_DESC = 3;
const COL_CONFIRM = 4;
const DURACION_MIN = 60;

function crearEventos() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hoja = ss.getSheetByName(HOJA_CITAS);
  const cal = CalendarApp.getCalendarById(CALENDAR_ID);

  const datos = hoja.getRange('A2:D100').getValues();

  datos.forEach((r, i) => {
    const fila = i + 2;
    const fecha = r[COL_FECHA - 1];
    const titulo = r[COL_TITULO - 1];
    const desc = r[COL_DESC - 1] || '';
    const confirmado = String(r[COL_CONFIRM - 1] || '').trim().toLowerCase();

    // Saltar filas vacías o ya confirmadas: así evitamos duplicados
    if (!fecha || !titulo) return;
    if (confirmado === 'sí' || confirmado === 'si' || confirmado === 'x') return;

    const inicio = new Date(fecha);
    if (isNaN(inicio.getTime())) {
      Logger.log('Fila ' + fila + ': fecha inválida: ' + fecha);
      return;
    }

    const fin = new Date(inicio.getTime() + DURACION_MIN * 60 * 1000);

    const evento = cal.createEvent(titulo, inicio, fin, {
      description: desc
    });

    hoja.getRange(fila, COL_CONFIRM).setValue('Sí');
    Logger.log('Evento creado fila ' + fila + ': ' + titulo + ' ' + inicio);
  });
}

function onAppointmentChange(e) {
  if (e.changeType === 'INSERT_ROW' || e.changeType === 'EDIT') {
    crearEventos();
  }
}