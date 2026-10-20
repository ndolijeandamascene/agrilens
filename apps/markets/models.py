"""
AgriLens Official Commodity Markets & Price Surveillance Models.
Maintains single authoritative dataset for both public surveillance and internal workflow:
Collection -> Validation -> Review -> Approval -> Publication.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.geography.models import Province, District
from apps.agriculture.models import Crop


class MarketLocation(models.Model):
    """Agricultural commercial market hubs across Rwanda's 30 districts."""
    MARKET_TYPES = [
        ('retail', 'Retail Consumer Market'),
        ('wholesale', 'Wholesale Trade Hub'),
        ('border', 'Cross-Border Trading Post'),
        ('assembly', 'Rural Assembly Market'),
    ]

    name = models.CharField(max_length=150)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='markets')
    province = models.ForeignKey(Province, on_delete=models.SET_NULL, null=True, blank=True, related_name='markets')
    market_type = models.CharField(max_length=30, choices=MARKET_TYPES, default='retail')
    is_major_hub = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['district__province__name', 'district__name', 'name']
        verbose_name = 'Market Location'
        verbose_name_plural = 'Market Locations'

    def save(self, *args, **kwargs):
        if self.district and not self.province:
            self.province = getattr(self.district, 'province', None)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.district.name})"


class MarketCommodity(models.Model):
    """Market commodity catalog configuration with expected price sanity bounds."""
    CATEGORIES = [
        ('Cereals', 'Cereals'),
        ('Legumes', 'Legumes & Pulses'),
        ('Roots & Tubers', 'Roots & Tubers'),
        ('Vegetables', 'Vegetables'),
        ('Fruits', 'Fruits'),
        ('Cash Crops', 'Export & Cash Crops'),
    ]

    name = models.CharField(max_length=100, unique=True)
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True, related_name='market_commodities')
    category = models.CharField(max_length=50, choices=CATEGORIES, default='Cereals')
    standard_unit = models.CharField(max_length=30, default='RWF/kg')
    min_expected_price = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    max_expected_price = models.DecimalField(max_digits=10, decimal_places=2, default=3500.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Market Commodity'
        verbose_name_plural = 'Market Commodities'

    def __str__(self):
        return f"{self.name} ({self.standard_unit})"


class CommodityPrice(models.Model):
    """
    Authoritative agricultural commodity price surveillance records.
    Governed by strict internal workflow and permission tiers.
    Public views only display records where status='published'.
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SUBMITTED = 'submitted', 'Submitted for Review'
        UNDER_REVIEW = 'under_review', 'Under Review'
        NEEDS_CORRECTION = 'needs_correction', 'Needs Correction'
        APPROVED = 'approved', 'Approved'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'
        SUPERSEDED = 'superseded', 'Superseded'

    PRICE_TYPES = [
        ('retail', 'Retail'),
        ('wholesale', 'Wholesale'),
        ('farmgate', 'Farm-gate'),
    ]

    SOURCE_TYPES = [
        ('field_officer', 'Field Data Collection'),
        ('esoko', 'e-Soko Market Surveillance'),
        ('survey', 'MINAGRI Survey'),
        ('partner', 'Partner Institution'),
    ]

    market = models.ForeignKey(MarketLocation, on_delete=models.CASCADE, related_name='prices')
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE, related_name='market_prices')
    price_per_kg_rwf = models.DecimalField(max_digits=10, decimal_places=2, help_text="Retail / standard quote (RWF/kg)")
    wholesale_price_rwf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    farmgate_price_rwf = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_type = models.CharField(max_length=20, choices=PRICE_TYPES, default='retail')
    unit = models.CharField(max_length=20, default='RWF/kg')
    date_recorded = models.DateField(db_index=True)
    time_recorded = models.TimeField(null=True, blank=True)

    # Workflow lifecycle
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PUBLISHED, db_index=True)
    source_type = models.CharField(max_length=50, choices=SOURCE_TYPES, default='field_officer')
    source_document = models.CharField(max_length=255, blank=True)

    # Actors & Governance
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='collected_prices'
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_prices'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comments = models.TextField(blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_prices'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)

    # Validation & Quality Flags
    validation_flags = models.JSONField(default=list, blank=True)
    
    # Audit & Lineage Tracking
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    correction_reason = models.TextField(blank=True)
    superseded_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='superseded_records'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_recorded', '-id']
        verbose_name = 'Commodity Market Price'
        verbose_name_plural = 'Commodity Market Prices'

    def __str__(self):
        return f"{self.crop.name} at {self.market.name}: {self.price_per_kg_rwf} RWF ({self.date_recorded}) [{self.get_status_display()}]"


class PriceCollectionAssignment(models.Model):
    """Assigns agricultural officers to collect periodic market surveillance data."""
    FREQUENCIES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
    ]

    officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_assignments')
    market = models.ForeignKey(MarketLocation, on_delete=models.CASCADE, related_name='assignments')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True, blank=True, related_name='price_assignments')
    frequency = models.CharField(max_length=20, choices=FREQUENCIES, default='weekly')
    day_of_week = models.CharField(max_length=20, default='Monday', blank=True)
    is_active = models.BooleanField(default=True)
    last_collection_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_active', 'market__name', 'officer__username']
        verbose_name = 'Price Collection Assignment'
        verbose_name_plural = 'Price Collection Assignments'

    def __str__(self):
        return f"{self.officer.username} &rarr; {self.market.name} ({self.get_frequency_display()})"


class PricePublicNotice(models.Model):
    """Public banner announcements for market alerts and price trends."""
    SEVERITY_CHOICES = [
        ('info', 'Informational Notice'),
        ('warning', 'Market Volatility Alert'),
        ('success', 'Price Stabilization Trend'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    effective_date = models.DateField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date', '-id']
        verbose_name = 'Price Public Notice'
        verbose_name_plural = 'Price Public Notices'

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"


class PriceAuditLog(models.Model):
    """Immutable audit trail for all commodity price operations."""
    price_record = models.ForeignKey(
        CommodityPrice, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)
    details = models.JSONField(default=dict, blank=True)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Price Audit Log'
        verbose_name_plural = 'Price Audit Logs'

    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"{self.action} by {actor_name} at {self.timestamp}"
