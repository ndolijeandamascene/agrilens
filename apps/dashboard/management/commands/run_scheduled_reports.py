"""
Management command to execute automated AgriLens report schedules.
Can be triggered via crontab, systemd timer, Celery/worker runner, or admin CLI.
Enforces Africa/Kigali reporting timezone, concurrency locks, duplicate prevention,
and error retry backoffs.
"""
from django.core.management.base import BaseCommand
from apps.dashboard.report_service import ReportSchedulerService


class Command(BaseCommand):
    help = "Executes active and due AgriLens automated institutional report schedules."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forces execution of schedules even if next_run_at is in the future.',
        )
        parser.add_argument(
            '--schedule-id',
            type=int,
            default=None,
            help='Runs only the specified ReportSchedule ID.',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        schedule_id = options.get('schedule_id')

        self.stdout.write(self.style.NOTICE("Initiating AgriLens Automated Report Scheduler..."))
        results = ReportSchedulerService.run_due_schedules(force=force, schedule_id=schedule_id)

        self.stdout.write(
            self.style.SUCCESS(
                f"Scheduler finished: {results['processed']} processed, "
                f"{results['succeeded']} succeeded, {results['skipped_duplicate']} skipped duplicates, "
                f"{results['failed']} failed."
            )
        )
        for job in results['jobs']:
            status_style = self.style.SUCCESS if job['status'] == 'success' else (
                self.style.WARNING if job['status'] == 'skipped_duplicate' else self.style.ERROR
            )
            self.stdout.write(status_style(f"  [{job['status'].upper()}] Schedule #{job['schedule_id']}: {job['title']}"))
