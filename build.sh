#!/bin/bash
pyinstaller --onefile --windowed \
    --add-data "assets:assets" \
    --add-data "config.json:." \
    --add-data "vendor:vendor" \
    pac-man.py
