# Zoho Projects AI Assistant Bot

An intelligent, agentic chatbot for Zoho Projects that uses GPT-4o Mini and LangChain to help teams manage their projects, tasks, and time tracking through natural conversation.

## Features

🤖 **Intelligent Agent**: Uses GPT-4o Mini with LangChain for natural conversation
📋 **Project Management**: Create, search, and manage projects
✅ **Task Management**: Handle tasks, task lists, and updates
⏰ **Time Tracking**: Log and manage time entries
💬 **Chat Interface**: CLI and web interfaces available
🔗 **Zoho Cliq Integration**: Works seamlessly in Zoho Cliq

## Quick Start

### 1. Prerequisites

- Python 3.8+
- OpenAI API key
- Zoho Projects account with API access
- Zoho OAuth credentials

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd zohobot

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 3. Configuration

Edit `.env` with your credentials:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Zoho Projects Configuration
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_REFRESH_TOKEN=your_zoho_refresh_token
ZOHO_PORTAL_ID=your_portal_id
```

### 4. Run the Bot

**CLI Interface:**
```bash
python main.py chat
```

**Web Interface:**
```bash
python -m src.web_app
# Open http://localhost:8000
```

**Single Query:**
```bash
python main.py query "Show me all my projects"
```

## Zoho Cliq Integration

The bot can be integrated with Zoho Cliq for team collaboration. See [CLIQ_INTEGRATION.md](CLIQ_INTEGRATION.md) for detailed setup instructions.

### Quick Cliq Setup

1. **Deploy the Bot Service**:
   ```bash
   python -m src.web_app --host 0.0.0.0 --port 8000
   ```

2. **Create Zoho Cliq Bot**:
   - Go to Zoho Cliq Administration
   - Create a new Conversational Bot
   - Configure webhook URL: `https://your-domain.com/cliq/webhook`

3. **Test Integration**:
   - Add bot to a Cliq channel
   - Mention the bot: "@projects show me all tasks"

## Available Commands

The bot understands natural language. Here are some examples:

### Projects
- "Show me all my projects"
- "Create a new project called 'Website Redesign'"
- "Get details for project 12345"
- "Find projects containing 'marketing'"

### Tasks
- "Show tasks in the Marketing project"
- "Create a task 'Review proposal' in Sales project"
- "Update task 12345 to 75% complete"
- "Set task priority to High"

### Time Tracking
- "Log 3 hours of work on task 12345"
- "Show time logs for task 67890"
- "Add billable time entry for yesterday"

### Task Lists
- "Show task lists in project 12345"
- "Create a new task list called 'Phase 2'"

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  LangChain      │───▶│  Zoho Projects  │
│   (CLI/Web/     │    │  Agent          │    │  API            │
│    Cliq)        │    │  (GPT-4o Mini)  │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                       ┌─────────────────┐
                       │  Tool Functions │
                       │  - Projects     │
                       │  - Tasks        │
                       │  - Time Logs    │
                       │  - Task Lists   │
                       └─────────────────┘
```

## Development

### Project Structure

```
zohobot/
├── src/
│   ├── agent.py           # Main LangChain agent
│   ├── tools.py           # Zoho API tools
│   ├── zoho_client.py     # Zoho API client
│   ├── cliq_integration.py # Cliq bot integration
│   ├── web_app.py         # FastAPI web interface
│   ├── cli.py             # Command line interface
│   └── config.py          # Configuration management
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── README.md             # This file
```

### Available Commands

```bash
# Start interactive chat
python main.py chat

# Send single query
python main.py query "your question here"

# Test connections
python main.py test-connection

# Show version info
python main.py version

# Run web server
python -m src.web_app
```

### Testing

```bash
# Run tests
pytest

# Test connection to Zoho
python main.py test-connection

# Test specific functionality
python main.py query "show me all projects"
```

## API Documentation

When running the web interface, visit:
- Main interface: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### Key Endpoints

- `POST /chat` - Send messages to the bot
- `GET /history` - Get conversation history
- `POST /clear` - Clear conversation history
- `GET /tools` - List available tools
- `GET /status` - Get system status
- `POST /cliq/webhook` - Zoho Cliq webhook (for integration)

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `ZOHO_CLIENT_ID` | Zoho OAuth client ID | Yes |
| `ZOHO_CLIENT_SECRET` | Zoho OAuth client secret | Yes |
| `ZOHO_REFRESH_TOKEN` | Zoho OAuth refresh token | Yes |
| `ZOHO_PORTAL_ID` | Your Zoho Projects portal ID | Yes |
| `OPENAI_MODEL` | OpenAI model (default: gpt-4o-mini) | No |
| `LOG_LEVEL` | Logging level (default: INFO) | No |
| `MAX_ITERATIONS` | Agent max iterations (default: 10) | No |

## Getting Zoho Credentials

1. **Create Zoho OAuth App**:
   - Go to [Zoho API Console](https://api-console.zoho.com/)
   - Create a new application
   - Set redirect URI to `http://localhost:8080`

2. **Get Authorization Code**:
   ```
   https://accounts.zoho.com/oauth/v2/auth?scope=ZohoProjects.projects.ALL,ZohoProjects.tasks.ALL,ZohoProjects.tasklists.ALL,ZohoProjects.timesheets.ALL&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=http://localhost:8080
   ```

3. **Exchange for Refresh Token**:
   ```bash
   curl -X POST https://accounts.zoho.com/oauth/v2/token \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "code=AUTHORIZATION_CODE" \
     -d "grant_type=authorization_code" \
     -d "redirect_uri=http://localhost:8080"
   ```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "src.web_app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Deployment

For production deployment:

1. Set environment variables securely
2. Use HTTPS for webhook endpoints
3. Configure proper logging
4. Set up monitoring and health checks
5. Use a process manager like PM2 or systemd

## Troubleshooting

### Common Issues

1. **Token Refresh Errors**:
   - Check your Zoho OAuth credentials
   - Ensure refresh token is valid
   - Verify portal ID is correct

2. **OpenAI API Errors**:
   - Check API key validity
   - Verify sufficient credits
   - Check rate limits

3. **Connection Issues**:
   - Run `python main.py test-connection`
   - Check network connectivity
   - Verify API endpoints

### Debugging

Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py chat
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the API documentation
- Open an issue on GitHub

## Changelog

### v1.0.0
- Initial release
- CLI and web interfaces
- Full Zoho Projects API integration
- Zoho Cliq bot integration
- GPT-4o Mini with LangChain
