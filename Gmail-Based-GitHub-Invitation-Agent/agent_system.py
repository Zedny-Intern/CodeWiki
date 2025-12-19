import os
import re
import time
import json
import subprocess
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import base64

load_dotenv()

# ==================== CONFIGURATION ====================

CONFIG = {
    # Gmail API Settings
    "GMAIL_CREDENTIALS_FILE": "credentials.json",
    "GMAIL_TOKEN_FILE": "token.json",
    "GMAIL_SCOPES": ['https://www.googleapis.com/auth/gmail.readonly'],
    
    # GitHub Credentials
    "GITHUB_USERNAME": os.getenv("GITHUB_USERNAME"),
    "GITHUB_PASSWORD": os.getenv("GITHUB_PASSWORD"),
    "GITHUB_EMAIL": os.getenv("GITHUB_EMAIL"),
    
    # Repository Settings
    "CLONE_BASE_PATH": "./cloned_repos",
    
    # Local LLM Settings (Ollama) - Using lightweight reasoning model
    "LLM_PROVIDER": "ollama",
    "LLM_MODEL": "qwen2.5:7b-instruct",  # Optimized for reasoning, not code generation
    "LLM_BASE_URL": "http://localhost:11434",
    "LLM_TEMPERATURE": 0,
    "LLM_ENABLED": True,  # Set to False to run without LLM
    
    # Selenium Settings
    "CHROME_DRIVER_PATH": "/usr/bin/chromedriver",  # Adjust for your system
    "HEADLESS_BROWSER": True,
    
    # GitHub API Settings
    "GITHUB_API_BASE": "https://api.github.com",
    "REQUEST_TIMEOUT": 30,
    
    # Agent Settings
    "MAX_RETRIES": 3,
    "VERBOSE": True,
    "CHECK_EMAIL_INTERVAL": 300,  # 5 minutes
}

# ==================== OUTPUT MODELS ====================

class RepositoryInfo(BaseModel):
    """Repository metadata extracted from invitation"""
    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/name)")
    repo_url: str = Field(..., description="Repository URL")
    invitation_url: str = Field(..., description="Invitation acceptance URL")

class InvitationDecision(BaseModel):
    """LLM decision output for each email - structured JSON schema"""
    email_id: str = Field(..., description="Unique email identifier")
    is_github_invitation: bool = Field(..., description="Whether email is a valid GitHub invitation")
    repository: Optional[RepositoryInfo] = Field(None, description="Repository info if valid invitation")
    action: str = Field(..., description="Decision: accept, skip, or retry")
    confidence: float = Field(..., description="Confidence score 0.0-1.0")

class EmailInvitation(BaseModel):
    """Model for GitHub invitation found in email"""
    sender: str = Field(..., description="Email sender (GitHub inviter)")
    repository_name: str = Field(..., description="Full repository name")
    repository_url: str = Field(..., description="Repository URL")
    invitation_url: str = Field(..., description="Direct invitation acceptance URL")
    invitation_id: str = Field(..., description="Unique invitation identifier")
    received_at: str = Field(..., description="Email received timestamp")

class InvitationAcceptance(BaseModel):
    """Model for invitation acceptance result"""
    repository_name: str = Field(..., description="Repository name")
    repository_url: str = Field(..., description="Repository URL")
    accepted: bool = Field(..., description="Whether invitation was accepted")
    status: str = Field(..., description="Acceptance status message")

class RepoCloneResult(BaseModel):
    """Model for repository clone result"""
    repo_url: str = Field(..., description="URL of the cloned repository")
    clone_path: str = Field(..., description="Local path where repo was cloned")
    success: bool = Field(..., description="Whether clone was successful")
    message: str = Field(..., description="Status message")

class WorkflowReport(BaseModel):
    """Final comprehensive workflow report - structured JSON output"""
    emails_checked: int = Field(..., description="Number of emails checked")
    valid_invitations: int = Field(..., description="Number of valid invitations found")
    accepted: int = Field(..., description="Number of invitations accepted")
    cloned: int = Field(..., description="Number of repos cloned")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    repositories: List[Dict[str, str]] = Field(default_factory=list, description="List of processed repositories")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO-8601 timestamp")

# ==================== GMAIL API INTEGRATION ====================

def authenticate_gmail():
    """Authenticate with Gmail API and return service object"""
    creds = None
    
    if os.path.exists(CONFIG['GMAIL_TOKEN_FILE']):
        creds = Credentials.from_authorized_user_file(CONFIG['GMAIL_TOKEN_FILE'], CONFIG['GMAIL_SCOPES'])
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CONFIG['GMAIL_CREDENTIALS_FILE']):
                raise FileNotFoundError(
                    f"Gmail credentials file not found: {CONFIG['GMAIL_CREDENTIALS_FILE']}\n"
                    "Please download OAuth 2.0 credentials from Google Cloud Console"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                CONFIG['GMAIL_CREDENTIALS_FILE'], CONFIG['GMAIL_SCOPES'])
            creds = flow.run_local_server(port=0)
        
        with open(CONFIG['GMAIL_TOKEN_FILE'], 'w') as token:
            token.write(creds.to_json())
    
    return build('gmail', 'v1', credentials=creds)

# ==================== LLM INITIALIZATION ====================

def initialize_llm():
    """Initialize local Ollama LLM with graceful fallback"""
    if not CONFIG.get('LLM_ENABLED', True):
        print("  LLM disabled in configuration. Running in direct execution mode.")
        return None
    
    print(f" Initializing Ollama LLM: {CONFIG['LLM_MODEL']}")
    print(f"   Base URL: {CONFIG['LLM_BASE_URL']}")
    
    try:
        response = requests.get(f"{CONFIG['LLM_BASE_URL']}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f" Ollama running with {len(models)} models")
            
            if not any(CONFIG['LLM_MODEL'] in name for name in model_names):
                print(f"  Model {CONFIG['LLM_MODEL']} not found!")
                print(f"   Run: ollama pull {CONFIG['LLM_MODEL']}")
                print("   Continuing without LLM...")
                return None
        else:
            print(" Ollama not responding. Continuing without LLM...")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"  Ollama connection failed: {e}")
        print("   System will run with direct tool execution (no LLM reasoning).")
        return None
    
    return LLM(
        model=f"ollama/{CONFIG['LLM_MODEL']}",
        base_url=CONFIG['LLM_BASE_URL'],
        temperature=CONFIG['LLM_TEMPERATURE']
    )

# Initialize LLM (may be None if unavailable)
llm = initialize_llm()

# ==================== TOOLS ====================

@tool
def check_gmail_for_invitations_tool(max_results: int = 10) -> dict:
    """
    Check Gmail inbox for GitHub repository invitation emails.
    
    Args:
        max_results: Maximum number of recent emails to check
    
    Returns:
        Dictionary with found invitations
    """
    try:
        print(" Checking Gmail for GitHub invitations...")
        
        service = authenticate_gmail()
        
        # Search for ALL GitHub notification emails (from noreply or notifications)
        # We perform specific filtering in Python
        query = 'from:noreply@github.com OR from:notifications@github.com'
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results,
            includeSpamTrash=True
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            print(" No invitation emails found")
            return {
                "status": "success",
                "invitations_found": 0,
                "invitations": [],
                "message": "No GitHub invitations found in Gmail"
            }
        
        invitations = []
        
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            # Extract email details
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Debug log to help diagnose missing emails
            print(f"   Scanned email: {subject[:60]}...")
            
            # Filter for invitation emails (case-insensitive)
            # We look for "invit" or "collaborate" in subject
            is_invitation = "invit" in subject.lower() or "collaborate" in subject.lower()
            
            # Get email body
            if 'parts' in msg_data['payload']:
                parts = msg_data['payload']['parts']
                data = parts[0]['body'].get('data', '')
            else:
                data = msg_data['payload']['body'].get('data', '')
            
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                
                # Double check body if subject was ambiguous
                if not is_invitation and ("invit" in body.lower() or "collaborate" in body.lower()):
                     is_invitation = True
                
                if not is_invitation:
                    continue
                
                # Extract repository information using regex (allow for newlines/whitespace)
                repo_match = re.search(r'collaborate on the\s+([^/\s]+/[^\s]+)\s+repository', body)
                repo_url_match = re.search(r'https://github\.com/([^/\s]+/[^/\s]+)', body)
                invitation_url_match = re.search(r'https://github\.com/([^/\s]+/[^/\s]+)/invitations', body)
                
                if repo_match and invitation_url_match:
                    repo_name = repo_match.group(1)
                    repo_url = f"https://github.com/{repo_name}"
                    invitation_url = invitation_url_match.group(0)
                    
                    invitation = {
                        "sender": sender,
                        "repository_name": repo_name,
                        "repository_url": repo_url,
                        "invitation_url": invitation_url,
                        "invitation_id": msg['id'],
                        "received_at": date
                    }
                    invitations.append(invitation)
                    print(f" Found invitation: {repo_name}")
        
        return {
            "status": "success",
            "invitations_found": len(invitations),
            "invitations": invitations,
            "message": f"Found {len(invitations)} GitHub invitations"
        }
    
    except Exception as e:
        print(f" Error checking Gmail: {str(e)}")
        return {
            "status": "error",
            "invitations_found": 0,
            "invitations": [],
            "message": f"Error: {str(e)}"
        }

@tool
def accept_github_invitation_tool(invitation_url: str, repo_name: str) -> dict:
    """
    Accept GitHub repository invitation using Selenium browser automation.
    
    Args:
        invitation_url: Direct URL to the invitation page
        repo_name: Repository name for logging
    
    Returns:
        Dictionary with acceptance status
    """
    try:
        if not invitation_url or "example" in invitation_url or "owner/repo" in invitation_url or "org1" in invitation_url or "repo1" in invitation_url or "repository_invitations" in invitation_url:
            print(f" Skipping invalid/example/hallucinated invitation URL: {invitation_url}")
            return {
                "status": "skipped",
                "repository_name": repo_name,
                "message": "Skipped invalid/example URL"
            }

        print(f" Accepting invitation for: {repo_name}")
        print(f"   URL: {invitation_url}")
        
        # Setup Chrome options
        chrome_options = Options()
        if CONFIG['HEADLESS_BROWSER']:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize driver
        service = Service(CONFIG['CHROME_DRIVER_PATH'])
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        try:
            # Navigate to GitHub login
            driver.get('https://github.com/login')
            time.sleep(2)
            
            # Login to GitHub
            print(" Logging in to GitHub...")
            username_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'login_field'))
            )
            username_field.send_keys(CONFIG['GITHUB_USERNAME'])
            
            password_field = driver.find_element(By.ID, 'password')
            password_field.send_keys(CONFIG['GITHUB_PASSWORD'])
            
            login_button = driver.find_element(By.NAME, 'commit')
            login_button.click()
            
            time.sleep(3)
            
            # Navigate to invitation page
            print(" Navigating to invitation page...")
            driver.get(invitation_url)
            time.sleep(3)
            
            # Find and click "Accept invitation" button
            print(" Clicking Accept Invitation...")
            accept_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept invitation')]"))
            )
            accept_button.click()
            
            time.sleep(3)
            
            # Verify acceptance by checking if we're redirected to repo
            current_url = driver.current_url
            if repo_name.replace('/', '') in current_url.replace('/', ''):
                print(f" Successfully accepted invitation!")
                return {
                    "status": "accepted",
                    "repository_name": repo_name,
                    "repository_url": f"https://github.com/{repo_name}",
                    "message": "Invitation accepted successfully"
                }
            else:
                return {
                    "status": "error",
                    "repository_name": repo_name,
                    "message": "Acceptance verification failed"
                }
        
        finally:
            try:
                driver.quit()
            except Exception:
                pass # Ignore PermissionError or other teardown errors
    
    except Exception as e:
        print(f" Error accepting invitation: {str(e)}")
        return {
            "status": "error",
            "repository_name": repo_name,
            "message": f"Error: {str(e)}"
        }

@tool
def clone_repository_tool(repo_url: str, clone_path: str) -> dict:
    """
    Clone GitHub repository to local path using git command.
    
    Args:
        repo_url: URL of repository to clone
        clone_path: Local directory path
    
    Returns:
        Dictionary with clone status
    """
    try:
        os.makedirs(clone_path, exist_ok=True)
        
        repo_name = repo_url.rstrip('/').split('/')[-1]
        full_path = os.path.join(clone_path, repo_name)
        
        if os.path.exists(full_path):
            print(f" Repository already exists: {full_path}")
            return {
                "status": "already_exists",
                "path": full_path,
                "success": True,
                "message": f"Repository already cloned at {full_path}"
            }
        
        print(f" Cloning repository: {repo_url}")
        print(f"   Destination: {full_path}")
        
        # Clone using git command
        cmd = ['git', 'clone', repo_url, full_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print(f" Clone successful!")
            return {
                "status": "success",
                "path": full_path,
                "success": True,
                "message": f"Repository cloned to {full_path}"
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
            "message": "Clone timeout (>5 minutes)"
        }
    except Exception as e:
        return {
            "status": "error",
            "path": None,
            "success": False,
            "message": f"Error: {str(e)}"
        }

# ==================== AGENTS ====================

# Build agent kwargs - LLM is optional
def get_agent_kwargs():
    """Get agent kwargs with optional LLM"""
    kwargs = {'verbose': CONFIG['VERBOSE']}
    if llm is not None:
        kwargs['llm'] = llm
    return kwargs

agent_kwargs = get_agent_kwargs()

email_monitor_agent = Agent(
    role="Email Classification & Extraction Specialist",
    goal="Analyze Gmail inbox for GitHub collaboration invitations and extract structured invitation data",
    backstory="""You are an intelligent reasoning agent specialized in email analysis.
    Your role is to CLASSIFY emails as valid GitHub invitations and EXTRACT structured 
    metadata including repository owner, name, URLs, and invitation links. You validate 
    the extracted data before passing it to the next agent. You do NOT write code - 
    you reason about data and make decisions.""",
    tools=[check_gmail_for_invitations_tool],
    **agent_kwargs
)

invitation_acceptor_agent = Agent(
    role="Invitation Acceptance Orchestrator",
    goal="Coordinate the acceptance of GitHub repository invitations via browser automation",
    backstory="""You are an orchestration agent that decides WHEN and HOW to accept 
    GitHub invitations. You analyze invitation details, determine the correct action 
    (accept/skip/retry), and coordinate with the browser automation tool. You reason 
    about edge cases and handle errors gracefully. You do NOT write code.""",
    tools=[accept_github_invitation_tool],
    **agent_kwargs
)

repository_cloner_agent = Agent(
    role="Repository Operations Coordinator",
    goal="Manage the cloning of accepted repositories to local storage",
    backstory="""You are a reasoning agent that coordinates repository cloning operations.
    You decide which repositories need cloning, handle conflicts (existing repos), and 
    ensure all operations complete successfully. You validate results and report any 
    issues. You do NOT write code - you orchestrate tools.""",
    tools=[clone_repository_tool],
    **agent_kwargs
)

workflow_coordinator_agent = Agent(
    role="Workflow Summary & Report Generator",
    goal="Synthesize all workflow results into a comprehensive structured JSON report",
    backstory="""You are the final reasoning agent that aggregates all results from 
    previous agents. You analyze the entire workflow execution, count successes and 
    failures, identify errors, and generate a structured JSON report following the 
    exact WorkflowReport schema. You produce machine-readable output.""",
    **agent_kwargs
)

# ==================== TASKS ====================

monitor_email_task = Task(
    description="""
    Monitor Gmail inbox for GitHub repository collaboration invitations.
    
    Steps:
    1. Use check_gmail_for_invitations_tool to scan recent emails
    2. Identify emails from notifications@github.com with invitation subject
    3. Extract repository names, URLs, and invitation links
    4. Return structured list of all found invitations. If NO invitations are found after scanning, return an EMPTY list []. Do NOT invent repository names.
    
    Focus on emails with subject containing "invited you to collaborate".
    """,
    expected_output="Structured list of GitHub invitations found in Gmail, or empty list if none.",
    agent=email_monitor_agent
)

accept_invitations_task = Task(
    description="""
    Accept all GitHub repository invitations found in previous task.
    
    Steps:
    1. Get invitation details from email monitor output
    2. For each invitation, use accept_github_invitation_tool
    3. Provide invitation URL and repository name
    4. Verify each acceptance was successful
    5. Return list of accepted repositories
    
    CRITICAL: If the list of invitations is empty, do NOT invent or retry with example URLs. 
    Simply return an empty list and state "No invitations to accept".
    
    Use GitHub credentials from CONFIG for login.
    """,
    expected_output="Confirmation of accepted invitations with repository details",
    agent=invitation_acceptor_agent
)

clone_repositories_task = Task(
    description=f"""
    Clone all accepted repositories to local storage.
    
    Steps:
    1. Get list of accepted repositories from previous task
    2. For each repository, use clone_repository_tool
    3. Clone to base path: {CONFIG['CLONE_BASE_PATH']}
    4. Verify successful clones
    5. Return paths of all cloned repositories
    
    Skip repositories that are already cloned.
    """,
    expected_output="Confirmation of cloned repositories with local paths",
    agent=repository_cloner_agent
)

generate_report_task = Task(
    description="""
    Generate comprehensive workflow report as structured JSON.
    
    Analyze all previous task outputs and create a WorkflowReport with:
    1. emails_checked: Total number of emails scanned
    2. valid_invitations: Number of valid GitHub invitations found
    3. accepted: Number of invitations successfully accepted
    4. cloned: Number of repositories successfully cloned
    5. errors: List of any error messages encountered
    6. repositories: List of processed repositories with details
    7. timestamp: ISO-8601 formatted timestamp
    
    Output MUST be valid JSON matching the WorkflowReport schema exactly.
    """,
    expected_output="Structured JSON WorkflowReport with all metrics",
    agent=workflow_coordinator_agent,
    output_json=WorkflowReport
)

# ==================== CREW ====================

def create_gmail_github_crew():
    """Create crew for Gmail-based GitHub invitation workflow"""
    return Crew(
        agents=[
            email_monitor_agent,
            invitation_acceptor_agent,
            repository_cloner_agent,
            workflow_coordinator_agent
        ],
        tasks=[
            monitor_email_task,
            accept_invitations_task,
            clone_repositories_task,
            generate_report_task
        ],
        process=Process.sequential,
        verbose=CONFIG['VERBOSE']
    )

# ==================== MAIN ====================

def main():
    """Main entry point for Gmail-based GitHub invitation agent"""
    
    print("\n" + "="*80)
    print(" GMAIL-BASED GITHUB INVITATION AGENT - LOCAL LLM EDITION")
    print("="*80 + "\n")
    
    # Show LLM status
    llm_status = " Active" if llm is not None else "  Disabled (direct execution)"
    
    print(f" Configuration:")
    print(f"   LLM Model: {CONFIG['LLM_MODEL']}")
    print(f"   LLM Status: {llm_status}")
    print(f"   GitHub User: {CONFIG['GITHUB_USERNAME']}")
    print(f"   Gmail: {CONFIG['GITHUB_EMAIL']}")
    print(f"   Clone Path: {CONFIG['CLONE_BASE_PATH']}")
    print(f"   Headless Browser: {CONFIG['HEADLESS_BROWSER']}")
    print()
    
    # Validate configuration
    if not CONFIG['GITHUB_PASSWORD']:
        print(" ERROR: GITHUB_PASSWORD not set in environment variables")
        print("   Add to .env file: GITHUB_PASSWORD=your_password")
        return
    
    if not os.path.exists(CONFIG['GMAIL_CREDENTIALS_FILE']):
        print(f" ERROR: Gmail credentials file not found: {CONFIG['GMAIL_CREDENTIALS_FILE']}")
        print("   Download OAuth 2.0 credentials from Google Cloud Console")
        print("   Visit: https://console.cloud.google.com/apis/credentials")
        return
    
    try:
        print(" Starting Gmail monitoring workflow...\n")
        
        crew = create_gmail_github_crew()
        result = crew.kickoff()
        
        print("\n" + "="*80)
        print(" WORKFLOW COMPLETED")
        print("="*80)
        print(f"\n{result}\n")
        
        # Save report to file
        report_file = f"reports/workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("reports", exist_ok=True)
        
        # Handle different result types
        if hasattr(result, 'model_dump'):
            report_data = result.model_dump()
        elif isinstance(result, dict):
            report_data = result
        else:
            report_data = {"raw_output": str(result), "timestamp": datetime.now().isoformat()}
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f" Report saved: {report_file}\n")
    
    except Exception as e:
        print(f"\n ERROR: Workflow failed:")
        print(f"   {str(e)}\n")
        raise

if __name__ == "__main__":
    main()