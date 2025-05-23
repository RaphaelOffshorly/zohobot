"""Main Zoho Projects Agent using LangChain and GPT-4o Mini"""

from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from loguru import logger
import json
from datetime import datetime

from .config import settings
from .zoho_client import ZohoProjectsClient
from .tools import create_zoho_tools


class ZohoProjectsAgent:
    """Agentic bot for Zoho Projects interactions"""
    
    def __init__(self):
        """Initialize the agent with LLM, tools, and memory"""
        # Initialize Zoho client
        self.zoho_client = ZohoProjectsClient()
        
        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key,
            max_tokens=2700
        )
        
        # Create tools
        self.tools = create_zoho_tools(self.zoho_client)
        
        # Initialize memory for conversation context
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Keep last 10 exchanges
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create the agent
        self.agent_executor = self._create_agent()
        
        logger.info("Zoho Projects Agent initialized successfully")
    
    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools and prompt"""
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=settings.max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=True
        )
        
        return agent_executor
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """You are an intelligent assistant for Zoho Projects, a project management platform. You can help users manage their projects, tasks, task lists, and time tracking through natural conversation.

**Your Capabilities:**
- Search for and manage projects
- Create, update, and search for tasks
- Manage task lists and organize work
- Track time and manage time logs
- Provide detailed information about projects and tasks

**Available Tools:**
- search_projects: Find projects by name
- get_project_details: Get detailed project information
- create_project: Create new projects
- search_tasks: Find tasks within projects
- get_task_details: Get detailed task information
- create_task: Create new tasks
- update_task: Update existing tasks
- get_tasklists: View task lists in projects
- create_tasklist: Create new task lists
- get_time_logs: View time logs for tasks
- add_time_log: Add time entries to tasks

**Guidelines:**
1. **Be Conversational**: Respond naturally and helpfully
2. **Be Proactive**: Ask clarifying questions when needed
3. **Be Informative**: Provide clear, structured responses
4. **Be Efficient**: Use tools strategically to accomplish user goals
5. **Be Concise**: Keep responses under 2500 characters. Be direct and focused.
6. **Handle Errors Gracefully**: If something fails, explain what happened and suggest alternatives

**Data Formats:**
- Dates: MM-DD-YYYY format (e.g., "12-25-2024")
- Time: HH:MM format (e.g., "02:30" for 2 hours 30 minutes)
- Priorities: None, Low, Medium, High
- Bill Status: Billable, Non Billable

**Helpful Behaviors:**
- When users mention projects or tasks by name, search for them first
- Provide project/task IDs when showing results for future reference
- Summarize actions taken and their results
- Offer related actions that might be helpful
- Remember context from the conversation

**Example Interactions:**
- "Show me all tasks in the Marketing project" → Search for Marketing project, then get its tasks
- "Create a task called 'Review proposal' in the Sales project" → Search for Sales project, then create the task
- "Update task 12345 to 50% complete" → Update the task with the completion percentage
- "Log 2 hours of work on the Design task yesterday" → Find the task and add time log

Always be helpful, accurate, and provide actionable information. If you're unsure about something, ask for clarification rather than making assumptions."""

    def chat(self, message: str) -> str:
        """Process a user message and return the agent's response"""
        try:
            # Log the incoming message
            logger.info(f"User message: {message}")
            
            # Prepare the input - only pass what the prompt expects
            input_data = {"input": message}
            
            # Execute the agent
            result = self.agent_executor.invoke(input_data)
            
            # Extract the response
            response = result.get("output", "I apologize, but I couldn't process your request.")
            
            # Log the response
            logger.info(f"Agent response: {response}")
            
            return response
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(f"Error in chat: {e}")
            return error_msg
    
    def reset_conversation(self):
        """Reset the conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory reset")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        messages = self.memory.chat_memory.messages
        history = []
        
        for message in messages:
            if isinstance(message, HumanMessage):
                history.append({"type": "human", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"type": "ai", "content": message.content})
        
        return history
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get information about available tools"""
        tool_info = []
        for tool in self.tools:
            tool_info.append({
                "name": tool.name,
                "description": tool.description
            })
        return tool_info
    
    async def achat(self, message: str) -> str:
        """Async version of chat for web interfaces"""
        try:
            # For now, we'll use the sync version
            # In a production environment, you'd want to implement proper async support
            return self.chat(message)
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            logger.error(f"Error in async chat: {e}")
            return error_msg


def create_agent() -> ZohoProjectsAgent:
    """Factory function to create a configured agent"""
    return ZohoProjectsAgent()
