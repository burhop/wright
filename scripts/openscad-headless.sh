#!/bin/bash
# Headless wrapper for OpenSCAD using Xvfb
exec xvfb-run /usr/bin/openscad "$@"
