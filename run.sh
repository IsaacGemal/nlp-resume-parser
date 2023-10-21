#! /bin/bash

export RESUME_PARSER_HOST=127.0.0.1
export RESUME_PARSER_PORT=8080
export OPENAI_API_KEY=

cd application
echo Parser Running at $RESUME_PARSER_HOST:$RESUME_PARSER_PORT
python3 server.py
