<!--
Sync Impact Report:
- Version change: Unratified Draft (template placeholders) → 1.0.0
- Ratification Date: 2026-11-16
- Principles Established:
  * I. Seguridad Absoluta y Gestión Estricta de Secretos (Reglas 1-3)
  * II. Estabilidad de Contratos entre Módulos e Interfaces Robustas (Reglas 4-7)
  * III. Comportamiento Fidedigno, Transparencia y Anclaje del Agente (Reglas 8-11)
  * IV. Calidad Verificada, Relevos Secuenciales y Trabajo en Equipo (Reglas 12-17)
  * V. Código Limpio, Documentación Original y Dominio Técnico Compartido (Reglas 18-20)
- Added Sections:
  * Estructura de Relevos y Responsabilidades por Integrante
  * Estándares de Flujo de Trabajo, Pruebas y Control de Cambios
- Removed Sections: Ninguna (plantilla base poblada y ratificada por primera vez).
- Follow-up TODOs: Ninguno (todos los tokens de plantilla fueron completados con directrices concretas).
-->

# PixelOrbe Constitution

## Core Principles

### I. Seguridad Absoluta y Gestión Estricta de Secretos
- **Aislamiento de credenciales (Regla 1)**: Las claves de acceso (API de LLM, Token de Telegram, credenciales SMTP/Gmail) NUNCA se escriben en el código fuente ni se suben al repositorio. Deben residir exclusivamente en el archivo local `.env`, el cual DEBE estar listado en `.gitignore`. Se DEBE mantener un archivo `.env.example` actualizado con variables documentadas y sin valores reales.
- **Higiene de exposición (Regla 2)**: Los secretos y claves NUNCA deben figurar en prompts enviados a modelos de IA, registros de depuración (logs), capturas de pantalla, presentaciones ni en el informe académico.
- **Parametrización SQL estricta (Regla 3)**: Toda consulta contra la base de datos DEBE ejecutarse mediante sentencias preparadas con marcadores de posición (`?`). Queda terminantemente PROHIBIDO concatenar o interpolar cadenas provenientes del usuario o del agente en sentencias SQL.

### II. Estabilidad de Contratos entre Módulos e Interfaces Robustas
- **Inmutabilidad de contratos públicos (Regla 4)**: Las firmas de las funciones públicas acordadas representan un contrato vinculante para el equipo y NO deben modificarse sin aprobación unánime de los tres integrantes. El contrato base comprende:
  - Base de datos (`tools_db.py`): `consultar_stock(producto: str) -> str`, `consultar_precio(producto: str) -> str`, `registrar_pedido(cliente: str, email: str, producto: str, cantidad: int) -> str`, `listar_pedidos(email: str) -> str`.
  - Recuperación RAG (`rag.py`): `buscar_documentos(consulta: str) -> str`.
  - Servicios externos (`tools_ext.py`): `tipo_de_cambio() -> str`, `enviar_correo(destinatario: str, asunto: str, cuerpo: str) -> str`.
  - Agente conversacional (`agent.py`): `responder(chat_id: str | int, texto: str) -> str`.
- **Manejo resiliente de tools (Regla 5)**: Todas las herramientas (tools) DEBEN retornar siempre un tipo `str` y NUNCA propagar excepciones no controladas hacia el agente. Cualquier error interno DEBE ser capturado e interpretado para retornar una descripción clara y amigable.
- **Moneda de referencia unificada (Regla 6)**: Toda la capa de datos almacena y procesa importes exclusivamente en dólares estadounidenses (USD). La conversión a moneda nacional (PEN / soles) es responsabilidad única de la herramienta de tipo de cambio y de las capas superiores.
- **Atomicidad transaccional (Regla 7)**: Cualquier operación de escritura o mutación de datos (`registrar_pedido`, registro de pagos) DEBE ejecutarse bajo una transacción atómica única: o se persisten todos los cambios o se realiza rollback inmediato ante cualquier inconsistencia.

### III. Comportamiento Fidedigno, Transparencia y Anclaje del Agente
- **Idioma y veracidad (Regla 8)**: El agente DEBE interactuar siempre en español formal y cortés. El agente NO DEBE alucinar ni inventar datos comerciales, stock o precios. Si no posee información certera en su contexto o herramientas, DEBE manifestarlo explícitamente con amabilidad.
- **Consentimiento y confirmación de pedidos (Regla 9)**: El agente DEBE solicitar una confirmación explícita del cliente indicando producto, cantidad y monto antes de invocar la tool de creación de un pedido (`registrar_pedido`).
- **Anclaje documental y citación RAG (Regla 10)**: Las respuestas sustentadas en políticas de la tienda, garantías o preguntas frecuentes DEBEN ceñirse estrictamente a la información recuperada del corpus y citar de forma explícita su procedencia con el formato `[Fuente: <archivo>]`.
- **Separación de responsabilidades de información (Regla 11)**: La información dinámica de alta variabilidad (precios, existencias de inventario, estados de orden) reside ÚNICAMENTE en la base de datos SQLite. El corpus documental del sistema RAG NUNCA debe contener precios ni cantidades de stock.

### IV. Calidad Verificada, Relevos Secuenciales y Trabajo en Equipo
- **Cumplimiento estricto de relevos (Regla 12)**: El desarrollo opera bajo fases secuenciales independientes. Ningún integrante DEBE iniciar su fase de desarrollo hasta que la fase predecesora haya completado y validado su checklist de entrega.
- **Propiedad de código y modificación acotada (Regla 13)**: Cada integrante modifica únicamente los módulos asignados a su fase. Quien extienda el archivo central del agente (`agent.py`) DEBE limitarse a registrar nuevas tools y refinar el prompt del sistema, sin refactorizar ni reescribir la lógica previa validada.
- **Resolución colaborativa de defectos (Regla 14)**: Si se identifica una anomalía o falla en código de otro integrante, se DEBE registrar un issue en GitHub y notificar al responsable; NUNCA se debe modificar de forma directa el código ajeno.
- **Criterio de entrega reproducible (Regla 15)**: Toda fase entregada DEBE contar con la suite de pruebas automatizadas (`pytest`) ejecutándose al 100% en verde y un archivo `README.md` actualizado con instrucciones que permitan desplegar y ejecutar el proyecto desde cero.
- **Estrategia de ramas y commits (Regla 16)**: El trabajo se realiza en ramas individuales asignadas (`rodrigo`, `jerzy`, `alisson`), fusionándose a `main` únicamente al terminar la fase correspondiente. Los commits DEBEN ser atómicos, descriptivos y bajo el estándar de Commits Convencionales (`feat:`, `test:`, `docs:`, `chore:`).
- **Observabilidad y tolerancia a fallos del bot (Regla 17)**: El bot de Telegram NUNCA debe colapsar o terminar en silencio. Las excepciones no capturadas DEBEN registrarse en los logs de la aplicación y el usuario DEBE recibir un mensaje informativo claro sobre la incidencia.

### V. Código Limpio, Documentación Original y Dominio Técnico Compartido
- **Claridad idiomática y docstrings (Regla 18)**: Todo el código fuente DEBE incluir comentarios explicativos y docstrings detallados en español en funciones, clases y módulos.
- **Originalidad intelectual (Regla 19)**: Todo contenido textual generado (fichas técnicas de productos, políticas de atención, documentación y el informe académico final) DEBE ser de redacción propia y original, sin copias textuales de fabricantes ni fuentes externas.
- **Dominio integral del proyecto (Regla 20)**: La especialización por relevos no exime del conocimiento global: cada uno de los tres integrantes DEBE comprender y ser capaz de sustentar técnicamente la totalidad del sistema y su flujo de extremo a extremo.

## Estructura de Relevos y Responsabilidades por Integrante

El flujo de trabajo se divide en tres fases secuenciales de relevo:

1. **Fase 1 - Capa Base, Persistencia y Fichas (Responsable: Rodrigo)**:
   - Diseño e inicialización del esquema SQLite (`init_db.py`).
   - Implementación y pruebas de tools de base de datos (`tools_db.py`).
   - Redacción original de fichas de catálogo y datos maestros (`data/`).
   - Pruebas unitarias de la capa de persistencia (`tests/test_tools_db.py`).
   - Validación de checklist de entrega y pase a Fase 2.

2. **Fase 2 - Agente Conversacional, RAG y Corpus (Responsable: Jerzy)**:
   - Configuración del corpus documental original en `data/docs/`.
   - Pipeline de ingestión y vectorización con ChromaDB y Sentence-Transformers (`ingest.py`, `rag.py`).
   - Evaluación y métricas de recuperación RAG (`evaluar_rag.py`).
   - Estructuración inicial del agente LLM con function calling y memoria conversacional (`agent.py`).
   - Pruebas de integración del subsistema cognitivo y pase a Fase 3.

3. **Fase 3 - Servicios Externos, Interfaz Telegram y E2E (Responsable: Alisson)**:
   - Implementación de servicios de tipo de cambio y correo SMTP (`tools_ext.py`).
   - Conexión del agente al bot de Telegram y gestión de sesiones (`bot.py`).
   - Elaboración de pruebas de integración de extremo a extremo (`tests/test_e2e.py`).
   - Integración final en `main`, documentación de despliegue en `README.md` y soporte al informe.

## Estándares de Flujo de Trabajo, Pruebas y Control de Cambios

- **Entorno y ejecución**: La aplicación utiliza Python 3 y `pytest`. El entorno se gestiona mediante variables de entorno en `.env`.
- **Ramas de Git**:
  - `main`: Rama de producción estable. Solo recibe merges tras completar y validar un relevo.
  - `rodrigo`: Rama para trabajo de base de datos, tools de datos y fichas.
  - `jerzy`: Rama para trabajo del agente, RAG y corpus documental.
  - `alisson`: Rama para servicios externos, bot de Telegram y pruebas e2e.
- **Políticas de Pull Request y Merge**:
  - Todo merge a `main` requiere que `pytest` pase sin advertencias bloqueantes ni errores.
  - Los commits deben usar prefijos convencionales: `feat:` para nuevas capacidades, `test:` para adición de pruebas, `docs:` para documentación, `chore:` para dependencias y configuración.
- **Gestión de fallos**: Toda incidencia detectada en código ajeno se reporta en un GitHub Issue con pasos de reproducción; el autor original es el único autorizado para aplicar la corrección correspondiente.

## Governance

- **Supremacía Constitucional**: Este documento de constitución gobierna todos los procesos técnicos, de arquitectura y de colaboración del proyecto PixelOrbe. Prevalece sobre cualquier acuerdo informal o convención individual no documentada.
- **Procedimiento de Enmiendas**: Cualquier modificación a estos principios o a los contratos entre módulos requiere una propuesta justificada, discusión y aprobación por consenso unánime de los tres integrantes (Rodrigo, Jerzy y Alisson).
- **Política de Versionado**:
  - `MAJOR` (X.0.0): Cambios incompatibles en contratos públicos, eliminación o redefinición radical de principios de seguridad o arquitectura.
  - `MINOR` (0.X.0): Incorporación de nuevos principios, nuevas herramientas acordadas o ampliación sustancial de directrices sin romper contratos previos.
  - `PATCH` (0.0.X): Correcciones ortográficas, precisiones de redacción o aclaraciones no semánticas.
- **Supervisión de Cumplimiento**: En cada relevo y antes de fusionar a la rama principal `main`, se revisará el cumplimiento de cada una de las 20 reglas estipuladas.

**Version**: 1.0.0 | **Ratified**: 2026-11-16 | **Last Amended**: 2026-11-16
