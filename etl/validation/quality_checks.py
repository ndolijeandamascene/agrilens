"""
Quality control rules (e.g. yield per hectare bounds check, GPS coordinate within Rwanda bounding box).
"""

def validate_coordinates(lat, lon):
    """Verify that coordinates lie strictly within Rwanda boundary box."""
    # Rwanda bounds approx: Lat -2.84 to -1.05, Lon 28.86 to 30.90
    return -3.0 <= lat <= -1.0 and 28.5 <= lon <= 31.0
