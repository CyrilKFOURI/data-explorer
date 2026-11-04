# Start the backend (FastAPI, auto-reload) and the frontend (Vite) for development.
# Backend: http://127.0.0.1:8000  ·  Frontend: http://127.0.0.1:5173 (proxies /api to the backend)

$root = Split-Path $PSScriptRoot -Parent

$backend = Start-Process -PassThru -NoNewWindow -WorkingDirectory "$root\backend" `
    -FilePath "uv" -ArgumentList "run", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"

try {
    Push-Location "$root\frontend"
    npm run dev
}
finally {
    Pop-Location
    # Kill the backend and its reload worker.
    taskkill /PID $backend.Id /T /F | Out-Null
}
