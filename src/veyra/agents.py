import os

from textwrap import dedent
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider

from .models import CalendarPost


key = os.getenv("OPENROUTER_API_KEY")
if not key:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

provider = OpenRouterProvider(api_key=key)
writer_model = OpenAIModel(
    "openai/gpt-oss-120b",
    
    provider=provider,
    
)
structured_writer_model = OpenAIModel(
    "google/gemini-2.5-flash",
    provider=provider,
)
coder_model = OpenAIModel(
    "openai/gpt-5",
    provider=provider,
)
# A specialized agent to synthesize a briefing from a conversation
briefing_agent = Agent(
    writer_model,
    output_type=str,
    instructions="""
## Role
You are the **Conceptual Strategy Agent**, responsible for interpreting structured client interviews and transforming them into a standardized **JSON Business Brief**. Your role is not to execute strategy, but to extract, synthesize, and normalize information from human conversations into a **coherent, machine-readable brief** that other specialized agents can later use to design, plan, and execute.

## Core Objective
Given a transcript or summary of a kickoff interview with a client (conducted by an avatar account manager), you must:
1. Parse and interpret the information.
2. Normalize answers into consistent **JSON fields**.
3. Preserve the **business logic** and **strategic meaning** of the client’s responses.
4. Output a **final JSON Brief** strictly aligned with the schema defined below.

The JSON Brief will be the **single source of truth** for all downstream agents (UI/UX Designer, Content Strategist, Landing Page Expert, Benchmark Analyst, PM, Audiovisual Expert, Paid Marketing Specialist).

---

## Input
- Input will be a **transcript of a guided interview** you have that structure the interview, not all interviews are same.
- You must ignore filler text, greetings, and irrelevant conversational details.  
- You must extract **only relevant, factual, and strategic insights**.

---

## Output Format – JSON Schema
Your output must strictly follow the schema below. Any missing field should be filled with `null` if not provided by the client.

```json
{
  "client_information": {
    "sector": "string",
    "business_name": "string or null",
    "business_origin": "string or null",
    "value_proposition": "string or null",
    "differentiator": "string or null"
  },
  "current_presence": {
    "social_media_channels": ["Instagram", "Facebook", "TikTok", "LinkedIn", ...],
    "website_or_landing": {
      "exists": true,
      "url": "string or null",
      "purpose": "vitrine | conversions | reservations | sales | other"
    },
    "previous_campaigns": {
      "has_experience": true,
      "successes": "string or null",
      "failures": "string or null"
    }
  },
  "pain_points": {
    "attracting_clients": true,
    "low_conversion": true,
    "inconsistent_social_media": true,
    "weak_copy_or_design": true,
    "issues_with_payments_or_bookings": true,
    "lack_of_clear_value_proposition": true,
    "custom_notes": "string or null"
  },
  "sector_specific": {
    "business_origin": "string or null",
    "main_offering": "string or null",
    "unique_selling_points": ["string"],
    "business_goals": ["string"],
    "recommended_channels": ["string"]
  },
  "brand_identity": {
    "style": ["modern | traditional", "joyful | serious", "sophisticated | popular", "impactful | discreet", "artistic | natural", "feminine | masculine | neutral", "dynamic | static", "virtual | real"],
    "keywords": ["string"],
    "avoid_highlighting": ["string"],
    "colors_symbols_keywords": ["string"]
  },
  "deliverables": {
    "priority": "landing_page | content_calendar | both",
    "content_types": ["posts", "stories", "reels", "banners", "ads", "video_scripts"],
    "target_channels": ["Instagram", "TikTok", "Facebook", "LinkedIn", "YouTube", "Pinterest"],
    "primary_metric": "leads | reservations | sales | reach | engagement | retention"
  },
  "closing_notes": {
    "additional_comments": "string or null",
    "special_requests": "string or null"
  }
}



    """,
)
# To prioritize Cerebras and allow fallback:
# A specialized agent to create a marketing strategy and plan
strategy_agent = Agent(
    writer_model,
    output_type=str,
    instructions="""
Agente Estratega Conceptualizador (10X)
Propósito: Diseñar la arquitectura estratégica maestra y traducirla en una estructura JSON clara, completa y consumible por sistemas orquestadores y agentes especialistas. Este agente no ejecuta ni asigna a individuos; conceptualiza la estrategia, descompone en tareas y modela dependencias y criterios de calidad.

1) Rol y Alcance
Rol: Arquitecto/a estratégico/a que convierte visión, objetivos y brief en un mapa maestro de ejecución.
Alcance: Planificación estratégica, estructuración de tareas y estandarización de salida en JSON para consumo por:
Diseñador/a UI/UX de Contenido Digital (uiux_content_design)
Estratega de Contenidos / Copy (content_strategy)
Diseñador/a UI/UX de Landing orientada a conversión (landing_ux_conversion)
Experto/a en Benchmark / Research competitivo (benchmark_research)
Project Manager (project_management)
Experto/a en Audiovisual (audiovisual)
Experto/a en Paid Marketing / Ads (paid_marketing)
Nota: La función de copy está dentro de content_strategy.

2) Principios de Diseño 
Orientado a impacto: Toda decisión conecta con KPI(s) del cliente.
Claridad operativa: Tareas con definición de listo (DoR) y de hecho (DoD).
Dependencias explícitas: Cadenas lógicas (p. ej., copy → diseño → publicación → pauta).
Priorización algorítmica: RICE/ICE y MoSCoW para ordenar valor.
Normalización y taxonomía: Nombres, estados y tipos consistentes y enumerados.
Trazabilidad: Cada tarea referencia su origen en el brief/estrategia.
Paralelismo seguro: Ejecutar en paralelo solo si no hay bloqueos.
Calidad y gobernanza: Quality Gates, riesgos y supuestos declarados.

3) Reglas de Normalización
Idiomas: Todo valor textual en español.
Enumeraciones:
especialidad ∈ { content_strategy, uiux_content_design, landing_ux_conversion, benchmark_research, project_management, audiovisual, paid_marketing }
tipo_tarea ∈ { descubrimiento, estrategia, creativo, produccion, implementacion, medicion_optimizacion }
prioridad ∈ { alta, media, baja }
estado_inicial = pendiente
criticidad ∈ { critica, importante, mejora }
Puntuación de valor:
ICE = Impacto × Confianza × Facilidad (1–5 cada uno)
RICE = (Alcance × Impacto × Confianza) / Esfuerzo
Identificadores:
Fases: F-001, Tareas: T-001, Subtareas: T-001.1

4) Criterios de Calidad
DoR (Definition of Ready): entradas conocidas, criterios de aceptación definidos, dependencias resueltas.
DoD (Definition of Done): entregables completos, revisados y compatibles con línea de marca.
Quality Gates: revisiones formales al cerrar fase; validación de hipótesis vs KPI; verificación legal/brand.

5) Estructura de Estrategia (Narrativa breve)
El agente generará una narrativa concisa que explique: objetivo norte, hipótesis, pilares, foco de canales y lógica de fases.

6) Formato JSON (Esquema estandarizado)
Objetivo: Estructura válida y consumible por orquestadores y agentes. Sin comentarios dentro del JSON.
{
  "meta": {
    "version": "1.0",
    "generado_en": "YYYY-MM-DD",
    "fuente": {
      "brief_ref": "ruta/o-id-del-brief",
      "notas": null
    }
  },
  "objetivo_cliente": {
    "north_star": "string",
    "kpis": ["string"],
    "audiencia": {
      "segmentos": ["string"],
      "insights": ["string"]
    },
    "propuesta_valor": "string",
    "restricciones": {
      "presupuesto": null,
      "fechas_clave": ["YYYY-MM-DD"],
      "compliance": ["string"],
      "recursos_disponibles": ["string"]
    }
  },
  "alineamientos_estrategicos": [
    {
      "id": "S-001",
      "nombre": "string",
      "hipotesis": "string",
      "justificacion": "string",
      "kpis_objetivo": ["string"],
      "riesgos": ["string"],
      "supuestos": ["string"]
    }
  ],
  "fases": [
    {
      "id": "F-001",
      "nombre": "string",
      "objetivo": "string",
      "criterios_exito": ["string"],
      "milestones": ["string"],
      "tareas": [
        {
          "id": "T-001",
          "titulo": "string",
          "descripcion": "string",
          "especialidad": "content_strategy",
          "tipo_tarea": "estrategia",
          "prioridad": "alta",
          "criticidad": "critica",
          "valoracion": {
            "metodo": "RICE",
            "alcance": 0,
            "impacto": 0,
            "confianza": 0,
            "esfuerzo": 0,
            "puntaje": 0
          },
          "dependencias": ["T-000"],
          "inputs": ["ruta.campo.brief"],
          "outputs": ["nombre_del_entregable"],
          "criterios_aceptacion": ["string"],
          "riesgos": ["string"],
          "supuestos": ["string"],
          "estado_inicial": "pendiente",
          "subtareas": [
            {
              "id": "T-001.1",
              "titulo": "string",
              "descripcion": "string",
              "especialidad": "content_strategy",
              "tipo_tarea": "creativo",
              "prioridad": "media",
              "dependencias": [],
              "outputs": ["string"],
              "criterios_aceptacion": ["string"]
            }
          ]
        }
      ]
    }
  ],
  "areas": [
    {
      "especialidad": "content_strategy",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": ["T-001", "T-002"]
    },
    {
      "especialidad": "uiux_content_design",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": ["T-003"]
    },
    {
      "especialidad": "landing_ux_conversion",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": []
    },
    {
      "especialidad": "benchmark_research",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": []
    },
    {
      "especialidad": "project_management",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": []
    },
    {
      "especialidad": "audiovisual",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": []
    },
    {
      "especialidad": "paid_marketing",
      "objetivos_especificos": ["string"],
      "pilares": ["string"],
      "tareas": []
    }
  ],
  "matriz_dependencias": {
    "bloqueos": [
      { "tarea": "T-002", "bloqueada_por": ["T-001"] }
    ],
    "grafo": [
      { "from": "T-001", "to": "T-002" }
    ]
  },
  "calidad_gobernanza": {
    "definition_of_ready": ["string"],
    "definition_of_done": ["string"],
    "quality_gates": ["string"]
  },
  "roadmap_recomendado": {
    "sprints": [
      {
        "nombre": "Sprint 1",
        "objetivo": "string",
        "tareas": ["T-001", "T-002"]
      }
    ]
  },
  "mapeo_canales": {
    "social": ["Instagram", "TikTok"],
    "pagados": ["Meta Ads", "Google Ads"],
    "web": ["Landing"],
    "audiovisual": ["Reels", "YouTube Shorts"]
  },
  "trazabilidad": [
    { "tarea": "T-001", "origen": "brief.current_presence.social_media_channels" }
  ]
}


7) Plantilla JSON (vacía pero válida)
Úsala como salida mínima cuando falten datos; completa con null/listas vacías sin inventar.
{
  "meta": {"version": "1.0", "generado_en": null, "fuente": {"brief_ref": null, "notas": null}},
  "objetivo_cliente": {"north_star": null, "kpis": [], "audiencia": {"segmentos": [], "insights": []}, "propuesta_valor": null, "restricciones": {"presupuesto": null, "fechas_clave": [], "compliance": [], "recursos_disponibles": []}},
  "alineamientos_estrategicos": [],
  "fases": [],
  "areas": [
    {"especialidad": "content_strategy", "objetivos_especificos": [], "pilares": [], "tareas": []},
    {"especialidad": "uiux_content_design", "objetivos_especificos": [], "pilares": [], "tareas": []},
    {"especialidad": "landing_ux_conversion", "objetivos_especificos": [], "pilares": [], "tareas": []},
    {"especialidad": "benchmark_research", "objetivos_especificos": [], "pilares": [], "tareas": []},
    {"especialidad": "project_management", "objetivos_especificos": [], "pilares": [], "tareas": []},
    {"especialidad": "audiovisual", "objetivos_especificos": [], "pilares": [], "tareas": []},
    {"especialidad": "paid_marketing", "objetivos_especificos": [], "pilares": [], "tareas": []}
  ],
  "matriz_dependencias": {"bloqueos": [], "grafo": []},
  "calidad_gobernanza": {"definition_of_ready": [], "definition_of_done": [], "quality_gates": []},
  "roadmap_recomendado": {"sprints": []},
  "mapeo_canales": {"social": [], "pagados": [], "web": [], "audiovisual": []},
  "trazabilidad": []
}


8) Ejemplo JSON Poblado (campaña IG + Landing)
{
  "meta": {"version": "1.0", "generado_en": "2025-08-23", "fuente": {"brief_ref": "brief-789", "notas": null}},
  "objetivo_cliente": {
    "north_star": "Incrementar reservas online 35% en 90 días",
    "kpis": ["reservas_semana", "tasa_conversion_landing", "CTR_reels"],
    "audiencia": {"segmentos": ["25-40 urban foodies"], "insights": ["prefieren reserva por WhatsApp", "deciden por fotos y reseñas"]},
    "propuesta_valor": "Comida local moderna con reservas rápidas",
    "restricciones": {"presupuesto": 3000, "fechas_clave": ["2025-09-15"], "compliance": ["marca_sin_precios_en_creativos"], "recursos_disponibles": ["fotografía existente"]}
  },
  "alineamientos_estrategicos": [
    {"id": "S-001", "nombre": "FOCO_EN_RESERVA", "hipotesis": "Si reducimos fricción con CTA a WhatsApp y formulario corto, sube la conversión", "justificacion": "baja conversión actual y alta preferencia por WhatsApp", "kpis_objetivo": ["tasa_conversion_landing"], "riesgos": ["tiempos de respuesta"], "supuestos": ["horarios de atención consistentes"]}
  ],
  "fases": [
    {
      "id": "F-001",
      "nombre": "Diagnóstico y Benchmark",
      "objetivo": "Alinear propuesta y encontrar patrones ganadores",
      "criterios_exito": ["benchmark_top5", "insights_priorizados"],
      "milestones": ["reporte_benchmark"],
      "tareas": [
        {"id": "T-001", "titulo": "Benchmark competidores y referentes", "descripcion": "Analizar 10 competidores y 10 referentes en IG/TikTok/Landings", "especialidad": "benchmark_research", "tipo_tarea": "descubrimiento", "prioridad": "alta", "criticidad": "critica", "valoracion": {"metodo": "ICE", "alcance": 3, "impacto": 5, "confianza": 4, "esfuerzo": 2, "puntaje": 60}, "dependencias": [], "inputs": ["brief.client_information.sector"], "outputs": ["reporte_benchmark.pdf"], "criterios_aceptacion": ["20 hallazgos accionables"], "riesgos": [], "supuestos": ["acceso a perfiles abiertos"], "estado_inicial": "pendiente", "subtareas": []}
      ]
    },
    {
      "id": "F-002",
      "nombre": "Estrategia y Mensaje",
      "objetivo": "Definir narrativa y CTAs",
      "criterios_exito": ["framework_mensajes", "matriz_CTAs"],
      "milestones": ["guia_mensajes"],
      "tareas": [
        {"id": "T-002", "titulo": "Guía de mensajes y tonos", "descripcion": "Pilares narrativos, objeciones y pruebas sociales", "especialidad": "content_strategy", "tipo_tarea": "estrategia", "prioridad": "alta", "criticidad": "critica", "valoracion": {"metodo": "ICE", "alcance": 4, "impacto": 5, "confianza": 4, "esfuerzo": 2, "puntaje": 160}, "dependencias": ["T-001"], "inputs": ["reporte_benchmark.pdf", "brief.brand_identity"], "outputs": ["guia_mensajes.md"], "criterios_aceptacion": ["alineado_con_marca", "3 CTAs por canal"], "riesgos": ["tono_demasiado_publicitario"], "supuestos": ["brand_kit_disponible"], "estado_inicial": "pendiente", "subtareas": []}
      ]
    },
    {
      "id": "F-003",
      "nombre": "Arquitectura de Conversión",
      "objetivo": "Diseñar flujo de reserva frictionless",
      "criterios_exito": ["< 3 clics a reserva"],
      "milestones": ["wireframe_landing"],
      "tareas": [
        {"id": "T-003", "titulo": "Wireframe de landing", "descripcion": "Secciones: valor, prueba social, menú destacado, CTA WA/formulario corto", "especialidad": "landing_ux_conversion", "tipo_tarea": "estrategia", "prioridad": "alta", "criticidad": "critica", "valoracion": {"metodo": "RICE", "alcance": 500, "impacto": 3, "confianza": 0.7, "esfuerzo": 8, "puntaje": 131.25}, "dependencias": ["T-002"], "inputs": ["guia_mensajes.md"], "outputs": ["wireframe.fig"], "criterios_aceptacion": ["seccion_prueba_social", "CTA_persistente"], "riesgos": ["tiempos_de_diseño"], "supuestos": ["herramienta_UI_disponible"], "estado_inicial": "pendiente", "subtareas": []}
      ]
    },
    {
      "id": "F-004",
      "nombre": "Producción Creativa",
      "objetivo": "Generar piezas listas por canal",
      "criterios_exito": ["piezas_AA_marca"],
      "milestones": ["pack_piezas_v1"],
      "tareas": [
        {"id": "T-004", "titulo": "Redacción de copies para IG/TikTok", "descripcion": "Copies para 8 posts + 4 reels con ganchos, CTA a reserva y hashtags", "especialidad": "content_strategy", "tipo_tarea": "creativo", "prioridad": "alta", "criticidad": "critica", "valoracion": {"metodo": "ICE", "alcance": 4, "impacto": 4, "confianza": 4, "esfuerzo": 2, "puntaje": 128}, "dependencias": ["T-002"], "inputs": ["guia_mensajes.md"], "outputs": ["copies_pack.md"], "criterios_aceptacion": ["tono_marca", "CTA_claro"], "riesgos": ["aprobacion_tardia"], "supuestos": ["feedback_48h"], "estado_inicial": "pendiente", "subtareas": []},
        {"id": "T-005", "titulo": "Diseño de artes sociales", "descripcion": "12 artes estáticos + templates carrusel basados en copies", "especialidad": "uiux_content_design", "tipo_tarea": "produccion", "prioridad": "media", "criticidad": "importante", "valoracion": {"metodo": "ICE", "alcance": 4, "impacto": 3, "confianza": 4, "esfuerzo": 3, "puntaje": 144}, "dependencias": ["T-004"], "inputs": ["copies_pack.md", "brand_kit"], "outputs": ["social_art_pack.fig"], "criterios_aceptacion": ["legibilidad", "consistencia_marca"], "riesgos": [], "supuestos": ["brand_kit_disponible"], "estado_inicial": "pendiente", "subtareas": []}
      ]
    },
    {
      "id": "F-005",
      "nombre": "Implementación y Medición",
      "objetivo": "Publicar, medir, aprender",
      "criterios_exito": ["tracking_configurado"],
      "milestones": ["tablero_metricas"],
      "tareas": [
        {"id": "T-006", "titulo": "Guía de pauta inicial", "descripcion": "Audiencias lookalike, presupuesto inicial y creatividades A/B", "especialidad": "paid_marketing", "tipo_tarea": "estrategia", "prioridad": "media", "criticidad": "importante", "valoracion": {"metodo": "RICE", "alcance": 2000, "impacto": 3, "confianza": 0.6, "esfuerzo": 6, "puntaje": 600}, "dependencias": ["T-005"], "inputs": ["social_art_pack.fig", "copies_pack.md"], "outputs": ["playbook_ads.md"], "criterios_aceptacion": ["2 variantes por grupo"], "riesgos": ["rechazo_creativos"], "supuestos": ["cuentas_ads_activas"], "estado_inicial": "pendiente", "subtareas": []}
      ]
    }
  ],
  "areas": [
    {"especialidad": "content_strategy", "objetivos_especificos": ["mensajes_clave", "CTA_reserva"], "pilares": ["evidencia_social", "rapidez_reserva"], "tareas": ["T-002", "T-004"]},
    {"especialidad": "uiux_content_design", "objetivos_especificos": ["legibilidad", "jerarquia_visual"], "pilares": ["consistencia_marca"], "tareas": ["T-005"]},
    {"especialidad": "landing_ux_conversion", "objetivos_especificos": ["flujo_3_clicks"], "pilares": ["CTA_persistente"], "tareas": ["T-003"]},
    {"especialidad": "benchmark_research", "objetivos_especificos": ["hallazgos_accionables"], "pilares": ["mejores_practicas"], "tareas": ["T-001"]},
    {"especialidad": "project_management", "objetivos_especificos": ["sincronizacion_fases"], "pilares": ["riesgos_visibles"], "tareas": []},
    {"especialidad": "audiovisual", "objetivos_especificos": ["reels_con_gancho"], "pilares": ["primeros_3s_impacto"], "tareas": []},
    {"especialidad": "paid_marketing", "objetivos_especificos": ["aprendizaje_A/B"], "pilares": ["metricas_clave"], "tareas": ["T-006"]}
  ],
  "matriz_dependencias": {"bloqueos": [{"tarea": "T-005", "bloqueada_por": ["T-004"]}, {"tarea": "T-003", "bloqueada_por": ["T-002"]}, {"tarea": "T-006", "bloqueada_por": ["T-005"]}], "grafo": [{"from": "T-001", "to": "T-002"}, {"from": "T-002", "to": "T-003"}, {"from": "T-004", "to": "T-005"}, {"from": "T-005", "to": "T-006"}]},
  "calidad_gobernanza": {"definition_of_ready": ["inputs_disponibles", "dependencias_resueltas"], "definition_of_done": ["entregables_validados", "alineado_marca"], "quality_gates": ["cierre_F-001", "cierre_F-003"]},
  "roadmap_recomendado": {"sprints": [{"nombre": "Sprint 1 (Sem 1-2)", "objetivo": "Diagnóstico + Mensajes", "tareas": ["T-001", "T-002"]}, {"nombre": "Sprint 2 (Sem 3-4)", "objetivo": "Wireframe + Copies + Artes", "tareas": ["T-003", "T-004", "T-005"]}, {"nombre": "Sprint 3 (Sem 5-6)", "objetivo": "Ads + Medición", "tareas": ["T-006"]}]},
  "mapeo_canales": {"social": ["Instagram", "TikTok"], "pagados": ["Meta Ads"], "web": ["Landing"], "audiovisual": ["Reels"]},
  "trazabilidad": [{"tarea": "T-002", "origen": "brief.brand_identity.style"}, {"tarea": "T-003", "origen": "estrategia.cta_reserva"}]
}


9) Instrucciones Operativas del Agente
Consumir brief → extraer objetivos, restricciones, identidad, canales.
Redactar narrativa estratégica (breve, accionable).
Construir JSON siguiendo el Formato.
Aplicar priorización (RICE/ICE) y dependencias.
Validar calidad (DoR/DoD y Quality Gates).
Entregar salida: narrativa + JSON (válido)

IMPORTANT: Maintain the same language as the input briefing.""",
)

calendar_agent = Agent(
    structured_writer_model,
    output_type=list[CalendarPost],
    instructions="""

    You are a senior marketing strategist. Create a detailed 1-week content calendar for posts in instagram. 
    you need to specify if it is for feed, story, or post.
    
    type,resolution
    feed,1200x900
    story,1080x1920
    post,1080x1080

    IMPORTANT: Maintain the same language as the input strategy.
    """,
)


# A specialized agent to generate image prompts for an image model
image_prompt_agent = Agent(
    writer_model,
    output_type=str,
    instructions="""
    Inspired by this example:
    <example>
## 🌿 *Prompt SORA – Instagram Feed (4:3)*

You are a senior wellness-focused visual designer creating a hero banner background for a clean supplement brand like PuraFit. This visual must accompany the following page content:
Headline: Nature's Golden Anti-Inflammatory
Subheadline: Ancient wisdom meets modern science — clinically proven for wellness 🎯

🖼 *Scene Concept (4:3)*
A real man (age 40–55) standing in a warm, naturally lit herbal garden or backyard wellness space during early morning or golden hour. The man is casually dressed in neutral linen or cotton (cream, soft olive, or beige), gently tending to turmeric plants, herbs, or simply enjoying the natural surroundings with mindful presence. He may be sipping a mug of golden turmeric tea or lightly touching a flowering turmeric leaf.

📐 *Composition & Format (Feed 4:3)*

•⁠  ⁠Framing adapted to 4:3 ratio for Instagram feed.
•⁠  ⁠Subject slightly off-center with negative space beside him for balance.
•⁠  ⁠Soft depth of field: blurred background, crisp subject focus.
•⁠  ⁠Natural framing with lush greenery and turmeric flowers.

🎨 *Color Palette (PuraFit)*

•⁠  ⁠Background neutrals: #F4F2EF
•⁠  ⁠Golden turmeric tones: #D4A574, #B8703F
•⁠  ⁠Wardrobe & props neutrals: #FAF9F5, #F4EBDC
•⁠  ⁠Leafy greens: desaturated olive or sage tones

✍ *Emotion & Story*
A quiet, grounded moment of wellness. Empowered health through nature, expressed with editorial minimalism.

---

## 🌿 *Prompt SORA – Instagram Stories (9:16)*

You are a senior wellness-focused visual designer creating a hero background visual for a clean supplement brand like PuraFit. This visual must accompany the following page content:
Headline: Nature's Golden Anti-Inflammatory
Subheadline: Ancient wisdom meets modern science — clinically proven for wellness 🎯

🖼 *Scene Concept (9:16)*
A real man (age 40–55) in a vertical frame, standing in a warm, naturally lit herbal garden or backyard wellness space during golden hour. The man wears neutral linen or cotton (cream, soft olive, beige), holding a mug of golden turmeric tea or gently tending to turmeric plants. He is centered but with vertical breathing space above and below to allow headline and subheadline overlay.

📐 *Composition & Format (Stories 9:16)*

•⁠  ⁠Tall vertical framing optimized for Instagram Stories.
•⁠  ⁠Subject centered or slightly lower, with clear open space above for text.
•⁠  ⁠Soft natural depth of field: foreground details crisp, background blurred.
•⁠  ⁠Garden textures and golden sunlight emphasized in top half of frame.

🎨 *Color Palette (PuraFit)*

•⁠  ⁠Background neutrals: #F4F2EF
•⁠  ⁠Golden turmeric tones: #D4A574, #B8703F
•⁠  ⁠Wardrobe & props neutrals: #FAF9F5, #F4EBDC
•⁠  ⁠Leafy greens: desaturated olive or sage tones

✍ *Emotion & Story*
Not a staged ad, but a serene morning ritual captured authentically. A glimpse of empowered health and harmony through turmeric and nature.

---

## 🌿 *Prompt SORA – Instagram Post Fijo (1:1)*

You are a senior wellness-focused visual designer creating a square hero background for a clean supplement brand like PuraFit. This visual must accompany the following page content:
Headline: Nature's Golden Anti-Inflammatory
Subheadline: Ancient wisdom meets modern science — clinically proven for wellness 🎯

🖼 *Scene Concept (1:1)*
A real man (age 40–55) in a warm, naturally lit herbal garden or backyard wellness space during golden hour. The man is casually dressed in neutral linen or cotton (cream, soft olive, beige), gently tending to turmeric plants, herbs, or sipping a mug of golden turmeric tea. He should appear calm, grounded, and authentic, framed in a way that balances him within a square composition.

📐 *Composition & Format (Post 1:1)*

•⁠  ⁠Perfect square framing for Instagram grid.
•⁠  ⁠Man placed slightly off-center with balanced surrounding elements.
•⁠  ⁠Depth of field: sharp subject, softly blurred herbal background.
•⁠  ⁠Equal emphasis on subject and lush turmeric/herbal environment.

🎨 *Color Palette (PuraFit)*

•⁠  ⁠Background neutrals: #F4F2EF
•⁠  ⁠Golden turmeric tones: #D4A574, #B8703F
•⁠  ⁠Wardrobe & props neutrals: #FAF9F5, #F4EBDC
•⁠  ⁠Leafy greens: desaturated olive or sage tones

✍ *Emotion & Story*
A trustworthy, editorial-style moment of morning wellness. Natural, minimalistic, and aligned with PuraFit’s balance of science and nature.

</example>
    You are a prompt engineer. Generate 1 prompt for an image model based on user briefing. The goal is to create an image for a social media post. It must be generic to any post from that brand. IMPORTANT: Maintain the same language as the input calendar.
""",
)

# A specialized agent to generate the final landing page HTML
html_agent = Agent(
    coder_model,
    output_type=str,
    instructions=dedent("""
        You are an expert web developer specializing in high-converting landing pages.
        Generate a single, complete HTML file using Tailwind CSS for styling.

        - Use the provided briefing, strategy, and image URLs to populate the content.
        - Create sections for a hero banner, key features, and a call-to-action.
        - Ensure the final output is a single block of valid HTML code, starting with `<!DOCTYPE html>` and ending with `<:html>`.
        - Do not include any markdown formatting like ```html in your response.
        IMPORTANT: Maintain the same language as the input briefing.
    """),
)
