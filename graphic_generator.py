import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os
from datetime import datetime

# Criar pasta para gráficos
os.makedirs('graphics', exist_ok=True)

# ===============================
# Leitura do CSV
# ===============================
df = pd.read_csv('repos_info_with_issues_prs.csv')

# Converter data de último commit e remover timezone
df['Last Commit Date'] = pd.to_datetime(df['Last Commit Date'], errors='coerce').dt.tz_localize(None)

# Calcular dias desde último commit
today = datetime(2025, 8, 27)
df['Days_Since_Last_Commit'] = (today - df['Last Commit Date']).dt.days

# ===============================
# Visualizações
# ===============================
sns.set(style="whitegrid")
plt.rcParams['figure.figsize'] = (10,6)

# RQ01 - Dias desde o último commit (Histograma)
plt.figure()
sns.histplot(df['Days_Since_Last_Commit'], bins=30, color='skyblue')
plt.title('RQ01 - Dias desde o Último Commit (Histograma)')
plt.xlabel('Dias desde último commit')
plt.ylabel('Quantidade de Repositórios')
plt.savefig('graphics/RQ01_Dias_Ultimo_Commit.png')
plt.show()

# RQ02 - Pull Requests (Violino)
plt.figure()
sns.violinplot(y=df['Pull Requests'], color='lightgreen')
plt.title('RQ02 - Distribuição de Pull Requests (Violino)')
plt.ylabel('Número de Pull Requests')
plt.savefig('graphics/RQ02_Pull_Requests.png')
plt.show()

# RQ03 - Forks (Boxplot)
plt.figure()
sns.boxplot(x=df['Forks'], color='lightcoral')
plt.title('RQ03 - Total de Forks por Repositório (Boxplot)')
plt.xlabel('Total de Forks')
plt.savefig('graphics/RQ03_Forks.png')
plt.show()

# RQ04 - Dias desde última atualização (Histograma)
plt.figure()
sns.histplot(df['Days_Since_Last_Commit'], bins=30, color='orchid')
plt.title('RQ04 - Dias desde a Última Atualização (Histograma)')
plt.xlabel('Dias desde última atualização')
plt.ylabel('Quantidade de Repositórios')
plt.savefig('graphics/RQ04_Dias_Ultima_Atualizacao.png')
plt.show()

# RQ05 - Linguagens mais populares (Barplot)
language_counts = df['Main Language'].value_counts().head(10)
plt.figure()
sns.barplot(x=language_counts.values, y=language_counts.index, palette="viridis")
plt.title('RQ05 - Top 10 Linguagens em Repositórios Populares (Barplot)')
plt.xlabel('Quantidade de Repositórios')
plt.ylabel('Linguagem')
plt.savefig('graphics/RQ05_Linguagens_Populares.png')
plt.show()

# RQ06 - Issues (Violino)
plt.figure()
sns.violinplot(y=df['Issues'], color='gold')
plt.title('RQ06 - Distribuição de Issues Totais (Violino)')
plt.ylabel('Número de Issues')
plt.savefig('graphics/RQ06_Issues.png')
plt.show()

# Heatmap de correlação (apenas numéricos)
numeric_cols = ['Stars', 'Forks', 'Watchers', 'Issues', 'Pull Requests', 'Days_Since_Last_Commit']
corr = df[numeric_cols].corr()

plt.figure(figsize=(8,6))
sns.heatmap(corr, annot=True, fmt=".2f", cmap='coolwarm')
plt.title('Heatmap - Correlação entre Métricas dos Repositórios')
plt.savefig('graphics/Heatmap_Correlacao.png')
plt.show()

print("===== Estatísticas Resumidas =====")
print("Dias desde último commit (mediana):", df['Days_Since_Last_Commit'].median())
print("Pull Requests (mediana):", df['Pull Requests'].median())
print("Forks (mediana):", df['Forks'].median())
print("Issues (mediana):", df['Issues'].median())
print("Top 10 linguagens:")
print(language_counts)
