# -*- coding: utf-8 -*-
"""
learnupon_exporter Django application initialization.
"""

from __future__ import absolute_import, unicode_literals

from django.apps import AppConfig

from openedx.core.djangoapps.plugins.constants import PluginSettings, ProjectType, SettingsType


class LearnUponExporterAppConfig(AppConfig):
    """
    Configuration for the learnup_exporter Django plugin application.

    See: https://github.com/edx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """

    name = 'learnupon_exporter'
    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings'},
            },
            ProjectType.CMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings'},
            },
        },
    }

    def ready(self):
        """
        Load signal handlers when the app is ready.
        """
        pass
