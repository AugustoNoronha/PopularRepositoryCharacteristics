import requests
import os
import time
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TOKEN")

def handle_rate_limit(response, attempt, max_retries):
    """Verifica se há rate limit e calcula tempo de espera"""
    if response.status_code == 403 and "rate limit" in response.text.lower():
        if attempt < max_retries - 1:

            wait_time = 2 ** attempt
            print(f"Rate limit atingido. Aguardando {wait_time} segundos...")
            time.sleep(wait_time)
            return True  
    return False

def make_graphql_request(url, headers, json_data, max_retries=3):
    """Faz requisição GraphQL com retry automático e tratamento de rate limit"""
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=json_data)
            

            if handle_rate_limit(response, attempt, max_retries):
                continue
            
            if response.status_code == 200:
                return response
            

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Erro HTTP {response.status_code}, tentando novamente em {wait_time} segundos...")
                time.sleep(wait_time)
                continue
            else:
                raise Exception(f"Erro HTTP persistente: {response.status_code}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️  Exceção: {e}, tentando novamente em {wait_time} segundos...")
                time.sleep(wait_time)
                continue
            else:
                raise e
    
    raise Exception(f"Falha após {max_retries} tentativas")

def get_top_starred_repos_graphql(max_repos=1000):

    
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    cursor = None
    per_page = 100
    all_repos = []
    
    # Query com paginação para buscar múltiplas páginas
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
    page_count = 0
    
    while len(all_repos) < max_repos:
        page_count += 1
        print(f"Buscando página {page_count}... (repositórios coletados: {len(all_repos)})")
        
        variables = {"cursor": cursor, "perPage": per_page}
        json_data = {"query": query, "variables": variables}
        
        try:
            response = make_graphql_request(url, headers, json_data)
            data = response.json()
            
            if "errors" in data:
                print("ERROS encontrados:")
                for error in data["errors"]:
                    print(f"- {error}")
                    break
                
                search_data = data["data"]["search"]
                page_info = search_data["pageInfo"]
                edges = search_data["edges"]
                
                # Extrair os repositórios desta página
                page_repos = [edge["node"] for edge in edges]
                all_repos.extend(page_repos)
                
                print(f"Página {page_count}: {len(page_repos)} repositórios encontrados")
                
                if not page_info["hasNextPage"]:
                    print("Não há mais páginas disponíveis")
                    break
                
                cursor = page_info["endCursor"]
                
                if len(all_repos) < max_repos:
                    time.sleep(1)
                
        except Exception as e:
            print(f"Erro ao buscar página {page_count}: {e}")
            break
    
    print(f"Total de repositórios coletados: {len(all_repos)}")
    return all_repos[:max_repos]  # Retorna no máximo max_repos


def get_repo_details_graphql(owner, repo_name, token, max_retries=3):
    """Busca detalhes completos de um repositório específico com retry automático"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Query principal com mais campos para issues e PRs
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        stargazerCount
        createdAt
        updatedAt
        pushedAt
        primaryLanguage { name }
        releases { totalCount }
        issues(states: OPEN) { totalCount }
        closedIssues: issues(states: CLOSED) { totalCount }
        totalIssues: issues { totalCount }
        pullRequests(states: MERGED) { totalCount }
        totalPullRequests: pullRequests { totalCount }
        forkCount
        diskUsage
        hasIssuesEnabled
        hasWikiEnabled
        hasProjectsEnabled
        licenseInfo { name }
        defaultBranchRef { name }
        languages(first: 10) {
          edges {
            node { name }
            size
          }
        }
        repositoryTopics(first: 20) {
          nodes {
            topic { name }
          }
        }
      }
    }
    """
    
    try:
        variables = {"owner": owner, "name": repo_name}
        json_data = {"query": query, "variables": variables}
        response = make_graphql_request(url, headers, json_data)
        
        data = response.json()
        if "errors" in data:
            print(f"Erro GraphQL ao buscar {owner}/{repo_name}: {data['errors']}")
            raise Exception(f"Erro GraphQL ao buscar {owner}/{repo_name}: {data['errors']}")
        
        repo_data = data["data"]["repository"]
        
        # Verificar se os dados críticos vieram corretamente
        issues_ok = repo_data.get('issues', {}).get('totalCount') is not None
        closed_issues_ok = repo_data.get('closedIssues', {}).get('totalCount') is not None
        prs_ok = repo_data.get('pullRequests', {}).get('totalCount') is not None
        
        # Se algum dado crítico não veio, tentar query alternativa
        if not all([issues_ok, closed_issues_ok, prs_ok]):
            print(f"Dados incompletos para {owner}/{repo_name}, tentando query alternativa...")
            
            # Query alternativa com paginação para issues e PRs
            alt_query = """
            query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                stargazerCount
                createdAt
                updatedAt
                pushedAt
                primaryLanguage { name }
                releases { totalCount }
                forkCount
                diskUsage
                hasIssuesEnabled
                hasWikiEnabled
                hasProjectsEnabled
                licenseInfo { name }
                defaultBranchRef { name }
                issues(first: 1) { totalCount }
                closedIssues: issues(states: CLOSED, first: 1) { totalCount }
                pullRequests(states: MERGED, first: 1) { totalCount }
                totalPullRequests: pullRequests(first: 1) { totalCount }
                languages(first: 10) {
                  edges {
                    node { name }
                    size
                  }
                }
                repositoryTopics(first: 20) {
                  nodes {
                    topic { name }
                  }
                }
              }
            }
            """
            
            alt_json_data = {"query": alt_query, "variables": variables}
            alt_response = make_graphql_request(url, headers, alt_json_data)
            
            if alt_response.status_code == 200:
                alt_data = alt_response.json()
                if "errors" not in alt_data:
                    repo_data = alt_data["data"]["repository"]
                    print(f"Query alternativa bem-sucedida para {owner}/{repo_name}")
                else:
                    print(f"Query alternativa também falhou para {owner}/{repo_name}")
            else:
                print(f"Query alternativa falhou com status {alt_response.status_code}")
        
        return repo_data
        
    except Exception as e:
        print(f"Erro ao buscar {owner}/{repo_name}: {e}")
        raise e

def get_specific_issues_and_prs(owner, repo_name, token):
    """Query específica para buscar issues e pull requests quando a query principal falhar"""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Query específica para issues e PRs com paginação
    specific_query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        issues(first: 1) { totalCount }
        closedIssues: issues(states: CLOSED, first: 1) { totalCount }
        openIssues: issues(states: OPEN, first: 1) { totalCount }
        pullRequests(states: MERGED, first: 1) { totalCount }
        totalPullRequests: pullRequests(first: 1) { totalCount }
        openPullRequests: pullRequests(states: OPEN, first: 1) { totalCount }
        closedPullRequests: pullRequests(states: CLOSED, first: 1) { totalCount }
      }
    }
    """
    
    try:
        variables = {"owner": owner, "name": repo_name}
        json_data = {"query": specific_query, "variables": variables}
        response = make_graphql_request(url, headers, json_data)
        
        data = response.json()
        if "errors" in data:
            print(f"Erro na query específica para {owner}/{repo_name}: {data['errors']}")
            return None
        
        return data["data"]["repository"]
        
    except Exception as e:
        print(f"Exceção na query específica para {owner}/{repo_name}: {e}")
        return None

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
        repos_with_issues = 0
        repos_with_prs = 0
        
        total_repos = len(basic_repos)
        for i, basic_repo in enumerate(basic_repos, 1):
            owner = basic_repo["owner"]["login"]
            repo_name = basic_repo["name"]
            
            print(f"Buscando detalhes do repositório {i}/{total_repos} ({i/total_repos*100:.1f}%): {owner}/{repo_name}")
            
            try:
                repo = get_repo_details_graphql(owner, repo_name, token)
            except Exception as e:
                print(f"EXCEÇÃO ao buscar {owner}/{repo_name}: {e}")
                continue
            
            if repo is None:
                continue
                
            if not isinstance(repo, dict):
                continue
                
            successful_repos += 1
            if repo is not None:
                print(f"Sucesso para {owner}/{repo_name}, processando dados...")
                
                
                if i < total_repos:
                    print(f"Aguardando 0.5 segundos antes da próxima requisição...")
                    time.sleep(0.5)
                
                issues_count = repo.get('issues', {}).get('totalCount', 0)
                closed_issues_count = repo.get('closedIssues', {}).get('totalCount', 0)
                total_issues_count = repo.get('totalIssues', {}).get('totalCount', 0)
                merged_prs_count = repo.get('pullRequests', {}).get('totalCount', 0)
                total_prs_count = repo.get('totalPullRequests', {}).get('totalCount', 0)
                
                
                if all(count == 0 for count in [issues_count, closed_issues_count, merged_prs_count, total_prs_count]):
                    print(f"Dados de issues/PRs não encontrados para {owner}/{repo_name}, tentando query específica...")
                    specific_data = get_specific_issues_and_prs(owner, repo_name, token)
                    if specific_data:
                        
                        repo.update(specific_data)
                        issues_count = repo.get('issues', {}).get('totalCount', 0)
                        closed_issues_count = repo.get('closedIssues', {}).get('totalCount', 0)
                        total_issues_count = repo.get('totalIssues', {}).get('totalCount', 0)
                        merged_prs_count = repo.get('pullRequests', {}).get('totalCount', 0)
                        total_prs_count = repo.get('totalPullRequests', {}).get('totalCount', 0)
                        print(f"Query específica bem-sucedida para {owner}/{repo_name}")
                
                
                if issues_count > 0 or closed_issues_count > 0:
                    repos_with_issues += 1
                if merged_prs_count > 0 or total_prs_count > 0:
                    repos_with_prs += 1
                
                f.write(f"REPOSITÓRIO {i:03d}: {repo_name}\n")
                f.write(f"Owner: {owner}\n")
                f.write(f"URL: {repo.get('url', 'N/A')}\n")
                f.write(f"Description: {repo.get('description', 'No description')}\n")
                f.write(f"Homepage: {repo.get('homepageUrl', 'N/A')}\n")
                f.write("\n--- MÉTRICAS PARA AS QUESTÕES DE PESQUISA ---\n")
                
                # RQ01: Idade do repositório
                f.write(f"RQ01 - Created At: {repo.get('createdAt', 'N/A')}\n")
                
                # RQ02: Contribuição externa (Pull Requests)
                f.write(f"RQ02_Merged_PRs: {merged_prs_count}\n")
                f.write(f"RQ02_Total_PRs: {total_prs_count}\n")
                
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
                f.write(f"RQ06 - Closed Issues: {closed_issues_count}\n")
                f.write(f"RQ06 - Open Issues: {issues_count}\n")
                f.write(f"RQ06 - Total Issues: {total_issues_count}\n")
                
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
        print(f"Repositórios com issues: {repos_with_issues}")
        print(f"Repositórios com pull requests: {repos_with_prs}")
        
        # Salvar estatísticas em arquivo separado
        stats_filename = filename.replace('.txt', '_stats.txt')
        with open(stats_filename, "w", encoding="utf-8") as stats_f:
            stats_f.write(f"Estatísticas da Coleta de Dados\n")
            stats_f.write(f"Total de repositórios processados: {successful_repos}\n")
            stats_f.write(f"Repositórios com issues: {repos_with_issues}\n")
            stats_f.write(f"Repositórios com pull requests: {repos_with_prs}\n")
            stats_f.write(f"Taxa de sucesso: {(successful_repos/len(basic_repos)*100):.1f}%\n")

def txt_to_csv_with_issues_prs(txt_filename, csv_filename):
    """Converte o arquivo .txt em CSV com colunas específicas incluindo Issues e PRs"""
    import csv
    import re
    
    # Cabeçalhos do CSV
    headers = [
        'Repository', 'Owner', 'URL', 'Stars', 'Forks', 'Watchers', 
        'Last Commit Date', 'Main Language', 'License', 'Size (KB)', 
        'Main Branch', 'Topics', 'Issues', 'Pull Requests'
    ]
    
    with open(txt_filename, 'r', encoding='utf-8') as txt_file, \
         open(csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
        
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        
        content = txt_file.read()
        
        # Dividir por repositórios (separados por =====)
        repos_sections = content.split('=' * 100)
        
        successful_repos = 0
        
        for section in repos_sections:
            if not section.strip() or 'REPOSITÓRIO' not in section:
                continue
                
            try:
                # Extrair informações básicas
                repo_name_match = re.search(r'REPOSITÓRIO \d+: (.+)', section)
                owner_match = re.search(r'Owner: (.+)', section)
                
                if not repo_name_match or not owner_match:
                    continue
                    
                repo_name = repo_name_match.group(1).strip()
                owner = owner_match.group(1).strip()
                
                # Extrair outras informações usando regex
                stars_match = re.search(r'Stars: (\d+)', section)
                forks_match = re.search(r'Forks: (\d+)', section)
                watchers_match = re.search(r'Watchers: (\d+)', section)
                created_match = re.search(r'RQ01 - Created At: (.+)', section)
                updated_match = re.search(r'RQ04 - Last Update: (.+)', section)
                pushed_match = re.search(r'RQ04_Last_Push: (.+)', section)
                language_match = re.search(r'RQ05 - Primary Language: (.+)', section)
                license_match = re.search(r'License: (.+)', section)
                size_match = re.search(r'Size: (\d+) KB', section)
                branch_match = re.search(r'Default Branch: (.+)', section)
                topics_match = re.search(r'Topics: (.+)', section)
                
                # Extrair Issues e PRs
                open_issues_match = re.search(r'RQ06 - Open Issues: (\d+)', section)
                closed_issues_match = re.search(r'RQ06 - Closed Issues: (\d+)', section)
                total_issues_match = re.search(r'RQ06 - Total Issues: (\d+)', section)
                merged_prs_match = re.search(r'RQ02_Merged_PRs: (\d+)', section)
                total_prs_match = re.search(r'RQ02_Total_PRs: (\d+)', section)
                
                # Construir linha do CSV
                row = {
                    'Repository': repo_name,
                    'Owner': owner,
                    'URL': f"https://github.com/{owner}/{repo_name}",
                    'Stars': int(stars_match.group(1)) if stars_match else 0,
                    'Forks': int(forks_match.group(1)) if forks_match else 0,
                    'Watchers': int(watchers_match.group(1)) if watchers_match else 0,
                    'Last Commit Date': pushed_match.group(1) if pushed_match else (updated_match.group(1) if updated_match else 'N/A'),
                    'Main Language': language_match.group(1) if language_match else 'Not specified',
                    'License': license_match.group(1) if license_match else 'No license',
                    'Size (KB)': int(size_match.group(1)) if size_match else 'N/A',
                    'Main Branch': branch_match.group(1) if branch_match else 'N/A',
                    'Topics': topics_match.group(1) if topics_match else '',
                    'Issues': int(total_issues_match.group(1)) if total_issues_match else 0,
                    'Pull Requests': int(total_prs_match.group(1)) if total_prs_match else 0
                }
                
                writer.writerow(row)
                successful_repos += 1
                
            except Exception as e:
                print(f"Erro ao processar seção do repositório: {e}")
                continue
        
        print(f"CSV criado com {successful_repos} repositórios processados")
        print(f"Arquivo salvo: {csv_filename}")

# Main
if __name__ == "__main__":
    print("=== LABORATÓRIO: CARACTERÍSTICAS DE REPOSITÓRIOS POPULARES ===")
    print("Coletando dados dos repositórios mais populares do GitHub...")
    
    # Configurações
    MAX_REPOS = 1000  # Número máximo de repositórios a coletar
    print(f"Configuração: Coletando até {MAX_REPOS} repositórios")
    
    try:
        repos = get_top_starred_repos_graphql(max_repos=MAX_REPOS)
        
        if repos:
            print(f"\nColeta concluída! {len(repos)} repositórios encontrados")
            
           
            
            filename = "lab_popular_repositories.txt"
            collect_and_print_repo_info(repos, filename)
            
            
            csv_filename = "repos_info_with_issues_prs.csv"
            txt_to_csv_with_issues_prs(filename, csv_filename)
            
           
        else:
            print("Nenhum repositório foi coletado")
            
    except Exception as e:
        print(f"Erro: {e}")
        print("\nDicas para resolver problemas:")
        