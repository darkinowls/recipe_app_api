"""
Django command to wait for db
"""
from django.db.utils import OperationalError

from django.core.management.base import BaseCommand

import time

from psycopg2 import OperationalError as Psycopg2Error


class Command(BaseCommand):
    """Django command to wait for db"""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for db...")
        db_up = False
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write("Waiting 1 second...")
                time.sleep(1)
        self.stdout.write(self.style.SUCCESS("DB is available!"))
