from pymongo import MongoClient
from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configurations
DATABASE_URL = os.getenv("DATABASE_URL")  # MongoDB connection string
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Google API key
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY")  # GitHub Token
JWT_SECRET = os.getenv("JWT_SECRET")  # JWT secret
PORT = int(os.getenv("PORT", 8000))  # Default port is 8000

# Initialize services
app = FastAPI()

# Initialize MongoDB client
client = MongoClient(DATABASE_URL)
db = client['digital_ninja_app']  # Replace 'digital_ninja_app' with the correct database name

# MongoDB Test Endpoint
@app.get("/db-test")
async def test_mongo():
    try:
        collections = db.list_collection_names()
        return {"status": "success", "collections": collections}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Google API Key Integration
@app.get("/google-api-test")
async def test_google_api():
    try:
        import requests
        response = requests.get(
            f"https://www.googleapis.com/some-google-api-endpoint?key={GOOGLE_API_KEY}"
        )
        return {"status": "success", "response": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# GitHub API Key Integration
@app.get("/github-api-test")
async def test_github_api():
    try:
        import requests
        headers = {"Authorization": f"token {GITHUB_API_KEY}"}
        response = requests.get("https://api.github.com/user", headers=headers)
        return {"status": "success", "response": response.json()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Start FastAPI server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
