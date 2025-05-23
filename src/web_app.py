"""Simple web interface for the Zoho Projects Bot using FastAPI"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
from pathlib import Path
from loguru import logger

from .agent import create_agent
from .config import settings
from .cliq_integration import create_cliq_router

# Initialize FastAPI app
app = FastAPI(
    title="Zoho Projects AI Bot",
    description="Agentic chatbot for Zoho Projects management",
    version="1.0.0"
)

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Global agent instance
agent = None


class ChatMessage(BaseModel):
    """Request model for chat messages"""
    message: str


class ChatResponse(BaseModel):
    """Response model for chat messages"""
    response: str
    success: bool
    error: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    try:
        logger.info("Initializing Zoho Projects Agent...")
        agent = create_agent()
        
        # Add Cliq integration router
        cliq_router = create_cliq_router(agent)
        app.include_router(cliq_router)
        
        logger.info("Agent and Cliq integration initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        raise


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat_message: ChatMessage):
    """Process a chat message and return response"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        response = await agent.achat(chat_message.message)
        return ChatResponse(response=response, success=True)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            response="An error occurred while processing your request.",
            success=False,
            error=str(e)
        )


@app.get("/history")
async def get_history():
    """Get conversation history"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        history = agent.get_conversation_history()
        return {"history": history, "success": True}
    except Exception as e:
        logger.error(f"History error: {e}")
        return {"success": False, "error": str(e)}


@app.post("/clear")
async def clear_history():
    """Clear conversation history"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        agent.reset_conversation()
        return {"success": True, "message": "History cleared"}
    except Exception as e:
        logger.error(f"Clear error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/tools")
async def get_tools():
    """Get available tools"""
    global agent
    
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        tools = agent.get_available_tools()
        return {"tools": tools, "success": True}
    except Exception as e:
        logger.error(f"Tools error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/status")
async def get_status():
    """Get system status"""
    global agent
    
    if not agent:
        return {"success": False, "error": "Agent not initialized"}
    
    try:
        # Test Zoho connection
        projects = agent.zoho_client.get_all_projects()
        
        return {
            "success": True,
            "status": {
                "openai_model": settings.openai_model,
                "zoho_portal": settings.zoho_portal_id,
                "projects_count": len(projects),
                "agent_initialized": True,
                "cliq_integration": True
            }
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "agent_ready": agent is not None}


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the web server"""
    uvicorn.run(
        "src.web_app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)
