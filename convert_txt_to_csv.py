#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para converter o arquivo lab_popular_repositories.txt em CSV
com as colunas especificadas incluindo Issues e Pull Requests
"""

from graphql import txt_to_csv_with_issues_prs

if __name__ == "__main__":
    print("=== CONVERSOR DE TXT PARA CSV ===")
    print("Convertendo lab_popular_repositories.txt para CSV...")
    
    try:
        txt_filename = "lab_popular_repositories.txt"
        csv_filename = "repos_info_with_issues_prs.csv"
        
        txt_to_csv_with_issues_prs(txt_filename, csv_filename)
        
        print(f"\n✅ Conversão concluída!")
        print(f"📁 Arquivo CSV criado: {csv_filename}")
        
    except FileNotFoundError:
        print("Arquivo lab_popular_repositories.txt não encontrado!")
        print("Execute primeiro o script principal para coletar os dados")
    except Exception as e:
        print(f"Erro durante a conversão: {e}")
