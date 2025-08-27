# Portfolio + LLM Chat (single service)

## Local
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# mac/linux:
# source .venv/bin/activate

pip install -r requirements.txt
# set OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"      # PowerShell: $env:OPENAI_API_KEY="<YOUR_OPENAI_API_KEY>"
bash start.sh                  # or: python -m uvicorn app.main:app --port 8000 --workers 1

Open http://localhost:8000
