# Módulos de Reportes - Sistema Empresa Limpieza
# Arquitectura modular para gestión de reportes especializados

from .reportes_obreros import ReportesObrerosManager
from .reportes_moderadores import ReportesModeradoresManager
from .reportes_generales_manager import ReportesGeneralesManager
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.unified_api_client import UnifiedAPIClient as ReportesAPIClient
from .report_components import (
    ReportCard,
    StatsCard,
    ExportButton,
    ErrorDisplay,
    LoadingIndicator
)

__all__ = [
    'ReportesObrerosManager',
    'ReportesModeradoresManager',
    'ReportesGeneralesManager',
    'ReportesAPIClient',
    'ReportCard',
    'StatsCard',
    'ExportButton',
    'ErrorDisplay',
    'LoadingIndicator'
]