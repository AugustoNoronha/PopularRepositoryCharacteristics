import requests
import csv
import time
import urllib3

token = "token" 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_top_starred_repos_paginated(num_repos):
   
    all_repos = []
    per_page = 100
    num_pages = (num_repos + per_page - 1) // per_page

    for page in range(1, num_pages + 1):
        url = f"https://api.github.com/search/repositories?q=stars:>0&sort=stars&order=desc&per_page={per_page}&page={page}"
        headers = {"Authorization": f"token {token}"}
        
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()  
            
            repos = response.json().get("items", [])
            all_repos.extend(repos)

            print(f"Página {page} de {num_pages} processada. Repositórios coletados: {len(all_repos)}")
            time.sleep(1) 
        
        except requests.exceptions.RequestException as e:
            print(f"Erro ao buscar repositórios na página {page}: {e}")
            break
    
    return all_repos


def get_repo_details(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {"Authorization": f"token {token}"}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar detalhes do repositório {owner}/{repo}: {e}")
        return None


def collect_and_save_repo_info_to_csv(repos, filename="repos_info.csv"):
    if not repos:
        print("Nenhum repositório para salvar.")
        return

    headers = [
        "Repository", "Owner", "URL", "Stars", "Forks", "Watchers",
        "Last Commit Date", "Main Language", "License", "Size (KB)",
        "Main Branch", "Topics"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        
        for i, repo in enumerate(repos):
            owner = repo.get("owner", {}).get("login")
            repo_name = repo.get("name")
            
            if not owner or not repo_name:
                continue

            repo_details = get_repo_details(owner, repo_name)
            
            if repo_details:
                license_name = "Sem licença"
                license_data = repo_details.get("license")
                if license_data and isinstance(license_data, dict):
                    license_name = license_data.get("name", "Sem licença")
                
                topics_list = repo_details.get("topics", [])
                topics_str = ", ".join(topics_list)

                row = {
                    "Repository": repo_details.get("name", "N/A"),
                    "Owner": repo_details.get("owner", {}).get("login", "N/A"),
                    "URL": repo_details.get("html_url", "N/A"),
                    "Stars": repo_details.get("stargazers_count", "N/A"),
                    "Forks": repo_details.get("forks_count", "N/A"),
                    "Watchers": repo_details.get("watchers_count", "N/A"),
                    "Last Commit Date": repo_details.get("pushed_at", "N/A"),
                    "Main Language": repo_details.get("language", "N/A"),
                    "License": license_name,
                    "Size (KB)": repo_details.get("size", "N/A"),
                    "Main Branch": repo_details.get("default_branch", "N/A"),
                    "Topics": topics_str
                }
                writer.writerow(row)
                print(f"Salvando {i+1}/{len(repos)}: {repo_name}")
                time.sleep(1)


if __name__ == "__main__":
    num_repos_to_collect = 1000
    print(f"Iniciando a coleta dos {num_repos_to_collect} repositórios mais populares...")
    
    repos = get_top_starred_repos_paginated(num_repos_to_collect)
    
    print(f"Coletados {len(repos)} repositórios. Salvando em arquivo CSV...")
    collect_and_save_repo_info_to_csv(repos)
    print("Dados salvos em repos_info.csv")
