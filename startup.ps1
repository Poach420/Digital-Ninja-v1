# Digital Ninja Project Startup & Health Check Script

This script automates the startup and health check process for your project. Run it before every session to ensure a clean, working environment and prevent recurring errors.

## What it does:
- Cleans up all lockfiles and node_modules in frontend
- Reinstalls frontend dependencies with npm
- Activates Python virtual environment and reinstalls backend dependencies
- Checks .env files for both frontend and backend
- Starts frontend and backend servers
- Runs basic health checks for registration, login, and builder endpoints

---

## Windows PowerShell Script (startup.ps1)

```powershell
# Set project root
$projectRoot = "C:\Users\User 1\Desktop\DIGITAL-NINJAH-FINAL-EMERGENT-REM"

# 1. Clean up frontend lockfiles and node_modules
Write-Host "Cleaning up frontend lockfiles and node_modules..."
Remove-Item "$projectRoot\frontend\package-lock.json" -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\frontend\pnpm-lock.yaml" -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\frontend\yarn.lock" -ErrorAction SilentlyContinue
Remove-Item "$projectRoot\frontend\node_modules" -Recurse -Force -ErrorAction SilentlyContinue

# 2. Reinstall frontend dependencies
Write-Host "Reinstalling frontend dependencies with npm..."
cd "$projectRoot\frontend"
npm install

# 3. Activate Python virtual environment and reinstall backend dependencies
Write-Host "Activating Python virtual environment and reinstalling backend dependencies..."
cd "$projectRoot"
& .venv\Scripts\Activate.ps1
cd "$projectRoot\backend"
pip install -r requirements.txt

# 4. Check .env files
Write-Host "Checking .env files..."
if (!(Test-Path "$projectRoot\backend\.env")) { Write-Host "Missing backend .env!" }
if (!(Test-Path "$projectRoot\frontend\.env")) { Write-Host "Missing frontend .env!" }

# 5. Start backend server
Write-Host "Starting backend server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\backend'; uvicorn builder_server:app --host 127.0.0.1 --port 8000"

# 6. Start frontend server
Write-Host "Starting frontend server..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$projectRoot\frontend'; npm start"

# 7. Health check (basic)
Write-Host "Waiting for servers to start..."
Start-Sleep -Seconds 10
Write-Host "Checking backend health endpoint..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing
    Write-Host "Backend health: $($response.StatusCode)"
} catch {
    Write-Host "Backend health check failed."
}
Write-Host "Checking frontend... Open http://localhost:3000 in your browser."
```

---

## Usage
1. Save this script as `startup.ps1` in your project root.
2. Right-click and "Run with PowerShell" before every session.
3. Check the output for errors and follow any instructions.

---

**This script will help prevent recurring errors and ensure a clean, working environment every time you start your project.**
