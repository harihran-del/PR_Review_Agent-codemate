class GitProvider:
    def get_pr_details(self, pr_url):
        raise NotImplementedError

class GitHubProvider(GitProvider):
    def get_pr_details(self, pr_url):
        # Your existing GitHub code here
        pass

class GitLabProvider(GitProvider):
    def get_pr_details(self, pr_url):
        # Extract project ID, merge request ID from GitLab URL
        # Use GitLab API: https://gitlab.com/api/v4/projects/{id}/merge_requests/{mr_iid}
        pass

class BitbucketProvider(GitProvider):
    def get_pr_details(self, pr_url):
        # Extract workspace, repo, PR ID from Bitbucket URL  
        # Use Bitbucket API: https://api.bitbucket.org/2.0/repositories/{workspace}/{repo}/pullrequests/{pr_id}
        pass

def get_git_provider(pr_url):
    if 'github.com' in pr_url:
        return GitHubProvider()
    elif 'gitlab.com' in pr_url:
        return GitLabProvider()
    elif 'bitbucket.org' in pr_url:
        return BitbucketProvider()
    else:
        raise ValueError("Unsupported git provider")