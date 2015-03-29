#!/usr/bin/env python
#
# Copyright 1998-2015 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tinderbox.settings")
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
