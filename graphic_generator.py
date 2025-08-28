import pandas as pd
import re
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt

# ===============================
# Leitura e processamento dos dados
# ===============================
repos_data = []

with open('lab_popular_repositories.txt', 'r', encoding='utf-8') as file:
    content = file.read()

repos = content.split('====================================================================================================')

for repo in repos:
    if 'REPOSITÓRIO' in repo:
        name = re.search(r'REPOSITÓRIO \d+: (\S+)', repo)
        created_at = re.search(r'RQ01 - Created At: ([\d\-T:Z]+)', repo)
        merged_prs = re.search(r'RQ02_Merged_PRs: (\d+)', repo)
        total_releases = re.search(r'RQ03_Total_Releases: (\d+)', repo)
        last_update = re.search(r'RQ04 - Last Update: ([\d\-T:Z]+)', repo)
        language = re.search(r'RQ05 - Primary Language: (.+)', repo)
        closed_issues = re.search(r'RQ06 - Closed Issues: (\d+)', repo)
        total_issues = re.search(r'RQ06 - Total Issues: (\d+)', repo)

        closed_percent = 0
        if total_issues and int(total_issues.group(1)) > 0:
            closed_percent = int(closed_issues.group(1)) / int(total_issues.group(1)) * 100
        
        repos_data.append({
            'Name': name.group(1) if name else None,
            'Created_At': datetime.fromisoformat(created_at.group(1).replace('Z','')) if created_at else None,
            'Merged_PRs': int(merged_prs.group(1)) if merged_prs else 0,
            'Total_Releases': int(total_releases.group(1)) if total_releases else 0,
            'Last_Update': datetime.fromisoformat(last_update.group(1).replace('Z','')) if last_update else None,
            'Primary_Language': language.group(1).strip() if language else 'Not specified',
            'Closed_Issues_Percent': closed_percent
        })

df = pd.DataFrame(repos_data)

today = datetime(2025, 8, 27) 
df['Repo_Age_Years'] = (today - df['Created_At']).dt.days / 365
df['Days_Since_Last_Update'] = (today - df['Last_Update']).dt.days

sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (10,6)

# ===============================
# RQ01 - Idade dos repositórios (Histograma)
# ===============================
plt.figure()
sns.histplot(df['Repo_Age_Years'], bins=20, kde=True, color='skyblue')
plt.title('RQ01 - Idade dos Repositórios (Histograma)')
plt.xlabel('Idade (anos)')
plt.ylabel('Quantidade de Repositórios')
plt.show()

# ===============================
# RQ02 - Contribuições externas (Gráfico de Violino)
# ===============================
plt.figure()
sns.violinplot(y=df['Merged_PRs'], color='lightgreen')
plt.title('RQ02 - Distribuição de Pull Requests Aceitas (Violino)')
plt.ylabel('Número de PRs Aceitas')
plt.show()

# ===============================
# RQ03 - Número de Releases (Boxplot)
# ===============================
plt.figure()
sns.boxplot(x=df['Total_Releases'], color='lightcoral')
plt.title('RQ03 - Total de Releases por Repositório (Boxplot)')
plt.xlabel('Total de Releases')
plt.show()

# ===============================
# RQ04 - Dias desde a última atualização (Histograma)
# ===============================
plt.figure()
sns.histplot(df['Days_Since_Last_Update'], bins=30, color='orchid')
plt.title('RQ04 - Dias desde a Última Atualização (Histograma)')
plt.xlabel('Dias')
plt.ylabel('Quantidade de Repositórios')
plt.show()

# ===============================
# RQ05 - Linguagens mais populares (Barplot)
# ===============================
language_counts = df['Primary_Language'].value_counts().head(10)
plt.figure()
sns.barplot(x=language_counts.values, y=language_counts.index, palette="viridis")
plt.title('RQ05 - Top 10 Linguagens em Repositórios Populares (Barplot)')
plt.xlabel('Quantidade de Repositórios')
plt.ylabel('Linguagem')
plt.show()

# ===============================
# RQ06 - Percentual de issues fechadas (Violin plot)
# ===============================
plt.figure()
sns.violinplot(y=df['Closed_Issues_Percent'], color='gold')
plt.title('RQ06 - Percentual de Issues Fechadas (Violino)')
plt.ylabel('% de Issues Fechadas')
plt.show()

# ===============================
# Heatmap de correlação entre métricas numéricas
# ===============================
numeric_cols = ['Repo_Age_Years', 'Merged_PRs', 'Total_Releases', 'Days_Since_Last_Update', 'Closed_Issues_Percent']
corr = df[numeric_cols].corr()

plt.figure(figsize=(8,6))
sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm')
plt.title('Heatmap - Correlação entre Métricas dos Repositórios')
plt.show()

# ===============================
# Estatísticas resumidas
# ===============================
print("===== Estatísticas Resumidas =====")
print("Idade mediana (anos):", df['Repo_Age_Years'].median())
print("PRs aceitas mediana:", df['Merged_PRs'].median())
print("Releases medianas:", df['Total_Releases'].median())
print("Dias desde última atualização mediana:", df['Days_Since_Last_Update'].median())
print("Percentual médio de issues fechadas:", df['Closed_Issues_Percent'].median())
print("Top 10 linguagens:")
print(language_counts)
