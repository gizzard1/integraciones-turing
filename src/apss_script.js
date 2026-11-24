const HOJA = 'Hoja 1';
const COLUMNA_PZS = 3;
const COLUMNA_SUBTOTAL = 4;
const COLUMNA_NOTIFICADA = 5;
const DESTINATARIO = 'admin@agenda-master.com.mx';

function revisarVentas() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const hoja = ss.getSheetByName(HOJA);

  const datos = hoja.getRange('A2:E100').getValues();
  const filas = datos.filter(r => r[0] !== '' && r[0] !== null);

  // 1. Calcular total acumulado
  let total = 0;
  filas.forEach(r => {
    const monto = parseFloat(r[COLUMNA_SUBTOTAL - 1]) * parseFloat(r[COLUMNA_PZS - 1]);
    if (!isNaN(monto)) total += monto;
  });

  // 2. Leer total anterior guardado en Resumen!A2
  let lastTotal = hoja.getRange('H2').getValue();
  if (lastTotal === '' || lastTotal === null) {
    hoja.getRange('H2').setValue(total);
    Logger.log('Primera revisión. Total: ' + total);
    return;
  }

  // 3. Ventas no notificadas: columna E vacía o "No"
  const pendientes = [];
  filas.forEach((r, i) => {
    const notificada = String(r[COLUMNA_NOTIFICADA - 1] || '').trim().toLowerCase();
    if (notificada !== 'sí' && notificada !== 'si' && notificada !== 'x') {
      pendientes.push({ fila: i + 2, datos: r });
    }
  });

  if (total === lastTotal || pendientes.length === 0) {
    Logger.log('Sin cambios. Total sigue en ' + total);
    return;
  }

  // 4. Mandar UN correo con todas las ventas nuevas
  const lineas = pendientes.map(p => '- Fila ' + p.fila + ': ' + p.datos.join(' | ')).join('\n');
  const cuerpo =
    'Cambió el total acumulado de ventas.\n\n' +
    'Total anterior: ' + lastTotal + '\n' +
    'Total actual: ' + total + '\n' +
    'Diferencia: ' + (total - lastTotal) + '\n\n' +
    'Ventas no notificadas:\n' + lineas;

  GmailApp.sendEmail(
    DESTINATARIO,
    'Total de ventas cambió: ' + lastTotal + ' → ' + total,
    cuerpo
  );

  // 5. Marcar esas filas como "Sí" en la columna E
  pendientes.forEach(p => {
    hoja.getRange(p.fila, COLUMNA_NOTIFICADA).setValue('Sí');
  });

  // 6. Actualizar el total guardado
  hoja.getRange('G2').setValue(total);
  Logger.log('Correo enviado. ' + pendientes.length + ' venta(s) marcadas.');
}

function onChange(e) {
  // Se dispara solo cuando se agrega o edita algo
    revisarVentas();
}