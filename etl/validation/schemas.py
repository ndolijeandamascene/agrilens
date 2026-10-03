"""
Validation schema definitions for inbound agricultural and survey data.
"""

SURVEY_SCHEMA = {
    'required_fields': ['farmer_id', 'sector_code', 'crop_code', 'season', 'area_planted_ha'],
}
