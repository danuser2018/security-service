# Contributing Guide

Bienvenido a **Security Service** (`security-service`). Este documento describe las normas y flujos de trabajo que todo colaborador debe seguir para mantener la calidad del código, la trazabilidad del historial de cambios y la eficiencia del desarrollo asistido con IA.

---

## Tabla de contenidos

1. [Modelo de ramificación](#modelo-de-ramificación)
2. [Ciclo de vida de una feature](#ciclo-de-vida-de-una-feature)
3. [Convenciones de commits](#convenciones-de-commits)
4. [Pull Requests](#pull-requests)
5. [Code Review](#code-review)
6. [Desarrollo asistido con IA](#desarrollo-asistido-con-ia)
7. [Estándares de código](#estándares-de-código)
8. [Testing](#testing)
9. [Gestión de secretos y seguridad](#gestión-de-secretos-y-seguridad)

---

## Modelo de ramificación

Este proyecto sigue **Trunk Based Development (TBD)**. La rama `main` es el tronco único y siempre debe estar en estado desplegable.

### Reglas fundamentales

- ✅ **Todas las features** se desarrollan en ramas de corta duración que parten de `main`.
- ✅ **Todo el código** regresa a `main` exclusivamente mediante una **Pull Request (PR)**.
- ❌ **Nunca** hagas commits directos sobre `main`.
- ❌ **Nunca** mergees código a `main` sin pasar por una PR aprobada.
- ❌ **Nunca** trabajes sobre `main` localmente.

### Nomenclatura de ramas

```
<tipo>/<descripcion-corta-en-kebab-case>

Ejemplos:
  feature/channel-rate-limiting
  fix/token-expiration-timezone
  chore/update-pydantic-v2
  docs/add-api-examples
  refactor/risk-evaluator-engine
```

| Prefijo | Uso |
|---|---|
| `feature/` | Nueva funcionalidad |
| `fix/` | Corrección de un bug |
| `chore/` | Tareas de mantenimiento sin impacto en lógica |
| `docs/` | Cambios exclusivos en documentación |
| `refactor/` | Refactorización sin cambio de comportamiento |
| `test/` | Adición o mejora de tests |

---

## Ciclo de vida de una feature

```
main ──────────────────────────────────────────► main
       │                                    ▲
       └─► feature/mi-feature ─── PR ──────┘
```

### Pasos

1. **Sincronizar** con `main` antes de crear la rama:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Crear la rama** desde `main`:
   ```bash
   git checkout -b feature/nombre-de-la-feature
   ```

3. **Desarrollar** en commits pequeños y atómicos.

4. **Mantener la rama al día** con `main` mediante rebase (preferido sobre merge):
   ```bash
   git fetch origin
   git rebase origin/main
   ```

5. **Abrir una PR** cuando la feature esté lista para revisión.

6. **Resolver los comentarios** del code review antes de mergear.

7. **Mergear** únicamente con la aprobación de al menos un revisor.

8. **Eliminar la rama** remota tras el merge.

> **Importante:** Las ramas de feature deben ser de corta duración (idealmente no más de 1-2 días de trabajo). Si una feature es grande, divídela en incrementos entregables más pequeños.

---

## Convenciones de commits

Usamos el estándar **[Conventional Commits](https://www.conventionalcommits.org/)**.

### Formato

```
<tipo>(<ámbito>): <descripción en imperativo>

[cuerpo opcional]

[pie opcional: breaking changes, referencias a issues]
```

### Tipos permitidos

| Tipo | Descripción |
|---|---|
| `feat` | Nueva funcionalidad |
| `fix` | Corrección de bug |
| `docs` | Cambios en documentación |
| `style` | Formato, espaciado (sin cambio lógico) |
| `refactor` | Refactorización sin bug fix ni feature |
| `test` | Añadir o modificar tests |
| `chore` | Tareas de mantenimiento del proyecto |
| `perf` | Mejora de rendimiento |
| `ci` | Cambios en pipelines de CI/CD |

### Ejemplos

```
feat(risk): añadir soporte para política de riesgo basada en rangos numéricos

fix(token): validar consistencia temporal estricta en claim expires_at

docs(api): documentar endpoint PUT /v1/security/channels/{channel_id}

chore(deps): actualizar PyJWT a v2.8.0
```

---

## Pull Requests

### Antes de abrir una PR

- [ ] El código compila y los tests pasan localmente (`PYTHONPATH=. pytest`).
- [ ] No hay advertencias críticas o errores de tipado.
- [ ] La rama está actualizada con `main` (rebase).
- [ ] El archivo [CHANGELOG.md](file:///home/danuser2018/workspace/security-service/CHANGELOG.md) ha sido actualizado bajo la sección correspondiente.
- [ ] La descripción de la PR está completa.

### Plantilla de PR

Al abrir una PR, completa siempre los siguientes apartados:

```markdown
## ¿Qué hace este cambio?
<!-- Descripción clara y concisa del cambio -->

## ¿Por qué es necesario?
<!-- Contexto del problema que resuelve y relación con el principio Fail Closed -->

## ¿Cómo se probó?
<!-- Tests unitarios o de integración ejecutados -->

## Checklist
- [ ] Tests añadidos / actualizados (cobertura mantenida > 90%)
- [ ] Documentación actualizada si aplica (README.md)
- [ ] Registro de cambios (CHANGELOG.md) actualizado
- [ ] No introduce secretos o claves HMAC hardcoded
- [ ] Principio Fail Closed respetado ante datos desconocidos o inválidos
- [ ] Breaking changes documentados (si aplica)

## Referencias
<!-- Issues relacionados, ADRs (ej. ADR-025), especificaciones -->
```

### Tamaño de las PRs

- **Objetivo:** PRs pequeñas y enfocadas (< 400 líneas cambiadas como referencia).
- Las PRs grandes dificultan la revisión y aumentan el riesgo de vulnerabilidades de seguridad.

---

## Code Review

### Para el revisor

- Prioriza la seguridad y el principio de **Fail Closed**: ante cualquier dato ausente, la respuesta debe ser `DENY`.
- Distingue entre **bloqueantes** (deben resolverse antes del merge) y **sugerencias** (mejoras opcionales). Usa prefijos como `[bloqueante]` o `[nit]`.
- Verifica la gestión y aislamiento de claves criptográficas y tiempos de vida de tokens.
- Aprueba cuando el código es correcto, seguro y robusto.

### Para el autor

- Responde a cada comentario, explicando razonamientos con datos o contexto cuando sea necesario.
- No introduzcas cambios no relacionados en la misma PR.

---

## Desarrollo asistido con IA

El uso de herramientas de IA (como Antigravity, GitHub Copilot, etc.) está expresamente bienvenido. Sin embargo, su uso conlleva responsabilidades específicas, especialmente en un componente crítico de seguridad como este.

### Principios generales

1. **El autor es siempre responsable del código.** No mergees lógica de evaluación o criptografía que no entiendas completamente.
2. **La IA como copiloto, no como piloto.** La IA sugiere; el desarrollador decide, audita y valida.
3. **El contexto lo pone el humano.** Define claramente los invariantes de seguridad (Fail Closed, atomicidad del plan, single-use tokens) antes de delegar tareas.

### Qué revisar específicamente en código de seguridad generado por IA

| Área | Qué comprobar |
|---|---|
| **Seguridad & Fail Closed** | Comprobar que cualquier rama de excepción o parámetro nulo conduce a `DENY` |
| **Criptografía** | Verificación estricta de firma HMAC, longitud de clave y validación de expiración |
| **Atomicidad** | Que un fallo en un paso del plan invalide el plan completo |
| **Rendimiento** | Evaluación determinista en memoria sin bucles redundantes ni bloqueos |
| **Tests** | Generación de casos negativos (mismatch de ids, tokens expirados, firmas manipuladas) |

---

## Estándares de código

- **Idioma del código:** inglés (nombres de clases, variables, funciones, docstrings y comentarios técnicos).
- **Idioma de la documentación:** español (README, CHANGELOG, CONTRIBUTING, comentarios de PR).
- **Tipado estricto:** uso intensivo de anotaciones de tipo (`typing`, `Pydantic`).
- **Inmutabilidad y validación:** modelar datos con `Pydantic BaseModel`.
- Prefiere **claridad sobre brevedad**: la lógica de seguridad debe ser transparente y auditable a simple vista.

---

## Testing

- **Toda nueva funcionalidad o modificación debe incluir tests.**
- Los tests deben ejecutarse localmente antes de enviar una PR:
  ```bash
  PYTHONPATH=. pytest -v
  ```
- **Pruebas negativas obligatorias:** Cualquier cambio en evaluación de riesgo o validación de tokens debe probar explícitamente escenarios de fallo y rechazo (`DENY`, tokens manipulados, firmas incorrectas).

---

## Gestión de secretos y seguridad

- ❌ **Nunca** hagas commit de secretos reales o claves de producción en el repositorio.
- Usa la variable de entorno `SECURITY_HMAC_SECRET` para configurar la clave de firma.
- El valor por defecto `"dev-secret-key-change-in-prod"` está restringido exclusivamente a entornos locales de desarrollo y pruebas.
- Si detectas una clave comprometida en el historial git, **notifícalo inmediatamente** para su revocación y rotación en los entornos afectados.

---

*Este documento es vivo. Si encuentras algo que mejorar, abre una PR con el prefijo `docs(contributing):`.*
