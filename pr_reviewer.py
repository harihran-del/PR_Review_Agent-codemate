import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN', '')  # Optional for public repos
BITBUCKET_USER = os.getenv('BITBUCKET_USER', '')
BITBUCKET_TOKEN = os.getenv('BITBUCKET_TOKEN', '')

def detect_git_provider(pr_url):
    """Detect which git provider the PR URL belongs to."""
    if 'github.com' in pr_url:
        return 'github'
    elif 'gitlab.com' in pr_url:
        return 'gitlab'
    elif 'bitbucket.org' in pr_url:
        return 'bitbucket'
    else:
        raise ValueError(f"Unsupported git provider in URL: {pr_url}")

def get_github_pr_details(pr_url):
    """Fetch PR details from GitHub."""
    headers = {'Authorization': f'token {GITHUB_TOKEN}'} if GITHUB_TOKEN else {}
    
    parts = pr_url.rstrip('/').split('/')
    owner = parts[-4]
    repo = parts[-3]
    pull_number = parts[-1]

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    response = requests.get(api_url, headers=headers)
    
    if response.status_code != 200:
        error_msg = response.json().get('message', 'Unknown error')
        raise Exception(f"GitHub API error ({response.status_code}): {error_msg}")
    
    pr_data = response.json()

    if 'diff_url' not in pr_data:
        raise Exception("PR not found or inaccessible.")

    diff_url = pr_data['diff_url']
    diff_response = requests.get(diff_url, headers=headers)
    
    if diff_response.status_code != 200:
        raise Exception(f"Failed to fetch diff: {diff_response.status_code}")
        
    return {
        'title': pr_data['title'],
        'body': pr_data['body'] or "No description provided",
        'diff': diff_response.text,
        'changed_files': pr_data['changed_files'],
        'provider': 'github'
    }

def get_gitlab_pr_details(pr_url):
    """Fetch PR details from GitLab."""
    headers = {}
    if GITLAB_TOKEN:
        headers['Authorization'] = f'Bearer {GITLAB_TOKEN}'
    
    # GitLab URL pattern: https://gitlab.com/owner/repo/-/merge_requests/123
    pattern = r'https://gitlab\.com/([^/]+)/([^/]+)/-/merge_requests/(\d+)'
    match = re.match(pattern, pr_url)
    
    if not match:
        raise ValueError("Invalid GitLab merge request URL format")
    
    owner, repo, mr_iid = match.groups()
    api_url = f"https://gitlab.com/api/v4/projects/{owner}%2F{repo}/merge_requests/{mr_iid}"
    
    response = requests.get(api_url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"GitLab API error ({response.status_code}): {response.text}")
    
    pr_data = response.json()
    
    # Get diff from GitLab
    diff_url = f"{api_url}/changes"
    diff_response = requests.get(diff_url, headers=headers)
    
    if diff_response.status_code != 200:
        raise Exception(f"Failed to fetch diff: {diff_response.status_code}")
    
    changes = diff_response.json().get('changes', [])
    diff_text = "\n".join([change.get('diff', '') for change in changes])
    
    return {
        'title': pr_data.get('title', ''),
        'body': pr_data.get('description', 'No description provided'),
        'diff': diff_text,
        'changed_files': len(changes),
        'provider': 'gitlab'
    }

def get_bitbucket_pr_details(pr_url):
    """Fetch PR details from Bitbucket."""
    headers = {}
    if BITBUCKET_USER and BITBUCKET_TOKEN:
        auth = (BITBUCKET_USER, BITBUCKET_TOKEN)
    else:
        auth = None
    
    # Bitbucket URL pattern: https://bitbucket.org/owner/repo/pull-requests/123
    pattern = r'https://bitbucket\.org/([^/]+)/([^/]+)/pull-requests/(\d+)'
    match = re.match(pattern, pr_url)
    
    if not match:
        raise ValueError("Invalid Bitbucket pull request URL format")
    
    owner, repo, pr_id = match.groups()
    api_url = f"https://api.bitbucket.org/2.0/repositories/{owner}/{repo}/pullrequests/{pr_id}"
    
    response = requests.get(api_url, auth=auth, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Bitbucket API error ({response.status_code}): {response.text}")
    
    pr_data = response.json()
    
    # Get diff from Bitbucket
    diff_url = f"{api_url}/diff"
    diff_response = requests.get(diff_url, auth=auth, headers=headers)
    
    if diff_response.status_code != 200:
        raise Exception(f"Failed to fetch diff: {diff_response.status_code}")
    
    return {
        'title': pr_data.get('title', ''),
        'body': pr_data.get('description', {}).get('raw', 'No description provided'),
        'diff': diff_response.text,
        'changed_files': len(pr_data.get('participants', [])),  # Approximate
        'provider': 'bitbucket'
    }

def get_pr_details(pr_url):
    """
    Extracts PR details from any supported git server.
    """
    provider = detect_git_provider(pr_url)
    
    try:
        if provider == 'github':
            return get_github_pr_details(pr_url)
        elif provider == 'gitlab':
            return get_gitlab_pr_details(pr_url)
        elif provider == 'bitbucket':
            return get_bitbucket_pr_details(pr_url)
    except Exception as e:
        raise Exception(f"Failed to fetch PR details from {provider}: {str(e)}")

def generate_ai_review(pr_details):
    """
    Uses a structured prompt and an AI model (conceptually via CodeMate)
    to analyze the PR diff and generate feedback.
    """
    prompt = f"""
    ACT like an expert senior software engineer performing a code review on a GitHub Pull Request.

    TASK: Review the following code changes and provide constructive, actionable feedback.

    GUIDELINES:
    1.  Focus on code structure, readability, and adherence to Python PEP standards.
    2.  Identify potential bugs, logical errors, or edge cases the author may have missed.
    3.  Suggest improvements for performance, security, or scalability if applicable.
    4.  Be professional and helpful. Frame feedback as suggestions, not commands.

    PULL REQUEST TITLE: {pr_details['title']}
    PULL REQUEST DESCRIPTION: {pr_details['body']}

    CODE DIFF (UNIFIED FORMAT):
    ```diff
    {pr_details['diff']}
    ```

    OUTPUT FORMAT:

    Provide inline review comments in this format:
    FILE: filename.js
    LINE: 42
    COMMENT: Suggestion to improve this function
    SUGGESTION: Consider using const instead of let

    FILE: anotherfile.py  
    LINE: 15
    COMMENT: Potential bug here
    SUGGESTION: Add null check before accessing property

    Also provide an overall summary and quality score:

    - **Overall Summary:** [1-2 sentence summary of the changes and overall quality]
    - **Potential Issues:** [Bullet list of bugs, anti-patterns, or concerns]
    - **Suggestions for Improvement:** [Bullet list of specific, actionable suggestions]
    - **Positive Feedback:** [What was done well?]

    Also provide a quality score from 0-100 based on:
    - Code quality (40%)
    - Testing (20%) 
    - Documentation (15%)
    - Security (15%)
    - Performance (10%)

    SCORE: 85/100

    Now, provide the review:
    """

    print("=== COPY THE PROMPT BELOW INTO CODEMATE CHAT ===")
    print(prompt)
    print("=== AFTER GETTING THE RESPONSE FROM CODEMATE ===")
    print("=== Save the response to a file named 'ai_response.txt' in this folder ===")
    print("=== Then press Enter to continue ===")
    
    # Wait for user to save the file
    input()

    try:
        with open('ai_response.txt', 'r', encoding='utf-8') as f:
            ai_response = f.read()
        
        # Clean up the file
        os.remove('ai_response.txt')
        
        return ai_response
    except FileNotFoundError:
        return "AI response file not found. Please make sure to save the response as 'ai_response.txt'"

# --- CLI Interface for CI/CD ---
def run_cli():
    """Command line interface for CI/CD integration."""
    import argparse
    import json
    import sys
    
    parser = argparse.ArgumentParser(description='AI PR Review Agent')
    parser.add_argument('pr_url', help='GitHub/GitLab/Bitbucket PR URL')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        print(f"🔍 Analyzing PR: {args.pr_url}", file=sys.stderr)
        pr_details = get_pr_details(args.pr_url)
        print(f"✅ Fetched PR details from {pr_details['provider']}", file=sys.stderr)
        
        print("🤖 Generating AI review...", file=sys.stderr)
        review = generate_ai_review(pr_details)
        
        result = {
            'pr_url': args.pr_url,
            'provider': pr_details['provider'],
            'title': pr_details['title'],
            'review': review,
            'changed_files': pr_details['changed_files']
        }
        
        if args.format == 'json':
            output = json.dumps(result, indent=2)
        else:
            output = review
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"💾 Output saved to {args.output}", file=sys.stderr)
        else:
            print(output)
            
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

# --- ADVANCED PATH (If you have time) ---
# If you configure CodeMate Build to provide an API endpoint for code review,
# you could potentially automate this. Check the CodeMate documentation for this possibility.
# response = requests.post('CODEMATE_API_ENDPOINT', json={'prompt': prompt})
# return response.json()['feedback']

if __name__ == '__main__':
    # Run as CLI tool when executed directly
    run_cli()