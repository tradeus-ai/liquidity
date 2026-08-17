"""
SMC Zones Backward Compatibility Module
=======================================
Re-exports zone drawing and management tools from the dedicated zone_service.py.
"""

from zone_service import (
    extract_demand_zones,
    extract_supply_zones,
    ZoneManager
)
