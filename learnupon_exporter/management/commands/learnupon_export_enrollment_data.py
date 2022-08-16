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
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

import pytz

from . import ExportCommand
from concurrent import futures


class Command(ExportCommand):
    """
    export_enrollment_data management command.
    """

    def handle(self, *args, **options):
        """
        Create the export
        """
        self.timestamp = timezone.now()
        self.output_dir = options["output_dir"]

        course_ids = options["course_ids"]
        if not course_ids:
            course_ids = CourseOverview.objects.values_list("id", flat=True).order_by("id")
            self.stdout.write(f"Exporting ALL {course_ids.count()} courses")
        else:
            self.stdout.write("Exporting courses: %s" % ", ".join(course_ids))

        self.course_indexes = {course_id: index for index, course_id in enumerate(course_ids, 1)}

        self.email_domain = options.get("email_domain")
        self.start_date = options.get("start_date")

        with futures.ThreadPoolExecutor() as executor:
            for result in executor.map(self.export_course_to_csv, course_ids):
                continue

    def export_course_to_csv(self, course_id):
        timestamp = self.timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"enrollment_export{timestamp}_{course_id}.csv"
        filepath = os.path.join(self.output_dir, filename)
        course_index = self.course_indexes[course_id]
        self.stdout.write(f"{course_id} - starting export #{course_index}")

        enrollments = self.get_enrollments_for_course(course_id)
        with open(filepath, "w", encoding="utf8") as csv_file:
            self.export_enrollments_to_csv(csv_file, enrollments, f"{course_id} - ")

        s3_bucket = self.get_s3_bucket()

        if s3_bucket is not None:
            self.stdout.write(f"{course_id} - uploading to s3")
            with open(filepath, "rb") as csv_file:
                self.upload_file_to_s3(s3_bucket, csv_file, filename)

        self.stdout.write(f"{course_id} - completed")

    def get_enrollments_for_course(self, course_id):
        enrollments = CourseEnrollment.objects.filter(course_id=course_id)

        if self.email_domain:
            enrollments = enrollments.filter(user__email__endswith=self.email_domain)

        if self.start_date:
            enrollments = enrollments.filter(created__gte=self.start_date)
        return enrollments

    def export_enrollments_to_csv(self, csv_file, enrollments, progress_prefix=""):
        """
        Export all enrollment data in the system
        """
        field_mapping = {
            "Login ID": "user.email",
            "Course Name": "course.display_name",
            "Enrollment Created Date": "created",
            "Enrollment Started Date": "created",
            "Enrollment Completed Date": "",
            "Enrollment Status": "",
            "Enrollment Access Expires Date": "course.end",
        }

        writer = csv.DictWriter(csv_file, fieldnames=field_mapping)

        writer.writeheader()
        record_count = enrollments.count()
        self.stdout.write(f"{progress_prefix}Writing {record_count} enrollments")
        batch_size = int(record_count / 10) or 1

        for record_index, enrollment in enumerate(enrollments):
            if record_index > 0 and record_index % batch_size == 0:
                self.stdout.write(
                    f"{progress_prefix}Completed: {record_index + 1} of {record_count}"
                )

            pseudo_context = {"obj": enrollment}
            row = {}
            for csv_field, instance_field in field_mapping.items():
                if not instance_field:
                    continue
                row[csv_field] = Variable(f"obj.{instance_field}").resolve(
                    pseudo_context
                )

            row["Enrollment Status"] = "not started"
            modules = enrollment.user.studentmodule_set.filter(
                course_id=enrollment.course_id
            ).order_by("-created")
            last_block_viewed_at = modules.values_list("created", flat=True).first()

            if last_block_viewed_at:
                row["Enrollment Status"] = "completed"
                row["Enrollment Completed Date"] = last_block_viewed_at

            writer.writerow(row)
