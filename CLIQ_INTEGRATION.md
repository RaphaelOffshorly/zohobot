# Zoho Cliq Integration Guide

This guide will walk you through integrating your Zoho Projects AI Assistant with Zoho Cliq, enabling your team to interact with the bot directly in their chat environment.

## Overview

The Zoho Cliq integration allows team members to:
- Query project information directly in Cliq channels
- Create and manage tasks through chat
- Log time entries conversationally
- Get project updates and notifications
- Use natural language commands

## Integration Methods

There are two ways to integrate with Zoho Cliq:

1. **Webhook Integration** (Recommended) - External service handles requests
2. **Bot Platform Integration** - Code runs within Cliq's environment

## Method 1: Webhook Integration (Recommended)

### Step 1: Deploy Your Bot Service

First, ensure your bot service is running and accessible:

```bash
# Run the web service
python -m src.web_app --host 0.0.0.0 --port 8000

# Or with custom settings
uvicorn src.web_app:app --host 0.0.0.0 --port 8000 --reload
```

Make sure the service is accessible from the internet. For development, you can use tools like ngrok:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 8000
```

Note the HTTPS URL provided by ngrok (e.g., `https://abc123.ngrok.io`).

### Step 2: Create Zoho Cliq Bot

1. **Access Cliq Administration**:
   - Go to your Zoho Cliq organization
   - Navigate to **Administration** → **Bots & Tools** → **Bots**

2. **Create New Bot**:
   - Click **"Create Bot"**
   - Fill in the details:
     - **Bot Name**: "Zoho Projects Assistant"
     - **Description**: "AI-powered assistant for Zoho Projects management"
     - **Bot Type**: "Conversational Bot"
     - **Icon**: Upload a relevant icon

3. **Configure Bot Settings**:
   - **Scope**: Organization-wide or specific channels
   - **Permissions**: Set appropriate permissions for your team

### Step 3: Configure Incoming Webhook

1. **Add Webhook Handler**:
   - In your bot settings, go to **"Incoming Webhook"**
   - Click **"Add Handler"**

2. **Webhook Configuration**:
   - **Handler Name**: "Projects Bot Handler"
   - **URL**: `https://your-domain.com/cliq/webhook`
   - **Method**: POST
   - **Authentication**: None (or configure as needed)

3. **Save Configuration**:
   - Save the webhook configuration
   - Note the webhook URL for testing

### Step 4: Test the Integration

1. **Add Bot to Channel**:
   - Go to a Cliq channel or create a test channel
   - Add your bot: Type `/bots` and select your bot

2. **Test Commands**:
   ```
   @projects show me all my projects
   @projects create a task called "Test task" in Marketing project
   @projects what are my overdue tasks?
   ```

## Method 2: Bot Platform Integration

If you prefer to run code within Cliq's environment:

### Step 1: Create Bot Platform Bot

1. **Go to Bot Platform**:
   - In Cliq Administration, go to **"Bot Platform"**
   - Click **"Create Bot"**

2. **Bot Configuration**:
   - **Bot Name**: "Zoho Projects Assistant"
   - **Description**: "AI assistant for project management"
   - **Bot Type**: "Conversational"

### Step 2: Add Handler Code

Copy this code to your bot's **Message Handler**:

```javascript
// Zoho Projects AI Assistant Bot Handler
response = Map();

// Get the message text and user info
messageText = message.get("text");
userInfo = message.get("user");
chatInfo = message.get("chat");

// Skip if no message or if it's from a bot
if(messageText == null || messageText.trim().isEmpty() || userInfo.get("is_bot")) {
    return Map();
}

// Check if bot is mentioned or it's a direct message
botMentioned = false;
mentions = message.get("mentions");
if(mentions != null) {
    for each mention in mentions {
        if(mention.get("type") == "bot") {
            botMentioned = true;
            break;
        }
    }
}

isDirect = chatInfo.get("type") == "direct";

// Only respond if mentioned or in direct message
if(!botMentioned && !isDirect) {
    return Map();
}

// Clean the message (remove bot mentions)
cleanText = messageText;
botPatterns = {"@zoho", "@projects", "@bot", "zoho projects", "projects bot"};
for each pattern in botPatterns {
    cleanText = cleanText.replaceAll(pattern, "").replaceAll(pattern.toTitleCase(), "");
}
cleanText = cleanText.trim();

// If no clean text, show help
if(cleanText.isEmpty()) {
    helpCard = Map();
    helpCard.put("title", "Zoho Projects AI Assistant");
    helpCard.put("theme", "modern-inline");
    
    section = Map();
    section.put("id", 1);
    
    element = Map();
    element.put("type", "text");
    element.put("text", "🤖 **Zoho Projects AI Assistant**\n\nI can help you manage your Zoho Projects! Here are some things you can ask me:\n\n**Projects:**\n• \"Show me all my projects\"\n• \"Create a new project called 'Website Redesign'\"\n• \"Get details for project 12345\"\n\n**Tasks:**\n• \"Find tasks in the Marketing project\"\n• \"Create a task called 'Review proposal' in Sales project\"\n• \"Update task 12345 to 75% complete\"\n\n**Time Tracking:**\n• \"Log 3 hours of work on task 12345\"\n• \"Show time logs for task 67890\"\n\nJust mention me (@projects) and ask your question naturally!");
    
    section.put("elements", {element});
    helpCard.put("sections", {section});
    
    response.put("card", helpCard);
    return response;
}

// Prepare payload for external service
payload = Map();
payload.put("text", cleanText);
payload.put("user", userInfo);
payload.put("chat", chatInfo);

// Make API call to your bot service
try {
    apiResponse = invokeurl [
        url: "YOUR_BOT_SERVICE_URL/cliq/webhook"
        type: POST
        parameters: payload.toString()
        headers: {"Content-Type": "application/json"}
    ];
    
    // Parse and return response
    if(apiResponse != null) {
        responseText = apiResponse.get("text");
        card = apiResponse.get("card");
        
        if(card != null) {
            response.put("card", card);
        } else if(responseText != null && !responseText.isEmpty()) {
            response.put("text", responseText);
        } else {
            response.put("text", "I received your message but couldn't generate a response.");
        }
    } else {
        response.put("text", "Sorry, I'm having trouble connecting to the Projects service right now.");
    }
} catch (e) {
    response.put("text", "Sorry, I encountered an error: " + e.toString());
}

return response;
```

### Step 3: Configure Welcome Handler (Optional)

Add this to your **Welcome Handler**:

```javascript
response = Map();
response.put("text", "👋 Hi! I'm your Zoho Projects AI Assistant. I can help you manage projects, tasks, and time tracking. Just ask me anything!");
return response;
```

### Step 4: Update Service URL

Replace `YOUR_BOT_SERVICE_URL` in the handler code with your actual service URL.

## Advanced Configuration

### Authentication

For production use, consider adding authentication:

1. **API Key Authentication**:
   ```javascript
   headers = {"Content-Type": "application/json", "X-API-Key": "your-api-key"};
   ```

2. **Bot Token Verification**:
   - Add token verification in your webhook endpoint
   - Validate requests are from your Cliq bot

### Message Formatting

The bot supports rich message formatting:

1. **Text Responses**: Simple text messages
2. **Card Responses**: Rich cards with sections and elements
3. **Quick Replies**: Predefined response options

### Error Handling

Implement robust error handling:

```javascript
try {
    // API call
} catch (e) {
    if(e.toString().contains("timeout")) {
        response.put("text", "The request timed out. Please try again.");
    } else if(e.toString().contains("401")) {
        response.put("text", "Authentication failed. Please contact admin.");
    } else {
        response.put("text", "An unexpected error occurred. Please try again later.");
    }
}
```

## Testing and Debugging

### Test Commands

Try these commands to test your integration:

```
# Basic queries
@projects help
@projects show me all projects
@projects what tasks are overdue?

# Project management
@projects create project "Test Project"
@projects find projects containing "website"

# Task management
@projects create task "Review documentation" in Marketing project
@projects update task 12345 to 50% complete
@projects show tasks in project 67890

# Time tracking
@projects log 2 hours on task 12345
@projects show my time logs for this week
```

### Debug Mode

Enable debug logging in your service:

```bash
export LOG_LEVEL=DEBUG
python -m src.web_app
```

Check logs for:
- Incoming webhook requests
- Message processing
- API responses
- Error details

### Common Issues

1. **Bot Not Responding**:
   - Check webhook URL is accessible
   - Verify bot is mentioned correctly
   - Check service logs for errors

2. **Authentication Errors**:
   - Verify Zoho API credentials
   - Check token expiration
   - Validate permissions

3. **Timeout Issues**:
   - Increase timeout settings
   - Optimize API calls
   - Check network connectivity

## Security Considerations

### Production Deployment

1. **Use HTTPS**: Always use HTTPS for webhook URLs
2. **Validate Requests**: Verify requests are from Zoho Cliq
3. **Rate Limiting**: Implement rate limiting to prevent abuse
4. **Input Validation**: Sanitize and validate all inputs
5. **Error Handling**: Don't expose sensitive information in errors

### Access Control

1. **Bot Permissions**: Configure appropriate bot permissions
2. **Channel Restrictions**: Limit bot to specific channels if needed
3. **User Validation**: Verify user permissions before executing actions
4. **Audit Logging**: Log all bot interactions for security

## Monitoring and Analytics

### Metrics to Track

1. **Usage Statistics**:
   - Messages processed
   - Commands executed
   - Users engaged

2. **Performance Metrics**:
   - Response times
   - Error rates
   - API call latency

3. **Business Metrics**:
   - Projects created
   - Tasks managed
   - Time logged

### Health Monitoring

Set up monitoring for:
- Service availability
- API endpoint health
- Database connections
- External service dependencies

## Customization

### Bot Personality

Customize the bot's responses:

1. **Greeting Messages**: Personalize welcome messages
2. **Help Content**: Tailor help information to your team
3. **Error Messages**: Use friendly, helpful error messages
4. **Success Confirmations**: Celebrate completed actions

### Team-Specific Features

1. **Custom Commands**: Add team-specific shortcuts
2. **Project Templates**: Pre-configured project setups
3. **Notification Preferences**: Customizable alert settings
4. **Integration Hooks**: Connect with other team tools

## Support and Maintenance

### Regular Maintenance

1. **Token Refresh**: Monitor and refresh API tokens
2. **Dependency Updates**: Keep libraries up to date
3. **Performance Optimization**: Monitor and optimize performance
4. **Security Patches**: Apply security updates promptly

### Getting Help

1. **Documentation**: Check API documentation for updates
2. **Community**: Join Zoho developer communities
3. **Support**: Contact Zoho support for API issues
4. **Logs**: Use detailed logging for troubleshooting

---

This completes the Zoho Cliq integration setup. Your team can now interact with the Zoho Projects AI Assistant directly within their Cliq channels, making project management more collaborative and efficient.
