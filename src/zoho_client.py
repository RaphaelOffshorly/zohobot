"""Zoho Projects API Client"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from loguru import logger

from .config import settings


class ZohoAuthError(Exception):
    """Raised when Zoho authentication fails"""
    pass


class ZohoAPIError(Exception):
    """Raised when Zoho API calls fail"""
    pass


class ZohoProjectsClient:
    """Client for interacting with Zoho Projects API"""
    
    def __init__(self):
        self.client_id = settings.zoho_client_id
        self.client_secret = settings.zoho_client_secret
        self.refresh_token = settings.zoho_refresh_token
        self.portal_id = settings.zoho_portal_id
        self.api_base = settings.zoho_api_base_url
        self.auth_base = settings.zoho_auth_base_url
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
    def _refresh_access_token(self) -> str:
        """Refresh the access token using the refresh token"""
        url = f"{self.auth_base}/oauth/v2/token"
        
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            
            # Set expiration time (usually 1 hour, but we'll refresh earlier)
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            logger.info("Successfully refreshed Zoho access token")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh Zoho access token: {e}")
            raise ZohoAuthError(f"Token refresh failed: {e}")
    
    def _get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary"""
        if (not self._access_token or 
            not self._token_expires_at or 
            datetime.now() >= self._token_expires_at):
            return self._refresh_access_token()
        
        return self._access_token
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Zoho API"""
        access_token = self._get_access_token()
        
        # Prepare headers
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Content-Type": "application/json"
        }
        
        # Merge with any additional headers
        if "headers" in kwargs:
            headers.update(kwargs["headers"])
            kwargs["headers"] = headers
        else:
            kwargs["headers"] = headers
        
        # Construct full URL
        url = f"{self.api_base}{endpoint}"
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            
            # Handle empty responses
            if not response.content:
                return {}
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Zoho API request failed: {method} {url} - {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response content: {e.response.text}")
            raise ZohoAPIError(f"API request failed: {e}")
    
    # Projects API Methods
    def get_all_projects(self, status: str = "active") -> List[Dict[str, Any]]:
        """Get all projects in the portal"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/"
        params = {"status": status}
        
        response = self._make_request("GET", endpoint, params=params)
        return response.get("projects", [])
    
    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """Get details of a specific project"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/"
        
        response = self._make_request("GET", endpoint)
        projects = response.get("projects", [])
        return projects[0] if projects else {}
    
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(project_data))
        projects = response.get("projects", [])
        return projects[0] if projects else {}
    
    def update_project(self, project_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(project_data))
        projects = response.get("projects", [])
        return projects[0] if projects else {}
    
    # Tasks API Methods
    def get_all_tasks(self, project_id: str, **filters) -> List[Dict[str, Any]]:
        """Get all tasks in a project"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/"
        
        response = self._make_request("GET", endpoint, params=filters)
        return response.get("tasks", [])
    
    def get_task_details(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """Get details of a specific task"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
        
        response = self._make_request("GET", endpoint)
        tasks = response.get("tasks", [])
        return tasks[0] if tasks else {}
    
    def create_task(self, project_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(task_data))
        tasks = response.get("tasks", [])
        return tasks[0] if tasks else {}
    
    def update_task(self, project_id: str, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(task_data))
        tasks = response.get("tasks", [])
        return tasks[0] if tasks else {}
    
    def delete_task(self, project_id: str, task_id: str) -> bool:
        """Delete a task"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/"
        
        response = self._make_request("DELETE", endpoint)
        return "success" in response.get("response", "").lower()
    
    # Task Lists API Methods
    def get_all_tasklists(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all task lists in a project"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasklists/"
        
        response = self._make_request("GET", endpoint)
        return response.get("tasklists", [])
    
    def create_tasklist(self, project_id: str, tasklist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new task list"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasklists/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(tasklist_data))
        tasklists = response.get("tasklists", [])
        return tasklists[0] if tasklists else {}
    
    def update_tasklist(self, project_id: str, tasklist_id: str, tasklist_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing task list"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasklists/{tasklist_id}/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(tasklist_data))
        tasklists = response.get("tasklists", [])
        return tasklists[0] if tasklists else {}
    
    def delete_tasklist(self, project_id: str, tasklist_id: str) -> bool:
        """Delete a task list"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasklists/{tasklist_id}/"
        
        response = self._make_request("DELETE", endpoint)
        return "success" in response.get("response", "").lower()
    
    # Time Tracking API Methods
    def get_time_logs(self, project_id: str, **filters) -> Dict[str, Any]:
        """Get time logs for a project"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/logs/"
        
        response = self._make_request("GET", endpoint, params=filters)
        return response.get("timelogs", {})
    
    def get_task_time_logs(self, project_id: str, task_id: str) -> Dict[str, Any]:
        """Get time logs for a specific task"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/logs/"
        
        response = self._make_request("GET", endpoint)
        return response.get("timelogs", {})
    
    def add_time_log(self, project_id: str, task_id: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a time log to a task"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/logs/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(log_data))
        timelogs = response.get("timelogs", {})
        tasklogs = timelogs.get("tasklogs", [])
        return tasklogs[0] if tasklogs else {}
    
    def update_time_log(self, project_id: str, task_id: str, log_id: str, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a time log"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/logs/{log_id}/"
        
        response = self._make_request("POST", endpoint, data=json.dumps(log_data))
        timelogs = response.get("timelogs", {})
        tasklogs = timelogs.get("tasklogs", [])
        return tasklogs[0] if tasklogs else {}
    
    def delete_time_log(self, project_id: str, task_id: str, log_id: str) -> bool:
        """Delete a time log"""
        endpoint = f"/restapi/portal/{self.portal_id}/projects/{project_id}/tasks/{task_id}/logs/{log_id}/"
        
        response = self._make_request("DELETE", endpoint)
        return "success" in response.get("response", "").lower()
    
    # Utility Methods
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """Search for projects by name"""
        projects = self.get_all_projects()
        return [p for p in projects if query.lower() in p.get("name", "").lower()]
    
    def search_tasks(self, project_id: str, query: str) -> List[Dict[str, Any]]:
        """Search for tasks by name in a project"""
        tasks = self.get_all_tasks(project_id)
        return [t for t in tasks if query.lower() in t.get("name", "").lower()]
