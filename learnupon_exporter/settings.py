"""
Common settings for the learnupon-exporter app.

See apps.py for details on how this sort of plugin configures itself for
integration with Open edX.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

# Declare defaults: ############################################################

# S3 Bucket to put files into. If empty no S3 upload is attempted.
LEARNUPON_EXPORTER_STATIC_FILES_BUCKET = ''
# Folder/Prefix to use within the S3 bucket for the output file.
LEARNUPON_EXPORTER_STATIC_FILES_PATH = 'learnupon_exports/'
# AWS Access Key
LEARNUPON_EXPORTER_AWS_ACCESS_KEY_ID = ''
# AWS Secret Key
LEARNUPON_EXPORTER_AWS_ACCESS_KEY_SECRET = ''

# Register settings: ###########################################################


def plugin_settings(settings):
    """
    Add our default settings to the edx-platform settings. Other settings files
    may override these values later, e.g. via envs/private.py.
    """
    settings.LEARNUPON_EXPORTER_STATIC_FILES_BUCKET = LEARNUPON_EXPORTER_STATIC_FILES_BUCKET
    settings.LEARNUPON_EXPORTER_STATIC_FILES_PATH = LEARNUPON_EXPORTER_STATIC_FILES_PATH
    settings.LEARNUPON_EXPORTER_AWS_ACCESS_KEY_ID = LEARNUPON_EXPORTER_AWS_ACCESS_KEY_ID
    settings.LEARNUPON_EXPORTER_AWS_ACCESS_KEY_SECRET = LEARNUPON_EXPORTER_AWS_ACCESS_KEY_SECRET
