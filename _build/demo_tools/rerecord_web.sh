#!/usr/bin/env bash
# Re-record the NutriLabel and PPE web demos with the DevTools screencast (high quality).
D=/c/Users/KAREMDAIANEMARCOMINI/Desktop/portfolio-demos
cd $D/nutrilabel-ocr && (nohup ../.venv-ocr/Scripts/nutrilabel ui --engine rapidocr --port 9000 --no-browser > ../recordings/nutrilabel-ui.log 2>&1 &)
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:9000 && break; sleep 1; done
cd $D && .venv-tools/Scripts/python tools/record_nutrilabel_ui.py 2>&1 | tail -2
netstat -ano | grep "127.0.0.1:9000" | grep LISTEN | awk '{print $5}' | sort -u | while read pid; do taskkill //PID $pid //F >/dev/null; done
cd $D/ppe-compliance-vlm && (STREAMLIT_SERVER_HEADLESS=true STREAMLIT_SERVER_ADDRESS=127.0.0.1 STREAMLIT_BROWSER_GATHER_USAGE_STATS=false nohup ../.venv-video/Scripts/ppe-compliance --vlm-model HuggingFaceTB/SmolVLM-500M-Instruct > ../recordings/streamlit.log 2>&1 &)
for i in $(seq 1 40); do curl -s -o /dev/null http://127.0.0.1:8501 && break; sleep 2; done
cd $D && .venv-tools/Scripts/python tools/record_streamlit_ppe.py 2>&1 | tail -2
netstat -ano | grep "127.0.0.1:8501" | grep LISTEN | awk '{print $5}' | sort -u | while read pid; do taskkill //PID $pid //F >/dev/null; done
echo ALL_DONE
