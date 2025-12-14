import os
import json
import subprocess
import requests
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from datetime import datetime


# CONFIGURATION


CONFIG = {
    # API Keys
    "GROQ_API_KEY": "",
    "GITHUB_PAT": "",
    
    # Agent GitHub Credentials
    "AGENT_GITHUB_USERNAME": "AgentCODEWIKI",
    "AGENT_GITHUB_EMAIL": "temp01234567899876543210@gmail.com",
    
    # Repository Settings
    "CLONE_BASE_PATH": "./cloned_repos",
    
    # LLM Settings
    "LLM_MODEL": "llama-3.3-70b-versatile",
    "LLM_TEMPERATURE": 0,
    
    # GitHub API Settings
    "GITHUB_API_BASE": "https://api.github.com",
    "REQUEST_TIMEOUT": 30,
    
    # Agent Settings
    "MAX_RETRIES": 3,
    "VERBOSE": True,
    
    # Workflow Settings
    "AUTO_ACCEPT_INVITATIONS": True,
    "REPO_TYPE": "private"  # Set to "private" or "public"
}


# OUTPUT MODELS


class NotificationInfo(BaseModel):
    """Model for GitHub notification information"""
    total_notifications: int = Field(..., description="Total number of notifications")
    invitations_found: int = Field(..., description="Number of invitations found")
    invitation_details: List[Dict[str, Any]] = Field(default_factory=list, description="List of invitation details")
    status: str = Field(..., description="Status of notification processing")

class InvitationAcceptance(BaseModel):
    """Model for invitation acceptance result"""
    accepted: bool = Field(..., description="Whether invitation was accepted")
    repo_url: str = Field(..., description="Repository URL after acceptance")
    repo_name: str = Field(..., description="Repository name")
    status: str = Field(..., description="Acceptance status")

class RepoCloneResult(BaseModel):
    """Model for repository clone result"""
    repo_url: str = Field(..., description="URL of the cloned repository")
    clone_path: str = Field(..., description="Local path where repo was cloned")
    success: bool = Field(..., description="Whether clone was successful")
    message: str = Field(..., description="Status message")

class ProjectReport(BaseModel):
    """Final report of the entire operation"""
    repo_type: str = Field(..., description="Type of repo (public/private)")
    notifications_checked: bool = Field(default=False)
    invitation_accepted: bool = Field(default=False)
    clone_successful: bool = Field(..., description="Whether clone succeeded")
    final_repo_path: Optional[str] = Field(None, description="Path to cloned repo")
    summary: str = Field(..., description="Summary of the operation")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# GITHUB API HELPER FUNCTIONS


def get_github_headers(token: str) -> Dict[str, str]:
    """Generate headers for GitHub API requests"""
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GitHub-Agent-System"
    }


# TOOLS DEFINITION


@tool
def check_github_notifications_tool(pat: str) -> dict:
    """
    Check GitHub notifications for collaboration invitations using GitHub API.
    
    Args:
        pat: GitHub Personal Access Token
    
    Returns:
        Dictionary with notification information including invitations
    """
    try:
        headers = get_github_headers(pat)
        url = f"{CONFIG['GITHUB_API_BASE']}/notifications"
        
        print("Checking GitHub notifications via API...")
        
        response = requests.get(
            url,
            headers=headers,
            timeout=CONFIG['REQUEST_TIMEOUT']
        )
        
        if response.status_code != 200:
            return {
                "status": "error",
                "total_notifications": 0,
                "invitations_found": 0,
                "invitation_details": [],
                "message": f"API error: {response.status_code} - {response.text}"
            }
        
        notifications = response.json()
        invitations = []
        
        # Filter for repository invitations
        for notif in notifications:
            if notif.get('subject', {}).get('type') == 'RepositoryInvitation':
                repo_info = {
                    "id": notif.get('id'),
                    "repository": notif.get('repository', {}).get('full_name'),
                    "repo_url": notif.get('repository', {}).get('html_url'),
                    "url": notif.get('url'),
                    "subject_url": notif.get('subject', {}).get('url'),
                    "updated_at": notif.get('updated_at')
                }
                invitations.append(repo_info)
        
        return {
            "status": "success",
            "total_notifications": len(notifications),
            "invitations_found": len(invitations),
            "invitation_details": invitations,
            "message": f"Found {len(invitations)} repository invitations"
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "total_notifications": 0,
            "invitations_found": 0,
            "invitation_details": [],
            "message": f"Request error: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "total_notifications": 0,
            "invitations_found": 0,
            "invitation_details": [],
            "message": f"Error: {str(e)}"
        }


@tool
def get_repository_invitations_tool(pat: str) -> dict:
    """
    Get pending repository invitations for the authenticated user.
    
    Args:
        pat: GitHub Personal Access Token
    
    Returns:
        Dictionary with list of pending invitations
    """
    try:
        headers = get_github_headers(pat)
        url = f"{CONFIG['GITHUB_API_BASE']}/user/repository_invitations"
        
        print("Fetching repository invitations via API...")
        
        response = requests.get(
            url,
            headers=headers,
            timeout=CONFIG['REQUEST_TIMEOUT']
        )
        
        if response.status_code != 200:
            return {
                "status": "error",
                "invitations": [],
                "message": f"API error: {response.status_code} - {response.text}"
            }
        
        invitations = response.json()
        
        formatted_invitations = []
        for inv in invitations:
            inv_info = {
                "invitation_id": inv.get('id'),
                "repository_name": inv.get('repository', {}).get('full_name'),
                "repository_url": inv.get('repository', {}).get('html_url'),
                "clone_url": inv.get('repository', {}).get('clone_url'),
                "inviter": inv.get('inviter', {}).get('login'),
                "permissions": inv.get('permissions')
            }
            formatted_invitations.append(inv_info)
        
        return {
            "status": "success",
            "invitations": formatted_invitations,
            "count": len(formatted_invitations),
            "message": f"Found {len(formatted_invitations)} pending invitations"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "invitations": [],
            "message": f"Error: {str(e)}"
        }


@tool
def accept_invitation_tool(invitation_id: int, pat: str) -> dict:
    """
    Accept a GitHub repository collaboration invitation using API.
    
    Args:
        invitation_id: ID of the invitation to accept
        pat: GitHub Personal Access Token
    
    Returns:
        Dictionary with acceptance status
    """
    try:
        headers = get_github_headers(pat)
        url = f"{CONFIG['GITHUB_API_BASE']}/user/repository_invitations/{invitation_id}"
        
        print(f"Accepting invitation ID: {invitation_id}...")
        
        response = requests.patch(
            url,
            headers=headers,
            timeout=CONFIG['REQUEST_TIMEOUT']
        )
        
        if response.status_code == 204:
            return {
                "status": "accepted",
                "invitation_id": invitation_id,
                "message": "Invitation accepted successfully"
            }
        else:
            return {
                "status": "error",
                "invitation_id": invitation_id,
                "message": f"Failed to accept: {response.status_code} - {response.text}"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "invitation_id": invitation_id,
            "message": f"Error: {str(e)}"
        }


@tool
def clone_repository_tool(repo_url: str, clone_path: str, pat: Optional[str] = None) -> dict:
    """
    Clone a GitHub repository to local path using git command.
    
    Args:
        repo_url: URL of the repository to clone
        clone_path: Local path where to clone the repo
        pat: GitHub Personal Access Token (for private repos)
    
    Returns:
        Dictionary with clone status
    """
    try:
        os.makedirs(clone_path, exist_ok=True)
        
        # Extract repo name from URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        full_path = os.path.join(clone_path, repo_name)
        
        if os.path.exists(full_path):
            return {
                "status": "already_exists",
                "path": full_path,
                "success": True,
                "message": f"Repository already exists at {full_path}"
            }
        
        print(f"Cloning repository: {repo_url}")
        print(f"Destination: {full_path}")
        
        # Prepare git clone command with PAT authentication
        if pat:
            # For private repos: use PAT in URL
            if repo_url.startswith('https://github.com/'):
                auth_url = repo_url.replace('https://github.com/', f'https://{pat}@github.com/')
            else:
                auth_url = repo_url
            cmd = ['git', 'clone', auth_url, full_path]
        else:
            # For public repos
            cmd = ['git', 'clone', repo_url, full_path]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return {
                "status": "success",
                "path": full_path,
                "success": True,
                "message": f"Repository cloned successfully to {full_path}"
            }
        else:
            return {
                "status": "error",
                "path": None,
                "success": False,
                "message": f"Clone failed: {result.stderr}"
            }
            
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "path": None,
            "success": False,
            "message": "Clone operation timed out (>5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "path": None,
            "success": False,
            "message": f"Clone error: {str(e)}"
        }


@tool
def validate_repo_url_tool(repo_url: str, pat: str) -> dict:
    """
    Validate if a GitHub repository URL is accessible via API.
    
    Args:
        repo_url: URL to validate
        pat: GitHub Personal Access Token
    
    Returns:
        Dictionary with validation result
    """
    try:
        import re
        
        # Extract owner and repo from URL
        match = re.search(r'github\.com/([^/]+)/([^/\.]+)', repo_url)
        if not match:
            return {
                "valid": False,
                "accessible": False,
                "is_private": None,
                "message": "Invalid GitHub URL format"
            }
        
        owner, repo = match.groups()
        
        headers = get_github_headers(pat)
        url = f"{CONFIG['GITHUB_API_BASE']}/repos/{owner}/{repo}"
        
        response = requests.get(url, headers=headers, timeout=CONFIG['REQUEST_TIMEOUT'])
        
        if response.status_code == 200:
            repo_data = response.json()
            return {
                "valid": True,
                "accessible": True,
                "is_private": repo_data.get('private', False),
                "full_name": repo_data.get('full_name'),
                "clone_url": repo_data.get('clone_url'),
                "message": "Repository is valid and accessible"
            }
        elif response.status_code == 404:
            return {
                "valid": True,
                "accessible": False,
                "is_private": None,
                "message": "Repository not found or not accessible"
            }
        else:
            return {
                "valid": False,
                "accessible": False,
                "is_private": None,
                "message": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "valid": False,
            "accessible": False,
            "is_private": None,
            "message": f"Validation error: {str(e)}"
        }


# AGENT DEFINITIONS


llm = LLM(
    model=f"groq/{CONFIG['LLM_MODEL']}",
    api_key=CONFIG['GROQ_API_KEY'],
    temperature=CONFIG['LLM_TEMPERATURE']
)

notification_monitor_agent = Agent(
    role="GitHub Notification Monitor",
    goal="Monitor GitHub notifications and identify collaboration invitations via API",
    backstory="""You are a specialized agent responsible for monitoring GitHub 
    notifications using the GitHub API. Your job is to check for collaboration 
    invitations and report them for processing.""",
    llm=llm,
    tools=[check_github_notifications_tool, get_repository_invitations_tool],
    verbose=CONFIG['VERBOSE']
)

invitation_handler_agent = Agent(
    role="GitHub Invitation Handler",
    goal="Accept GitHub repository collaboration invitations via API",
    backstory="""You are responsible for handling GitHub collaboration invitations 
    using the GitHub API. When invitations are found, you accept them and extract 
    repository information for cloning.""",
    llm=llm,
    tools=[accept_invitation_tool],
    verbose=CONFIG['VERBOSE']
)

repository_cloner_agent = Agent(
    role="Repository Clone Specialist",
    goal="Clone GitHub repositories to local storage",
    backstory="""You are an expert at cloning GitHub repositories using git commands. 
    You handle both public and private repositories with proper authentication.""",
    llm=llm,
    tools=[clone_repository_tool, validate_repo_url_tool],
    verbose=CONFIG['VERBOSE']
)

workflow_coordinator_agent = Agent(
    role="Workflow Coordinator",
    goal="Coordinate the entire repository access and clone workflow",
    backstory="""You are the master coordinator who oversees the entire process 
    of accessing and cloning repositories. You orchestrate the workflow based on 
    repository type.""",
    llm=llm,
    verbose=CONFIG['VERBOSE']
)


# TASK DEFINITIONS


check_notifications_task = Task(
    description=f"""
    Check GitHub notifications and repository invitations using the GitHub API.
    
    Steps:
    1. Use get_repository_invitations_tool to get pending invitations
    2. Use check_github_notifications_tool to check all notifications
    3. Identify all pending collaboration invitations
    4. Extract invitation IDs and repository information
    5. Report findings with structured data
    
    Use PAT from CONFIG for authentication.
    """,
    expected_output="Structured report of all repository invitations with IDs and details",
    agent=notification_monitor_agent,
    output_json=NotificationInfo
)

accept_invitation_task = Task(
    description=f"""
    Accept all pending GitHub collaboration invitations using the API.
    
    Steps:
    1. Get invitation details from previous task
    2. For each invitation, use accept_invitation_tool with invitation ID
    3. Confirm acceptance for each invitation
    4. Extract repository URLs and clone URLs
    5. Return list of accepted repositories
    
    Use PAT from CONFIG for authentication.
    """,
    expected_output="Confirmation of accepted invitations with repository URLs",
    agent=invitation_handler_agent
)

clone_repository_task = Task(
    description=f"""
    Clone the GitHub repository to local storage.
    
    Steps:
    1. Get repository URL from previous task (private) or from config (public)
    2. Validate the repository URL using validate_repo_url_tool
    3. Use clone_repository_tool with PAT for authentication
    4. Verify clone was successful
    5. Return local path where repo was cloned
    
    Clone to: {CONFIG['CLONE_BASE_PATH']}
    Use PAT from CONFIG for private repository authentication.
    """,
    expected_output="Confirmation of successful clone with local path",
    agent=repository_cloner_agent,
    output_json=RepoCloneResult
)

generate_report_task = Task(
    description="""
    Generate a comprehensive report of the repository access and clone operation.
    
    Include:
    1. Type of repository (public/private)
    2. Steps taken (notifications, invitations, clone)
    3. Final status of clone operation
    4. Local path where repository is stored
    5. Any issues encountered
    6. Timestamp of operation
    """,
    expected_output="Comprehensive report of the workflow",
    agent=workflow_coordinator_agent,
    output_json=ProjectReport
)


# CREW SETUP


def create_private_repo_crew():
    """Create crew for private repository workflow"""
    return Crew(
        agents=[
            notification_monitor_agent,
            invitation_handler_agent,
            repository_cloner_agent,
            workflow_coordinator_agent
        ],
        tasks=[
            check_notifications_task,
            accept_invitation_task,
            clone_repository_task,
            generate_report_task
        ],
        process=Process.sequential,
        verbose=CONFIG['VERBOSE']
    )


def create_public_repo_crew(repo_url: str):
    """Create crew for public repository workflow"""
    
    clone_task = Task(
        description=f"""
        Clone the public repository: {repo_url}
        
        Steps:
        1. Validate URL: {repo_url}
        2. Clone to: {CONFIG['CLONE_BASE_PATH']}
        3. Verify clone success
        4. Return local path
        """,
        expected_output="Clone confirmation with path",
        agent=repository_cloner_agent,
        output_json=RepoCloneResult
    )
    
    report_task = Task(
        description=f"""
        Generate report for public repository clone.
        Repository: {repo_url}
        """,
        expected_output="Comprehensive report",
        agent=workflow_coordinator_agent,
        output_json=ProjectReport
    )
    
    return Crew(
        agents=[repository_cloner_agent, workflow_coordinator_agent],
        tasks=[clone_task, report_task],
        process=Process.sequential,
        verbose=CONFIG['VERBOSE']
    )


# MAIN EXECUTION


def main():
    """Main entry point - runs automatically based on CONFIG"""
    
    print("\n" + "="*70)
    print("GITHUB REPOSITORY CLONE AGENT SYSTEM - PRODUCTION")
    print("="*70 + "\n")
    
    print(f"Configuration:")
    print(f"  Repository Type: {CONFIG['REPO_TYPE']}")
    print(f"  Clone Path: {CONFIG['CLONE_BASE_PATH']}")
    print(f"  GitHub User: {CONFIG['AGENT_GITHUB_USERNAME']}")
    print(f"  Auto Accept: {CONFIG['AUTO_ACCEPT_INVITATIONS']}")
    print()
    
    try:
        if CONFIG['REPO_TYPE'].lower() == 'private':
            print("Starting private repository workflow...")
            print("Steps: Check notifications -> Accept invitations -> Clone\n")
            
            crew = create_private_repo_crew()
            result = crew.kickoff()
            
            print("\n" + "="*70)
            print("WORKFLOW COMPLETED - PRIVATE REPOSITORY")
            print("="*70)
            print(f"\nResult: {result}\n")
            
        elif CONFIG['REPO_TYPE'].lower() == 'public':
            # For public repos, you need to set PUBLIC_REPO_URL in CONFIG
            if 'PUBLIC_REPO_URL' not in CONFIG:
                print("ERROR: PUBLIC_REPO_URL not set in CONFIG")
                print("Add CONFIG['PUBLIC_REPO_URL'] = 'https://github.com/owner/repo' for public repos")
                return
            
            repo_url = CONFIG['PUBLIC_REPO_URL']
            print(f"Starting public repository workflow...")
            print(f"Repository: {repo_url}\n")
            
            crew = create_public_repo_crew(repo_url)
            result = crew.kickoff()
            
            print("\n" + "="*70)
            print("WORKFLOW COMPLETED - PUBLIC REPOSITORY")
            print("="*70)
            print(f"\nResult: {result}\n")
            
        else:
            print(f"ERROR: Invalid REPO_TYPE '{CONFIG['REPO_TYPE']}'")
            print("Set CONFIG['REPO_TYPE'] to 'private' or 'public'")
            
    except Exception as e:
        print(f"\nERROR: Workflow failed with exception:")
        print(f"{str(e)}\n")
        raise


if __name__ == "__main__":
    main()