# Rúbrica de Evaluaciones: Proyecto VulnApp

## Contexto y Objetivo del Documento

Este documento establece la rúbrica de evaluación y los requerimientos base del proyecto **VulnApp**, que se desarrollará a lo largo de las tres Pruebas de Evaluación Parcial (PEP) del semestre.

Los requerimientos descritos a continuación son un punto de partida y no acotan el alcance del proyecto. La captura de requerimientos definitiva debe hacerla cada grupo en reuniones con el cliente. En particular, las correcciones de interfaz y experiencia de usuario que se van a solicitar durante el semestre solo se pueden resolver si los grupos asisten a esas reuniones y levantan el detalle correspondiente. No asistir no es justificación válida para entregar requerimientos incompletos.

El diagnóstico técnico completo del estado actual del proyecto, en seguridad y en escalabilidad, se adjunta como anexo a este documento.

---

## Rúbrica de Evaluación

### Pesos de las Evaluaciones Parciales

| PEP | Peso en la nota final |
| :--- | :--- |
| **PEP 1** | 35% |
| **PEP 2** | 35% |
| **PEP 3** | 30% |

### Desglose de Calificación por PEP

La calificación de cada PEP se compone de:
* **Entrega de los requerimientos:** 45%
* **Defensa de preguntas durante la presentación:** 55%

> **Nota:** Promedio mínimo de aprobación es de **4.0** en cada PEP.

---

## Herramientas Obligatorias de DevSecOps

El presente ramo se orienta a la práctica de **DevSecOps**, por lo que el pipeline de integración continua y las herramientas de análisis de seguridad constituyen un componente central de la evaluación, no un aspecto accesorio. Tener estas herramientas operativas sobre la totalidad del repositorio es de vital importancia para el resultado de cada PEP.

* **Historial del Pipeline:** El proyecto contó, en versiones anteriores, con un pipeline de DevSecOps completo compuesto por Jenkins, una instancia autoalojada de SonarQube y un análisis dinámico de seguridad (DAST) mediante OWASP ZAP contra la API y el frontend. Ese pipeline fue eliminado del repositorio durante el desarrollo previo y ha sido recuperado para esta entrega. Se encuentra disponible, sin activar, en la carpeta `dev-tools/`, junto con las indicaciones correspondientes en su documentación interna.
* **Estado Actual:** Actualmente, el único proceso que se ejecuta de forma automática es el flujo de GitHub Actions definido en `.github/workflows/sonar.yml`, que corre las pruebas del backend y el análisis de SonarCloud en cada entrega al repositorio.
* **Responsabilidad:** Corresponde a cada grupo revisar, reparar y activar de forma progresiva los componentes restantes del pipeline, documentando las decisiones tomadas en cada etapa.

---

## Requerimientos Base: PEP 1

Estos requerimientos cubren diferentes aspectos (seguridad, escalabilidad y organización del código) y ya están diagnosticados. Los requerimientos de frontend y cualquier otro no listado aquí deben capturarlos directamente con el cliente en las reuniones de requerimientos.

### 1. Seguridad

| Severidad | Hallazgo | Ubicación |
| :--- | :--- | :--- |
| **Crítica** | El JWT se firma con un secreto por defecto. El código lee `JWT_SECRET`, pero el env define `SECRET_KEY`, así que esa variable nunca existe en el entorno real y cualquiera con el código puede generar un token válido. | `vuln-api/app/auth.py:15` |
| **Alta** | No existe control de intentos en `/auth/login`, combinado con un usuario `admin/admin` activo desde el arranque. | `vuln-api/app/main.py` |
| **Alta** | El `.env` con credenciales reales está incluido en el repositorio, en lugar de un `.env.example`. | `env` |
| **Media** | No existe un sistema de roles. Cualquier usuario autenticado administra todo. | `vuln-api/app/main.py` |
| **Media** | `VERIFY_SSL` está en `False` por defecto, lo que desactiva la verificación del certificado TLS hacia el indexador de Wazuh. | `vuln-api/app/wazuh_client.py:7` |

### 2. Escalabilidad

| Severidad | Hallazgo | Ubicación |
| :--- | :--- | :--- |
| **Crítica** | `GET /vulns` no pagina ni filtra en el servidor. Devuelve todas las filas con su historial completo. | `vuln-api/app/main.py` (`list_vulns`) |
| **Crítica** | El Dashboard obtiene todas las vulnerabilidades y filtra, ordena y pagina en el navegador. | `frontend/.../Dashboard.vue` |
| **Crítica** | La sincronización con Wazuh hace una consulta SQL individual por vulnerabilidad recibida, sin operación masiva de inserción o actualización. | `vuln-api/app/main.py` (`process_wazuh_vulnerabilities`) |
| **Alta** | El Timeline trunca los datos sin advertencia clara al superar 2000 registros por conexión. | `frontend/.../timeline/useTimelineData.js` |
| **Crítica** | TimescaleDB nunca se activó. La imagen usada es Postgres estándar y el script que crearía la hypertable nunca se montó en ningún `docker-compose`, en ningún commit de la historia. Confirmado directamente en el servidor de producción. | `docker-compose.yml`, `db-init/10-init.sql` |
| **Media** | Nunca se implementaron funciones anidadas SQL propias (`plpgsql`), las cuales son esenciales para optimizar búsqueda por rangos y otros filtros. El cálculo de dwell time y edad de cada vulnerabilidad se hace en la consulta ORM en vez de una función en la base de datos. | `vuln-api/app/main.py` (`list_vulns`) |

### 3. Organización del Código

| Severidad | Hallazgo | Ubicación |
| :--- | :--- | :--- |
| **Alta** | Rutas, esquemas y lógica de sincronización están concentrados en un único archivo, sin separación en routers, servicios o modelos. | `vuln-api/app/main.py` |

> *El detalle técnico completo está en los anexos de seguridad y escalabilidad.*

---

## Alcance de PEP 2 y PEP 3

### PEP 2: Unificación de Dashboard y Timeline
El Dashboard y el Timeline cargan actualmente los datos de vulnerabilidades por separado, duplicando la carga sobre el servidor. El tema central de la PEP 2 es unificar ambas vistas en una sola, incorporar filtros adicionales y separar las líneas de tiempo en dos:
1. Una correspondiente a **vulnerabilidades**.
2. Otra correspondiente a **CIS Benchmark**.

*El alcance exacto de este requerimiento se definirá en las reuniones de requerimientos con el cliente.*

### PEP 3: CIS Benchmarks
El tema central de la PEP 3 es la integración de **CIS Benchmarks** en la aplicación, sobre la base entregada en la PEP 2.

---

## Examen de Recuperación

Aplicará únicamente en caso de que alguna PEP registre un promedio inferior a **4.0**. 

El examen consistirá en la integración de todo el desarrollo realizado durante el semestre con el **envío de tickets a GLPI**, funcionalidad que deberá quedar integrada directamente en la aplicación.