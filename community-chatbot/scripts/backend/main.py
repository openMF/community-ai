import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import get_settings
from backend.api.routes import github_routes, jira_routes, slack_routes
from backend.services.jira_service import get_jira_service
from backend.services.github_service import get_github_agent
from backend.core.state import slack_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eager initialization during startup
    try:
        print("Initializing agents... (This may take a moment)")
        # Pre-warm caches by invoking factory for Singletons
        get_jira_service()
        get_github_agent()
        
        # Original slack initialized a default conversation memory list
        slack_store.get_session("1") 
        print("Agents initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to fully initialize some agents (Missing env vars?): {e}")
        # Server won't crash here so that other valid routes can still be tested
    yield

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Unified global CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with prefixes inside the unified API schema
app.include_router(github_routes.router, prefix=f"{settings.API_V1_STR}/github")
app.include_router(jira_routes.router, prefix=f"{settings.API_V1_STR}/jira")
app.include_router(slack_routes.router, prefix=f"{settings.API_V1_STR}/slack")

@app.get(f"{settings.API_V1_STR}/health")
async def root_health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
