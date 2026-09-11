# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## Guía de uso

Cada versión se documenta bajo su número de versión y fecha de publicación.
Los cambios se agrupan en las siguientes categorías:

- **Añadido** — nuevas funcionalidades.
- **Cambiado** — cambios en funcionalidades existentes.
- **Obsoleto** — funcionalidades que serán eliminadas en versiones futuras.
- **Eliminado** — funcionalidades eliminadas en esta versión.
- **Corregido** — corrección de errores.
- **Seguridad** — correcciones de vulnerabilidades.

## [1.0.0] - 2026-09-11

### Añadido
- Implementación inicial del microservicio **Security Service** (`security-service`) para la autorización **User → Service** (MVP) en el ecosistema Nova.
- Modelos de datos Pydantic en `app/models/security.py`:
  - `RiskLevel`: enumeración semántica con ordenación estricta (`low < medium < high`).
  - `RiskPolicy`: soporte para políticas `fixed` (`FixedRiskPolicy`) y `lookup` (`LookupRiskPolicy`).
  - `ActionDefinition` y `RegisterActionsRequest`: registro de capacidades y políticas declaradas por plugins.
  - `ChannelPolicy` y `ChannelPolicyConfig`: umbrales de riesgo aceptables por canal.
  - `ExecutionPlanPayload`, `SecurityContextPayload`, `AuthorizationRequest` y `AuthorizationResponse`.
  - `AuthorizationTokenItem`.
- Servicios del núcleo (`app/services/`):
  - `ActionRegistry`: registro en memoria de acciones publicadas por `orchestrator`.
  - `LookupTableRegistry`: catálogo en memoria para tablas dinámicas (ej. `host_commands` publicadas por `host-service`).
  - `ChannelPolicyManager`: gestión en memoria de políticas por canal con configuración por defecto (`voice` → `high`, `cli` → `medium`, `api` → `low`).
  - `RiskEvaluator`: motor determinista de evaluación de riesgo efectivo con manejo de errores tipados (`MISSING_SOURCE_PARAMETER`, `LOOKUP_TABLE_NOT_FOUND`, `LOOKUP_VALUE_NOT_FOUND`).
  - `AuthorizationTokenManager`: generador y verificador de tokens de autorización firmados mediante HMAC-SHA256 (JWT/HS256) acotados a `execution_id`, `action_id` y tiempo de vida (`expires_at`).
  - `AuthorizationEngine`: motor de autorización atómica de planes bajo el principio de **Fail Closed** (un solo paso denegado deniega el plan completo y emite cero tokens).
- Endpoints REST en `app/api/routes.py`:
  - `POST /v1/security/actions/register`: registro de acciones de plugins.
  - `POST /v1/security/tables/{table_name}`: publicación de catálogos y tablas dinámicas.
  - `POST /v1/security/authorize`: evaluación y autorización de planes de ejecución.
  - `GET /v1/security/channels` y `PUT /v1/security/channels/{channel_id}`: consulta y actualización dinámica de políticas de canal.
  - `GET /health`: endpoint de healthcheck para Docker y observabilidad.
- Configuración centralizada (`app/config.py`) mediante `pydantic-settings` con soporte para variables de entorno (`SECURITY_HMAC_SECRET`, `TOKEN_TTL_SECONDS`, `PORT`, `LOG_LEVEL`).
- Empaquetado Docker con imagen base `python:3.11-slim` en `Dockerfile`.
- Suite completa de 25 pruebas unitarias y de integración en `tests/`:
  - `test_risk_level.py`: ordenación estricta y comparaciones con strings.
  - `test_fixed_policy_evaluator.py`: evaluación de políticas fijas.
  - `test_lookup_policy_evaluator.py`: evaluación de búsqueda, parámetros ausentes y tablas/valores inexistentes.
  - `test_channel_policy_manager.py`: políticas iniciales y actualización dinámica.
  - `test_token_manager.py`: emisión, validación de firma, verificación de expiración y discrepancia de identificadores.
  - `test_authorization_engine.py`: flujos `ALLOW`, `DENY` por superación de riesgo, canales no registrados y evaluación atómica fail-closed.
  - `test_actions_api.py`, `test_tables_api.py` y `test_authorize_api.py`: contratos HTTP de la API REST.
- Especificación técnica completa en `README.md`.
