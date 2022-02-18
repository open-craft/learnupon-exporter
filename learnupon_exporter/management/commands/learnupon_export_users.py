"""
Export the list of users to a CSV file
"""
from __future__ import absolute_import, print_function, unicode_literals

import csv
import os

from django.contrib.auth import get_user_model
from django.utils import timezone

from common.djangoapps.student.models import CourseEnrollment

from . import ExportCommand


class Command(ExportCommand):
    """
    export_users management command.
    """
    def handle(self, *args, **options):
        """
        Create the user export
        """
        self.set_logging(options['verbosity'])
        now = timezone.now()
        filename = f"user_export{now:%Y%m%d_%H%M%S}.csv"
        filepath = os.path.join(options['output_dir'], filename)
        self.course_ids = options['course_ids']

        with open(filepath, 'w+', encoding='utf8') as csv_file:
            self.export_users(csv_file)
            s3_bucket = self.get_s3_bucket()
            if s3_bucket is not None:
                self.upload_file_to_s3(s3_bucket, csv_file, filename)

    def export_users(self, csv_file):
        """
        Export all user data to a CSV file.
        """
        field_mapping = {
            'email': 'email',
            'firstname': 'first_name',
            'lastname': 'last_name',
            'username': 'username'
        }

        writer = csv.DictWriter(csv_file, fieldnames=field_mapping)

        user_ids = CourseEnrollment.objects.filter(course__in=self.course_ids).values('user_id')

        writer.writeheader()
        for user in get_user_model().objects.filter(pk__in=user_ids):
            row = {}
            for csv_field, instance_field in field_mapping.items():
                row[csv_field] = getattr(user, instance_field, "")
            writer.writerow(row)
