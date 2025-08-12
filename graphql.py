import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")

def get_top_starred_repos_graphql():
    print("estou rodando")
    print(f"Token: {token[:10]}..." if token else "Token vazio!")
    
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    cursor = None
    per_page = 100
    # Query SIMPLES - apenas repositórios mais populares (básico)
    query = """
    query($cursor: String, $perPage: Int!) {
          search(query: "stars:>1 sort:stars-desc is:public", type: REPOSITORY, first: $perPage, after: $cursor) {
            pageInfo { endCursor hasNextPage }
            edges {
              node {
                ... on Repository {
                  name
                  owner { login }
                }
              }
            }
          }
        }
        
    """
    variables = {"cursor": cursor, "perPage": per_page}
    json_data = {"query": query, "variables": variables}
    response = requests.post(url, headers=headers, json=json_data)

    if response.status_code == 200:
        data = response.json()
        print("Resposta completa da API:")
        print(data)
        
        # Verificar se há erros na resposta
        if "errors" in data:
            print("ERROS encontrados:")
            for error in data["errors"]:
                print(f"- {error}")
            return []
      
        # Extrair os nodes dos edges
        repos = [edge["node"] for edge in data["data"]["search"]["edges"]]
        print(f"Encontrados {len(repos)} repositórios")
        return repos
        
        
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")


def get_repo_details_graphql(owner, repo_name, token):
    """Busca detalhes completos de um repositório específico"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        stargazerCount
        createdAt
        updatedAt
        primaryLanguage { name }
        releases { totalCount }
        issues(states: OPEN) { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
        pullRequests(states: MERGED) { totalCount }
      }
    }
    """
    
    variables = {"owner": owner, "name": repo_name}
    json_data = {"query": query, "variables": variables}
    response = requests.post(url, headers=headers, json=json_data)
    
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"Erro ao buscar {owner}/{repo_name}: {data['errors']}")
            raise Exception(f"Erro ao buscar {owner}/{repo_name}: {data['errors']}")
        return data["data"]["repository"]
    else:
        print(f"Erro HTTP ao buscar {owner}/{repo_name}: {response.status_code}")
        raise Exception(f"Erro HTTP ao buscar {owner}/{repo_name}: {response.status_code}")

# Função para coletar e salvar dados para análise do laboratório
def collect_and_print_repo_info(basic_repos, filename):
    """
    Recebe lista básica de repositórios e busca detalhes completos de cada um
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Análise de Repositórios Populares do GitHub\n")
        f.write("# Dados coletados para responder às Questões de Pesquisa (RQs)\n")
        f.write("=" * 100 + "\n\n")
        
        successful_repos = 0
        
        for i, basic_repo in enumerate(basic_repos, 1):
            owner = basic_repo["owner"]["login"]
            repo_name = basic_repo["name"]
            
            print(f"Buscando detalhes do repositório {i}/{len(basic_repos)}: {owner}/{repo_name}")
            
            try:
                repo = get_repo_details_graphql(owner, repo_name, token)
            except Exception as e:
                print(f"⚠️  EXCEÇÃO ao buscar {owner}/{repo_name}: {e}")
                continue
            
            if repo is None:
                continue
                
            if not isinstance(repo, dict):
                continue
                
            successful_repos += 1
            if repo is not None:
                print(f"✅ Sucesso para {owner}/{repo_name}, processando dados...")
                
                f.write(f"REPOSITÓRIO {i:03d}: {repo_name}\n")
                f.write(f"Owner: {owner}\n")
                f.write(f"URL: {repo.get('url', 'N/A')}\n")
                f.write(f"Description: {repo.get('description', 'No description')}\n")
                f.write(f"Homepage: {repo.get('homepageUrl', 'N/A')}\n")
                f.write("\n--- MÉTRICAS PARA AS QUESTÕES DE PESQUISA ---\n")
                
                # RQ01: Idade do repositório
                f.write(f"RQ01 - Created At: {repo.get('createdAt', 'N/A')}\n")
                
                # RQ02: Contribuição externa (Pull Requests)
                merged_prs = repo.get('pullRequests', {}).get('totalCount', 0)
                total_prs = repo.get('totalPullRequests', {}).get('totalCount', 0)
                f.write(f"RQ02_Merged_PRs: {merged_prs}\n")
                f.write(f"RQ02_Total_PRs: {total_prs}\n")
                
                # RQ03: Releases
                releases = repo.get('releases', {}).get('totalCount', 0)
                f.write(f"RQ03_Total_Releases: {releases}\n")
                
                # RQ04: Última atualização
                f.write(f"RQ04_Last_Push: {repo.get('pushedAt', 'N/A')}\n")
                f.write(f"RQ04 - Last Update: {repo.get('updatedAt', 'N/A')}\n")
                
                # RQ05: Linguagem primária
                primary_lang_obj = repo.get('primaryLanguage')
                primary_lang = primary_lang_obj.get('name', 'Not specified') if primary_lang_obj else 'Not specified'
                f.write(f"RQ05 - Primary Language: {primary_lang}\n")
                
                # RQ06: Issues fechadas vs total
                closed_issues = repo.get('closedIssues', {}).get('totalCount', 0)
                total_issues = repo.get('totalIssues', {}).get('totalCount', 0)
                open_issues = repo.get('openIssues', {}).get('totalCount', 0)
                f.write(f"RQ06 - Closed Issues: {closed_issues}\n")
                f.write(f"RQ06 - Open Issues: {open_issues}\n")
                f.write(f"RQ06 - Total Issues: {total_issues}\n")
                
                # Métricas de popularidade
                f.write("\n--- MÉTRICAS DE POPULARIDADE ---\n")
                f.write(f"Stars: {repo.get('stargazerCount', 0)}\n")
                f.write(f"Forks: {repo.get('forkCount', 0)}\n")
                watcher_obj = repo.get('watcherCount')
                watchers = watcher_obj.get('totalCount', 0) if watcher_obj else 0
                f.write(f"Watchers: {watchers}\n")
                
                                 # Informações adicionais
                f.write("\n--- INFORMAÇÕES ADICIONAIS ---\n")
                license_obj = repo.get('licenseInfo')
                license_name = license_obj.get('name', 'No license') if license_obj else 'No license'
                f.write(f"License: {license_name}\n")
                f.write(f"Size: {repo.get('diskUsage', 'N/A')} KB\n")
                branch_obj = repo.get('defaultBranchRef')
                default_branch = branch_obj.get('name', 'N/A') if branch_obj else 'N/A'
                
                f.write(f"Default Branch: {default_branch}\n")
                
                # Linguagens utilizadas
                if repo.get('languages', {}).get('edges'):
                    langs = [f"{edge['node']['name']} ({edge['size']} bytes)" for edge in repo['languages']['edges']]
                    f.write(f"Languages: {', '.join(langs)}\n")
                
                # Tópicos
                if repo.get('repositoryTopics', {}).get('nodes'):
                    topics = [topic_node['topic']['name'] for topic_node in repo['repositoryTopics']['nodes']]
                    f.write(f"Topics: {', '.join(topics)}\n")
                
                # Configurações
                f.write(f"Has Issues: {repo.get('hasIssuesEnabled', 'N/A')}\n")
                f.write(f"Has Wiki: {repo.get('hasWikiEnabled', 'N/A')}\n")
                f.write(f"Has Projects: {repo.get('hasProjectsEnabled', 'N/A')}\n")
                
                f.write("\n" + "=" * 100 + "\n\n")
            
        print(f"\nProcessados {successful_repos}/{len(basic_repos)} repositórios com sucesso")

# Main
if __name__ == "__main__":
    print("=== LABORATÓRIO: CARACTERÍSTICAS DE REPOSITÓRIOS POPULARES ===")
    print("Coletando dados dos repositórios mais populares do GitHub...")
    
    # Começar com teste pequeno, depois aumentar para 100/1000
    try:
        repos = get_top_starred_repos_graphql()
        
        if repos:
            filename = "lab_popular_repositories.txt"
            collect_and_print_repo_info(repos, filename)
            
            
        else:
            print("Nenhum repositório foi coletado")
            
    except Exception as e:
        print(f"Erro: {e}")