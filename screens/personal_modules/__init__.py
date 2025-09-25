"""
Módulos especializados para gestión de personal
Sistema modular para cuadrillas, moderadores y obreros
"""

# Versión del sistema modular
__version__ = "1.0.0"

# Imports principales para facilitar el uso
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.unified_api_client import UnifiedAPIClient as PersonalAPIClient
from .validators import PersonalValidators
from .utils import PersonalUtils
from .ui_components import PersonalUIComponents

# Managers especializados
from .obreros_manager import ObrerosManager
from .moderadores_manager import ModeradoresManager
from .cuadrillas_manager import CuadrillasManager

__all__ = [
    'PersonalAPIClient',
    'PersonalValidators',
    'PersonalUtils',
    'PersonalUIComponents',
    'ObrerosManager',
    'ModeradoresManager',
    'CuadrillasManager'
]