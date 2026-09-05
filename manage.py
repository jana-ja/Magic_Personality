#!/usr/bin/env python
"""Django-Kommandozeile. Lokale Entwicklung nutzt config.settings.dev."""

import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django konnte nicht importiert werden. Ist die virtuelle "
            "Umgebung aktiviert und sind die Abhängigkeiten installiert "
            "(pip install -r requirements/dev.txt)?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
