@echo off

set RESUME_PARSER_HOST=127.0.0.1
set RESUME_PARSER_PORT=8080
set OPENAI_API_KEY=

cd application
echo Parser Running at %RESUME_PARSER_HOST%:%RESUME_PARSER_PORT%
python server.py
