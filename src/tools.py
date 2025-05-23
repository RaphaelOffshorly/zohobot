"""LangChain tools for Zoho Projects API interactions"""

from typing import Any, Dict, List, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import json
import threading
from datetime import datetime
from loguru import logger

from .zoho_client import ZohoProjectsClient, ZohoAPIError

_context = threading.local()


def set_user_context(user_id: str, user_name: str = ""):
    """Set the current user context for tools"""
    _context.user_id = user_id
    _context.user_name = user_name


def get_user_context() -> Dict[str, str]:
    """Get the current user context"""
    return {
        'user_id': getattr(_context, 'user_id', None),
        'user_name': getattr(_context, 'user_name', '')
    }


# Input schemas for tools
class ProjectSearchInput(BaseModel):
    """Input for project search tool"""
    query: str = Field(description="Search query for project name")
    limit: Optional[int] = Field(default=None, description="Maximum number of results to return (default: no limit)")


class ListAllProjectsInput(BaseModel):
    """Input for listing all projects"""
    status: Optional[str] = Field(default="active", description="Project status: active, archived, or all")
    limit: Optional[int] = Field(default=None, description="Maximum number of results to return (default: no limit)")


class ProjectDetailsInput(BaseModel):
    """Input for getting project details"""
    project_id: str = Field(description="ID of the project to get details for")


class CreateProjectInput(BaseModel):
    """Input for creating a new project"""
    name: str = Field(description="Name of the project")
    description: Optional[str] = Field(default="", description="Description of the project")
    start_date: Optional[str] = Field(default=None, description="Start date in MM-DD-YYYY format")
    end_date: Optional[str] = Field(default=None, description="End date in MM-DD-YYYY format")


class TaskSearchInput(BaseModel):
    """Input for task search tool"""
    project_id: str = Field(description="ID of the project to search tasks in")
    query: str = Field(description="Search query for task name")
    limit: Optional[int] = Field(default=None, description="Maximum number of results to return (default: no limit)")


class TaskDetailsInput(BaseModel):
    """Input for getting task details"""
    project_id: str = Field(description="ID of the project")
    task_id: str = Field(description="ID of the task to get details for")


class CreateTaskInput(BaseModel):
    """Input for creating a new task"""
    project_id: str = Field(description="ID of the project to create task in")
    name: str = Field(description="Name of the task")
    description: Optional[str] = Field(default="", description="Description of the task")
    start_date: Optional[str] = Field(default=None, description="Start date in MM-DD-YYYY format")
    end_date: Optional[str] = Field(default=None, description="End date in MM-DD-YYYY format")
    priority: Optional[str] = Field(default="None", description="Priority: None, Low, Medium, or High")
    tasklist_id: Optional[str] = Field(default=None, description="ID of the tasklist to add the task to")


class UpdateTaskInput(BaseModel):
    """Input for updating a task"""
    project_id: str = Field(description="ID of the project")
    task_id: str = Field(description="ID of the task to update")
    name: Optional[str] = Field(default=None, description="New name for the task")
    description: Optional[str] = Field(default=None, description="New description for the task")
    percent_complete: Optional[int] = Field(default=None, description="Completion percentage (0-100)")
    priority: Optional[str] = Field(default=None, description="Priority: None, Low, Medium, or High")


class TaskListInput(BaseModel):
    """Input for tasklist operations"""
    project_id: str = Field(description="ID of the project")


class CreateTaskListInput(BaseModel):
    """Input for creating a new tasklist"""
    project_id: str = Field(description="ID of the project to create tasklist in")
    name: str = Field(description="Name of the tasklist")
    flag: Optional[str] = Field(default="internal", description="Flag: internal or external")


class TimeLogInput(BaseModel):
    """Input for time log operations"""
    project_id: str = Field(description="ID of the project")
    task_id: str = Field(description="ID of the task")
    limit: Optional[int] = Field(default=None, description="Maximum number of results to return (default: no limit)")


class AllTimeLogsInput(BaseModel):
    """Input for getting all time logs across projects"""
    limit: Optional[int] = Field(default=None, description="Maximum number of results to return (default: no limit)")
    start_date: Optional[str] = Field(default=None, description="Start date filter in MM-DD-YYYY format")
    end_date: Optional[str] = Field(default=None, description="End date filter in MM-DD-YYYY format")


class AddTimeLogInput(BaseModel):
    """Input for adding time log"""
    project_id: str = Field(description="ID of the project")
    task_id: str = Field(description="ID of the task")
    date: str = Field(description="Date in MM-DD-YYYY format")
    hours: str = Field(description="Time in HH:MM format")
    bill_status: str = Field(description="Billable or Non Billable")
    notes: Optional[str] = Field(default="", description="Notes for the time log")


# Tool implementations
class ListAllProjectsTool(BaseTool):
    """Tool to list all projects"""
    name: str = "list_all_projects"
    description: str = "List all projects in the portal. No search query required - returns all projects."
    args_schema: Type[BaseModel] = ListAllProjectsInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, status: str = "active", limit: Optional[int] = None) -> str:
        try:
            projects = self.zoho_client.get_all_projects(status)
            if not projects:
                return f"No {status} projects found"
            
            # Apply limit if specified
            if limit:
                projects = projects[:limit]
            
            result = f"Found {len(projects)} {status} projects:\n\n"
            for project in projects:
                result += f"• **{project.get('name', 'Unknown')}** (ID: {project.get('id', 'N/A')})\n"
                result += f"  Status: {project.get('status', 'Unknown')}\n"
                if project.get('description'):
                    result += f"  Description: {project['description'][:100]}...\n"
                result += "\n"
            
            if len(projects) == limit and limit:
                result += f"(Showing first {limit} results)\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error listing projects: {e}")
            return f"Error listing projects: {str(e)}"


class ProjectSearchTool(BaseTool):
    """Tool to search for projects"""
    name: str = "search_projects"
    description: str = "Search for projects by name. Returns a list of matching projects with their details."
    args_schema: Type[BaseModel] = ProjectSearchInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, query: str, limit: Optional[int] = None) -> str:
        try:
            projects = self.zoho_client.search_projects(query)
            if not projects:
                return f"No projects found matching '{query}'"
            
            # Apply limit if specified
            if limit:
                projects = projects[:limit]
            
            result = f"Found {len(projects)} projects matching '{query}':\n\n"
            for project in projects:
                result += f"• **{project.get('name', 'Unknown')}** (ID: {project.get('id', 'N/A')})\n"
                result += f"  Status: {project.get('status', 'Unknown')}\n"
                if project.get('description'):
                    result += f"  Description: {project['description'][:100]}...\n"
                result += "\n"
            
            if len(projects) == limit and limit:
                result += f"(Showing first {limit} results)\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error searching projects: {e}")
            return f"Error searching projects: {str(e)}"


class ProjectDetailsTool(BaseTool):
    """Tool to get project details"""
    name: str = "get_project_details"
    description: str = "Get detailed information about a specific project by its ID."
    args_schema: Type[BaseModel] = ProjectDetailsInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str) -> str:
        try:
            project = self.zoho_client.get_project_details(project_id)
            if not project:
                return f"No project found with ID: {project_id}"
            
            result = f"**Project Details:**\n\n"
            result += f"**Name:** {project.get('name', 'Unknown')}\n"
            result += f"**ID:** {project.get('id', 'N/A')}\n"
            result += f"**Status:** {project.get('status', 'Unknown')}\n"
            
            if project.get('description'):
                result += f"**Description:** {project['description']}\n"
            
            if project.get('start_date'):
                result += f"**Start Date:** {project['start_date']}\n"
            
            if project.get('end_date'):
                result += f"**End Date:** {project['end_date']}\n"
            
            # Task counts
            task_count = project.get('task_count', {})
            if task_count:
                result += f"**Tasks:** {task_count.get('open', 0)} open, {task_count.get('closed', 0)} closed\n"
            
            # Milestone counts
            milestone_count = project.get('milestone_count', {})
            if milestone_count:
                result += f"**Milestones:** {milestone_count.get('open', 0)} open, {milestone_count.get('closed', 0)} closed\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error getting project details: {e}")
            return f"Error getting project details: {str(e)}"


class CreateProjectTool(BaseTool):
    """Tool to create a new project"""
    name: str = "create_project"
    description: str = "Create a new project with specified details."
    args_schema: Type[BaseModel] = CreateProjectInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, name: str, description: str = "", start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        try:
            project_data = {"name": name}
            
            if description:
                project_data["description"] = description
            if start_date:
                project_data["start_date"] = start_date
            if end_date:
                project_data["end_date"] = end_date
            
            project = self.zoho_client.create_project(project_data)
            
            if project:
                result = f"✅ **Project created successfully!**\n\n"
                result += f"**Name:** {project.get('name', 'Unknown')}\n"
                result += f"**ID:** {project.get('id', 'N/A')}\n"
                result += f"**Status:** {project.get('status', 'Unknown')}\n"
                return result
            else:
                return "❌ Failed to create project. No data returned."
                
        except ZohoAPIError as e:
            logger.error(f"Error creating project: {e}")
            return f"❌ Error creating project: {str(e)}"


class TaskSearchTool(BaseTool):
    """Tool to search for tasks in a project"""
    name: str = "search_tasks"
    description: str = "Search for tasks by name within a specific project."
    args_schema: Type[BaseModel] = TaskSearchInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, query: str, limit: Optional[int] = None) -> str:
        try:
            tasks = self.zoho_client.search_tasks(project_id, query)
            if not tasks:
                return f"No tasks found matching '{query}' in project {project_id}"
            
            # Apply limit if specified
            if limit:
                tasks = tasks[:limit]
            
            result = f"Found {len(tasks)} tasks matching '{query}':\n\n"
            for task in tasks:
                result += f"• **{task.get('name', 'Unknown')}** (ID: {task.get('id', 'N/A')})\n"
                result += f"  Status: {task.get('status', {}).get('name', 'Unknown')}\n"
                result += f"  Priority: {task.get('priority', 'None')}\n"
                result += f"  Completion: {task.get('percent_complete', '0')}%\n"
                result += "\n"
            
            if len(tasks) == limit and limit:
                result += f"(Showing first {limit} results)\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error searching tasks: {e}")
            return f"Error searching tasks: {str(e)}"


class TaskDetailsTool(BaseTool):
    """Tool to get task details"""
    name: str = "get_task_details"
    description: str = "Get detailed information about a specific task."
    args_schema: Type[BaseModel] = TaskDetailsInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, task_id: str) -> str:
        try:
            task = self.zoho_client.get_task_details(project_id, task_id)
            if not task:
                return f"No task found with ID: {task_id}"
            
            result = f"**Task Details:**\n\n"
            result += f"**Name:** {task.get('name', 'Unknown')}\n"
            result += f"**ID:** {task.get('id', 'N/A')}\n"
            result += f"**Status:** {task.get('status', {}).get('name', 'Unknown')}\n"
            result += f"**Priority:** {task.get('priority', 'None')}\n"
            result += f"**Completion:** {task.get('percent_complete', '0')}%\n"
            
            if task.get('description'):
                result += f"**Description:** {task['description']}\n"
            
            if task.get('start_date'):
                result += f"**Start Date:** {task['start_date']}\n"
            
            if task.get('end_date'):
                result += f"**End Date:** {task['end_date']}\n"
            
            # Owners
            owners = task.get('details', {}).get('owners', [])
            if owners:
                owner_names = [owner.get('name', 'Unknown') for owner in owners]
                result += f"**Owners:** {', '.join(owner_names)}\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error getting task details: {e}")
            return f"Error getting task details: {str(e)}"


class CreateTaskTool(BaseTool):
    """Tool to create a new task"""
    name: str = "create_task"
    description: str = "Create a new task in a project with specified details."
    args_schema: Type[BaseModel] = CreateTaskInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, name: str, description: str = "", start_date: Optional[str] = None, 
             end_date: Optional[str] = None, priority: str = "None", tasklist_id: Optional[str] = None) -> str:
        try:
            task_data = {"name": name}
            
            if description:
                task_data["description"] = description
            if start_date:
                task_data["start_date"] = start_date
            if end_date:
                task_data["end_date"] = end_date
            if priority and priority != "None":
                task_data["priority"] = priority
            if tasklist_id:
                task_data["tasklist_id"] = tasklist_id
            
            task = self.zoho_client.create_task(project_id, task_data)
            
            if task:
                result = f"✅ **Task created successfully!**\n\n"
                result += f"**Name:** {task.get('name', 'Unknown')}\n"
                result += f"**ID:** {task.get('id', 'N/A')}\n"
                result += f"**Status:** {task.get('status', {}).get('name', 'Unknown')}\n"
                result += f"**Priority:** {task.get('priority', 'None')}\n"
                return result
            else:
                return "❌ Failed to create task. No data returned."
                
        except ZohoAPIError as e:
            logger.error(f"Error creating task: {e}")
            return f"❌ Error creating task: {str(e)}"


class UpdateTaskTool(BaseTool):
    """Tool to update an existing task"""
    name: str = "update_task"
    description: str = "Update an existing task with new information."
    args_schema: Type[BaseModel] = UpdateTaskInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, task_id: str, name: Optional[str] = None, 
             description: Optional[str] = None, percent_complete: Optional[int] = None, 
             priority: Optional[str] = None) -> str:
        try:
            task_data = {}
            
            if name:
                task_data["name"] = name
            if description:
                task_data["description"] = description
            if percent_complete is not None:
                task_data["percent_complete"] = percent_complete
            if priority:
                task_data["priority"] = priority
            
            if not task_data:
                return "❌ No update data provided."
            
            task = self.zoho_client.update_task(project_id, task_id, task_data)
            
            if task:
                result = f"✅ **Task updated successfully!**\n\n"
                result += f"**Name:** {task.get('name', 'Unknown')}\n"
                result += f"**ID:** {task.get('id', 'N/A')}\n"
                result += f"**Status:** {task.get('status', {}).get('name', 'Unknown')}\n"
                result += f"**Priority:** {task.get('priority', 'None')}\n"
                result += f"**Completion:** {task.get('percent_complete', '0')}%\n"
                return result
            else:
                return "❌ Failed to update task. No data returned."
                
        except ZohoAPIError as e:
            logger.error(f"Error updating task: {e}")
            return f"❌ Error updating task: {str(e)}"


class GetTaskListsTool(BaseTool):
    """Tool to get all task lists in a project"""
    name: str = "get_tasklists"
    description: str = "Get all task lists in a specific project."
    args_schema: Type[BaseModel] = TaskListInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str) -> str:
        try:
            tasklists = self.zoho_client.get_all_tasklists(project_id)
            if not tasklists:
                return f"No task lists found in project {project_id}"
            
            result = f"Found {len(tasklists)} task lists:\n\n"
            for tasklist in tasklists:
                result += f"• **{tasklist.get('name', 'Unknown')}** (ID: {tasklist.get('id', 'N/A')})\n"
                result += f"  Status: {'Completed' if tasklist.get('completed') else 'Active'}\n"
                result += f"  View Type: {tasklist.get('view_type', 'Unknown')}\n"
                result += "\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error getting task lists: {e}")
            return f"Error getting task lists: {str(e)}"


class CreateTaskListTool(BaseTool):
    """Tool to create a new task list"""
    name: str = "create_tasklist"
    description: str = "Create a new task list in a project."
    args_schema: Type[BaseModel] = CreateTaskListInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, name: str, flag: str = "internal") -> str:
        try:
            tasklist_data = {
                "name": name,
                "flag": flag
            }
            
            tasklist = self.zoho_client.create_tasklist(project_id, tasklist_data)
            
            if tasklist:
                result = f"✅ **Task list created successfully!**\n\n"
                result += f"**Name:** {tasklist.get('name', 'Unknown')}\n"
                result += f"**ID:** {tasklist.get('id', 'N/A')}\n"
                result += f"**View Type:** {tasklist.get('view_type', 'Unknown')}\n"
                return result
            else:
                return "❌ Failed to create task list. No data returned."
                
        except ZohoAPIError as e:
            logger.error(f"Error creating task list: {e}")
            return f"❌ Error creating task list: {str(e)}"


class GetTimeLogsTool(BaseTool):
    """Tool to get time logs for a task"""
    name: str = "get_time_logs"
    description: str = "Get time logs for a specific task."
    args_schema: Type[BaseModel] = TimeLogInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, task_id: str, limit: Optional[int] = None) -> str:
        try:
            time_logs = self.zoho_client.get_task_time_logs(project_id, task_id)
            tasklogs = time_logs.get('tasklogs', [])
            
            if not tasklogs:
                return f"No time logs found for task {task_id}"
            
            # Apply limit if specified
            if limit:
                tasklogs = tasklogs[:limit]
            
            result = f"Found {len(tasklogs)} time logs:\n\n"
            total_hours = time_logs.get('total_log_hours', '0:00')
            result += f"**Total Time:** {total_hours}\n\n"
            
            for log in tasklogs:
                result += f"• **{log.get('hours_display', '0:00')}** on {log.get('log_date', 'Unknown')}\n"
                result += f"  Owner: {log.get('owner_name', 'Unknown')}\n"
                result += f"  Status: {log.get('bill_status', 'Unknown')}\n"
                if log.get('notes'):
                    result += f"  Notes: {log['notes'][:50]}...\n"
                result += "\n"
            
            if len(tasklogs) == limit and limit:
                result += f"(Showing first {limit} results)\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error getting time logs: {e}")
            return f"Error getting time logs: {str(e)}"


class GetAllTimeLogsTool(BaseTool):
    """Tool to get ALL time logs across all projects"""
    name: str = "get_all_time_logs"
    description: str = "Get ALL time logs across all projects, regardless of project. This allows you to retrieve all your time tracking data."
    args_schema: Type[BaseModel] = AllTimeLogsInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, limit: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
        try:
            # Get current user context
            user_context = get_user_context()
            current_user_id = user_context.get('user_id')
            
            # Use the "Get My Time Logs" API endpoint which gets logs across all projects
            # Build filters based on date range
            filters = {
                'bill_status': 'All',  # Get both billable and non-billable
                'component_type': 'task',  # Focus on task logs
                'users_list': current_user_id if current_user_id else 'all'  # Use current user or all if no context
            }
            
            # Handle date filtering
            if start_date and end_date:
                # Use custom_date for date range
                filters['view_type'] = 'custom_date'
                filters['custom_date'] = {
                    "start_date": start_date,
                    "end_date": end_date
                }
            elif start_date:
                # Use single date
                filters['view_type'] = 'day'
                filters['date'] = start_date
            else:
                # Default to current week
                filters['view_type'] = 'week'
                from datetime import datetime
                today = datetime.now()
                filters['date'] = today.strftime('%m-%d-%Y')
            
            # Apply limit to range if specified
            if limit:
                filters['range'] = limit
            
            # Get time logs using the cross-project endpoint
            time_logs = self.zoho_client.get_my_time_logs(**filters)
            
            if not time_logs or 'date' not in time_logs:
                date_filter = ""
                if start_date or end_date:
                    date_filter = f" (filtered by date: {start_date or 'any'} to {end_date or 'any'})"
                return f"No time logs found{date_filter}"
            
            # Extract all logs from all date entries
            all_logs = []
            for date_entry in time_logs.get('date', []):
                tasklogs = date_entry.get('tasklogs', [])
                for log in tasklogs:
                    # Add date info to each log
                    log['log_date'] = date_entry.get('date', 'Unknown')
                    all_logs.append(log)
            
            if not all_logs:
                date_filter = ""
                if start_date or end_date:
                    date_filter = f" (filtered by date: {start_date or 'any'} to {end_date or 'any'})"
                return f"No time logs found{date_filter}"
            
            # Sort by date (most recent first)
            all_logs.sort(key=lambda x: x.get('log_date', ''), reverse=True)
            
            # Apply limit if specified and not already applied to API call
            if limit and 'range' not in filters:
                all_logs = all_logs[:limit]
            
            # Calculate total hours from the API response
            total_hours = time_logs.get('grandtotal', '0:00')
            billable_hours = time_logs.get('billable_hours', '0:00')
            non_billable_hours = time_logs.get('non_billable_hours', '0:00')
            
            result = f"Found {len(all_logs)} time logs:\n\n"
            result += f"**Total Time Logged:** {total_hours}\n"
            result += f"**Billable:** {billable_hours} | **Non-Billable:** {non_billable_hours}\n\n"
            
            for log in all_logs:
                result += f"• **{log.get('hours_display', '0:00')}** on {log.get('log_date', 'Unknown')}\n"
                
                # Get project info
                project_info = log.get('project', {})
                if project_info:
                    result += f"  Project: {project_info.get('name', 'Unknown')} (ID: {project_info.get('id', 'N/A')})\n"
                else:
                    result += f"  Project: Unknown\n"
                
                # Get task info
                task_info = log.get('task', {})
                if task_info:
                    result += f"  Task: {task_info.get('name', 'Unknown')} (ID: {task_info.get('id', 'N/A')})\n"
                else:
                    result += f"  Task: Unknown\n"
                
                result += f"  Owner: {log.get('owner_name', 'Unknown')}\n"
                result += f"  Status: {log.get('bill_status', 'Unknown')}\n"
                result += f"  Approval: {log.get('approval_status', 'Unknown')}\n"
                
                if log.get('notes'):
                    result += f"  Notes: {log['notes'][:50]}...\n"
                result += "\n"
            
            if len(all_logs) == limit and limit:
                result += f"(Showing first {limit} results)\n"
            
            return result
        except ZohoAPIError as e:
            logger.error(f"Error getting all time logs: {e}")
            return f"Error getting all time logs: {str(e)}"


class AddTimeLogTool(BaseTool):
    """Tool to add a time log to a task"""
    name: str = "add_time_log"
    description: str = "Add a time log entry to a specific task."
    args_schema: Type[BaseModel] = AddTimeLogInput
    zoho_client: ZohoProjectsClient = Field(exclude=True)
    
    def __init__(self, zoho_client: ZohoProjectsClient):
        super().__init__(zoho_client=zoho_client)
    
    def _run(self, project_id: str, task_id: str, date: str, hours: str, 
             bill_status: str, notes: str = "") -> str:
        try:
            log_data = {
                "date": date,
                "hours": hours,
                "bill_status": bill_status,
                "notes": notes
            }
            
            time_log = self.zoho_client.add_time_log(project_id, task_id, log_data)
            
            if time_log:
                result = f"✅ **Time log added successfully!**\n\n"
                result += f"**Date:** {time_log.get('log_date', 'Unknown')}\n"
                result += f"**Hours:** {time_log.get('hours_display', '0:00')}\n"
                result += f"**Owner:** {time_log.get('owner_name', 'Unknown')}\n"
                result += f"**Billing Status:** {time_log.get('bill_status', 'Unknown')}\n"
                return result
            else:
                return "❌ Failed to add time log. No data returned."
                
        except ZohoAPIError as e:
            logger.error(f"Error adding time log: {e}")
            return f"❌ Error adding time log: {str(e)}"


def create_zoho_tools(zoho_client: ZohoProjectsClient) -> List[BaseTool]:
    """Create all Zoho tools with the given client"""
    return [
        ListAllProjectsTool(zoho_client),
        ProjectSearchTool(zoho_client),
        ProjectDetailsTool(zoho_client),
        CreateProjectTool(zoho_client),
        TaskSearchTool(zoho_client),
        TaskDetailsTool(zoho_client),
        CreateTaskTool(zoho_client),
        UpdateTaskTool(zoho_client),
        GetTaskListsTool(zoho_client),
        CreateTaskListTool(zoho_client),
        GetTimeLogsTool(zoho_client),
        GetAllTimeLogsTool(zoho_client),
        AddTimeLogTool(zoho_client),
    ]
