Learnupon Exporter
==================

This is a Django app plugin for exporting user data from edX to LearnUpon.

It has management commands to export the user data.


## Installation

```
make studio-shell
cd /edx/src
git clone https://github.com/open-craft/learnupon-exporter.git
pip install -e /edx/src/learnupon-exporter
```

## Usage

```
./manage.py lms learnupon_export_users output_dir course_id [course_id2 course_id3...]
./manage.py lms learnupon_export_enrollment_data ouput_dir [course_id2 course_id3...]
```

In both cases an export file will be created in `output` named based on the current server time.

## SETTINGS

- `LEARNUPON_EXPORTER_STATIC_FILES_BUCKET = ''` # S3 Bucket to put files into. If empty no S3 upload is attempted.
`- LEARNUPON_EXPORTER_STATIC_FILES_PATH = 'learnupon_exports/'` # Folder/Prefix to use within the S3 bucket for the output file.
`- LEARNUPON_EXPORTER_AWS_ACCESS_KEY_ID = ''` # AWS Access Key
`- LEARNUPON_EXPORTER_AWS_ACCESS_KEY_SECRET = ''` # AWS Secret Key


