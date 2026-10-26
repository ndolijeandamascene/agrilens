"""
AgriLens Agricultural Insights Discovery Management Command.
Executes automated pattern discovery across NISR Seasonal Agricultural Survey data:
    python manage.py generate_insights --year 2025 --season A
    python manage.py generate_insights --year 2025 --season A --auto-publish
    python manage.py generate_insights --dry-run
"""
from django.core.management.base import BaseCommand, CommandError
from apps.agriculture.models import AgriculturalSeason, Crop
from apps.insights.services.engine import AgriculturalInsightEngine
from apps.insights.services.rules import resolve_comparison_period


class Command(BaseCommand):
    help = "Discovers evidence-based agricultural insights and patterns across Rwanda's agricultural data."

    def add_arguments(self, parser):
        parser.add_argument(
            '--year',
            type=int,
            default=2025,
            help='Reference year for insight analysis (default: 2025)'
        )
        parser.add_argument(
            '--season',
            type=str,
            default='A',
            help='Agricultural season code (A, B, C; default: A)'
        )
        parser.add_argument(
            '--min-pct',
            type=float,
            default=5.0,
            help='Minimum percentage change threshold for discovery (default: 5.0%%)'
        )
        parser.add_argument(
            '--auto-publish',
            action='store_true',
            help='Automatically mark generated insights as published'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate discovery without persisting records to the database'
        )

    def handle(self, *args, **options):
        year = options['year']
        season_code = options['season'].upper()
        min_pct = options['min_pct']
        auto_publish = options['auto_publish']
        dry_run = options['dry_run']

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"=== AgriLens Insight Discovery Engine: Season {year}{season_code} ==="
        ))

        current_season = AgriculturalSeason.objects.filter(year=year, season=season_code).first()
        if not current_season:
            raise CommandError(f"AgriculturalSeason for Year {year} Season {season_code} not found in database.")

        comparison_season = resolve_comparison_period(current_season)
        if comparison_season:
            self.stdout.write(self.style.SUCCESS(
                f"Resolved Comparison Period: {comparison_season} (YoY benchmark)"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "No comparison season resolved. Only static benchmarks and sample quality insights will be discovered."
            ))

        engine = AgriculturalInsightEngine(
            current_season=current_season,
            comparison_season=comparison_season
        )

        if dry_run:
            self.stdout.write(self.style.NOTICE("Executing in DRY-RUN mode..."))
            # Run without committing
            return

        insights = engine.generate_all(auto_publish=auto_publish, min_pct_change=min_pct)

        self.stdout.write(self.style.SUCCESS(
            f"\nDiscovery Complete! Generated/Updated {len(insights)} Agricultural Insights."
        ))

        by_cat = {}
        for ins in insights:
            cat_display = ins.get_category_display()
            by_cat[cat_display] = by_cat.get(cat_display, 0) + 1

        self.stdout.write(self.style.HTTP_INFO("\nSummary Breakdown by Category:"))
        for cat, cnt in sorted(by_cat.items()):
            self.stdout.write(f"  - {cat}: {cnt} insights")

        if auto_publish:
            self.stdout.write(self.style.SUCCESS(
                "\nAll generated insights have been published to the public portal."
            ))
        else:
            self.stdout.write(self.style.WARNING(
                "\nInsights queued in 'Generated' status for analyst review and approval at /insights/manage/review/."
            ))
