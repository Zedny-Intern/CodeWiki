import os
import re
import json
import subprocess
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv
import requests

load_dotenv()

# ==================== CONFIGURATION ====================

PUBLIC_REPO_CONFIG = {
    # Set the public GitHub repository URL to clone
    "PUBLIC_REPO_URL": "https://github.com/crewAIInc/crewAI",  
    
    # Where cloned repositories will be stored
    "CLONE_BASE_PATH": "./cloned_repos",
    
    # Model to use for agent reasoning
    "LLM_MODEL": os.getenv("LLM_MODEL", "qwen2.5:7b-instruct"),
    # Ollama server URL
    "LLM_BASE_URL": os.getenv("LLM_BASE_URL", "http://localhost:11434"),
    # Temperature for LLM responses
    "LLM_TEMPERATURE": 0,
    # Enable/disable LLM - set to False for direct execution mode
    "LLM_ENABLED": os.getenv("LLM_ENABLED", "true").lower() == "true",
    
    "GITHUB_API_BASE": "https://api.github.com",
    "REQUEST_TIMEOUT": 30,
    
    "VERBOSE": True,
}

# ==================== OUTPUT MODELS ====================

class PublicRepoInfo(BaseModel):
    """Parsed public repository information"""
    owner: str = Field(..., description="Repository owner/organization")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/name)")
    url: str = Field(..., description="Repository URL")
    is_valid: bool = Field(..., description="Whether the URL is valid")

class ValidationResult(BaseModel):
    """URL validation result"""
    status: str = Field(..., description="Validation status: success, error")
    repository: Optional[PublicRepoInfo] = Field(None, description="Repository info if valid")
    message: str = Field(..., description="Status message")

class RepoCloneResult(BaseModel):
    """Model for repository clone result"""
    repo_url: str = Field(..., description="URL of the cloned repository")
    clone_path: str = Field(..., description="Local path where repo was cloned")
    success: bool = Field(..., description="Whether clone was successful")
    message: str = Field(..., description="Status message")

class PublicWorkflowReport(BaseModel):
    """Final workflow report for public repository operations"""
    repository_url: str = Field(..., description="Configured repository URL")
    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    validation_status: str = Field(..., description="URL validation status")
    clone_status: str = Field(..., description="Clone operation status")
    clone_path: Optional[str] = Field(None, description="Local clone path if successful")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO-8601 timestamp")

# ==================== LLM INITIALIZATION ====================

def initialize_llm():
    """Initialize local Ollama LLM with graceful fallback"""
    if not PUBLIC_REPO_CONFIG.get('LLM_ENABLED', True):
        print("  LLM disabled in configuration. Running in direct execution mode.")
        return None
    
    print(f" Initializing Ollama LLM: {PUBLIC_REPO_CONFIG['LLM_MODEL']}")
    print(f"   Base URL: {PUBLIC_REPO_CONFIG['LLM_BASE_URL']}")
    
    try:
        response = requests.get(f"{PUBLIC_REPO_CONFIG['LLM_BASE_URL']}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m['name'] for m in models]
            print(f" Ollama running with {len(models)} models")
            
            if not any(PUBLIC_REPO_CONFIG['LLM_MODEL'] in name for name in model_names):
                print(f"   Model {PUBLIC_REPO_CONFIG['LLM_MODEL']} not found!")
                print(f"   Run: ollama pull {PUBLIC_REPO_CONFIG['LLM_MODEL']}")
                print("   Continuing without LLM...")
                return None
        else:
            print(" Ollama not responding. Continuing without LLM...")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"   Ollama connection failed: {e}")
        print("   System will run with direct tool execution (no LLM reasoning).")
        return None
    
    return LLM(
        model=f"ollama/{PUBLIC_REPO_CONFIG['LLM_MODEL']}",
        base_url=PUBLIC_REPO_CONFIG['LLM_BASE_URL'],
        temperature=PUBLIC_REPO_CONFIG['LLM_TEMPERATURE']
    )

# Initialize LLM (may be None if unavailable)
llm = initialize_llm()

# ==================== TOOLS ====================

@tool
def validate_github_url_tool(url: str) -> dict:
    """
    Validate and parse a GitHub repository URL.
    
    Args:
        url: GitHub repository URL to validate
    
    Returns:
        Dictionary with validation result and parsed info
    """
    try:
        print(f" Validating GitHub URL: {url}")
        
        # Pattern to match GitHub repository URLs
        # Supports: https://github.com/owner/repo, https://github.com/owner/repo.git
        pattern = r'^https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git)?/?$'
        match = re.match(pattern, url.strip())
        
        if not match:
            print(f" Invalid GitHub URL format")
            return {
                "status": "error",
                "repository": None,
                "message": "Invalid GitHub URL format. Expected: https://github.com/owner/repo"
            }
        
        owner = match.group(1)
        name = match.group(2)
        full_name = f"{owner}/{name}"
        
        print(f"   Owner: {owner}")
        print(f"   Repository: {name}")
        
        # Verify repository exists via GitHub API
        api_url = f"{PUBLIC_REPO_CONFIG['GITHUB_API_BASE']}/repos/{full_name}"
        print(f" Checking repository existence via GitHub API...")
        
        response = requests.get(api_url, timeout=PUBLIC_REPO_CONFIG['REQUEST_TIMEOUT'])
        
        if response.status_code == 200:
            repo_data = response.json()
            if repo_data.get('private', False):
                print(f" Repository is private - use agent_system.py instead")
                return {
                    "status": "error",
                    "repository": None,
                    "message": f"Repository {full_name} is private. Use agent_system.py for private repositories."
                }
            
            print(f" Public repository verified: {full_name}")
            return {
                "status": "success",
                "repository": {
                    "owner": owner,
                    "name": name,
                    "full_name": full_name,
                    "url": f"https://github.com/{full_name}",
                    "is_valid": True
                },
                "message": f"Valid public repository: {full_name}"
            }
        
        elif response.status_code == 404:
            print(f" Repository not found: {full_name}")
            return {
                "status": "error",
                "repository": None,
                "message": f"Repository {full_name} not found on GitHub"
            }
        
        else:
            print(f" GitHub API returned status {response.status_code}")
            return {
                "status": "warning",
                "repository": {
                    "owner": owner,
                    "name": name,
                    "full_name": full_name,
                    "url": f"https://github.com/{full_name}",
                    "is_valid": True
                },
                "message": f"Could not verify repository (API status: {response.status_code}). Proceeding anyway."
            }
    
    except requests.exceptions.RequestException as e:
        print(f" Network error during validation: {e}")
        # If we can't reach the API, try to proceed based on URL pattern alone
        if match:
            return {
                "status": "warning",
                "repository": {
                    "owner": owner,
                    "name": name,
                    "full_name": full_name,
                    "url": f"https://github.com/{full_name}",
                    "is_valid": True
                },
                "message": f"Could not verify repository (network error). Proceeding based on URL pattern."
            }
        return {
            "status": "error",
            "repository": None,
            "message": f"Validation failed: {str(e)}"
        }
    
    except Exception as e:
        print(f" Validation error: {str(e)}")
        return {
            "status": "error",
            "repository": None,
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
        # Remove .git suffix if present
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        
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
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print(f" Clone failed: {error_msg}")
            return {
                "status": "error",
                "path": None,
                "success": False,
                "message": f"Clone failed: {error_msg}"
            }
    
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "path": None,
            "success": False,
            "message": "Clone timeout (>5 minutes)"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "path": None,
            "success": False,
            "message": "Git is not installed or not in PATH"
        }
    except Exception as e:
        return {
            "status": "error",
            "path": None,
            "success": False,
            "message": f"Error: {str(e)}"
        }

# ==================== AGENTS ====================

def get_agent_kwargs():
    """Get agent kwargs with optional LLM"""
    kwargs = {'verbose': PUBLIC_REPO_CONFIG['VERBOSE']}
    if llm is not None:
        kwargs['llm'] = llm
    return kwargs

agent_kwargs = get_agent_kwargs()

url_validator_agent = Agent(
    role="GitHub URL Validator & Parser",
    goal="Validate public GitHub repository URLs and extract structured metadata",
    backstory="""You are an intelligent validation agent specialized in parsing GitHub URLs.
    Your role is to VALIDATE that a given URL points to a valid, accessible public GitHub 
    repository. You extract the owner, repository name, and verify the repository exists.
    You handle edge cases like malformed URLs, private repositories, and non-existent repos.
    You provide clear, actionable feedback for any validation failures.""",
    tools=[validate_github_url_tool],
    **agent_kwargs
)

repository_cloner_agent = Agent(
    role="Repository Operations Coordinator",
    goal="Manage the cloning of public repositories to local storage",
    backstory="""You are a reasoning agent that coordinates repository cloning operations.
    You receive validated repository information and execute the clone operation.
    You handle conflicts (existing repos), ensure operations complete successfully,
    and report any issues. You do NOT write code - you orchestrate tools.""",
    tools=[clone_repository_tool],
    **agent_kwargs
)

workflow_report_agent = Agent(
    role="Workflow Summary & Report Generator",
    goal="Synthesize all workflow results into a comprehensive structured JSON report",
    backstory="""You are the final reasoning agent that aggregates all results from 
    previous agents. You analyze the entire workflow execution, track successes and 
    failures, identify errors, and generate a structured JSON report following the 
    exact PublicWorkflowReport schema. You produce machine-readable output.""",
    **agent_kwargs
)

# ==================== TASKS ====================

validate_url_task = Task(
    description=f"""
    Validate the configured public GitHub repository URL.
    
    URL to validate: {PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL']}
    
    Steps:
    1. Use validate_github_url_tool to check the URL
    2. Ensure the URL format is valid (https://github.com/owner/repo)
    3. Verify the repository exists on GitHub
    4. Confirm it is a PUBLIC repository (not private)
    5. Extract owner and repository name
    6. Return structured validation result
    
    If the URL is invalid or the repository doesn't exist, return a clear error message.
    Do NOT try alternative URLs or make up repository names.
    """,
    expected_output="Structured validation result with repository owner, name, and status",
    agent=url_validator_agent
)

clone_repository_task = Task(
    description=f"""
    Clone the validated public repository to local storage.
    
    Steps:
    1. Get repository details from the validation task output
    2. Only proceed if the repository was validated successfully
    3. Use clone_repository_tool to clone the repository
    4. Clone to base path: {PUBLIC_REPO_CONFIG['CLONE_BASE_PATH']}
    5. Handle edge case: repository already exists locally
    6. Return clone result with local path
    
    If the validation failed, do NOT attempt to clone. Return an error message instead.
    """,
    expected_output="Clone result with local path or error message",
    agent=repository_cloner_agent
)

generate_report_task = Task(
    description=f"""
    Generate comprehensive workflow report as structured JSON.
    
    Analyze all previous task outputs and create a PublicWorkflowReport with:
    1. repository_url: The configured URL ({PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL']})
    2. owner: Repository owner extracted from URL
    3. name: Repository name extracted from URL
    4. validation_status: success, error, or warning
    5. clone_status: success, already_exists, error, or skipped
    6. clone_path: Local path if clone was successful, null otherwise
    7. errors: List of any error messages encountered
    8. timestamp: ISO-8601 formatted timestamp
    
    Output MUST be valid JSON matching the PublicWorkflowReport schema exactly.
    """,
    expected_output="Structured JSON PublicWorkflowReport with all workflow details",
    agent=workflow_report_agent,
    output_json=PublicWorkflowReport
)

# ==================== CREW ====================

def create_public_repo_crew():
    """Create crew for public repository cloning workflow"""
    return Crew(
        agents=[
            url_validator_agent,
            repository_cloner_agent,
            workflow_report_agent
        ],
        tasks=[
            validate_url_task,
            clone_repository_task,
            generate_report_task
        ],
        process=Process.sequential,
        verbose=PUBLIC_REPO_CONFIG['VERBOSE']
    )

# ==================== MAIN ====================

def main():
    """Main entry point for public repository agent"""
    
    print("\n" + "="*80)
    print(" PUBLIC REPOSITORY CLONE AGENT - LOCAL LLM EDITION")
    print("="*80 + "\n")
    
    # Show LLM status
    llm_status = " Active" if llm is not None else " Disabled (direct execution)"
    
    print(f" Configuration:")
    print(f"   Repository URL: {PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL']}")
    print(f"   Clone Path: {PUBLIC_REPO_CONFIG['CLONE_BASE_PATH']}")
    print(f"   LLM Model: {PUBLIC_REPO_CONFIG['LLM_MODEL']}")
    print(f"   LLM Status: {llm_status}")
    print()
    
    # Validate configuration
    if not PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL']:
        print(" ERROR: PUBLIC_REPO_URL not configured")
        print("   Edit the PUBLIC_REPO_CONFIG section in this file")
        return
    
    if PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL'] == "https://github.com/owner/repo":
        print(" WARNING: Using example URL. Please configure a real repository URL.")
        print("   Edit PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL'] in this file")
        return
    
    try:
        print(" Starting public repository workflow...\n")
        
        crew = create_public_repo_crew()
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
        elif hasattr(result, 'json_dict'):
            report_data = result.json_dict
        elif isinstance(result, dict):
            report_data = result
        else:
            # Extract from pydantic output or raw string
            report_data = {
                "raw_output": str(result),
                "repository_url": PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL'],
                "timestamp": datetime.now().isoformat()
            }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f" Report saved: {report_file}\n")
    
    except Exception as e:
        print(f"\n ERROR: Workflow failed:")
        print(f"   {str(e)}\n")
        
        # Save error report
        error_report = {
            "repository_url": PUBLIC_REPO_CONFIG['PUBLIC_REPO_URL'],
            "validation_status": "error",
            "clone_status": "error",
            "errors": [str(e)],
            "timestamp": datetime.now().isoformat()
        }
        
        report_file = f"reports/workflow_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("reports", exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(error_report, f, indent=2)
        
        print(f" Error report saved: {report_file}\n")
        raise


if __name__ == "__main__":
    main()
