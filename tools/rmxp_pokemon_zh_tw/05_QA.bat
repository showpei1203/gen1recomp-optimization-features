@echo off
if not exist build mkdir build
python toolchain\rmxp_zh_tw.py qa work\translation_manifest.tsv --report build\qa_report.tsv
echo Exit code %ERRORLEVEL%
pause
