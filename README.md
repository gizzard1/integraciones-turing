# Integración de Google Sheets con Gmail

Este proyecto documenta una automatización que revisa las ventas de una hoja de
cálculo y envía un correo cuando se detectan ventas pendientes de notificar. El
proceso tuvo dos propuestas de ejecución automática: primero se preparó una
ejecución periódica con Cloud Scheduler y después se implementó la opción final,
disparada al editar la hoja.

## Proceso de elaboración

### 1. Crear y activar Google Workspace

Antes de comenzar, se necesita un dominio propio y acceso a la configuración DNS
del proveedor donde está registrado.

1. Inicia el registro de Google Workspace. Indica los datos de la organización,
   el país y crea la primera cuenta, que será la administradora. Elige un plan
   de acuerdo con las necesidades actuales de la organización.
2. Indica que ya tienes un dominio y escribe el dominio que vas a asociar.

   ![Registro de un dominio propio para Workspace](https://home.agenda-master.com.mx/storage/turing/dia2/step4.png)

3. Verifica la propiedad del dominio. Google proporciona un registro TXT; crea
   ese registro en el panel DNS del proveedor y vuelve al asistente para
   confirmar la verificación. No copies el valor del registro en el README ni
   en capturas públicas.

   ![Pasos para configurar y verificar el dominio](https://home.agenda-master.com.mx/storage/turing/dia2/step6.png)

4. Completa la configuración inicial de Workspace y activa Gmail. Para recibir
   correo en Gmail, configura en DNS los registros MX que indique el asistente
   de Google para ese dominio. Los valores pueden variar; no reutilices valores
   de una captura antigua sin compararlos con las instrucciones actuales.

   ![Finalización del asistente de Workspace](https://home.agenda-master.com.mx/storage/turing/dia2/step8.png)

   ![Ejemplo de configuración de registros MX](https://home.agenda-master.com.mx/storage/turing/dia2/step10.png)

5. Espera la propagación DNS y confirma que el asistente indique que el dominio
   y Gmail están activos.

   ![Confirmación de dominio verificado y Gmail activo](https://home.agenda-master.com.mx/storage/turing/dia2/step11.png)

### 2. Crear usuarios y configurar el acceso

Desde la consola de administración, entra a **Directorio > Usuarios > Añadir
usuario** y crea una cuenta individual para cada persona que necesite usar
Workspace. Asigna las licencias y aplicaciones que correspondan, completa el
proceso de primer acceso y configura métodos de recuperación y verificación en
dos pasos según las políticas de la organización.

Para las integraciones:

- Usa una identidad dedicada para la automatización cuando sea posible; evita
  depender de la cuenta personal de una persona.
- Activa Gmail para la identidad que enviará los avisos y comparte con ella la
  hoja de cálculo. Dale permiso de edición si el proceso debe marcar filas o
  actualizar celdas; usa solo lectura si únicamente va a consultar datos.
- El activador instalable de Apps Script se ejecuta con la identidad de quien
  lo creó. Esa identidad debe poder editar la hoja y enviar correo.
- Si se necesita una dirección común para un equipo, crea un grupo aparte en
  **Directorio > Grupos**, limita quién puede unirse y publicar, e invita solo a
  los miembros necesarios. Un grupo no sustituye a la cuenta que autoriza la
  integración.

  ![Ejemplo de permisos restringidos para un grupo](https://home.agenda-master.com.mx/storage/turing/dia2/step13.png)

Las capturas del listado de usuarios contienen direcciones reales; por eso esta
guía describe su configuración sin volver a publicarlas.

### 3. Configurar proyecto de Google Cloud y OAuth (alternativa Python)

Este paso es necesario para ejecutar [`src/main.py`](src/main.py); no es un
requisito para autorizar el Apps Script final.

1. Crea un proyecto de Google Cloud y habilita las APIs de Google Sheets y
   Gmail.
2. Configura la pantalla de consentimiento de OAuth. Restringe el acceso a los
   usuarios que realmente probarán o utilizarán la aplicación.
3. Crea un cliente OAuth de tipo aplicación de escritorio y descarga su archivo
   JSON.
4. Guarda el archivo como `src/client_secret.json`, instala las dependencias de
   [`src/requirements.txt`](src/requirements.txt) y ejecuta el script. En la
   primera ejecución, inicia sesión con la identidad que tiene acceso a la hoja
   y permiso para enviar el correo.

El programa usa OAuth para Gmail y Sheets. El token y el JSON de cliente son
credenciales: no los compartas ni los subas al repositorio. `src/.gitignore`
excluye `client_secret.json`, `secrets.json` y `token.json`. 

### 4. Alternativa automática: Cloud Scheduler

Como primera propuesta, se creó un trabajo de Cloud Scheduler para ejecutar la
revisión de forma periódica. Las capturas muestran una programación diaria a las
09:00 UTC, en la región `us-west2`, junto con la preparación de una función en
Cloud Run.

Primero se configuró el despliegue de la función desde el repositorio y la rama
principal mediante Cloud Build:

![Configuración del despliegue de la función](https://home.agenda-master.com.mx/storage/turing/dia2/step28.png)

Después se vinculó el repositorio de GitHub como origen del código:

![Selección del repositorio para Cloud Build](https://home.agenda-master.com.mx/storage/turing/dia2/step29.png)

Esta alternativa puede consultarse en el commit 1213241 de [`src/main.py`](src/main.py).
El programa consulta Sheets, calcula el total y usa Gmail para enviar un único
correo con las ventas pendientes. Se conserva como alternativa programada; no
es el flujo final basado en cambios en la hoja.

![Configuración del trabajo de Cloud Scheduler](https://home.agenda-master.com.mx/storage/turing/dia2/step30.png)

### 5. Implementación final: envío al modificar Sheets

La implementación final se preparó en Google Apps Script, asociado a la hoja de
cálculo. El código de referencia está en
[`src/apss_script.js`](src/apss_script.js). El flujo es:

Apps Script permite automatizar la hoja sin desplegar un servicio externo:

![Entorno de Apps Script en Google Workspace](https://home.agenda-master.com.mx/storage/turing/dia2/step1.png)

La hoja contiene las ventas que se revisan y las columnas usadas para calcular
el total:

![Estructura de la hoja de ventas](https://home.agenda-master.com.mx/storage/turing/dia2/step24.png)

1. Leer las filas de ventas y calcular el total usando piezas y subtotal.
2. Identificar las filas que aún no están marcadas como notificadas.
3. Si hay ventas pendientes y cambió el total, enviar un correo con el total
   anterior, el actual y el detalle de las filas pendientes.
4. Marcar las filas enviadas como `Sí` en la columna de notificación.
5. Guardar el total para la siguiente comparación.

Para automatizarlo, se configura un activador instalable desde Apps Script:
función `onChange`, origen **Desde la hoja de cálculo** y tipo de evento **Al
editar**. Así la revisión se ejecuta cuando se modifica la hoja, en lugar de
esperar a una ejecución programada.

Al crear el activador, autoriza los permisos solicitados por Google. Confirma
que el propietario del activador tenga acceso de edición a la hoja y permiso
para enviar correo.

Se abre el editor desde **Extensiones > Apps Script** en la hoja:

![Acceso a Apps Script desde Sheets](https://home.agenda-master.com.mx/storage/turing/dia2/step31.png)

En el editor de Apps Script se abre la sección **Activadores**:

![Acceso a la sección Activadores](https://home.agenda-master.com.mx/storage/turing/dia2/step33.png)

Desde ahí se crea el activador de edición:

![Configuración del activador de edición](https://home.agenda-master.com.mx/storage/turing/dia2/step34.png)

### 6. Comprobación del flujo

Se comprobó que el correo resume el cambio del total y que las filas notificadas
quedan marcadas en la hoja.

![Hoja con ventas marcadas como notificadas](https://home.agenda-master.com.mx/storage/turing/dia2/step26.png)

## Archivos principales

- [`src/apss_script.js`](src/apss_script.js): implementación final con Apps
  Script y activador de cambios.
- [`src/main.py`](src/main.py): alternativa en Python para la ejecución
  programada.
- [`src/requirements.txt`](src/requirements.txt): dependencias de Python.
- [`src/apps_script_appointment.js`](src/apps_script_appointment.js):
  integración aparte para crear eventos de Calendar a partir de citas.

## Configuración y precauciones

- Configura en el código la hoja, el destinatario y los datos de acceso que
  correspondan a tu entorno; no publiques credenciales, tokens ni secretos.
- Para ejecutar la alternativa Python se necesitan las APIs de Sheets y Gmail,
  las dependencias de `src/requirements.txt` y un archivo OAuth local. La
  primera ejecución solicita autorización y crea el token local.
- Antes de activar la implementación final, verifica las columnas y el rango de
  datos de tu hoja.
- **Revisar las celdas del total en `src/apss_script.js`:** actualmente el
  script lee `H2` como total anterior y escribe el nuevo total en `G2`. Para
  comparar ejecuciones sucesivas correctamente, ambas operaciones deben usar
  la celda destinada al total de referencia.
