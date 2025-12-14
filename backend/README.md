# Backend - Instagram Mini Clone

This is a FastAPI-based backend implementing a subset of Instagram features:
- Authentication (register/login) with JWT
- Follow/unfollow
- Posts (create/list/get)
- Likes
- Comments
- Feed

Run locally:

1. Create virtual environment and activate (PowerShell):
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install backend dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Run the server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```

Open API docs at http://127.0.0.1:8000/docs
