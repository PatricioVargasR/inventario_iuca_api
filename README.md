# 🖥️ Sistema de Inventario IUCA — API REST

API REST del sistema de inventario institucional del IUCA – Tulancingo. Desarrollada con Flask y PostgreSQL, provee todos los endpoints necesarios para la gestión de equipos de cómputo, mobiliario, responsables, accesos, catálogos y auditoría.

---

## 🚀 Tecnologías

| Tecnología | Versión | Uso |
|---|---|---|
| [Flask](https://flask.palletsprojects.com/) | 3.1.2 | Framework web principal |
| [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) | 3.1.1 | ORM para PostgreSQL |
| [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/) | 4.7.1 | Autenticación con JWT |
| [Flask-CORS](https://flask-cors.readthedocs.io/) | 6.0.2 | Control de CORS |
| [psycopg2-binary](https://www.psycopg.org/) | 2.9.11 | Driver de PostgreSQL |
| [bcrypt](https://pypi.org/project/bcrypt/) | 5.0.0 | Hash de contraseñas |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | 1.2.2 | Variables de entorno |

---

## 📁 Estructura del proyecto

```
├── app.py                  # Fábrica de la aplicación (create_app)
├── config.py               # Configuración por entorno
├── api/
│   └── index.py            # Punto de entrada para Vercel
├── models/
│   ├── __init__.py         # Todos los modelos SQLAlchemy
│   └── mixins.py           # VersionMixin (control de versiones y auditoría)
├── routes/
│   ├── auth_routes.py      # Login, logout, sesión
│   ├── equipos_routes.py   # CRUD de equipos de cómputo
│   ├── mobiliario_routes.py# CRUD de mobiliario
│   ├── usuarios_routes.py  # CRUD de responsables y accesos
│   ├── catalogos_routes.py # CRUD de catálogos
│   ├── historial_routes.py # Consulta de historial de auditoría
│   ├── vistas_routes.py    # Endpoints de vistas desnormalizadas
│   ├── concurrency_routes.py # Bloqueos de concurrencia
│   └── health_routes.py    # Health check
├── utils/
│   ├── concurrency.py      # Lógica de bloqueos optimistas
│   ├── constants.py        # Valores estáticos centralizados
│   ├── crud_catalogo.py    # Generador genérico de CRUD para catálogos
│   ├── decorators.py       # Decorador require_permission
│   ├── error_handlers.py   # Manejadores de errores HTTP globales
│   ├── extesions.py        # Instancias de db y jwt
│   ├── historial_tracker.py# Inyección del usuario en triggers de BD
│   ├── lock_required.py    # Decorador lock_required para DELETE
│   ├── responsables.py     # Utilidad sync_responsables para activos
│   └── validators.py       # Validaciones de entrada por módulo
├── requirements.txt
└── vercel.json
```

---

## ⚙️ Instalación y uso

### Prerrequisitos

- Python >= 3.10
- PostgreSQL >= 14
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd iuca-inventario-api

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Iniciar el servidor
python app.py
```

### Variables de entorno

```env
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_db
JWT_SECRET_KEY=tu_clave_secreta_jwt
SECRET_KEY=tu_clave_secreta_flask
FLASK_DEBUG=True
ORIGINS=http://localhost:5173,https://tu-frontend.vercel.app
```

---

## 📡 Endpoints

Todos los endpoints requieren autenticación JWT salvo `/api/auth/login`.

### Health check — `/api/health`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Verifica que la API está en funcionamiento |

### Autenticación — `/api/auth`

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/login` | Iniciar sesión, retorna JWT |
| `POST` | `/force-login` | Forzar cierre de sesión anterior (mismo dispositivo) |
| `POST` | `/logout` | Cerrar sesión y limpiar token |
| `GET` | `/me` | Obtener usuario actual y validar sesión |

### Equipos de cómputo — `/api/equipos`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/<id>` | Obtener equipo con especificaciones y responsables |
| `POST` | `/` | Crear equipo con especificaciones y responsables |
| `PUT` | `/<id>` | Actualizar equipo (con control de versiones) |
| `DELETE` | `/<id>` | Eliminar equipo (requiere bloqueo previo) |

### Mobiliario — `/api/mobiliario`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Listar mobiliario con filtros y paginación |
| `GET` | `/<id>` | Obtener mueble con responsables |
| `POST` | `/` | Crear mueble con responsables |
| `PUT` | `/<id>` | Actualizar mueble (con control de versiones) |
| `DELETE` | `/<id>` | Eliminar mueble (requiere bloqueo previo) |

### Responsables y accesos — `/api/usuarios`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/responsables` | Listar responsables |
| `GET` | `/responsable/<id>` | Obtener responsable por ID |
| `POST` | `/responsables` | Crear responsable |
| `PUT` | `/responsables/<id>` | Actualizar responsable |
| `DELETE` | `/responsables/<id>` | Eliminar responsable (verifica asignaciones activas) |
| `GET` | `/accesos` | Listar cuentas con permisos |
| `GET` | `/accesos/<id>` | Obtener cuenta por ID |
| `POST` | `/accesos` | Crear cuenta con permisos por módulo |
| `PUT` | `/accesos/<id>` | Actualizar cuenta y/o permisos |
| `DELETE` | `/accesos/<id>` | Eliminar cuenta (no puede auto-eliminarse) |
| `GET` | `/accesos-filtro` | Lista ligera de accesos para filtros del frontend |

### Catálogos — `/api/catalogos`

Cada catálogo (áreas, estados, tipos de activo, tipos de mobiliario) expone los mismos endpoints:

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/{recurso}-completo` | Lista completa sin paginar (solo activos, para selects) |
| `GET` | `/{recurso}` | Lista paginada con búsqueda y filtros |
| `GET` | `/{recurso}/<id>` | Obtener registro por ID |
| `POST` | `/{recurso}` | Crear registro |
| `PUT` | `/{recurso}/<id>` | Actualizar registro |
| `DELETE` | `/{recurso}/<id>` | Eliminar registro (requiere bloqueo previo) |

### Vistas desnormalizadas — `/api/vistas`

Endpoints de lectura optimizada que combinan múltiples tablas:

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/equipos-completo/` | Equipos con tipo, estado, responsables y especificaciones |
| `GET` | `/equipo-completo/<id>` | Detalle completo de un equipo |
| `GET` | `/mobiliarios-completo/` | Mobiliario con tipo, estado y responsables |
| `GET` | `/mobiliario-completo/<id>` | Detalle completo de un mueble |
| `GET` | `/responsables-completo/` | Responsables con conteo de bienes asignados |
| `GET` | `/responsable-completo/<id>` | Detalle de un responsable |
| `GET` | `/accesos-completo/` | Accesos con permisos y filtros avanzados |
| `GET` | `/acceso-completo/<id>` | Detalle de un acceso |

### Historial — `/api/historial`

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Historial paginado con filtros (tabla, operación, usuario, fechas) |
| `GET` | `/<id>` | Detalle de un movimiento con cambios campo a campo |
| `GET` | `/tabla/<tabla>` | Historial de una tabla específica |
| `GET` | `/registro/<tabla>/<id>` | Historial completo de un registro |

### Concurrencia — `/api/concurrency`

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/lock` | Adquirir bloqueo de edición o eliminación |
| `POST` | `/unlock` | Liberar un bloqueo |
| `GET` | `/check-lock` | Verificar estado de bloqueo de un registro |
| `GET` | `/active-locks` | Ver todos los bloqueos activos del sistema |
| `GET` | `/my-locks` | Ver bloqueos del usuario actual |

---

## 🔐 Autenticación

El sistema usa **JWT** con expiración de 8 horas. Cada petición debe incluir el token en el header:

```
Authorization: Bearer <token>
```

### Control de sesión única

Cada usuario solo puede tener una sesión activa a la vez. El sistema distingue dos escenarios:

- **Mismo dispositivo** (misma IP + User-Agent): se puede forzar el inicio de sesión cerrando la sesión anterior mediante `/force-login`.
- **Dispositivo diferente**: el acceso queda bloqueado hasta que el otro dispositivo cierre sesión.

El endpoint `/me` valida en cada petición que el token JWT coincida con el token de sesión activa almacenado en la base de datos, permitiendo invalidar sesiones de forma remota.

---

## 🔒 Permisos

Los permisos se definen por usuario y por módulo. Cada combinación usuario-módulo puede tener habilitados de forma independiente:

- `puede_leer`
- `puede_crear`
- `puede_actualizar`
- `puede_eliminar`

El decorador `@require_permission(modulo, accion)` protege cada endpoint verificando los permisos en base de datos antes de ejecutar la función.

**Módulos disponibles:** `computo`, `mobiliario`, `responsable`, `catalogos`, `historial`, `acceso`.

---

## 🔄 Control de concurrencia

Para evitar conflictos al editar registros simultáneamente, se implementa un sistema de **bloqueos en base de datos** (`bloqueos_activos`):

**Flujo de edición:**
1. El frontend solicita un bloqueo (`POST /api/concurrency/lock`, tipo `edicion`).
2. Si el registro ya está bloqueado por otro usuario, se retorna un `409` con información del usuario que lo tiene.
3. Si el bloqueo es del mismo usuario, se renueva el tiempo de expiración.
4. Al guardar, el backend libera el bloqueo automáticamente.

**Flujo de eliminación:**
1. El frontend solicita un bloqueo (`POST /api/concurrency/lock`, tipo `eliminacion`).
2. El decorador `@lock_required(tabla)` verifica que el bloqueo de eliminación existe antes de ejecutar el `DELETE`.
3. El bloqueo se elimina junto con el registro en la misma transacción.

**Configuración de expiración:**
- Bloqueos de edición: 10 minutos (renovables automáticamente desde el frontend).
- Bloqueos de eliminación: 2 minutos.
- Los bloqueos expirados se limpian automáticamente en cada operación de concurrencia.

---

## 📋 Control de versiones (Optimistic Locking)

Los modelos que heredan de `VersionMixin` (`EquipoComputo`, `Mobiliario`, `Usuario`, `Acceso` y catálogos) cuentan con un campo `version` que se incrementa automáticamente en cada actualización mediante triggers de PostgreSQL.

En los endpoints de actualización (`PUT`), el frontend envía la versión que tiene. Si no coincide con la versión actual en BD, se retorna un `409 conflict` indicando que el registro fue modificado por otro usuario mientras se editaba.

---

## 📊 Historial de auditoría

El historial se registra automáticamente mediante **triggers de PostgreSQL** en las tablas principales. Para asociar cada cambio al usuario que lo realizó, cada petición autenticada ejecuta:

```sql
SET LOCAL app.current_user_id = <id_usuario>;
```

El historial almacena los cambios campo a campo en formato JSON con valores anteriores y nuevos, y los expone de forma legible en los endpoints de `/api/historial`.

---

## 🛠️ Utilidades principales

| Archivo | Descripción |
|---|---|
| `utils/crud_catalogo.py` | Genera las 6 funciones CRUD (completo, paginado, one, create, update, delete) para cualquier modelo de catálogo de forma genérica |
| `utils/validators.py` | Validaciones de entrada con mensajes por campo; incluye `handle_db_error` que traduce errores de PostgreSQL (SQLSTATE) a mensajes legibles |
| `utils/concurrency.py` | Lógica completa de bloqueos: crear, liberar, verificar y limpiar bloqueos expirados |
| `utils/decorators.py` | `@require_permission(modulo, accion)` para proteger endpoints |
| `utils/lock_required.py` | `@lock_required(tabla)` para verificar bloqueo de eliminación antes de ejecutar `DELETE` |
| `utils/responsables.py` | `sync_responsables(...)` calcula el diff entre responsables actuales y nuevos en una tabla pivote, eliminando los que ya no corresponden e insertando los faltantes; funciona con `EquipoResponsable` y `MobiliarioResponsable` |
| `utils/constants.py` | Valores estáticos centralizados: módulos, aliases de búsqueda para historial, mensajes de FK, campos editables por catálogo |

---

## 📝 Notas de desarrollo

- La zona horaria de la base de datos se fuerza a `America/Mexico_City` mediante un listener de SQLAlchemy en cada conexión nueva.
- El pool de conexiones está configurado con `pool_size=10`, `pool_recycle=3600` y `pool_pre_ping=True` para mayor estabilidad.
- Los errores de constraint de PostgreSQL (unicidad, nulo, FK, check) se traducen automáticamente a mensajes legibles en español usando el código SQLSTATE en `handle_db_error`.
- El módulo `historial` excluye de la vista campos de solo auditoría interna (como `ultimo_acceso`, `version`, `contrasena_hash`) para no mostrar ruido innecesario en el historial visible al usuario.
- Los endpoints de equipos y mobiliario aceptan y devuelven `responsables_ids` como array de enteros, permitiendo asignar múltiples responsables por activo.