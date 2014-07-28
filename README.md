routeros-config-diff-report
===========================

Generates LaTeX PDF report about difference between current
and previously saved RouterOS configurations. The PDF file
is opened in PDF viewer.

Connection is made via Python 3 `paramiko` module (SSH).

PDF report backups are saved in `report_backups` directory.

Requirements
============

1. Python 3
2. `pip3 install paramiko`
3. LaTeX with `verbatim` package

Usage
=====

Run `python3 ./report.py`.

Customize the report text in `report.tex`.
