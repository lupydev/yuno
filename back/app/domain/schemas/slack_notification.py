"""
Slack Notification Schemas

Modelos Pydantic simplificados para que la IA genere el contenido de las notificaciones.
La IA genera texto plano y el código lo convierte a Slack Block Kit.
"""

from pydantic import BaseModel, Field


class AIGeneratedSlackNotification(BaseModel):
    """
    Contenido generado por IA para notificación de Slack.
    
    La IA solo genera el texto, no los bloques de Slack.
    El código Python construye los bloques a partir de este contenido.
    """
    
    # Texto principal del header
    header_text: str = Field(
        ..., 
        description="Título corto y claro del problema (max 150 caracteres)"
    )
    
    # Resumen ejecutivo
    summary: str = Field(
        ..., 
        description="Resumen ejecutivo en 1-2 oraciones del problema y su impacto"
    )
    
    # Detalles técnicos
    details: str = Field(
        ..., 
        description="Detalles técnicos del problema, causas, y patrones detectados"
    )
    
    # Métricas clave
    metrics_text: str = Field(
        ..., 
        description="Métricas relevantes formateadas (success rate, eventos fallidos, etc.)"
    )
    
    # Acciones recomendadas
    actions_text: str = Field(
        ..., 
        description="Lista de acciones inmediatas recomendadas"
    )
    
    # Contexto adicional (opcional)
    footer_context: str | None = Field(
        default=None,
        description="Información adicional de contexto (opcional)"
    )
    
    # Color sugerido para la barra lateral
    suggested_color: str = Field(
        default="danger",
        description="Color sugerido: 'danger' (rojo), 'warning' (amarillo), 'good' (verde)"
    )

