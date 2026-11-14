# FaceAttend — Sistema de Control de Asistencia Facial

**Proyecto académico de reconocimiento facial y registro de asistencia mediante Python, Django, OpenCV y SQLite.**

FaceAttend es una aplicación web local que presenta **una sola interfaz de asistencia**. Al abrirla, solicita acceso a la cámara del navegador, detecta rostros en tiempo real, busca coincidencias en un modelo facial entrenado previamente y, cuando se cumplen las condiciones programadas, registra la asistencia del estudiante en SQLite. También muestra contadores y las últimas asistencias del día sin recargar la página.

> **Estado del proyecto:** las funciones descritas están implementadas en el código del proyecto revisado. Su precisión y funcionamiento integral todavía deben validarse con pruebas. El reconocimiento facial **no constituye una verificación infalible de identidad**.

## 1. Funcionalidades

- **Interfaz única:** no requiere navegar entre módulos para tomar asistencia.
- **Cámara automática:** intenta activar la webcam al cargar la página, sujeto al permiso del navegador.
- **Detección facial:** OpenCV localiza rostros y dibuja recuadros sobre el video.
- **Reconocimiento facial:** utiliza el algoritmo **LBPH (Local Binary Patterns Histograms)** con un modelo entrenado a partir de fotografías precargadas.
- **Identificación por nombre:** asocia la etiqueta numérica del modelo con el estudiante activo guardado en SQLite.
- **Registro automático:** crea una asistencia después de una secuencia de coincidencias aceptadas.
- **Sin duplicados:** un estudiante tiene como máximo una asistencia por sesión diaria.
- **Avisos:** muestra mensajes de asistencia registrada, asistencia previamente registrada, verificación en curso, rostro no identificado y errores.
- **Contadores en vivo:** estudiantes registrados, asistencias del día y estudiantes pendientes de registro.
- **Historial del día:** presenta las **últimas 10 asistencias** (código, nombre, hora y estado).
- **Carga por CSV:** permite agregar o actualizar estudiantes sin una pantalla de registro.
- **Entrenamiento reutilizable:** permite incorporar nuevas fotografías y regenerar el modelo.

**No incluye:** una pantalla para registrar estudiantes, inicio de sesión personalizado, selección de materias, control de permanencia en clase, registro de ausencias confirmado ni una aplicación móvil. La ruta administrativa estándar de Django está configurada, pero los modelos no están registrados en `admin.py`.

## 2. Tecnologías

| Tecnología | Uso en FaceAttend |
|---|---|
| **Python** | Lógica y comandos del proyecto |
| **Django 6.1.3** | Servidor web, vistas, sesiones, ORM y plantillas |
| **SQLite** | Almacenamiento de estudiantes, sesiones y asistencias |
| **OpenCV Contrib 4.13.0.92** | Detectores Haar Cascade y reconocedor LBPH |
| **NumPy 2.4.6** | Procesamiento de imágenes como arreglos |
| **HTML, CSS y JavaScript** | Interfaz, webcam, recuadros y actualización de datos |

SQLite se utiliza a través de Django; no hace falta instalar un servidor de base de datos independiente.

## 3. Estructura del proyecto

La raíz del proyecto es **la carpeta que contiene `manage.py`**:

```text
Asistencia/
├── asistencia/
│   ├── management/
│   │   └── commands/
│   │       ├── cargar_estudiantes.py
│   │       └── entrenar_rostros.py
│   ├── migrations/
│   ├── templates/
│   │   └── asistencia/
│   │       └── inicio.html
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── reconocedor.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── modelos/
│   └── rostros_lbph.yml       # Se genera con el entrenamiento
├── rostros_registrados/
│   ├── EST001/
│   ├── EST002/
│   └── EST003/
├── estudiantes.csv
├── db.sqlite3                 # Se genera con las migraciones
├── manage.py
└── requirements.txt
```

La estructura anterior muestra los archivos funcionales, **sin incluir** `venv/` ni `__pycache__/`. Las carpetas de fotografías pueden contener tantos archivos válidos como se necesiten; los códigos son ejemplos.

## 4. Requisitos previos

- Windows con Python y `pip` instalados, en versiones compatibles con las dependencias indicadas.
- Una webcam accesible desde el navegador, o una webcam externa conectada.
- Microsoft Edge, Google Chrome u otro navegador compatible con `getUserMedia()`.
- Fotografías de referencia proporcionadas por participantes voluntarios y con autorización.
- Acceso a internet durante la primera instalación de paquetes. Luego, el procesamiento de este proyecto se realiza localmente.

Para comprobar Python:

```cmd
python --version
python -m pip --version
```

## 5. Instalación en Windows

**Ejecutar los comandos desde la carpeta que contiene `manage.py`.**

### 5.1 Crear y activar un entorno virtual

En **CMD**:

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

En **PowerShell**, si prefieres utilizarlo:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Al activarse, la terminal suele mostrar `(venv)`.

### 5.2 Instalar dependencias

La versión del ZIP revisado contiene un `requirements.txt` generado con `pip freeze`, con **numerosos paquetes que no utiliza el código actual** (incluidos `torch`, `Flask` y `ultralytics`). **Antes de compartir el proyecto**, se recomienda reemplazar su contenido por estas dependencias directas:

```txt
Django==6.1.3
opencv-contrib-python==4.13.0.92
numpy==2.4.6
```

Una vez corregido `requirements.txt`, ejecutar:

```cmd
python -m pip install -r requirements.txt
```

> No instales `opencv-python` a la vez que `opencv-contrib-python`: ambos distribuyen el módulo `cv2`. El proyecto necesita **Contrib** para `cv2.face.LBPHFaceRecognizer_create()`.

Comprobar que las dependencias están disponibles:

```cmd
python -c "import django, cv2, numpy; print('Dependencias disponibles'); print('LBPH:', hasattr(cv2, 'face') and hasattr(cv2.face, 'LBPHFaceRecognizer_create'))"
```

El resultado de `LBPH` debe ser `True`.

### 5.3 Crear la base de datos SQLite

```cmd
python manage.py migrate
```

Este comando aplica las migraciones existentes y crea `db.sqlite3` si todavía no existe. **No hace falta ejecutar `makemigrations` al agregar fotografías o estudiantes desde CSV.**

### 5.4 Cargar estudiantes

Crear o editar `estudiantes.csv` en la raíz del proyecto, por ejemplo:

```csv
codigo,nombre
EST001,Estudiante Ejemplo Uno
EST002,Estudiante Ejemplo Dos
EST003,Estudiante Ejemplo Tres
```

Estos nombres son ficticios. Asegúrate de que los códigos coincidan con las carpetas de fotografías.

Ejecutar:

```cmd
python manage.py cargar_estudiantes
```

El comando utiliza `update_or_create()`: **crea estudiantes nuevos o actualiza sus nombres según el código**. No elimina automáticamente los estudiantes que se hayan quitado del CSV.

### 5.5 Agregar fotografías de referencia

Colocar las imágenes autorizadas en la carpeta correspondiente:

```text
rostros_registrados/
├── EST001/
│   ├── foto1.jpg
│   └── foto2.jpg
├── EST002/
│   └── foto1.png
└── EST003/
    ├── foto1.jpg
    ├── foto2.jpg
    └── foto3.jpg
```

El comando de entrenamiento revisado admite las extensiones `.jpg`, `.jpeg`, `.png` y `.bmp`. No importa que el archivo tenga otro nombre, siempre que su extensión sea válida y esté en la carpeta correcta.

Se recomienda utilizar **varias fotos con el rostro claramente visible**, buena iluminación, un solo participante por imagen y leves variaciones de posición. El sistema puede rechazar fotografías en las que no encuentre un rostro adecuado.

### 5.6 Entrenar el modelo facial

```cmd
python manage.py entrenar_rostros
```

El entrenamiento:

1. Recorre los estudiantes activos de SQLite.
2. Busca fotografías dentro de `rostros_registrados/<codigo>/`.
3. Prueba detectores Haar y distintas versiones de contraste.
4. Selecciona una región facial cuando cumple sus condiciones.
5. Redimensiona y ecualiza el rostro a **160 × 160 píxeles**.
6. Entrena un reconocedor **LBPH** con las imágenes aceptadas y las etiquetas `Estudiante.id`.
7. Guarda el modelo en `modelos/rostros_lbph.yml`.

Al finalizar, muestra cuántas fotos encontró, aceptó y rechazó. **Si no se acepta ninguna foto, el comando informa el error y no reemplaza el modelo existente.**

No abras ni edites manualmente `rostros_lbph.yml`: es un archivo generado por OpenCV.

### 5.7 Iniciar FaceAttend

Puerto predeterminado:

```cmd
python manage.py runserver
```

Abrir `http://127.0.0.1:8000/`.

O, si deseas utilizar el puerto empleado durante el desarrollo:

```cmd
python manage.py runserver 8002
```

Abrir `http://127.0.0.1:8002/`.

El navegador puede solicitar autorización para la webcam. Al concederla, la página intentará comenzar a procesar imágenes automáticamente.

Para detener Django, presiona `Ctrl + C`. Para desactivar `venv`, ejecuta `deactivate`.

## 6. ¿Cómo funciona la asistencia?

```text
Abrir FaceAttend
       ↓
Autorizar webcam en el navegador
       ↓
JavaScript toma fotogramas periódicos
       ↓
POST /detectar/ → Django + OpenCV
       ↓
Detectar rostro → comparar con LBPH
       ↓
¿Hay exactamente un rostro con coincidencia aceptada?
       ├── No → no registrar; mostrar advertencia
       └── Sí → comprobar coincidencias consecutivas
                     ↓
             ¿Se cumplen 4 coincidencias?
                     ├── No → seguir verificando
                     └── Sí → buscar sesión del día
                                   ↓
                         Registrar si no existe
                                   ↓
                   Actualizar contadores e historial
```

**Detalles concretos del código actual:**

- El navegador envía aproximadamente **un fotograma cada 900 ms** a `/detectar/` y evita solicitudes simultáneas desde la misma página.
- OpenCV busca los rostros en escala de grises.
- El reconocedor LBPH devuelve una **etiqueta de estudiante** y una **distancia**, no un porcentaje de confianza.
- En `asistencia/reconocedor.py`, el umbral actual es **`UMBRAL_RECONOCIMIENTO = 60.0`**, valor **provisional y no calibrado**. Una distancia superior se rechaza.
- Para registrar la asistencia se exigen **4 coincidencias consecutivas**, con intervalos inferiores a 3 segundos y asociadas al mismo estudiante en la sesión del navegador.
- La sesión de asistencia corresponde a **una fecha**, se crea automáticamente cuando corresponde y se encuentra activa.
- `get_or_create()` junto con una restricción de unicidad evita dos registros del mismo estudiante en una sesión diaria.
- Si una identidad es reconocida nuevamente, el backend devuelve `YA_REGISTRADA`; el HTML muestra **«Ya tienes tu asistencia registrada»**.
- Si el rostro se detecta pero **no se identifica**, el sistema no puede determinar si ese estudiante ya asistió y muestra una advertencia en lugar de confirmar su identidad.

> **Limitación importante:** obtener cuatro predicciones consecutivas no equivale a comprobar que la identificación es correcta ni que la persona permaneció durante toda una clase. Este sistema debe utilizarse como demostración académica; no como única prueba de identidad en un entorno real.

## 7. Interfaz web

La página principal (`/`) presenta:

| Sección | Contenido |
|---|---|
| **Reconocimiento facial** | Video de la webcam, recuadros verdes o naranjas, nombre o «Desconocido» |
| **Mensajes** | Verificación, primera asistencia, asistencia ya registrada y errores |
| **Estudiantes registrados** | Cantidad de estudiantes activos en SQLite |
| **Asistencias registradas** | Cantidad de estudiantes activos con asistencia del día |
| **Pendientes de registro** | Total de estudiantes activos menos presentes |
| **Asistencias del día** | Últimos 10 registros con código, nombre, hora y «Presente» |

Los recuadros **verdes** significan que la predicción superó el umbral provisional; los **naranjas** indican que el rostro no se ha identificado. Un recuadro verde **no garantiza** la identidad por sí solo.

La fecha de la cabecera usa el formato del navegador. Los horarios de asistencia los calcula Django según su configuración de zona horaria.

## 8. Base de datos y reglas

Los modelos de `asistencia/models.py` son:

| Modelo | Campos principales | Función |
|---|---|---|
| `Estudiante` | `codigo` (único), `nombre`, `activo` | Identidad del estudiante |
| `SesionAsistencia` | `fecha` (única), `hora_inicio`, `estado` | Sesión de asistencia por día |
| `Asistencia` | `estudiante`, `sesion`, `fecha_hora`, `metodo_verificacion` | Registro de asistencia |

La tabla `Asistencia` posee una restricción única sobre (`estudiante`, `sesion`). El método predeterminado de verificación es `FACIAL`.

**Nota:** la interfaz actual muestra «Pendientes de registro», no ausencias confirmadas. El historial visible presenta solo el día actual y solo los 10 registros más recientes; los demás registros no se eliminan por esa limitación de visualización.

## 9. Rutas y archivos principales

| Ruta o archivo | Función |
|---|---|
| `GET /` | Abre la interfaz principal |
| `POST /detectar/` | Recibe un fotograma JPEG en Base64, procesa rostros y devuelve JSON |
| `asistencia/views.py` | Procesamiento, sesión diaria, registro, contadores e historial |
| `asistencia/reconocedor.py` | Carga el modelo LBPH y busca coincidencias en SQLite |
| `asistencia/management/commands/cargar_estudiantes.py` | Importa/actualiza estudiantes desde CSV |
| `asistencia/management/commands/entrenar_rostros.py` | Entrena y guarda el modelo LBPH |
| `asistencia/templates/asistencia/inicio.html` | Interfaz y lógica del navegador |
| `config/settings.py` | Base de datos, aplicaciones, zona horaria y configuración |

La comunicación con `/detectar/` utiliza peticiones POST y token CSRF de Django. El archivo de video no se almacena permanentemente como parte del flujo normal de procesamiento.

## 10. Cambios habituales

### Agregar una fotografía a un estudiante existente

1. Copiar la imagen a `rostros_registrados/ESTxxx/`.
2. Ejecutar `python manage.py entrenar_rostros`.
3. Reiniciar Django si necesitas asegurarte de que el modelo actualizado se cargue en el proceso activo.

**No necesita migraciones.**

### Agregar un estudiante nuevo

1. Añadir su código y nombre a `estudiantes.csv`.
2. Crear `rostros_registrados/<codigo>/` y colocar fotografías autorizadas.
3. Ejecutar:

```cmd
python manage.py cargar_estudiantes
python manage.py entrenar_rostros
```

**No necesita migraciones.**

### Cambiar el nombre de un estudiante

Editar `estudiantes.csv` y ejecutar:

```cmd
python manage.py cargar_estudiantes
```

El modelo LBPH contiene identificadores numéricos; un cambio de nombre no requiere reentrenarlo **si el `Estudiante.id` no cambió**.

### Reiniciar las asistencias de hoy (solo datos de demostración)

**Atención: elimina registros de manera permanente.** Utilizar únicamente si son datos de prueba que no necesites conservar:

```cmd
python manage.py shell -c "from asistencia.models import Asistencia; from django.utils import timezone; hoy=timezone.localdate(); n=Asistencia.objects.filter(sesion__fecha=hoy).delete()[0]; print('Registros eliminados:', n)"
```

Esto no borra estudiantes, fotos, sesiones ni el modelo facial. Si la sesión diaria se encuentra `CERRADA`, eliminar registros no la vuelve a abrir.

## 11. Errores frecuentes

| Problema | Revisión recomendada |
|---|---|
| `No module named 'cv2'` | Activar el entorno virtual correcto e instalar `opencv-contrib-python` |
| `LBPH: False` | Verificar instalación de OpenCV Contrib y posible conflicto con `opencv-python` |
| `No existe la carpeta rostros_registrados` | La carpeta debe estar junto a `manage.py`, no dentro de la aplicación `asistencia/` |
| `No se encontraron fotografías válidas` | Revisar rutas, formatos, iluminación, tamaño y resultados de detección |
| Rostro identificado como «Desconocido» | Revisar entrenamiento, distancia LBPH y umbral provisional; no aumentarlo a ciegas |
| `No se encontró ninguna cámara` | Comprobar webcam física, permisos del navegador y Windows |
| `No se encuentra estudiantes.csv` | Colocar el CSV en la raíz, al lado de `manage.py` |
| `No installed app with label 'asistencia'` | Verificar `'asistencia'` en `INSTALLED_APPS` |
| Error de modelo no encontrado | Ejecutar entrenamiento con imágenes válidas para generar `modelos/rostros_lbph.yml` |
| Nombre incorrecto | Comprobar los datos de SQLite y que las etiquetas del modelo coincidan con los IDs originales |

Para revisar estudiantes sin modificar la base de datos:

```cmd
python manage.py shell -c "from asistencia.models import Estudiante; print(list(Estudiante.objects.values('id','codigo','nombre','activo')))"
```

## 12. Observaciones detectadas en la versión del proyecto revisada

Estas observaciones corresponden al ZIP del proyecto inspeccionado, no a cambios que este README haya aplicado automáticamente:

1. **Zona horaria duplicada:** `config/settings.py` declara `TIME_ZONE = 'America/Guayaquil'` y, después, `TIME_ZONE = 'UTC'`. **La segunda declaración prevalece.** Si deseas el horario de Ecuador, elimina la segunda y conserva únicamente:

   ```python
   TIME_ZONE = 'America/Guayaquil'
   USE_TZ = True
   ```

2. **Dependencias excesivas:** el `requirements.txt` incluido enumera muchos paquetes que el proyecto no utiliza directamente. Se recomienda dejar las tres dependencias directas indicadas en la sección 5 y verificar la instalación en un entorno limpio.
3. **Pruebas automáticas:** `asistencia/tests.py` se encuentra prácticamente vacío. No se deben presentar pruebas automatizadas como ejecutadas si todavía no se implementaron.
4. **Configuración de desarrollo:** `DEBUG = True`, `ALLOWED_HOSTS = []` y una clave de Django dentro de `settings.py` son propios del entorno local. No publicar esa configuración como despliegue seguro de producción.
5. **Reconocimiento no calibrado:** el umbral `60.0` no está calibrado frente a un conjunto de rostros conocidos y desconocidos; es posible tener falsos rechazos o falsas coincidencias.

## 13. Privacidad y entrega

Las fotografías y los modelos faciales son datos sensibles. Utiliza imágenes de participantes voluntarios con la autorización correspondiente; si se trata de menores, gestiona también la autorización del responsable según corresponda.

Para compartir una versión de código por ZIP o GitHub:

- **Incluir:** `asistencia/`, `config/`, `manage.py`, `requirements.txt`, `README.md`, migraciones y, si procede, un `estudiantes.csv` con datos ficticios.
- **Excluir:** `venv/`, `__pycache__/`, fotografías privadas de `rostros_registrados/`, el modelo biométrico `modelos/rostros_lbph.yml`, `db.sqlite3` con datos reales y cualquier clave o secreto de producción.
- El ZIP inspeccionado **sí contiene** `venv/`, SQLite, fotografías y un modelo entrenado; prepara una copia limpia antes de subirla a un repositorio público.
- Actualmente no existe un archivo `.gitignore` en el ZIP revisado. Conviene crearlo y excluir esos archivos antes de publicar.

**Ejemplo orientativo de `.gitignore`:**

```gitignore
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.env
.env.*
db.sqlite3
rostros_registrados/
modelos/
```

Para una demostración privada, las personas encargadas pueden compartir fotografías autorizadas por un medio restringido y volver a ejecutar el entrenamiento en la computadora de destino. **No basta con copiar un modelo entrenado a una base SQLite nueva si los identificadores de estudiantes cambian.**

## 14. Limitaciones y alcance académico

FaceAttend es una **práctica de reconocimiento facial**, no una solución biométrica lista para producción. El sistema usa LBPH y clasificadores Haar, que pueden presentar dificultades con iluminación variable, ángulos, oclusiones y diferentes cámaras. No tiene verificación de vida (*liveness*) ni un mecanismo completo de confirmación manual en la interfaz. Su función de asistencia registra una presencia candidata validada por reglas del modelo, pero no garantiza identidad ni permanencia durante toda una clase.

Para usos reales harían falta, entre otras cosas, evaluación de precisión, revisión de errores, control de acceso, medidas más estrictas de privacidad y un procedimiento alternativo no biométrico.

---

**FaceAttend — Proyecto académico de control de asistencia facial.**
