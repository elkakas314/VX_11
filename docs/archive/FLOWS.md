# VX11 v5.0 — FLOWS & DIAGRAMS

## Flujo 1: Arquitectura Global VX11

```mermaid
graph TB
    Client["Client / Copilot"]
    
    Client -->|HTTP| Gateway["Gateway (8000)"]
    
    Gateway -->|route| Madre["Madre (8001)"]
    Gateway -->|route| Switch["Switch (8002)"]
    Gateway -->|route| Hermes["Hermes (8003)"]
    Gateway -->|route| Hormiguero["Hormiguero (8004)"]
    Gateway -->|route| Manifestator["Manifestator (8005)"]
    Gateway -->|route| MCP["MCP (8006)"]
    Gateway -->|route| Shub["Shub (8007)"]
    
    Madre -->|BD| SQLite["SQLite<br/>madre.db"]
    Switch -->|BD| SQLite
    Hermes -->|BD| SQLite
    
    Manifestator -->|audit| Madre
    Manifestator -->|audit| Switch
    Manifestator -->|audit| Hermes
    
    style Gateway fill:#4CAF50
    style SQLite fill:#FFC107
    style Madre fill:#2196F3
    style Manifestator fill:#FF5722
```

---

## Flujo 2: Ciclo Autónomo Madre (v3)

```mermaid
sequenceDiagram
    participant Madre
    participant Switch
    participant Hermes
    participant Hormiguero
    participant Manifestator
    participant DB as SQLite
    
    Madre->>Madre: Esperar 30s<br/>(si enabled)
    Madre->>DB: Leer tareas pending
    Madre->>Switch: Elegir provider/modelo
    Madre->>Hermes: Ejecutar acción
    alt CLI disponible
        Hermes->>Hermes: Ejecutar CLI
        Hermes->>Madre: Resultado
    else Necesita modelo
        Hermes->>Hermes: Cargar modelo HF
        Hermes->>Madre: Output generado
    end
    
    Madre->>Hormiguero: ¿Paralela?
    alt Sí
        Hormiguero->>Hormiguero: Distribuir a hormigas
        Hormiguero->>Madre: Resultados
    else No
        Madre->>Madre: Procesar secuencial
    end
    
    Madre->>Manifestator: Auditar cambios
    Manifestator->>Manifestator: Detectar drift
    Manifestator->>Madre: Reportar
    
    Madre->>DB: Guardar IADecision
    Madre->>DB: Guardar Report
    Madre->>Madre: Sig. iteración
```

---

## Flujo 3: Switch — Selección y Scoring

```mermaid
graph LR
    A["Prompt +<br/>Task Type"]
    
    A -->|Consulting| B["ProviderSelector"]
    
    B -->|Score| C1["DeepSeek R1"]
    B -->|Score| C2["Local Mistral"]
    B -->|Score| C3["Hermes CLI"]
    B -->|Score| C4["HuggingFace"]
    
    C1 -->|Latency<br/>Success Rate| D["Scoring<br/>Algorithm"]
    C2 -->|Latency<br/>Success Rate| D
    C3 -->|Latency<br/>Success Rate| D
    C4 -->|Latency<br/>Success Rate| D
    
    D -->|Max Score| E["Selected<br/>Provider"]
    
    E -->|Persist| F["IADecision<br/>en BD"]
    
    B -->|Learning| G["Learner"]
    F -->|Feedback| G
    G -->|Update Weights| B
    
    style B fill:#4CAF50
    style E fill:#2196F3
    style G fill:#FF9800
```

---

## Flujo 4: Hermes — Ejecución de CLIs + Auto-Discovery

```mermaid
graph TB
    Request["POST /hermes/exec"]
    
    Request -->|CLI + args| Scanner["AdvancedCLIScanner<br/>~50+ CLIs"]
    
    Scanner -->|Check| Available{¿CLI<br/>disponible?}
    
    Available -->|Sí| Executor["Ejecutor seguro"]
    Available -->|No| HFSearch["¿HF Model?"]
    
    Executor -->|Timeout| Result["stdout/stderr<br/>return_code"]
    Result -->|Cache| Cache["Job registry"]
    
    HFSearch -->|Buscar| HF["HuggingFace<br/>API"]
    HF -->|Descargar| Download["Download model<br/>respetando<br/>256MB limit"]
    Download -->|Cargar| Runner["Inferencia"]
    Runner -->|Output| Result
    
    Cache -->|Persistir| DB["switch.hermes.db"]
    
    style Scanner fill:#2196F3
    style Executor fill:#4CAF50
    style HF fill:#9C27B0
    style Download fill:#FF9800
```

---

## Flujo 5: Hormiguero — Queen + Ants Paralelización

```mermaid
graph TB
    Task["Tarea paralela<br/>items = [A, B, C, D]"]
    
    Task -->|Crear| Queen["Queen<br/>(coordinadora)"]
    
    Queen -->|Distribuir| Ant1["Ant 1 (worker)"]
    Queen -->|Distribuir| Ant2["Ant 2 (worker)"]
    Queen -->|Distribuir| Ant3["Ant 3 (worker)"]
    Queen -->|Distribuir| Ant4["Ant 4 (worker)"]
    
    Ant1 -->|Procesar A| R1["Result A"]
    Ant2 -->|Procesar B| R2["Result B"]
    Ant3 -->|Procesar C| R3["Result C"]
    Ant4 -->|Procesar D| R4["Result D"]
    
    R1 -->|Recolectar| Queen
    R2 -->|Recolectar| Queen
    R3 -->|Recolectar| Queen
    R4 -->|Recolectar| Queen
    
    Queen -->|Escalado| Decision{¿Más<br/>items?}
    Decision -->|Sí, crear +workers| Ant5["Ant 5"]
    Decision -->|No, reducir| Pruning["Pruning"]
    
    Pruning -->|Finalizar| Output["Output consolidado"]
    
    style Queen fill:#FF9800
    style Ant1 fill:#4CAF50
    style Ant2 fill:#4CAF50
    style Ant3 fill:#4CAF50
    style Ant4 fill:#4CAF50
```

---

## Flujo 6: Manifestator — Drift Detect + Auto-Patch

```mermaid
sequenceDiagram
    participant User
    participant Manifestator
    participant Baseline
    participant ModuleA as Módulo (ej. Madre)
    participant AI
    participant Validator
    participant Archiver
    
    User->>Manifestator: GET /drift
    Manifestator->>Baseline: Leer snapshot v5.0
    Manifestator->>ModuleA: Leer código actual
    Manifestator->>Manifestator: Comparar (diff)
    
    alt Cambios encontrados
        Manifestator->>Manifestator: Detectar severidad
        Manifestator->>Archiver: Registrar change
        Manifestator->>User: Reportar drifts
        
        User->>Manifestator: POST /generate-patch
        Manifestator->>AI: Sugerir parche (si auto_suggest=true)
        AI->>Manifestator: Patch + reasoning
        Manifestator->>User: Return patch_id
        
        User->>Manifestator: POST /apply-patch
        Manifestator->>Validator: Validar cambios
        alt Validación OK
            Manifestator->>ModuleA: Aplicar parche
            Manifestator->>Archiver: Log success
            Manifestator->>User: "Applied ✓"
        else Validación FAIL
            Manifestator->>ModuleA: Rollback automático
            Manifestator->>User: "Rolled back ✗"
        end
    else Sin cambios
        Manifestator->>User: "Sistema intacto ✓"
    end
```

---

## Flujo 7: Shub Niggurath — Pipeline IA

```mermaid
graph TB
    Input["Input<br/>(archivo/texto)"]
    
    Input -->|Detectar tipo| TypeDetect["Type Detection<br/>PDF/TXT/IMG/AUDIO"]
    
    TypeDetect -->|PDF| OCR["OCR<br/>Tesseract / PyPDF2"]
    TypeDetect -->|IMG| Vision["Vision Model<br/>ViT / ResNet"]
    TypeDetect -->|AUDIO| STT["Speech-to-Text<br/>Whisper"]
    TypeDetect -->|TXT| Direct["Directo"]
    
    OCR -->|Texto| Normalize["Normalización"]
    Vision -->|Descripción| Normalize
    STT -->|Transcripción| Normalize
    Direct -->|Ya texto| Normalize
    
    Normalize -->|Clean| Embeddings["Embeddings<br/>(Sentence-BERT)"]
    
    Embeddings -->|Vector| Model["Modelo IA<br/>(Generación/Análisis)"]
    
    Model -->|Output| PostProcess["Post-procesamiento"]
    
    PostProcess -->|Cache| Cache["models/ dir<br/>respetando<br/>límites"]
    
    PostProcess -->|Return| Output["Output<br/>(JSON/texto)"]
    
    style Input fill:#4CAF50
    style Model fill:#9C27B0
    style Output fill:#2196F3
```

---

## Flujo 8: MCP — Conversación + Orquestación de Acciones

```mermaid
sequenceDiagram
    participant Copilot
    participant MCP
    participant Madre
    participant Switch
    participant Hermes
    participant ContextDB
    
    Copilot->>MCP: POST /mcp/chat "¿Analizar datos?"
    
    MCP->>ContextDB: Cargar sesión
    MCP->>MCP: Parse intención ("analyze_data")
    MCP->>MCP: Generar plan (acción sugerida)
    
    alt AI Reasoning (internamente)
        MCP->>Switch: ¿Provider disponible?
        Switch->>MCP: Recomendación
        MCP->>Madre: ¿Crear task?
        Madre->>MCP: task_id asignado
    end
    
    MCP->>Copilot: Response + actions_suggested
    Copilot->>User: Chat + botones [Ejecutar análisis]
    
    User->>Copilot: Click [Ejecutar]
    Copilot->>MCP: POST /mcp/action { action: "analyze_data" }
    
    MCP->>Hermes: Ejecutar análisis
    Hermes->>MCP: Resultados
    
    MCP->>ContextDB: Guardar sesión + resultado
    MCP->>Copilot: Action result JSON
    
    Copilot->>User: "Análisis completado ✓"
    
    style MCP fill:#FF9800
    style Copilot fill:#2196F3
    style ContextDB fill:#FFC107
```

---

## Flujo 9: Ultra-Low-Memory — Garbage Collection & Evicción

```mermaid
graph TB
    Container["Contenedor (512MB)"]
    
    Container -->|Monitorear| Monitor["Memory Monitor<br/>psutil"]
    
    Monitor -->|Cada 30s| Check{¿Uso ><br/>80%?}
    
    Check -->|No| Idle["Idle"]
    Idle -->|30s| Monitor
    
    Check -->|Sí| Trigger["GC Trigger"]
    
    Trigger -->|1| Clear1["Limpiar<br/>cache CLIs"]
    Trigger -->|2| Clear2["Limpiar<br/>sesiones idle"]
    Trigger -->|3| Clear3["Evicción LRU<br/>contextos"]
    
    Clear1 --> Check1{¿Suficiente?}
    Clear2 --> Check1
    Clear3 --> Check1
    
    Check1 -->|Sí| OK["Continuar ✓"]
    Check1 -->|No| Emergency["Emergency:<br/>Unload Models"]
    
    Emergency -->|último recurso| Unload["Descargar<br/>modelos HF"]
    Unload -->|Guardadas| Disk["Guardadas en<br/>disk (cache)"]
    Unload -->|Siguiente uso| Reload["Reload en<br/>demanda"]
    
    Disk -->|OK| OK
    
    style Container fill:#4CAF50
    style Monitor fill:#2196F3
    style Emergency fill:#FF5722
```

---

## Flujo 10: Self-Healing — Monitoring + Auto-Restart + Optimización

```mermaid
graph TB
    HealthCheck["Health Check<br/>(cada 30s)"]
    
    HealthCheck -->|GET /health| AllModules["Verificar<br/>8 módulos"]
    
    AllModules -->|Analizar| Detector["Detector de<br/>problemas"]
    
    Detector -->|Status| Decision{¿Módulo<br/>OK?}
    
    Decision -->|Sí| Log1["Log: OK ✓"]
    Decision -->|No: Caído| Restart["Restart<br/>automático"]
    Decision -->|No: Lento| Optimize["Optimización"]
    
    Restart -->|docker-compose| Kill["Kill contenedor"]
    Kill -->|Auto-recovery| Spawn["Spawn nuevo<br/>contenedor"]
    Spawn -->|Verificar| ReCheck{"¿Health OK?"}
    
    ReCheck -->|Sí| Log2["Log: Recovered ✓"]
    ReCheck -->|No x3| Alert["ALERT:<br/>Manual intervention"]
    
    Optimize -->|Detectar causa| Analyze{Problema?}
    
    Analyze -->|Memoria| ClearMem["Trigger GC"]
    Analyze -->|CPU| Throttle["Throttle threads"]
    Analyze -->|BD| Vacuum["VACUUM SQLite"]
    
    ClearMem -->|Después| Log3["Log: Optimized"]
    Throttle -->|Después| Log3
    Vacuum -->|Después| Log3
    
    Log1 -->|Ciclo| HealthCheck
    Log2 -->|Ciclo| HealthCheck
    Log3 -->|Ciclo| HealthCheck
    
    style HealthCheck fill:#2196F3
    style Restart fill:#FF9800
    style Alert fill:#FF5722
    style Optimize fill:#4CAF50
```

---

## Resumen de Flujos

| Flujo | Propósito | Actores clave |
|-------|-----------|---------------|
| 1 | Arquitectura global | Todos los 8 módulos |
| 2 | Ciclo autónomo Madre | Madre → Switch → Hermes → Hormiguero → Manifestator |
| 3 | Selección de provider | Switch + Scoring + Learner |
| 4 | Ejecución de CLIs | Hermes + AdvancedCLIScanner + HF |
| 5 | Paralelización | Hormiguero (Queen + Ants) |
| 6 | Auditoría y parches | Manifestator + Baseline + AI |
| 7 | Procesamiento IA | Shub Niggurath (OCR + Vision + STT + Embeddings) |
| 8 | Conversación | MCP + Copilot + Orquestación |
| 9 | Gestión de memoria | Garbage collection + Evicción LRU |
| 10 | Auto-healing | Health checks + Restart + Optimización |

---

## Cómo usar estos diagramas

1. **Visualizar:** Copiar código Mermaid a https://mermaid.live/
2. **Documentación:** Incluir en READMEs y wikis de proyecto
3. **Debugging:** Usar para rastrear flujos cuando hay errores
4. **Onboarding:** Mostrar a nuevos desarrolladores la arquitectura

---

**VX11 v5.0 Flows — 10 diagramas para entender la arquitectura completa.**
