"""
VX11 DSL Parser — Convertir lenguaje natural a comandos VX11.

PASO 4: Parser completo con soporte para 8 dominios VX11::*

COMANDOS SOPORTADOS:
  VX11::TASK       - Crear/gestionar tareas generales
  VX11::AUDIO      - Procesamiento de audio (Shub)
  VX11::PATCH      - Generación/aplicación de parches
  VX11::SCAN       - Escanear sistema/drift
  VX11::HERMES     - Ejecutar herramientas CLI
  VX11::SHUB       - Orquestación de Shub-Niggurath
  VX11::HORMIGUERO - Control de colonia de hormigas
  VX11::OPERATOR   - Comandos del operador

EJEMPLO:
  Input:  "crear tarea audio con archivo.mp3"
  Output: VX11::TASK type="audio" action="create" file="archivo.mp3"

STATUS: Implementación completa PASO 4
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime

logger = logging.getLogger("vx11.madre.dsl_parser")


class VX11Domain(Enum):
    """Dominios VX11 canónicos"""
    
    TASK = "TASK"
    AUDIO = "AUDIO"
    PATCH = "PATCH"
    SCAN = "SCAN"
    HERMES = "HERMES"
    SHUB = "SHUB"
    HORMIGUERO = "HORMIGUERO"
    OPERATOR = "OPERATOR"


class VX11Intent:
    """Estructura de intent parseado"""
    
    def __init__(self, 
                 domain: VX11Domain,
                 action: str,
                 parameters: Dict[str, Any],
                 confidence: float = 0.7,
                 original_text: str = ""):
        self.domain = domain
        self.action = action
        self.parameters = parameters
        self.confidence = confidence
        self.original_text = original_text
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para serialización"""
        return {
            "domain": self.domain.value,
            "action": self.action,
            "parameters": self.parameters,
            "confidence": self.confidence,
            "original_text": self.original_text,
            "timestamp": self.timestamp,
        }
    
    def to_vx11_command(self) -> str:
        """Genera comando VX11 formal"""
        params_str = " ".join([
            f'{k}="{v}"' if isinstance(v, str) else f'{k}={v}'
            for k, v in self.parameters.items()
        ])
        
        if params_str:
            return f'VX11::{self.domain.value} action="{self.action}" {params_str}'
        else:
            return f'VX11::{self.domain.value} action="{self.action}"'


class VX11DSLParser:
    """
    Parser DSL de VX11.
    
    Convierte lenguaje natural a intents estructurados.
    Mapea automáticamente a dominios correctos.
    """
    
    def __init__(self):
        self.domain_patterns = self._init_domain_patterns()
        self.action_patterns = self._init_action_patterns()
        logger.info("DSL Parser VX11 inicializado (PASO 4)")
    
    def _init_domain_patterns(self) -> Dict[VX11Domain, List[Tuple[str, float]]]:
        """Patrones para detectar dominios con pesos de confianza"""
        return {
            VX11Domain.TASK: [
                (r"(crear|nueva|crear tarea|nueva tarea|task|tarea)", 0.9),
                (r"(genera|generar).*(tarea|proceso)", 0.8),
                (r"(ejecuta|run).*(tarea)", 0.85),
            ],
            VX11Domain.AUDIO: [
                (r"(audio|sonido|música|music|mix|mezcla)", 0.95),
                (r"(shub|shubniggurath)", 0.99),
                (r"(denoise|denoise|restore|restoration)", 0.9),
                (r"(mastering|master|loudness|LUFS)", 0.9),
                (r"(reaper|DAW|estudio)", 0.85),
            ],
            VX11Domain.PATCH: [
                (r"(parche|patch|fix|reparar|repair)", 0.9),
                (r"(manifesto|manifest|validar|validate)", 0.85),
                (r"(drift|drift detection)", 0.95),
                (r"(aplica|apply).*(parche|patch)", 0.95),
            ],
            VX11Domain.SCAN: [
                (r"(escanea|scan|analiza|analyze).*(sistema|system)", 0.9),
                (r"(estado|status).*(sistema|system)", 0.8),
                (r"(diagnóstico|diagnostic)", 0.85),
                (r"(verificar|verify|check).*(estructura|structure)", 0.8),
            ],
            VX11Domain.HERMES: [
                (r"(ejecuta|run).*(comando|command|cli)", 0.9),
                (r"(hermes|CLI|tool)", 0.85),
                (r"(shell|bash|script)", 0.8),
                (r"(modelo local|local model)", 0.85),
            ],
            VX11Domain.SHUB: [
                (r"(shub|niggurath|audio engine)", 0.99),
                (r"(restoration|arrangement|restoration|audio)", 0.85),
                (r"(track|vocal|instrument|drums)", 0.75),
            ],
            VX11Domain.HORMIGUERO: [
                (r"(hormiguero|hormiga|ant|queen|reina)", 0.98),
                (r"(feromonas|pheromone)", 0.95),
                (r"(mutación|mutation|GA|evolution)", 0.85),
            ],
            VX11Domain.OPERATOR: [
                (r"(operador|operator|controla|control)", 0.8),
                (r"(chat|conversación|conversation)", 0.7),
            ],
        }
    
    def _init_action_patterns(self) -> Dict[VX11Domain, Dict[str, List[str]]]:
        """Patrones para detectar acciones por dominio"""
        return {
            VX11Domain.TASK: {
                "create": ["crear", "nueva", "new", "crear tarea"],
                "status": ["estado", "status", "show", "lista"],
                "cancel": ["cancela", "detén", "para", "cancel", "stop"],
                "execute": ["ejecuta", "run", "start"],
            },
            VX11Domain.AUDIO: {
                "restore": ["restore", "restaura", "denoise", "denoise"],
                "arrange": ["arrange", "arregla", "mezcla", "mix"],
                "analyze": ["analiza", "analyze"],
                "master": ["master", "mastering", "loudness"],
                "process": ["procesa", "process", "fx", "effect"],
            },
            VX11Domain.PATCH: {
                "generate": ["genera", "generate", "crea", "create"],
                "apply": ["aplica", "apply", "ejecuta", "run"],
                "validate": ["valida", "validate", "verify", "verifica"],
                "scan": ["escanea", "scan"],
            },
            VX11Domain.SCAN: {
                "system": ["sistema", "system", "status"],
                "drift": ["drift", "cambios", "changes"],
                "health": ["salud", "health", "diagnóstico"],
            },
            VX11Domain.HERMES: {
                "execute": ["ejecuta", "run", "call"],
                "list": ["lista", "list", "enumerate"],
                "search": ["busca", "search"],
            },
            VX11Domain.SHUB: {
                "restore": ["restore", "restoration"],
                "arrange": ["arrange", "arrangement"],
                "analyze": ["analyze", "analysis"],
            },
            VX11Domain.HORMIGUERO: {
                "create": ["crea", "create", "spawn"],
                "report": ["reporte", "report"],
                "control": ["controla", "control"],
            },
            VX11Domain.OPERATOR: {
                "chat": ["chat", "conversación"],
                "control": ["controla", "control"],
            },
        }
    
    def parse(self, input_text: str) -> Optional[VX11Intent]:
        """
        Parsea texto natural a VX11Intent.
        
        Args:
            input_text: Texto natural
        
        Returns:
            VX11Intent si parsea exitosamente, None si no hay dominio claro
        """
        logger.info(f"Parsing DSL: {input_text[:80]}...")
        
        text_lower = input_text.lower()
        
        # 1) Detectar dominio
        domain, confidence = self._detect_domain(text_lower)
        if not domain:
            logger.warning(f"No domain detected: {input_text[:50]}")
            return None
        
        # 2) Detectar acción
        action = self._detect_action(text_lower, domain)
        if not action:
            action = "default"
        
        # 3) Extraer parámetros
        parameters = self._extract_parameters(text_lower, domain, action)
        
        # 4) Crear intent
        intent = VX11Intent(
            domain=domain,
            action=action,
            parameters=parameters,
            confidence=confidence,
            original_text=input_text,
        )
        
        logger.info(f"Intent parsed: {intent.to_vx11_command()}")
        return intent
    
    def _detect_domain(self, text_lower: str) -> Tuple[Optional[VX11Domain], float]:
        """
        Detecta dominio con confianza.
        
        Returns:
            (Domain, confidence) o (None, 0.0)
        """
        best_domain = None
        best_confidence = 0.0
        
        for domain, patterns in self.domain_patterns.items():
            for pattern, weight in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if weight > best_confidence:
                        best_confidence = weight
                        best_domain = domain
        
        return best_domain, best_confidence
    
    def _detect_action(self, text_lower: str, domain: VX11Domain) -> Optional[str]:
        """Detecta acción dentro de un dominio"""
        action_map = self.action_patterns.get(domain, {})
        
        for action, keywords in action_map.items():
            for keyword in keywords:
                if re.search(rf"\b{keyword}\b", text_lower, re.IGNORECASE):
                    return action
        
        return None
    
    def _extract_parameters(self, text_lower: str, domain: VX11Domain, action: str) -> Dict[str, Any]:
        """Extrae parámetros específicos según dominio y acción"""
        params = {}
        
        # Parámetros genéricos
        # archivo/file
        file_match = re.search(r"(?:archivo|file|archivo|with)\s+([^\s,]+\.(?:mp3|wav|flac|ogg))", text_lower)
        if file_match:
            params["file"] = file_match.group(1)
        
        # prioridad
        priority_match = re.search(r"prioridad\s+(\d+)", text_lower)
        if priority_match:
            params["priority"] = int(priority_match.group(1))
        
        # Parámetros específicos por dominio
        if domain == VX11Domain.AUDIO:
            if "denoise" in text_lower:
                params["operation"] = "denoise"
                if "agresivo" in text_lower or "heavy" in text_lower:
                    params["intensity"] = "heavy"
                else:
                    params["intensity"] = "medium"
            elif "master" in text_lower:
                params["operation"] = "mastering"
                lufs_match = re.search(r"(-?\d+\.?\d*)\s*LUFS", text_lower)
                if lufs_match:
                    params["target_loudness"] = float(lufs_match.group(1))
        
        elif domain == VX11Domain.PATCH:
            if "manifiesto" in text_lower:
                params["target"] = "manifest"
            elif "drift" in text_lower:
                params["target"] = "drift_detection"
        
        elif domain == VX11Domain.TASK:
            # Tipo de tarea
            if "audio" in text_lower:
                params["type"] = "audio"
            elif "código" in text_lower or "code" in text_lower:
                params["type"] = "code"
            elif "análisis" in text_lower or "analysis" in text_lower:
                params["type"] = "analysis"
        
        return params
    
    def format_command(self, intent: VX11Intent) -> str:
        """Convierte intent a comando VX11 formal"""
        return intent.to_vx11_command()
    
    def parse_natural_language(self, text: str) -> Dict[str, Any]:
        """
        API compatible: parsea lenguaje natural y retorna dict.
        (Mantiene compatibilidad con otros módulos)
        """
        intent = self.parse(text)
        if intent:
            return intent.to_dict()
        return {
            "domain": "UNKNOWN",
            "action": "default",
            "parameters": {},
            "confidence": 0.0,
            "original_text": text,
            "timestamp": datetime.utcnow().isoformat(),
        }

