from enum import Enum

import requests as r

import re as regex

import xml.dom.minidom
import pandas as pd

class SalesSoap:
            
    """ Classe destinada a armazenar dados de sessão e métodos para interação com a API
    
    """
    
    def __init__(self, username, senha, secret, url=None):
        
        self.username = username
        self.senha, self.secret = senha, secret
    
        self.url = SalesforceEndpoints.URL_SOAP_PADRAO.value if url is None else url 
        self.url_instancia_soap = "" # URL da instância concatenado com o endpoint SalesforceEndpoints.SERVICO_SOAP.value. * Inicializado no método __login()

        self.tt = self.__login()
        
    def __del__(self):
        
        self.logout()
        
    def __login(self):
        
        """ Método destinado a realização da Autenticação/Login junto a Salesforce API Soap.
            
        """
        
        # Coleta o XML e adequa os respectivos dados
        xml_login = regex.sub("USERNAME", self.username, SalesforceConfiguracoes.XML_LOGIN.value)
        xml_login = regex.sub("SENHA_SECRET", self.senha + self.secret, xml_login)
        
        headers = {

            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPAction": "login",
            "Accept": "text/xml"

        }
        
        # Realiza a requisição junto ao serviço
        resposta = r.post(self.url, headers=headers, data=xml_login)

        if resposta.status_code != 200:
            
            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'sf:exceptionCode'
                             )
            
            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                            resposta.content, 'sf:exceptionMessage'
                          )
            
            raise SalesforceAuthenticationFailed(codigo_excecao, msg_excecao)

        sessao_id = Utilidades.retorna_valorelemento_pornome(
                        resposta.content, 'sessionId'
                    )
        org_instancia_url = Utilidades.retorna_valorelemento_pornome(
                        resposta.content, 'serverUrl'
                    )
        
        org_instancia_url = org_instancia_url.split("/services")[0]
        
        self.url_instancia_soap = org_instancia_url + SalesforceEndpoints.SERVICO_SOAP.value
        self.sessao_id = sessao_id; self.org_instancia_url = org_instancia_url
        
    def logout(self):
        
        """ Método destinado ao encerramento da Autenticação/Login junto a Salesforce API Soap.
            
        """
        
        headers = {

            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPAction": "logout",

        }
        
        # Coleta o XML e adequa os respectivos dados
        xml_logout = regex.sub("SESSAO_ID", self.sessao_id, SalesforceConfiguracoes.XML_LOGOUT.value)
        
        # Realiza a requisição junto ao serviço
        resposta = r.post(self.url_instancia_soap, headers=headers, data=xml_logout)

        if resposta.status_code != 200:
            
            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'sf:exceptionCode'
                             )
            
            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                            resposta.content, 'sf:exceptionMessage'
                          )
            
            raise SalesforceAuthenticationFailed(codigo_excecao, msg_excecao)
        
        return resposta.text

    def query(self, query_string, tamanho_match_query=None):
    
        """ Método destinado a realização de consultas ao Banco de Dados da ORG.
            
            query_string: str - Consulta
            tamanho_match_query: str - Tamanho da Batch para execução
            
        """
        
        headers = {

            "Content-Type": "text/xml", 
            "SOAPAction": "queryAll"

        }

        # Coleta o XML e adequa os respectivos dados
        xml_query = regex.sub("SESSAO_ID", self.sessao_id, SalesforceConfiguracoes.XML_QUERY.value)
        xml_query = regex.sub("QUERY_STRING", query_string, xml_query)
        tamanho_match_query = SalesforceConfiguracoes.TAMANHO_BATCH_QUERY.value if tamanho_match_query is None else tamanho_match_query
        xml_query = regex.sub("TAMANHO_BATCH_QUERY", tamanho_match_query, xml_query)
        
        # Realiza a requisição junto ao serviço
        resposta = r.post(self.org_instancia_url + SalesforceEndpoints.SERVICO_SOAP.value, 
                     data=xml_query, 
                     headers=headers
                    )

        if resposta.status_code != 200:

            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'sf:exceptionCode'
                                 )

            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'sf:exceptionMessage'
                              )

            raise Exception(codigo_excecao, msg_excecao)
            
        # Coleta os campos solicitados na String de Consulta. Sendo estes mais à frente coletados junto ao retorno,
        # visto que todo sistema é falho e não é desejável dados não solicitados
        query_campos = []
        query_campos_tmp = [

            campo for campo in query_string.replace(",", "").split()

        ]
        query_campos_tmp.remove("SELECT")

        for campo in query_campos_tmp:

            if campo == "FROM":

                break

            query_campos.append(campo)
            
        del query_campos_tmp
        
        # Coleta os dados da query e armazena no pandas.DataFrame: df_query_dados 
        df_query_dados = pd.DataFrame()
        
        for campo in query_campos:
            
            padrao_regex = regex.compile(f"\s+.*?<sf:{campo}>(.*?)</sf:{campo}>", regex.IGNORECASE)
            items = regex.split(padrao_regex, resposta.text)
            df_query_dados[campo] = [item for item in regex.split(padrao_regex, resposta.text) if item[0] != "<"]
            
        return df_query_dados
    
    def insert(self, df: pd.DataFrame, nome_objeto: str):

        """ Método destinado a realização de Inserções ao Banco de Dados da ORG.

                df: pd.DataFrame - DataFrame contendo os registros para Inserção
                nome_objeto: str - Nome do Objeto para Inserção

        """

        # Cabeçalho da requisição
        headers: dict = {

            "Content-Type": "text/xml", 
            "SOAPAction": "create"

        }

        # String destinada a armazenar os registros
        string_registro_parcial: str = "\t<urn:sObjects>\n\t\t<urn1:type>NOME_OBJETO</urn1:type>\nDADOS\n\t</urn:sObjects>".replace("NOME_OBJETO", nome_objeto)

        # Aloca uma list para cada registro
        string_registros_parcial: list = ["" for _ in range(len(df))]
        # Monta um campo XML para cada
        # valor do DataFrame
        for coluna in df.columns:

            i = 0
            for valor in df[coluna].astype(str):

                string_campos = "\t\t"
                string_campos += f"<{coluna}>" + valor + f"</{coluna}>"
                string_registros_parcial[i] += "\n" + string_campos if len(string_registros_parcial[i]) > 0 else string_campos

                i += 1

        # Adequa os campos aos padrões do XML
        for indice in range(len(string_registros_parcial)):

            string_registros_parcial[indice] = string_registro_parcial.replace("DADOS", string_registros_parcial[indice])

        string_registros_completa = ""
        for registro in string_registros_parcial:

            string_registros_completa += registro + "\n"

        # Coleta o XML e adequa os respectivos campos
        xml_insert = regex.sub("SESSAO_ID", self.sessao_id, SalesforceConfiguracoes.XML_INSERT.value)
        xml_insert = regex.sub("REGISTROS", string_registros_completa, xml_insert)

        # Realiza a requisição junto ao serviço
        resposta = r.post(self.org_instancia_url + SalesforceEndpoints.SERVICO_SOAP.value, 
                     data=xml_insert, 
                     headers=headers
                    )

        if resposta.status_code != 200:

            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'sf:exceptionCode'
                                 )

            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'sf:exceptionMessage'
                              )

            raise Exception(codigo_excecao, msg_excecao)

        elif Utilidades.retorna_valorelemento_pornome(
                    tmp.content, 'success'
             ) == 'false':
            
            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'fields'
                                 )
            
            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'message'
                              )

            raise Exception(codigo_excecao, msg_excecao)
        
        return resposta

class SalesforceConfiguracoes(Enum):
    
    """ Classe destinada a armazenar contantes de configuração 
    
    """
    
    VERSAO_API_PADRAO = "58.0"
    TIPO_LOGIN_PADRAO = "u" # utilizar "c" para partner
    TAMANHO_BATCH_QUERY = "50"
    
    # XML para realização de login
    XML_LOGIN = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
   <soapenv:Body>
      <urn:login>
         <urn:username>USERNAME</urn:username>
         <urn:password>SENHA_SECRET</urn:password>
      </urn:login>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
    # XML para realização de logout
    XML_LOGOUT = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
   <soapenv:Header>
      <urn:SessionHeader>
         <urn:sessionId>SESSAO_ID</urn:sessionId>
      </urn:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <urn:logout/>
   </soapenv:Body>
</soapenv:Envelope>
"""

    # XML para realização de Querys
    XML_QUERY = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
   <soapenv:Header>
      <urn:QueryOptions>
         <urn:batchSize>TAMANHO_BATCH_QUERY</urn:batchSize>
      </urn:QueryOptions>
      <urn:SessionHeader>
         <urn:sessionId>SESSAO_ID</urn:sessionId>
      </urn:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <urn:queryAll>
         <urn:queryString>QUERY_STRING</urn:queryString>
      </urn:queryAll>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
    XML_INSERT = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com" xmlns:urn1="urn:sobject.partner.soap.sforce.com">
   <soapenv:Header>
      <urn:SessionHeader>
         <urn:sessionId>SESSAO_ID</urn:sessionId>
      </urn:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <urn:create>
         REGISTROS
      </urn:create>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
class SalesforceEndpoints(Enum):
    
    """ Classe destinada a armazenar URLs dos Endpoints SOAP
    
    """
    
    URL_SOAP_PADRAO = f"https://login.salesforce.com/services/Soap/{SalesforceConfiguracoes.TIPO_LOGIN_PADRAO.value}/{SalesforceConfiguracoes.VERSAO_API_PADRAO.value}"
    
    SERVICO_SOAP = "/services/Soap" + "/" + SalesforceConfiguracoes.TIPO_LOGIN_PADRAO.value + "/" + SalesforceConfiguracoes.VERSAO_API_PADRAO.value
    SOBJ_SERVICE = '/services/data/v%s/sobjects%s'
    REVOKE_SERVICE = '/services/oauth2/revoke'
    VERSIONS_SERVICE = '/services/data/'
    QUERY_SERVICE = "/services/data/v" + SalesforceConfiguracoes.VERSAO_API_PADRAO.value + "/query"
    SEARCH_SERVICE = '/services/data/v%s/search/?%s'
    TOOLING_ANONYMOUS = '/services/data/v%s/tooling/executeAnonymous/?%s'
    APPROVAL_SERVICE = '/services/data/v%s/process/approvals/'    
    
    VERSAO_API_PADRAO = "58.0" 

class Utilidades:
    
    """ Classe destinada a armazenar métodos auxiliares para a biblioteca
                
    """
    
    @staticmethod
    def retorna_valorelemento_pornome(xml_string, nome_elemento):
        
        """ Retorna o conteúdo interno de um XML se encontrado, caso contrário, retorna None
        
            xml_string: str - XML para manipulação 
            nome_elemento: str - Nome da TAG para a procura
            
        """
        
        xmlDom = xml.dom.minidom.parseString(xml_string)
        elementos = xmlDom.getElementsByTagName(nome_elemento)
        
        if len(elementos) > 0:
            valores_elemento = (
                elementos[0]
                .toxml()
                .replace('<' + nome_elemento + '>', '')
                .replace('</' + nome_elemento + '>', '')
            )
            
        return valores_elemento if len(elementos) > 0 else None
