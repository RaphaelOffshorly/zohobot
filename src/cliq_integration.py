"""Zoho Cliq Bot Integration for the Zoho Projects Agent"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
from loguru import logger
from datetime import datetime
from .tools import set_user_context

from .agent import ZohoProjectsAgent


class CliqMessage(BaseModel):
    """Cliq incoming message model"""
    text: str
    user: Dict[str, Any]
    chat: Dict[str, Any]
    timestamp: Optional[str] = None


class CliqResponse(BaseModel):
    """Cliq response model"""
    text: str
    card: Optional[Dict[str, Any]] = None
    bot: Optional[Dict[str, Any]] = None


class CliqIntegration:
    """Integration handler for Zoho Cliq"""
    
    def __init__(self, agent: ZohoProjectsAgent):
        self.agent = agent
        self.router = APIRouter(prefix="/cliq", tags=["cliq"])
        self.setup_routes()
    
    def setup_routes(self):
        """Setup FastAPI routes for Cliq integration"""
        
        @self.router.post("/webhook")
        async def handle_cliq_webhook(request: Request):
            """Handle incoming webhook from Zoho Cliq"""
            try:
                # Parse the incoming request
                body = await request.json()
                logger.info(f"Received Cliq webhook: {body}")
                
                # Extract message details
                message_text = body.get("text", "").strip()
                user_info = body.get("user", {})
                chat_info = body.get("chat", {})
                # Set user context for tools (ADD THIS)
                user_id = user_info.get("id")
                user_name = user_info.get("name", "")
                if user_id:
                    set_user_context(user_id, user_name)
                # Skip if no message text or if it's a bot message
                if not message_text or user_info.get("is_bot", False):
                    return {"text": ""}
                
                # Check if bot is mentioned, if it's a direct message, or if it's a bot conversation
                bot_mentioned = self._is_bot_mentioned(message_text, body)
                is_direct_message = chat_info.get("type") == "direct"
                is_bot_conversation = chat_info.get("type") == "bot"
                
                if not (bot_mentioned or is_direct_message or is_bot_conversation):
                    return {"text": ""}
                
                # Clean the message (remove bot mentions)
                clean_message = self._clean_message(message_text)
                
                if not clean_message:
                    return self._create_help_response()
                
                # Process with the agent
                try:
                    response = await self.agent.achat(clean_message)
                    return self._format_response(response, user_info.get("name", "User"))
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    return {
                        "text": f"Sorry, I encountered an error processing your request: {str(e)}"
                    }
                    
            except Exception as e:
                logger.error(f"Error handling Cliq webhook: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/status")
        async def cliq_status():
            """Get Cliq integration status"""
            return {
                "status": "active",
                "agent_ready": self.agent is not None,
                "integration": "zoho_cliq",
                "version": "1.0.0"
            }
    
    def _is_bot_mentioned(self, text: str, body: Dict[str, Any]) -> bool:
        """Check if the bot is mentioned in the message"""
        # Check for explicit mentions in the mentions array
        mentions = body.get("mentions", [])
        for mention in mentions:
            if mention.get("type") == "bot":
                return True
        
        # Check for common bot mention patterns
        bot_triggers = ["@zoho", "@projects", "@bot", "zoho projects", "projects bot"]
        text_lower = text.lower()
        
        return any(trigger in text_lower for trigger in bot_triggers)
    
    def _clean_message(self, text: str) -> str:
        """Clean the message by removing bot mentions and formatting"""
        # Remove common bot mention patterns
        bot_patterns = ["@zoho", "@projects", "@bot", "zoho projects", "projects bot"]
        
        clean_text = text
        for pattern in bot_patterns:
            clean_text = clean_text.replace(pattern, "").replace(pattern.title(), "")
        
        # Remove extra whitespace and clean up
        clean_text = " ".join(clean_text.split()).strip()
        
        return clean_text
    
    def _format_response(self, response: str, user_name: str) -> Dict[str, Any]:
        """Format the agent response for Cliq"""
        # Split long responses into manageable chunks
        max_length = 4000  # Cliq message limit
        
        if len(response) <= max_length:
            return {"text": response}
        
        # For long responses, create a card
        return {
            "text": f"Hi {user_name}! Here's the information you requested:",
            "card": {
                "title": "Zoho Projects Response",
                "theme": "modern-inline",
                "sections": [
                    {
                        "id": 1,
                        "elements": [
                            {
                                "type": "text",
                                "text": response[:max_length] + ("..." if len(response) > max_length else "")
                            }
                        ]
                    }
                ]
            }
        }
    
    def _create_help_response(self) -> Dict[str, Any]:
        """Create a help response for the user"""
        help_text = """
🤖 **Zoho Projects AI Assistant**

I can help you manage your Zoho Projects! Here are some things you can ask me:

**Projects:**
• "Show me all my projects"
• "Create a new project called 'Website Redesign'"
• "Get details for project 12345"

**Tasks:**
• "Find tasks in the Marketing project"
• "Create a task called 'Review proposal' in Sales project"
• "Update task 12345 to 75% complete"
• "Show me details for task 67890"

**Time Tracking:**
• "Log 3 hours of work on task 12345"
• "Show time logs for task 67890"

**Task Lists:**
• "Show task lists in project 12345"
• "Create a new task list called 'Phase 2'"

Just mention me (@projects) and ask your question naturally!
        """
        
        return {
            "card": {
                "title": "Zoho Projects AI Assistant",
                "theme": "modern-inline",
                "sections": [
                    {
                        "id": 1,
                        "elements": [
                            {
                                "type": "text",
                                "text": help_text.strip()
                            }
                        ]
                    }
                ]
            }
        }


def create_cliq_router(agent: ZohoProjectsAgent) -> APIRouter:
    """Create and return the Cliq integration router"""
    integration = CliqIntegration(agent)
    return integration.router


# Cliq Bot Handler Functions (for bot development platform)
def get_bot_handler_code() -> str:
    """Generate the bot handler code for Zoho Cliq Bot Platform"""
    return '''
// Zoho Projects AI Assistant Bot Handler
// This code should be added to your Zoho Cliq Bot in the Bot Platform

// Message Handler
response = Map();

// Get the message text
messageText = message.get("text");
userInfo = message.get("user");

// Check if message is empty
if(messageText == null || messageText.trim().isEmpty()) {
    response.put("text", "Hi! I'm your Zoho Projects AI Assistant. Ask me anything about your projects and tasks!");
    return response;
}

// Prepare the payload for our external service
payload = Map();
payload.put("message", messageText);

// Make API call to our bot service
try {
    apiResponse = invokeurl [
        url: "YOUR_BOT_SERVICE_URL/cliq/webhook"
        type: POST
        parameters: payload.toString()
        headers: Map {"Content-Type": "application/json"}
    ];
    
    // Parse response
    if(apiResponse != null) {
        responseText = apiResponse.get("text");
        card = apiResponse.get("card");
        
        if(card != null) {
            response.put("card", card);
        } else {
            response.put("text", responseText);
        }
    } else {
        response.put("text", "Sorry, I'm having trouble connecting to the Projects service right now.");
    }
} catch (e) {
    response.put("text", "Sorry, I encountered an error: " + e.toString());
}

return response;
'''


def get_bot_setup_instructions() -> str:
    """Get setup instructions for Zoho Cliq bot"""
    return '''
# Zoho Cliq Bot Setup Instructions

## Step 1: Create a Zoho Cliq Bot

1. Go to Zoho Cliq Administration
2. Navigate to Bots & Tools > Bots
3. Click "Create Bot"
4. Fill in bot details:
   - Bot Name: "Zoho Projects Assistant"
   - Description: "AI-powered assistant for Zoho Projects management"
   - Bot Type: "Conversational Bot"

## Step 2: Configure Bot Handlers

### Message Handler:
1. In the Bot Platform, go to "Message Handler"
2. Copy and paste the bot handler code (use the `get_bot_handler_code()` function)
3. Replace `YOUR_BOT_SERVICE_URL` with your actual bot service URL
4. Save the handler

### Welcome Handler (Optional):
```javascript
response = Map();
response.put("text", "👋 Hi! I'm your Zoho Projects AI Assistant. I can help you manage projects, tasks, and time tracking. Just ask me anything!");
return response;
```

## Step 3: Deploy Your Bot Service

1. Deploy your FastAPI application with Cliq integration
2. Make sure the `/cliq/webhook` endpoint is accessible
3. Update the bot handler code with your service URL

## Step 4: Test the Integration

1. Add the bot to a Cliq channel or chat
2. Send a message mentioning the bot
3. The bot should respond with helpful information

## Bot Commands

Users can interact with the bot using natural language:
- "Show me all projects"
- "Create a task in Marketing project"
- "Update task 12345 to 50% complete"
- "Log 2 hours on task 67890"

## Webhook Alternative

If you prefer webhook integration:

1. Use the FastAPI webhook endpoint: `/cliq/webhook`
2. Configure it as an incoming webhook in your Cliq bot
3. The bot will automatically handle incoming messages

## Security Considerations

- Ensure your bot service URL is secure (HTTPS)
- Consider adding authentication if needed
- Monitor bot usage and logs
'''
