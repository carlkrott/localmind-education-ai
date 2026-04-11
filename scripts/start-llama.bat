@echo off
REM LocalMind — Start ik_llama.cpp server (ik_llama.cpp fork, better CPU perf)
REM Runs natively on Windows for maximum performance without Docker overhead

set LLAMA_BIN=C:\AI_Workspace\ik_llama.cpp\build_mingw\bin\llama-server.exe
set MODEL=C:\Users\Korph\localmind-education-ai\models\gemma-4-education.gguf

echo Starting ik_llama.cpp server with Gemma 4 model...
"%LLAMA_BIN%" ^
  -m "%MODEL%" ^
  --host 0.0.0.0 ^
  --port 8080 ^
  --ctx-size 32768 ^
  --threads 6 ^
  --threads-batch 6 ^
  --parallel 1 ^
  --n-predict 2048 ^
  --repeat-penalty 1.1 ^
  -ctk q4_0 ^
  -ctv q4_0 ^
  --chat-template gemma
