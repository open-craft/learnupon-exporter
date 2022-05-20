"""
Export the list of users to a CSV file
"""
from __future__ import absolute_import, print_function, unicode_literals

import csv
import datetime
import os

from django.contrib.auth import get_user_model
from django.template import Variable
from django.utils import timezone

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.grades.models import PersistentCourseGrade

import pytz

from . import ExportCommand


class Command(ExportCommand):
    """
    export_enrollment_data management command.
    """

    def handle(self, *args, **options):
        """
        Create the export
        """
        self.set_logging(options["verbosity"])

        now = timezone.now()
        filename = f"enrollment_export{now:%Y%m%d_%H%M%S}.csv"
        filepath = os.path.join(options["output_dir"], filename)

        self.course_ids = options["course_ids"]
        self.logger.info("Exporting courses: %s", ", ".join(self.course_ids))
        self.enrollments = CourseEnrollment.objects.filter(course__in=self.course_ids)

        start_date = options.get("start_date")

        if start_date:
            self.enrollments = self.enrollments.filter(created__gte=start_date)

        email_domain = options.get("email_domain")
        if email_domain:
            self.enrollments = self.enrollments.filter(
                user__email__endswith=email_domain
            )

        self.stdout.write("Fetching grades...")
        self.grades = {
            (grade.user_id, grade.course_id): grade
            for grade in PersistentCourseGrade.objects.all()
        }

        with open(filepath, "w", encoding="utf8") as csv_file:
            self.export_enrollment_data(csv_file)

        s3_bucket = self.get_s3_bucket()

        if s3_bucket is not None:
            with open(filepath, "rb") as csv_file:
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
            "Enrollment Access Expires Date": "course.end",
        }

        writer = csv.DictWriter(csv_file, fieldnames=field_mapping)

        writer.writeheader()
        enrollments = self.enrollments

        record_count = self.enrollments.count()
        self.stdout.write(f"Writing {record_count} enrollments")
        batch_size = int(record_count / 10) or 1

        for record_index, enrollment in enumerate(enrollments):
            if record_index > 0 and record_index % batch_size == 0:
                self.stdout.write(f"Completed: {record_index + 1} of {record_count}")

            pseudo_context = {"obj": enrollment}
            row = {}
            for csv_field, instance_field in field_mapping.items():
                if not instance_field:
                    continue
                row[csv_field] = Variable(f"obj.{instance_field}").resolve(
                    pseudo_context
                )

            row["Enrollment Status"] = "not started"
            grade = self.grades.get((enrollment.user_id, enrollment.course_id))
            modules = enrollment.user.studentmodule_set.filter(
                course_id=enrollment.course_id
            ).order_by("created")
            first_block_viewed_at = modules.values_list("created", flat=True).first()

            if first_block_viewed_at:
                row["Enrollment Status"] = "completed"
                row["Enrollment Started Date"] = first_block_viewed_at

            if grade:
                row["Enrollment Score"] = grade.percent_grade
                row["Enrollment Completed Date"] = grade.created
                row["Enrollment Status"] = "completed"
            writer.writerow(row)
        self.stdout.write("Done!")
