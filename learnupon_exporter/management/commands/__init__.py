"""
Base functions for management commands
"""
import logging
import os

import boto3
from django.conf import settings
from django.core.management.base import BaseCommand
from common.djangoapps.student.models import CourseEnrollment


def dir_path(string):
    """ Check that an argument is a valid directory """
    if os.path.isdir(string):
        return string
    else:
        raise ValueError("{string} is not a directory")

class ExportCommand(BaseCommand): # pylint: disable=abstract-method
    """
    Base command for export classes.
    """
    def add_arguments(self, parser):
        """
        Add named arguments.
        """
        self.args['output_dir'] = parser.add_argument(
            'output_dir',
            type=dir_path,
            default='/edx/src/learnupon-exporter/out',
            help='Directory to put the LearnUpon output files',
        )

        self.args['course_ids'] = parser.add_argument(
            'course_ids',
            type=str,
            help='List of Course Ids to export',
            nargs='+'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.options = {}
        self.help = __doc__
        self.logger = logging.getLogger()
        self.args = {}
        self.course_ids = []
        self.enrollments = CourseEnrollment.objects.none()

    def set_logging(self, verbosity):
        """
        Set the logging level depending on the desired vebosity
        """
        handler = logging.StreamHandler()
        root_logger = logging.getLogger('')
        root_logger.addHandler(handler)
        handler.setFormatter(logging.Formatter('%(levelname)s|%(message)s'))

        if verbosity == 1:
            self.logger.setLevel(logging.WARNING)
        elif verbosity == 2:
            self.logger.setLevel(logging.INFO)
        elif verbosity == 3:
            self.logger.setLevel(logging.DEBUG)
            handler.setFormatter(logging.Formatter('%(name)s|%(asctime)s|%(levelname)s|%(message)s'))

    def get_s3_bucket(self):
        """
        Retrieve reference to the defined s3 bucket.

        Returns None if config settings aren't defined.
        """
        if not settings.LEARNUPON_EXPORTER_AWS_ACCESS_KEY_ID:
            return None
        # Connect to AWS:
        session = boto3.Session(
            aws_access_key_id=settings.LEARNUPON_EXPORTER_AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.LEARNUPON_EXPORTER_AWS_ACCESS_KEY_SECRET,
        )
        s3 = session.resource('s3')
        return s3.Bucket(settings.LEARNUPON_EXPORTER_STATIC_FILES_BUCKET)

    def upload_file_to_s3(self, s3_bucket, file_object, filename):
        """
        Uploads the file_object to s3_bucket under filename.
        """
        file_object.seek(0)
        s3_path_prefix = settings.LEARNUPON_EXPORTER_STATIC_FILES_PATH
        return s3_bucket.put_object(Key=s3_path_prefix + filename, Body=file_object)

    def format_date(self, date):
        """
        Returns the date in the CSV format for learnupon with is dd/mm/yyyy
        """

        if not date:
            return date
        return date.strftime('%d/%m/%Y')
