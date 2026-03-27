"""
Django management command to generate and update PR numbers.
Usage: python manage.py generate_pr_numbers
"""

from django.core.management.base import BaseCommand
from apps.pr.models import PurchaseRequisition


class Command(BaseCommand):
    help = 'Generate PR numbers for requisitions that are approved'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration of PR numbers',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        # Get PRs that are approved but don't have a PR number yet
        if force:
            prs = PurchaseRequisition.objects.filter(status='APPROVED')
        else:
            prs = PurchaseRequisition.objects.filter(
                status='APPROVED',
                pr_number__isnull=True
            )
        
        count = 0
        for pr in prs:
            if not pr.pr_number or force:
                # PR number generation would be done by a service
                # For now, just mark as processed
                self.stdout.write(
                    f'Would generate PR number for {pr.pr_id}'
                )
                count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {count} requisitions'
            )
        )
