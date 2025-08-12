import requests

token = "token"


def get_top_starred_repos(num_repos):
    url = f"https://api.github.com/search/repositories?q=stars:>0&sort=stars&order=desc&per_page={num_repos}"
    headers = {"Authorization": f"token {token}"}  # use seu token aqui
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        raise Exception(f"Failed to fetch repositories: {response.status_code}")

# Função para obter os repositórios mais populares com a palavra-chave "microservices"
def get_popular_repos(keyword, num_repos):
    url = f"https://api.github.com/search/repositories?q={keyword}&sort=stars&order=desc&per_page={num_repos}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["items"]
    else:
        raise Exception(f"Failed to fetch repositories: {response.status_code}")

# Função para obter detalhes de um repositório
def get_repo_details(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch repository details: {response.status_code}")

# Função para obter o número de pull requests com paginação
def get_pull_requests(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all"
    headers = {"Authorization": f"token {token}"}
    page = 1
    pull_requests = []
    while True:
        print("entrou while get_pull page: "+ str(page))
        response = requests.get(f"{url}&page={page}&per_page=100", headers=headers)
        if response.status_code == 200:
            page_pull_requests = response.json()
            if not page_pull_requests:
                print("caiu no break get_pull")
                break
            pull_requests.extend(page_pull_requests)
            page += 1
        else:
            raise Exception(f"Failed to fetch pull requests: {response.status_code}")
    return len(pull_requests)

# Função para obter o número de releases com paginação
def get_releases(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    headers = {"Authorization": f"token {token}"}
    page = 1
    releases = []
    while True:
        print("entrou while get_release")
        response = requests.get(f"{url}?page={page}&per_page=100", headers=headers)
        if response.status_code == 200:
            page_releases = response.json()
            if not page_releases:
                print("caiu no break get_release")
                break
            releases.extend(page_releases)
            page += 1
        else:
            raise Exception(f"Failed to fetch releases: {response.status_code}")
    return len(releases)

# Função para obter o número de issues fechadas com paginação
def get_closed_issues(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/issues?state=closed"
    headers = {"Authorization": f"token {token}"}
    page = 1
    closed_issues = []
    while True:
        print("entrou while get_closed")
        response = requests.get(f"{url}&page={page}&per_page=100", headers=headers)
        if response.status_code == 200:
            page_closed_issues = response.json()
            if not page_closed_issues:
                print("caiu no break get_closed")
                break
            closed_issues.extend(page_closed_issues)
            page += 1
        else:
            raise Exception(f"Failed to fetch closed issues: {response.status_code}")
    return len(closed_issues)

# Função para coletar e imprimir informações dos repositórios
def collect_and_print_repo_info(repos, filename="repos_info.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        for repo in repos:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]
            repo_details = get_repo_details(owner, repo_name)
            
            #pull_requests = get_pull_requests(owner, repo_name)
            #releases = get_releases(owner, repo_name)
            #closed_issues = get_closed_issues(owner, repo_name)

            f.write(f"Repository: {repo_name}\n")
            f.write(f"Owner: {owner}\n")
            f.write(f"URL: {repo_details['html_url']}\n")
            f.write(f"Stars: {repo_details['stargazers_count']}\n")
            f.write(f"Forks: {repo_details['forks_count']}\n")
            f.write(f"Commits: {repo_details['open_issues_count']}\n")
            f.write(f"Watchers: {repo_details['watchers_count']}\n")
            #f.write(f"Pull Requests: {pull_requests if pull_requests is not None else 'N/A'}\n")
            f.write(f"Last Commit Date: {repo_details['pushed_at']}\n")
            f.write(f"Main Language: {repo_details['language']}\n")
            f.write(f"License: {repo_details['license']['name'] if repo_details['license'] else 'No license'}\n")
            f.write(f"Size: {repo_details['size']} KB\n")
            f.write(f"Main Branch: {repo_details['default_branch']}\n")
            #f.write(f"Releases: {releases if releases is not None else 'N/A'}\n")
            #f.write(f"Closed Issues: {closed_issues if closed_issues is not None else 'N/A'}\n")
            f.write(f"Topics: {', '.join(repo_details['topics']) if 'topics' in repo_details else 'No topics'}\n")
            f.write("-" * 100 + "\n")

# Main
if __name__ == "__main__":
    keyword = "microservices"
    print("rodando")
    num_repos = 100  # Número de repositórios a serem coletados
    try:
        repos = get_top_starred_repos(num_repos)
        collect_and_print_repo_info(repos)
        print("Dados salvos em repos_info.txt")
    except Exception as e:
        print(e)