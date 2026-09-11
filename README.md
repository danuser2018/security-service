# Security Service — Especificación Técnica

## 1. Visión general

El **Security Service** (`security-service`) es la autoridad centralizada de seguridad y autorización **User → Service** dentro del ecosistema Nova. Su propósito principal es evaluar si las acciones planificadas en un `ExecutionPlan` solicitado por un usuario pueden ejecutarse de forma segura según el canal de entrada (`voice`, `cli`, `api`) y las políticas de riesgo configuradas.

El servicio opera bajo una estricta filosofía binaria (**ALLOW** o **DENY**) y aplica el principio fundamental de **Fail Closed**: cualquier dato faltante, inconsistencia, canal desconocido o riesgo no determinable resulta en la denegación inmediata de todo el plan. En caso de autorización exitosa (`ALLOW`), emite tokens criptográficos HMAC-SHA256 (JWT/HS256) de único uso vinculados a cada acción y ejecución.

---

## 2. Principios de diseño

1. **Fail Closed Absoluto:** Si el servicio no puede demostrar positivamente que una acción está autorizada, la deniega. La ausencia de información equivale a `DENY`.
2. **Independencia del mecanismo de ejecución:** El servicio no conoce cómo se ejecutan los comandos, aplicaciones o APIs de terceros; evalúa abstracciones de acciones, canales y riesgos.
3. **El riesgo pertenece a la acción:** Cada plugin o capacidad define su política de riesgo (`fixed` o `lookup`). El cliente que solicita la autorización (`interaction-manager`) no puede imponer arbitrariamente el nivel de riesgo.
4. **El canal pertenece al contexto de seguridad:** Las políticas de riesgo máximo admitido por canal son propiedad exclusiva de `security-service`.
5. **Evaluación atómica del plan:** Los planes de ejecución no admiten ejecución parcial. Si una sola acción es denegada, se deniega el plan completo y se emiten cero tokens.
6. **Tokens criptográficos acotados (Single-Use):** Cada token de autorización expedido está vinculado estrictamente a un `execution_id` y `action_id`, con tiempo de vida limitado (`expires_at`), impidiendo su reutilización en otras acciones o ejecuciones.

---

## 3. Responsabilidades

### Lo que HACE:
- Mantener en memoria el registro de acciones publicadas por los plugins de `orchestrator` (`POST /v1/security/actions/register`).
- Mantener en memoria el catálogo de comandos del sistema y sus niveles de riesgo publicados por `host-service` (`POST /v1/security/tables/{table_name}`).
- Gestionar los umbrales de riesgo aceptables por canal (`GET` y `PUT /v1/security/channels`).
- Evaluar de forma determinista solicitudes de autorización de planes de ejecución (`POST /v1/security/authorize`).
- Generar y verificar tokens de autorización firmados criptográficamente mediante HMAC-SHA256 (JWT/HS256).

### Lo que NO HACE:
- Ejecutar código, scripts o comandos en el host o en plugins.
- Gestionar identidades de usuario, contraseñas o autenticación Service → Service.
- Diálogos de confirmación interactiva, 2FA, TOTP o pasos de verificación multi-turno (fuera de alcance del MVP).
- Persistencia en base de datos en el MVP (el estado es deliberadamente volátil en memoria; los emisores re-registran en el arranque).

---

## 4. Arquitectura interna

El servicio sigue una arquitectura modular en Python con FastAPI:

```text
security-service/
├── app/
│   ├── api/
│   │   └── routes.py                 # Definición de endpoints REST y ruteo
│   ├── config.py                     # Configuración y variables de entorno (BaseSettings)
│   ├── main.py                       # Punto de entrada FastAPI y ensamblado de dependencias
│   ├── models/
│   │   └── security.py               # Modelos Pydantic (RiskLevel, RiskPolicy, Requests/Responses)
│   └── services/
│       ├── action_registry.py        # Registro en memoria de acciones de plugins
│       ├── authorization_engine.py   # Motor central de autorización y evaluación atómica
│       ├── channel_policy_manager.py # Gestión en memoria de políticas por canal
│       ├── lookup_table_registry.py  # Registro en memoria de tablas de búsqueda dinámicas
│       ├── risk_evaluator.py         # Evaluador de riesgo efectivo (fixed y lookup)
│       └── token_manager.py          # Generador y verificador de tokens HMAC-SHA256 (JWT)
├── tests/                            # Suite exhaustiva de pruebas unitarias y de integración
├── Dockerfile                        # Imagen Docker de producción (python:3.11-slim)
├── requirements.txt                  # Dependencias del servicio
└── README.md                         # Esta especificación
```

---

## 5. Modelo de riesgo

### 5.1 Niveles de riesgo (`RiskLevel`)
Valores semánticos y estrictamente ordenables:
```text
low < medium < high
```

| Nivel | Semántica | Ejemplos |
|---|---|---|
| `low` | Consultas de información pura, operaciones de solo lectura y bajo impacto. | Saludo, hora, clima, estado de volumen, ayuda. |
| `medium` | Acciones que modifican estado local, hardware o generan artefactos salientes. | Subir/bajar volumen, silenciar, generar correo de capacidades/festivos, backup. |
| `high` | Acciones con impacto sistémico potencialmente destructivo o crítico. | Formatear disco, comandos privilegiados del sistema. |

### 5.2 Políticas de riesgo (`RiskPolicy`)

1. **Política Fija (`fixed`):**
   El riesgo es constante e independiente de los parámetros.
   ```json
   {
     "policy": "fixed",
     "value": "medium"
   }
   ```

2. **Política de Búsqueda (`lookup`):**
   El riesgo se determina dinámicamente buscando el valor de un parámetro en una tabla registrada (ej. `host_commands`).
   ```json
   {
     "policy": "lookup",
     "source": "command",
     "table": "host_commands"
   }
   ```
   * Si el parámetro no está presente en la solicitud → `DENY`.
   * Si la tabla no existe o el valor no está catalogado → `DENY`.

### 5.3 Políticas por canal
Configuración inicial por defecto en memoria:

| Canal | Riesgo máximo admitido (`max_risk`) | Justificación |
|---|---|---|
| `voice` | `high` | Canal principal interactivo local por voz. |
| `cli` | `medium` | Línea de comandos / scripts de automatización. |
| `api` | `low` | Acceso programático remoto o no supervisado. |

---

## 6. Endpoints REST

### 1. Registrar acciones de plugins
- **Ruta:** `POST /v1/security/actions/register`
- **Descripción:** Invocado por `orchestrator` al arrancar para registrar las acciones y políticas de riesgo de todos los plugins cargados.
- **Request Body:**
```json
{
  "plugin_id": "volume",
  "actions": [
    {
      "id": "volume-up",
      "risk": {
        "policy": "fixed",
        "value": "medium"
      }
    }
  ]
}
```
- **Response (200 OK):**
```json
{
  "success": true,
  "registered_actions": 1
}
```

---

### 2. Registrar catálogo en tabla de búsqueda
- **Ruta:** `POST /v1/security/tables/{table_name}`
- **Ejemplo:** `POST /v1/security/tables/host_commands`
- **Descripción:** Invocado por `host-service` al arrancar para publicar los comandos del sistema y su nivel de riesgo.
- **Request Body:**
```json
{
  "commands": [
    {"name": "calculator", "risk": "low"},
    {"name": "github", "risk": "low"},
    {"name": "backup", "risk": "medium"},
    {"name": "format-disk", "risk": "high"}
  ]
}
```
- **Response (200 OK):**
```json
{
  "success": true,
  "table": "host_commands",
  "entries_registered": 4
}
```

---

### 3. Autorizar ExecutionPlan
- **Ruta:** `POST /v1/security/authorize`
- **Descripción:** Invocado por `interaction-manager` tras la resolución del plan para verificar si procede su ejecución.
- **Request Body:**
```json
{
  "execution_plan": {
    "execution_id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
    "actions": [
      {
        "action_id": "volume-up",
        "parameters": {}
      }
    ]
  },
  "security_context": {
    "channel": "voice"
  }
}
```

- **Respuesta ALLOW (200 OK):**
```json
{
  "decision": "ALLOW",
  "authorization_tokens": [
    {
      "action_id": "volume-up",
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
  ],
  "reason": null
}
```

- **Respuesta DENY (200 OK):**
```json
{
  "decision": "DENY",
  "authorization_tokens": null,
  "reason": "Action 'format-disk' effective risk 'high' exceeds channel 'cli' max risk 'medium'"
}
```

---

### 4. Consultar políticas de canales
- **Ruta:** `GET /v1/security/channels`
- **Response (200 OK):**
```json
{
  "channels": {
    "voice": {"max_risk": "high"},
    "cli": {"max_risk": "medium"},
    "api": {"max_risk": "low"}
  }
}
```

---

### 5. Actualizar política de un canal
- **Ruta:** `PUT /v1/security/channels/{channel_id}`
- **Request Body:**
```json
{
  "max_risk": "high"
}
```
- **Response (200 OK):**
```json
{
  "success": true,
  "channel": "cli",
  "max_risk": "high"
}
```

---

### 6. Health Check
- **Ruta:** `GET /health`
- **Response (200 OK):**
```json
{
  "status": "ok"
}
```

---

## 7. Estructura y validación del token de autorización

Los tokens de autorización emitidos siguen el estándar **JWT firmado mediante HMAC-SHA256 (algoritmo HS256)** utilizando la clave simétrica `SECURITY_HMAC_SECRET`:

### Payload del token:
```json
{
  "execution_id": "a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6",
  "action_id": "volume-up",
  "audience": "nova-orchestrator",
  "issued_at": 1786960000,
  "expires_at": 1786960300,
  "nonce": "f47ac105-0304-470b-9dc4-c14dc390935b"
}
```

### Reglas de validación en `orchestrator` (`PlanExecutor`):
1. **Firma criptográfica:** Calculada y verificada contra `SECURITY_HMAC_SECRET`.
2. **Coherencia de ejecución:** `payload.execution_id` coincide con `step.context.correlation_id`.
3. **Coherencia de acción:** `payload.action_id` coincide con `step.plugin`.
4. **Audiencia:** `payload.audience == "nova-orchestrator"`.
5. **Vigencia temporal:** `current_timestamp < payload.expires_at`.

Si cualquier paso incumple estas condiciones, el `orchestrator` rechaza la ejecución con HTTP `403 Forbidden` (`UNAUTHORIZED_ACTION`).

---

## 8. Configuración

El servicio se configura mediante variables de entorno (o archivo `.env`):

| Variable | Valor por defecto | Descripción |
|---|---|---|
| `SERVICE_NAME` | `security-service` | Nombre de la aplicación FastAPI |
| `HOST` | `0.0.0.0` | Dirección IP de escucha |
| `PORT` | `8000` | Puerto interno del microservicio |
| `LOG_LEVEL` | `INFO` | Nivel de logging (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `SECURITY_HMAC_SECRET` | `dev-secret-key-change-in-prod` | Clave secreta para firmar/verificar tokens HMAC |
| `TOKEN_TTL_SECONDS` | `300` | Tiempo de expiración de los tokens emitidos (5 minutos) |

---

## 9. Ejecución y Pruebas

### Prerrequisitos
Python 3.10+ y dependencias instaladas:
```bash
pip install -r requirements.txt
```

### Ejecutar localmente
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Ejecutar suite de pruebas
```bash
PYTHONPATH=. pytest -v
```

---

## 10. Despliegue en Docker

El servicio se despliega dentro de la red `assistant-network` del ecosistema Nova:

```yaml
security-service:
  image: danuser2018/security-service:latest
  container_name: security-service
  env_file:
    - config/security-service.env
  ports:
    - "8010:8000"
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 5s
    retries: 3
  networks:
    - assistant-network
```

Los servicios dependientes (`orchestrator` e `interaction-manager`) configuran `depends_on` con condición `service_healthy` hacia `security-service` para asegurar que el registro de capacidades y políticas esté siempre garantizado antes de procesar interacciones de usuario.
