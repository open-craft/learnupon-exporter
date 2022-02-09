"""
Export the list of users to a CSV file
"""
from __future__ import absolute_import, print_function, unicode_literals

import csv
import os

from django.contrib.auth import get_user_model
from django.template import Variable
from django.utils import timezone

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.grades.models import PersistentCourseGrade
from edxlearndot.learndot import LearndotAPIClient
from edxlearndot.models import CourseMapping, EnrolmentStatusLog

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

        self.course_ids = options['course_ids']
        self.logger.info("Exporting courses: %s", ', '.join(self.course_ids))
        self.enrollments = CourseEnrollment.objects.filter(course__in=self.course_ids)

        with open(filepath, 'w', encoding='utf8') as csv_file:
            self.export_enrollment_data(csv_file)

        s3_bucket = self.get_s3_bucket()

        if s3_bucket is not None:
            with open(filepath, 'rb') as csv_file:
                self.upload_file_to_s3(s3_bucket, csv_file, filename)

    def get_enrollment_ids_for_user(self, user, course_mappings):
        """
        Fetch the learndot enrollment ids for the provided user.

        Returns:
        - Dictionary with
           - key=learndot enrollment id
           - value=the relevant CourseEnrollment instance
        """
        self.logger.debug("Fetching enrollment ids for user: %s", user)
        enrollments = self.enrollments.filter(user=user).select_related('user')
        learndot_client = LearndotAPIClient()
        enrollment_ids = {}
        contact_id = learndot_client.get_contact_id(user)

        for enrollment in enrollments:
            course_key = str(enrollment.course_id)
            if course_key in course_mappings and contact_id:
                course_mapping = course_mappings[course_key]
                enrollment_id = learndot_client.get_enrolment_id(contact_id, course_mapping.learndot_component_id)
                enrollment_ids[enrollment] = enrollment_id
            else:
                enrollment_ids[enrollment] = None

        self.logger.info("Fetched enrollment ids for user: %s", user)
        return enrollment_ids

    def fetch_learndot_enrollments(self):
        """
        Fetch learndot enrollment ids for all users in the system.

        Returns:
        - Dictionary with
           - key=learndot enrollment id
           - value=the relevant CourseEnrollment instance
        """

        enrollment_ids = {}
        course_mappings = {str(m.edx_course_key): m for m in CourseMapping.objects.all()}

        user_ids = self.enrollments.filter(course__in=self.course_ids).values('user_id')
        users = get_user_model().objects.filter(pk__in=user_ids)
        for user in users:
            user_enrollment_ids = self.get_enrollment_ids_for_user(user, course_mappings)
            enrollment_ids.update(user_enrollment_ids)

        return enrollment_ids

    def export_enrollment_data(self, csv_file):
        """
        Export all enrollment data in the system
        """
        field_mapping = {
            "Login ID": "user.email",
            "Course Name": "course.display_name",
            "Enrollment Status": "",
            "Enrollment Completed Date": "",
            "Enrollment Created Date": "",
            "Enrollment Started Date": "",
            "Enrollment Score": "",
            "Enrollment Access Expires Date": ""
        }

        writer = csv.DictWriter(csv_file, fieldnames=field_mapping)

        writer.writeheader()
        enrollment_statuses = {es.learndot_enrolment_id: es for es in EnrolmentStatusLog.objects.all()}

        for enrollment, enrollment_id in self.fetch_learndot_enrollments().items():
            pseudo_context = {"obj": enrollment}
            row = {}
            for csv_field, instance_field in field_mapping.items():
                if not instance_field:
                    row[csv_field] = ""
                else:
                    row[csv_field] = Variable("{{obj.%s}}" % instance_field).resolve(pseudo_context)

            row['Enrollment Status'] = 'not started'
            enrollment_status = enrollment_statuses.get(enrollment_id)
            if enrollment_status:
                grade = enrollment_status.status.lower()
                if grade == 'passed':
                    row['Enrollment Status'] = 'passed'
                    row['Enrollment Completed Date'] = self.format_date(enrollment_status.updated_at)

            writer.writerow(row)
