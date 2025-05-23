"""Command Line Interface for the Zoho Projects Bot"""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich.markdown import Markdown
from loguru import logger
import sys
from pathlib import Path

from .agent import create_agent
from .config import settings

# Initialize Rich console
console = Console()
app = typer.Typer(help="Zoho Projects Agentic Bot - Chat with your projects!")


def setup_logging():
    """Configure logging"""
    logger.remove()  # Remove default logger
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )


def print_welcome():
    """Print welcome message"""
    welcome_text = """
# 🤖 Zoho Projects AI Assistant

Welcome! I'm your intelligent assistant for Zoho Projects. I can help you:

- **Manage Projects**: Search, create, and get details about your projects
- **Handle Tasks**: Create, update, search, and manage tasks within projects  
- **Organize Work**: Manage task lists and organize your workflow
- **Track Time**: Add and view time logs for your tasks
- **Get Information**: Retrieve detailed information about any project or task

Just type your requests in natural language, and I'll help you get things done!

**Example commands:**
- "Show me all my projects"
- "Create a new project called 'Website Redesign'"
- "Find tasks in the Marketing project"
- "Update task 12345 to 75% complete"
- "Log 3 hours of work on the Design task"

Type 'help' for more commands or 'quit' to exit.
    """
    
    console.print(Panel(
        Markdown(welcome_text),
        title="🚀 Zoho Projects Bot",
        border_style="blue"
    ))


def print_help():
    """Print help information"""
    help_text = """
## Available Commands:

**Chat Commands:**
- Just type naturally! Ask me anything about your projects and tasks
- Examples: "show my projects", "create a task", "update task status"

**System Commands:**
- `help` - Show this help message
- `tools` - List available tools and their descriptions
- `history` - Show conversation history
- `clear` - Clear conversation history
- `status` - Show connection status
- `quit` or `exit` - Exit the application

**Tips:**
- You can reference projects and tasks by name or ID
- Use natural language - I understand context from our conversation
- I'll ask for clarification if I need more information
- All dates should be in MM-DD-YYYY format
- Time should be in HH:MM format
    """
    
    console.print(Panel(
        Markdown(help_text),
        title="📖 Help",
        border_style="green"
    ))


def print_tools(agent):
    """Print available tools"""
    tools = agent.get_available_tools()
    
    table = Table(title="🛠️ Available Tools", show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    
    for tool in tools:
        table.add_row(tool["name"], tool["description"])
    
    console.print(table)


def print_history(agent):
    """Print conversation history"""
    history = agent.get_conversation_history()
    
    if not history:
        console.print("[yellow]No conversation history yet.[/yellow]")
        return
    
    console.print(Panel("[bold]Conversation History[/bold]", border_style="yellow"))
    
    for i, message in enumerate(history[-10:], 1):  # Show last 10 messages
        if message["type"] == "human":
            console.print(f"[bold blue]You ({i}):[/bold blue] {message['content']}")
        else:
            console.print(f"[bold green]Bot ({i}):[/bold green] {message['content']}")
        console.print()


def check_status(agent):
    """Check connection status"""
    try:
        # Test Zoho connection by trying to get projects
        projects = agent.zoho_client.get_all_projects()
        
        table = Table(title="🔌 Connection Status", show_header=True)
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")
        
        table.add_row("OpenAI", "✅ Connected", f"Model: {settings.openai_model}")
        table.add_row("Zoho Projects", "✅ Connected", f"Portal: {settings.zoho_portal_id}")
        table.add_row("Projects Found", "📊 Data", f"{len(projects)} projects")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]❌ Connection Error: {str(e)}[/red]")


@app.command()
def chat():
    """Start an interactive chat session with the Zoho Projects bot"""
    setup_logging()
    
    try:
        # Print welcome message
        print_welcome()
        
        # Initialize the agent
        with console.status("[bold green]Initializing AI agent..."):
            agent = create_agent()
        
        console.print("[green]✅ Agent initialized successfully![/green]\n")
        
        # Main chat loop
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
                
                # Handle system commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    break
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                elif user_input.lower() == 'tools':
                    print_tools(agent)
                    continue
                elif user_input.lower() == 'history':
                    print_history(agent)
                    continue
                elif user_input.lower() == 'clear':
                    agent.reset_conversation()
                    console.print("[green]✅ Conversation history cleared.[/green]")
                    continue
                elif user_input.lower() == 'status':
                    check_status(agent)
                    continue
                elif not user_input:
                    continue
                
                # Process the message with the agent
                with console.status("[bold green]🤖 Thinking..."):
                    response = agent.chat(user_input)
                
                # Display the response
                console.print(f"\n[bold green]🤖 Bot:[/bold green]")
                console.print(Panel(
                    Markdown(response),
                    border_style="green",
                    padding=(1, 2)
                ))
                
            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {str(e)}[/red]")
                logger.error(f"Chat error: {e}")
    
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize agent: {str(e)}[/red]")
        logger.error(f"Initialization error: {e}")
        raise typer.Exit(1)


@app.command()
def query(message: str = typer.Argument(..., help="The message to send to the bot")):
    """Send a single query to the bot and get a response"""
    setup_logging()
    
    try:
        # Initialize the agent
        with console.status("[bold green]Initializing AI agent..."):
            agent = create_agent()
        
        # Process the message
        with console.status("[bold green]🤖 Processing..."):
            response = agent.chat(message)
        
        # Display the response
        console.print(Panel(
            Markdown(response),
            title="🤖 Response",
            border_style="green"
        ))
        
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def test_connection():
    """Test the connection to Zoho Projects and OpenAI"""
    setup_logging()
    
    try:
        with console.status("[bold green]Testing connections..."):
            agent = create_agent()
        
        check_status(agent)
        
    except Exception as e:
        console.print(f"[red]❌ Connection test failed: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command() 
def version():
    """Show version information"""
    from . import __version__
    
    table = Table(title="📋 Version Information")
    table.add_column("Component", style="cyan")
    table.add_column("Version", style="green")
    
    table.add_row("Zoho Projects Bot", __version__)
    table.add_row("OpenAI Model", settings.openai_model)
    table.add_row("Portal ID", settings.zoho_portal_id)
    
    console.print(table)


def main():
    """Main entry point"""
    app()


if __name__ == "__main__":
    main()
