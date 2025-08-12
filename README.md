# PopularRepositoryCharacteristics

## Relatório do Laboratório: Características de Repositórios Populares do GitHub

### Visão Geral do Projeto

Este laboratório foi desenvolvido para analisar as características dos repositórios mais populares do GitHub, coletando dados que respondem a seis questões de pesquisa (RQs) específicas sobre a qualidade e atividade dos projetos open source.

### Evolução da Implementação

#### Fase 1: Implementação com API REST (Resultados Insatisfatórios)

**Problemas Identificados:**
- **Performance Extremamente Lenta**: A implementação inicial usando a API REST do GitHub (`main.py`) apresentou tempos de resposta muito elevados
- **Múltiplas Chamadas HTTP**: Para cada repositório, eram necessárias múltiplas requisições separadas:
  - Busca básica do repositório
  - Detalhes completos
  - Pull requests (com paginação)
  - Releases (com paginação)
  - Issues fechadas (com paginação)
- **Rate Limiting**: Limitações da API REST resultaram em delays significativos entre requisições
- **Complexidade de Paginação**: Implementação manual de paginação para cada endpoint, aumentando a complexidade do código

**Código Problemático Identificado:**
```python
# Exemplo de múltiplas chamadas necessárias para um repositório
repo_details = get_repo_details(owner, repo_name)
pull_requests = get_pull_requests(owner, repo_name)  # Requisições paginadas
releases = get_releases(owner, repo_name)            # Requisições paginadas
closed_issues = get_closed_issues(owner, repo_name)  # Requisições paginadas
```

#### Fase 2: Migração para GraphQL (Melhoria Significativa)

**Benefícios Alcançados:**
- **Redução Drástica de Requisições**: Uma única query GraphQL retorna todos os dados necessários
- **Performance Superior**: Tempo de coleta reduzido de horas para minutos
- **Dados Mais Consistentes**: Estrutura unificada de resposta
- **Menor Complexidade**: Eliminação da necessidade de gerenciar múltiplas chamadas e paginação

**Implementação GraphQL:**
```python
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
```

### Desafios Enfrentados

#### 1. Inconsistência dos Servidores GitHub
- **Erros 502**: Ocorrências frequentes de "Bad Gateway" durante a coleta
- **Instabilidade de Resposta**: Servidores retornando dados incompletos ou inconsistentes
- **Timeouts**: Interrupções na comunicação com a API

#### 2. Dados Incompletos na Primeira Tentativa
- **Campos Nulos**: Alguns repositórios retornavam campos essenciais como `null`
- **Informações Ausentes**: Dados como `forkCount`, `watcherCount` e `licenseInfo` não estavam disponíveis imediatamente
- **Estrutura de Resposta Variável**: Diferentes repositórios retornavam estruturas ligeiramente diferentes

#### 3. Tratamento de Erros e Resiliência
- **Implementação de Retry Logic**: Necessidade de reintentar requisições falhadas
- **Validação de Dados**: Verificação de integridade dos dados recebidos
- **Fallbacks**: Estratégias alternativas quando dados primários não estavam disponíveis

### Soluções Implementadas

#### 1. Sistema de Tratamento de Erros Robusto
```python
try:
    repo = get_repo_details_graphql(owner, repo_name, token)
except Exception as e:
    print(f"⚠️  EXCEÇÃO ao buscar {owner}/{repo_name}: {e}")
    continue
```

#### 2. Validação de Dados
```python
if repo is None or not isinstance(repo, dict):
    continue
```

#### 3. Coleta Seletiva de Dados
- Foco nas métricas essenciais para as RQs
- Coleta de dados secundários quando disponíveis
- Estrutura flexível para acomodar variações na API

### Métricas Coletadas para Análise

#### Questões de Pesquisa (RQs):
- **RQ01**: Idade do repositório (`createdAt`)
- **RQ02**: Contribuição externa (`pullRequests` merged vs total)
- **RQ03**: Frequência de releases (`releases.totalCount`)
- **RQ04**: Atividade recente (`updatedAt`, `pushedAt`)
- **RQ05**: Linguagem primária (`primaryLanguage.name`)
- **RQ06**: Gestão de issues (`closedIssues` vs `openIssues`)

#### Métricas de Popularidade:
- Stars (`stargazerCount`)
- Forks (`forkCount`)
- Watchers (`watcherCount`)

### Resultados Alcançados

#### Antes (API REST):
- Tempo de coleta: **Horas**
- Complexidade: **Alta**
- Confiabilidade: **Baixa**
- Dados coletados: **Limitados**

#### Depois (GraphQL):
- Tempo de coleta: **Minutos**
- Complexidade: **Baixa**
- Confiabilidade: **Alta**
- Dados coletados: **Completos**

### Arquivos de Saída

1. **`lab_popular_repositories.txt`**: Dados completos coletados via GraphQL (2.873 linhas)
2. **`repos_info.txt`**: Dados básicos coletados via API REST (limitado)
3. **`output.txt`**: Log de execução

### Lições Aprendidas

#### 1. Escolha da Tecnologia
- **GraphQL** é significativamente superior para coleta de dados complexos
- **API REST** pode ser adequada para consultas simples, mas não para análises abrangentes

#### 2. Desafios de APIs de Terceiros
- **Instabilidade de Servidores**: Necessidade de implementar estratégias de resiliência
- **Rate Limiting**: Planejamento adequado de limites de requisição
- **Inconsistência de Dados**: Validação e tratamento de dados incompletos

#### 3. Arquitetura de Coleta
- **Single Query vs Multiple Queries**: Impacto significativo na performance
- **Tratamento de Erros**: Necessidade de estratégias robustas de fallback
- **Validação de Dados**: Verificação de integridade antes do processamento

### Conclusões

Este laboratório demonstrou claramente os desafios e soluções na captação de dados de terceiros, especialmente em APIs complexas como a do GitHub. A migração de REST para GraphQL resultou em uma melhoria dramática na performance e confiabilidade, evidenciando a importância da escolha adequada de tecnologias para diferentes cenários de uso.

Os problemas enfrentados com inconsistências de servidores e dados incompletos são comuns em sistemas distribuídos e destacam a necessidade de implementar estratégias robustas de tratamento de erros e validação de dados em projetos de coleta de dados em larga escala.

### Tecnologias Utilizadas

- **Python 3.x**
- **GitHub GraphQL API**
- **GitHub REST API**
- **Requests library**
- **Environment variables para tokens**

### Como Executar

1. Configure o token do GitHub em um arquivo `.env`:
   ```
   TOKEN=seu_token_aqui
   ```

2. Execute a versão GraphQL (recomendada):
   ```bash
   python graphql.py
   ```

3. Execute a versão REST (para comparação):
   ```bash
   python main.py
   ```

### Estrutura do Projeto

```
PopularRepositoryCharacteristics/
├── main.py                      # Implementação REST (descontinuada)
├── graphql.py                   # Implementação GraphQL (atual)
├── lab_popular_repositories.txt # Dados completos coletados
├── repos_info.txt              # Dados básicos REST
├── output.txt                  # Log de execução
└── README.md                   # Este arquivo
```
