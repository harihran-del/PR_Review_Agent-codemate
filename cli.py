import argparse
import json
from pr_reviewer import analyze_pr

def main():
    parser = argparse.ArgumentParser(description='PR Review Agent')
    parser.add_argument('pr_url', help='PR URL to analyze')
    parser.add_argument('--output', '-o', choices=['json', 'text'], default='text')
    parser.add_argument('--provider', choices=['github', 'gitlab', 'bitbucket'])
    
    args = parser.parse_args()
    
    result = analyze_pr(args.pr_url)
    
    if args.output == 'json':
        print(json.dumps(result, indent=2))
    else:
        # Format text output
        pass
        
    # Exit with error code if issues found
    exit(1 if result.get('issues', 0) > 0 else 0)

if __name__ == '__main__':
    main()