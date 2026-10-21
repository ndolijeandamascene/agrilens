"""
Agricultural domain models:
- Crops (Maize, Beans, Irish Potato, Cassava, Rice, Coffee, Tea)
- Agricultural Seasons in Rwanda (Season A, Season B, Season C)
- Cultivation practices and farming categories.
"""
from django.db import models

class CropCategory(models.Model):
    name = models.CharField(max_length=50) # Cereals, Legumes, Tubers, Cash crops
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Crop(models.Model):
    category = models.ForeignKey(CropCategory, on_delete=models.PROTECT, related_name='crops')
    name = models.CharField(max_length=100)
    kinyarwanda_name = models.CharField(max_length=100, blank=True)
    scientific_name = models.CharField(max_length=120, blank=True)
    is_priority_crop = models.BooleanField(default=False)
    image = models.ImageField(upload_to='crops/', blank=True, null=True, help_text="Uploaded crop photo thumbnail")
    icon = models.CharField(max_length=50, blank=True, default='', help_text="Professional SVG icon name (e.g. cereal, tuber, legume, leaf)")

    def __str__(self):
        return self.name

    @property
    def image_url_or_default(self):
        """Returns the uploaded image URL if available, else a preset static thumbnail or empty string."""
        if self.image:
            try:
                return self.image.url
            except Exception:
                pass
        name_lower = self.name.lower()
        if 'cassava' in name_lower:
            return '/static/images/crops/cassava.jpg'
        elif 'potato' in name_lower:
            return '/static/images/crops/potato.jpg'
        elif 'rice' in name_lower:
            return '/static/images/crops/rice.svg'
        elif 'maize' in name_lower or 'corn' in name_lower:
            return '/static/images/crops/maize.svg'
        return ''

    @property
    def default_icon(self):
        """Professional icon identifier (never emojis) for clean SVG rendering."""
        if self.icon and not any(ord(char) > 127 for char in self.icon):
            return self.icon
        name_lower = self.name.lower()
        if 'maize' in name_lower or 'wheat' in name_lower or 'sorghum' in name_lower:
            return 'cereal'
        elif 'rice' in name_lower:
            return 'rice'
        elif 'potato' in name_lower or 'cassava' in name_lower or 'tuber' in name_lower:
            return 'tuber'
        elif 'bean' in name_lower or 'soy' in name_lower or 'legume' in name_lower:
            return 'legume'
        elif 'tomato' in name_lower or 'onion' in name_lower or 'cabbage' in name_lower or 'vegetable' in name_lower:
            return 'vegetable'
        elif 'banana' in name_lower or 'mango' in name_lower or 'fruit' in name_lower:
            return 'fruit'
        elif 'coffee' in name_lower or 'tea' in name_lower:
            return 'cash-crop'
        return 'leaf'

class AgriculturalSeason(models.Model):
    class SeasonCode(models.TextChoices):
        SEASON_A = 'A', 'Season A (Sept - Feb)'
        SEASON_B = 'B', 'Season B (Mar - June)'
        SEASON_C = 'C', 'Season C (July - Sept / Marshlands)'

    year = models.PositiveIntegerField()
    season = models.CharField(max_length=2, choices=SeasonCode.choices)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('year', 'season')

    @property
    def season_code(self):
        """Convenience property returning the season letter (e.g. 'A', 'B', 'C')."""
        return self.season

    def __str__(self):
        return f"{self.year} {self.get_season_display()}"
