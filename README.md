## SalesPy
# Utilização Básica / Quickstart

Está é uma biblioteca inicialmente destinada a Analistas/Cientistas de Dados (meu caso ![grinning-face_1f600](https://github.com/thegabrielbee/SalesPy/assets/96505027/da2b808e-74ee-4743-9401-7f20520ad59d)
) que desejam realizar Análises e/ou manipulações no Banco de Dados de sua ORG. * E limitante a isto!

Devido a necessidades expostas em comunidades de Salesforce e em que eu mesmo passei ou passo nos meus dias de trabalho. Irei ampliar esta biblioteca para que sejam possíveis a realizações dos seguintes tópicos:

- Manipulação de Metadados (Usuários, Perfis, Papéis, Documentação de Código e Flows)
- Migração de Metadados entre ORGs
- Migrações de Dados entre ORGs
- E qualquer outra solução que passe pela minha cabeça ou me seja solicitada


 # HORA DO CÓDIGO!!

Primeiramente você vai precisar clonar o repositório. Portanto, vá até o diretório que seja mais adequado à você e digite comando no teminal:
```bash
 git clone https://github.com/thegabrielbee/SalesPy.git
```

Pronto! Agora iremos importar a biblioteca dentro do python

### Importando a Biblioteca
```python
import sys

# O DIRETÓRIO/PATH PODE SER RELATIVO (~/SalesPy/Main) OU ABSOLUTO (/home/SalesPy/Main)
# FICA A SEU CARGO E FORMA DE USO DECIDIR COMO IMPORTAR 
diretorio = "SalesPy/Main"
sys.path.append(path)

# IREI UTILIZAR COMO NOMENCLARUTA PADRÃO sfpy
import salespy as sfpy

# BIBLIOTECA PARA MANIPULAÇÃO DOS RESULTADOS DA QUERY
import pandas as pd
```

### Instanciando e Realizando Querys
```python
# PARA INSTANCIAR SUA ORG, BASTA UTILIZAR A CLASSE SalesSoap DO MÓDULO salespy IMPORTADO
# E PREENCHER COM SEUS DADOS DE ACESSO
# CASO TENHA DÚVIDAS DE COMO CONSEGUIR SEU SECRET/SECURITY TOKEN
# ACESSE: https://www.newsfcrm.com/en/blog-sfbasic-get-security-token-in-salesforce-lightning
username = "XXX"
senha = "XXX"
secret = "XXX"
org = sfpy.SalesSoap(username=username, senha=senha, secret=secret)

# VOCÊ PODE UTILIZAR STRING SIMPLES OU EXTENSAS (COMO A SEGUIR PARA FINS DE ORGANIZAÇÃO)
# PARA FAZER SUAS QUERY EM SOQL
query_string = """

SELECT

  ID, 
  CASENUMBER, 
  DESCRIPTION, 
  CREATEDDATE

FROM

  CASE
"""

# PRONTO!!! VOCÊ VAI OBTER UM DATEFRAME (df) COM OS DADOS DE SUA QUERY
df_casos = org.query(query_string)
```
