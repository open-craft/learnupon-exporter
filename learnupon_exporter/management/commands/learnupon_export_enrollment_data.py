"""
Export the list of users to a CSV file
"""
from __future__ import absolute_import, print_function, unicode_literals

import csv
import os

from django.template import Variable
from django.utils import timezone

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.grades.models import PersistentCourseGrade

from . import ExportCommand


class Command(ExportCommand):
    """
    export_enrollment_data management command.
    """
    def handle(self, *args, **options):
        """
        Create the export
        """
        self.set_logging(options['verbosity'])
        now = timezone.now()
        filename = f"enrollment_export{now:%Y%m%d_%H%M%S}.csv"
        filepath = os.path.join(options['output_dir'], filename)

        with open(filepath, 'w', encoding='utf8') as csv_file:
            self.export_enrollment_data(csv_file)

        s3_bucket = self.get_s3_bucket()

        if s3_bucket is not None:
            with open(filepath, 'rb') as csv_file:
                self.upload_file_to_s3(s3_bucket, csv_file, filename)

    def export_enrollment_data(self, csv_file):
        """
        Export all enrollment data in the system
        """
        field_mapping = {
            "Login ID": "user.email",
            "Course Name": "course.display_name",
            "Enrollment Created Date": "created",
            "Enrollment Started Date": "",
            "Enrollment Completed Date": "",
            "Enrollment Score": "",
            "Enrollment Status": "",
            "Enrollment Access Expires Date": "course.end"
        }

        writer = csv.DictWriter(csv_file, fieldnames=field_mapping)

        writer.writeheader()
        enrollments = CourseEnrollment.objects.select_related('user', 'course')
        grades = {(grade.user_id, grade.course_id): grade for grade in PersistentCourseGrade.objects.all()}

        for enrollment in enrollments:
            pseudo_context = {"obj": enrollment}
            row = {}
            for csv_field, instance_field in field_mapping.items():
                if not instance_field:
                    continue
                row[csv_field] = Variable(f"obj.{instance_field}").resolve(pseudo_context)

            row['Enrollment Status'] = "not started"
            grade = grades.get((enrollment.user_id, enrollment.course_id))
            modules = enrollment.user.studentmodule_set.filter(course_id=enrollment.course_id).order_by('created')
            first_block_viewed_at = modules.values_list('created', flat=True).first()

            if first_block_viewed_at:
                row['Enrollment Status'] = "started"
                row['Enrollment Started Date'] = first_block_viewed_at

            if grade:
                row["Enrollment Score"] = grade.percent_grade
                row["Enrollment Completed Date"] = grade.created
                if grade.passed_timestamp:
                    row['Enrollment Status'] = "failed" if not grade.letter_grade else "passed"
                else:
                    row['Enrollment Status'] = "completed"
            writer.writerow(row)
