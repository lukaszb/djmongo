#!/usr/bin/env python
import sys
from django.core.management import execute_manager

sys.path.insert(0, 'djmongo')

import testsettings as settings

def main():
    execute_manager(settings)

if __name__ == '__main__':
    main()

