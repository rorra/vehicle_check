# Vehicle Check API

Sistema backend para gestionar inspecciones anuales de vehículos, citas y resultados de inspección. Construido con FastAPI y SQLAlchemy.

## Descripción General

Esta API proporciona funcionalidad para:
- Gestión de usuarios con acceso basado en roles (CLIENT, INSPECTOR, ADMIN)
- Registro y seguimiento de vehículos
- Programación y gestión de inspecciones anuales
- Reserva y confirmación de citas
- Resultados de inspección con verificaciones detalladas de ítems

## Stack Tecnológico

- **FastAPI** - Framework web para construir APIs
- **SQLAlchemy** - ORM para interacciones con la base de datos
- **MySQL** - Base de datos con driver PyMySQL
- **Alembic** - Herramienta de migración de base de datos
- **Pydantic** - Validación de datos y gestión de configuración

## Instrucciones de Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copiar el archivo de ejemplo de entorno y actualizar con las credenciales de su base de datos:

```bash
cp .env.example .env
```

Editar `.env` y configurar los detalles de la aplicación.

**Nota sobre Gmail:** Para usar Gmail como servidor SMTP, necesitas crear una contraseña de aplicación. Ve a tu cuenta de Google → Seguridad → Verificación en dos pasos → Contraseñas de aplicaciones.

### 3. Crear Base de Datos

Primero, crear las bases de datos MySQL (una para desarrollo y otra para pruebas):

```sql
CREATE DATABASE vehicle_check;
CREATE DATABASE vehicle_check_test;
```

Luego ejecutar las migraciones de Alembic para crear todas las tablas:

```bash
# Aplicar las migraciones existentes
alembic upgrade head
```

**Nota:** Si necesitas crear una nueva migración después de modificar los modelos:

```bash
# Generar una nueva migración automáticamente
alembic revision --autogenerate -m "descripción de los cambios"

# Aplicar la nueva migración
alembic upgrade head
```

Opcionalmente puedes crear datos de prueba:
```bash
python scripts/create_test_data.py
```

## Ejecutar la Aplicación

### Opción 1: Usando el script de inicio (recomendado)

```bash
python run.py
```

### Opción 2: Usando uvicorn directamente

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Parámetros:**
- `--reload`: Recarga automática cuando detecta cambios en el código
- `--host 0.0.0.0`: Permite conexiones desde cualquier IP (usa `127.0.0.1` para solo local)
- `--port 8000`: Puerto en el que escucha el servidor

La API estará disponible en `http://localhost:8000`

## Documentación de la API

Una vez que el servidor esté ejecutándose, puede acceder a:
- Documentación interactiva de la API: `http://localhost:8000/docs`
- Documentación alternativa de la API: `http://localhost:8000/redoc`

## Protección de Endpoints y Roles

El sistema incluye un sistema de autenticación y autorización basado en roles. Todos los endpoints protegidos requieren un token JWT válido en el header `Authorization`.

### Validación de Sesión

Todos los endpoints protegidos validan que:
- El token JWT sea válido y no haya expirado
- La sesión exista en la base de datos y no haya sido revocada
- El usuario esté activo

## Pruebas

El proyecto incluye una suite completa de pruebas unitarias para todos los modelos de la base de datos.

**Importante:** Las pruebas utilizan una base de datos MySQL real (`vehicle_check_test`) configurada en `DATABASE_TEST_URL` del archivo `.env`. Asegúrese de que la base de datos de pruebas esté creada antes de ejecutar las pruebas.

### Ejecutar Todas las Pruebas

```bash
pytest tests/
```

### Ejecutar Pruebas con Cobertura

```bash
pytest tests/ --cov=app --cov-report=html
```

Esto generará un reporte de cobertura en `htmlcov/index.html`
