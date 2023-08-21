# Enunciados
from enum import Enum

# Interações Web
import requests as r

# Análise de texto
import re as regex

# Manipulação de Dados
import xml.dom.minidom
import pandas as pd
import numpy as np

# Tipagem
from collections.abc import Iterable

# Logs
from loguru import logger as lgg

class SalesforceError(Exception):
    """Base Salesforce API exception"""

    message = 'Unknown error occurred for {url}. Response content: {content}'

    def __init__(self, url, status, resource_name, content):
        """Initialize the SalesforceError exception

        SalesforceError is the base class of exceptions in simple-salesforce

        Args:
            url: Salesforce URL that was called
            status: Status code of the error response
            resource_name: Name of the Salesforce resource being queried
            content: content of the response
        """
        # TODO exceptions don't seem to be using parent constructors at all.
        # this should be fixed.
        # pylint: disable=super-init-not-called
        self.url = url
        self.status = status
        self.resource_name = resource_name
        self.content = content

    def __str__(self):
        return self.message.format(url=self.url, content=self.content)

    def __unicode__(self):
        return self.__str__()

    
class SalesforceAuthenticationFailed(SalesforceError):
    """
    Thrown to indicate that authentication with Salesforce failed.
    """

    def __init__(self, code, message):
        # TODO exceptions don't seem to be using parent constructors at all.
        # this should be fixed.
        # pylint: disable=super-init-not-called
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.code}: {self.message}'
    
class SoapDados:
    
    """ Classe destinada a realização de manipulações
        do Bancoo de Dados da ORG
    """
    
    query_localizador = ""
    query_campos = []
    query_campos_tmp = []
    objeto = ""
    
    def delete(self, ids: Iterable[list, np.array, pd.DataFrame, pd.Series]):

        """ Método destinado a realização de Deleções ao Banco de Dados da ORG.

            ids: Iterável - Iterável contendo os Ids dos registros para Deleção

        """

        if type(ids) == type(pd.DataFrame()):

            if "ID" not in df.columns.str.upper():

                raise Exception("O seu DataFrame deve conter uma coluna chamada Id (Case-Insensitive): {}".format(df.columns))

            ids.columns = ids.columns.str.upper()
            ids = df["ID"].values

        # Cabeçalho da requisição
        headers: dict = {

            "Content-Type": "text/xml", 
            "SOAPAction": "delete"

        }

        # String destinada a armazenar os registros
        string_registro_completa: str = ""

        for id in ids:

            string_registro_completa += "<urn:ids>{}</urn:ids>".format(id)
        
        # Coleta o XML e adequa os respectivos campos
        xml_delete = regex.sub("SESSAO_ID", self.sessao_id, SalesforceConfiguracoes.XML_DELETE.value)
        xml_delete = regex.sub("REGISTROS", string_registro_completa, xml_delete)

        # Realiza a requisição junto ao serviço
        resposta = r.post(self.org_instancia_url + SalesforceEndpoints.SERVICO_SOAP.value, 
                     data=xml_delete, 
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
                    resposta.content, 'success'
             ) == 'false':

            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'fields'
                                 )

            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'message'
                              )

            raise Exception(codigo_excecao, msg_excecao)

        return resposta
    
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
        string_registro_parcial: str = "<urn:sObjects><urn1:type>NOME_OBJETO</urn1:type>DADOS</urn:sObjects>".replace("NOME_OBJETO", nome_objeto)

        # Aloca uma list para cada registro
        string_registros_parcial: list = ["" for _ in range(len(df))]
        # Monta um campo XML para cada
        # valor do DataFrame
        for coluna in df.columns:

            i = 0
            for valor in df[coluna].astype(str):

                string_campos = ""
                string_campos += f"<{coluna}>" + valor + f"</{coluna}>"
                string_registros_parcial[i] += "" + string_campos if len(string_registros_parcial[i]) > 0 else string_campos

                i += 1

        # Adequa os campos aos padrões do XML
        for indice in range(len(string_registros_parcial)):

            string_registros_parcial[indice] = string_registro_parcial.replace("DADOS", string_registros_parcial[indice])

        string_registros_completa = ""
        for registro in string_registros_parcial:

            string_registros_completa += registro + ""

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
                    resposta.content, 'success'
             ) == 'false':
            
            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'fields'
                                 )
            
            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'message'
                              )

            raise Exception(codigo_excecao, msg_excecao)
        
        return resposta
    
    def undelete(self, ids: Iterable[list, np.array, pd.DataFrame, pd.Series]):

        """ Método destinado a realização de Recuperação Deleções ao Banco de Dados da ORG.

            ids: Iterável - Iterável contendo os Ids dos registros para Recuperação de Deleção

        """

        if type(ids) == type(pd.DataFrame()):

            if "ID" not in df.columns.str.upper():

                raise Exception("O seu DataFrame deve conter uma coluna chamada Id (Case-Insensitive): {}".format(df.columns))

            ids.columns = ids.columns.str.upper()
            ids = df["ID"].values

        # Cabeçalho da requisição
        headers: dict = {

            "Content-Type": "text/xml", 
            "SOAPAction": "undelete"

        }

        # String destinada a armazenar os registros
        string_registro_completa: str = ""

        for id in ids:

            string_registro_completa += "<urn:ids>{}</urn:ids>".format(id)
        
        # Coleta o XML e adequa os respectivos campos
        xml_undelete = regex.sub("SESSAO_ID", self.sessao_id, SalesforceConfiguracoes.XML_UNDELETE.value)
        xml_undelete = regex.sub("REGISTROS", string_registro_completa, xml_undelete)

        # Realiza a requisição junto ao serviço
        resposta = r.post(self.org_instancia_url + SalesforceEndpoints.SERVICO_SOAP.value, 
                     data=xml_undelete, 
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
                    resposta.content, 'success'
             ) == 'false':

            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'fields'
                                 )

            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'message'
                              )

            raise Exception(codigo_excecao, msg_excecao)

        return resposta
    
    def update(self, df: pd.DataFrame, nome_objeto: str):

        """ Método destinado a realização de Atualizações ao Banco de Dados da ORG.

                df: pd.DataFrame - DataFrame contendo os registros para Inserção
                nome_objeto: str - Nome do Objeto para Inserção

        """
        
        if "ID" not in df.columns.str.upper():
            
            raise Exception("O seu DataFrame deve conter uma coluna chamada Id (Case-Insensitive): {}".format(df.columns))
            
        # Cabeçalho da requisição
        headers: dict = {

            "Content-Type": "text/xml", 
            "SOAPAction": "update"

        }

        # String destinada a armazenar os registros
        string_registro_parcial: str = "<urn:sObjects><urn1:type>NOME_OBJETO</urn1:type>DADOS</urn:sObjects>".replace("NOME_OBJETO", nome_objeto)

        # Aloca uma list para cada registro
        string_registros_parcial: list = ["" for _ in range(len(df))]
        # Monta um campo XML para cada
        # valor do DataFrame
        for coluna in df.columns:

            i = 0
            for valor in df[coluna].astype(str):

                string_campos = ""
                string_campos += f"<{coluna}>" + valor + f"</{coluna}>"
                string_registros_parcial[i] += "" + string_campos if len(string_registros_parcial[i]) > 0 else string_campos

                i += 1

        # Adequa os campos aos padrões do XML
        for indice in range(len(string_registros_parcial)):

            string_registros_parcial[indice] = string_registro_parcial.replace("DADOS", string_registros_parcial[indice])

        string_registros_completa = ""
        for registro in string_registros_parcial:

            string_registros_completa += registro + ""

        # Coleta o XML e adequa os respectivos campos
        xml_insert = regex.sub("SESSAO_ID", self.sessao_id, SalesforceConfiguracoes.XML_UPDATE.value)
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
                    resposta.content, 'success'
             ) == 'false':
            
            codigo_excecao = Utilidades.retorna_valorelemento_pornome(
                                    resposta.content, 'fields'
                                 )
            
            msg_excecao = Utilidades.retorna_valorelemento_pornome(
                                resposta.content, 'message'
                              )

            raise Exception(codigo_excecao, msg_excecao)
        
        return resposta
    
    def query(self, query_string="", tamanho_match_query=None):
    
        """ Método destinado a realização de consultas ao Banco de Dados da ORG.
            
            query_string: str - Consulta
            tamanho_match_query: str - Tamanho da Batch para execução
            
        """
        
        headers = {

            "Content-Type": "text/xml", 
            "SOAPAction": "queryMore"

        }

        if self.query_localizador not in ["", '<queryLocator xsi:nil="true"/>']:
            
            xml_query = SalesforceConfiguracoes.XML_QUERY_MORE.value
            xml_query = regex.sub("QUERY_LOCALIZADOR", self.query_localizador, xml_query)
            
        else:
            
            xml_query = SalesforceConfiguracoes.XML_QUERY_ALL.value
            xml_query = regex.sub("QUERY_STRING", query_string, xml_query)
        
        # Coleta o XML e adequa os respectivos dados
        xml_query = regex.sub("SESSAO_ID", self.sessao_id, xml_query)
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
            
        query_campos = []
        
        if query_string:

            # Coleta os campos solicitados na String de Consulta. Sendo estes mais à frente coletados junto ao retorno,
            # visto que todo sistema é falho e não é desejável dados não solicitados    
            self.query_campos_tmp = [

                campo for campo in query_string.replace(",", "").split()

            ]
            self.query_campos_tmp.remove("SELECT")

            for i, campo in enumerate(self.query_campos_tmp):

                if campo == "FROM":

                    self.objeto = self.query_campos_tmp[i+1]
                    break

                self.query_campos.append(campo)

        # Coleta os dados da query e armazena no pandas.DataFrame: df_query_dados 
        df_query_dados = pd.DataFrame()
        
        for campo in self.query_campos:

            df_query_dados[campo] = Utilidades.valores_campos_xml(xml_string=resposta.text, objeto=self.objeto, nome_elemento=campo, case_insensitive=True)

        self.query_localizador = Utilidades.retorna_valorelemento_pornome(xml_string=resposta.text, nome_elemento="queryLocator")
        
        while self.query_localizador not in ["", '<queryLocator xsi:nil="true"/>']:
            
            df = self.query()
            lgg.debug(self.query_localizador + " - " + str(len(df)) + " " + str(self.query_campos_tmp))
            
            df_query_dados = pd.concat([df_query_dados, df])
            
        self.query_localizador = ""
        self.query_campos = []
        
        return df_query_dados
    
class SoapAuth:
    
    """ Classe destinada a realização de login e logout da ORG
    """
    
    def __init__(self, username, senha, secret, url=None):
        
        self.username = username
        self.senha, self.secret = senha, secret
    
        self.url = SalesforceEndpoints.URL_SOAP_PADRAO.value if url is None else url 
        self.url_instancia_soap = "" # URL da instância concatenado com o endpoint SalesforceEndpoints.SERVICO_SOAP.value. * Inicializado no método __login()
        self.login()
        
    def login(self):
        
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

                 

        self.sessao_id = ""

class SalesSoap(SoapDados, SoapAuth):
            
    """ Classe destinada a armazenar dados de sessão e métodos para interação com a API
    
    """
    
    def __init__(self, username, senha, secret, url=None):
        
        super().__init__(username, senha, secret, url=None)
            
class SalesforceConfiguracoes(Enum):
    
    """ Classe destinada a armazenar contantes de configuração 
    
    """
    
    VERSAO_API_PADRAO = "58.0"
    TIPO_LOGIN_PADRAO = "u" # utilizar "c" para partner
    TAMANHO_BATCH_QUERY = "50"

    # XML para realização de Exclusões
    XML_DELETE = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
   <soapenv:Header>
      <urn:SessionHeader>
         <urn:sessionId>SESSAO_ID</urn:sessionId>
      </urn:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <urn:delete>
         REGISTROS
      </urn:delete>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
    # XML para realização de Inserções
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
    
    # XML para realização de Atualizações
    XML_UPDATE = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com" xmlns:urn1="urn:sobject.partner.soap.sforce.com">
   <soapenv:Header>
       <urn:SessionHeader>
         <urn:sessionId>SESSAO_ID</urn:sessionId>
      </urn:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <urn:update>
         REGISTROS
      </urn:update>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
    # XML para realização de Recuperação de Exclusões
    XML_UNDELETE = """
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
   <soapenv:Header>
      <urn:SessionHeader>
         <urn:sessionId>SESSAO_ID</urn:sessionId>
      </urn:SessionHeader>
   </soapenv:Header>
   <soapenv:Body>
      <urn:undelete>
        REGISTROS
      </urn:undelete>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
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
    XML_QUERY_ALL = """
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
    # XML para realização de Querys
    XML_QUERY_MORE = """
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
      <urn:queryMore>
         <urn:queryLocator>QUERY_LOCALIZADOR</urn:queryLocator>
      </urn:queryMore>
   </soapenv:Body>
</soapenv:Envelope>
"""
    
class SalesforceEndpoints(Enum):
    
    """ Classe destinada a armazenar URLs dos Endpoints SOAP
    
    """
    
    URL_SOAP_PADRAO = f"https://login.salesforce.com/services/Soap/{SalesforceConfiguracoes.TIPO_LOGIN_PADRAO.value}/{SalesforceConfiguracoes.VERSAO_API_PADRAO.value}"
    
    SERVICO_SOAP = "/services/Soap" + "/" + SalesforceConfiguracoes.TIPO_LOGIN_PADRAO.value + "/" + SalesforceConfiguracoes.VERSAO_API_PADRAO.value
    
    VERSAO_API_PADRAO = "58.0" 

class Utilidades:
    
    """ Classe destinada a armazenar métodos auxiliares para a biblioteca
                
    """
    
    @staticmethod
    def retorna_valorelemento_pornome(xml_string, nome_elemento, erro=False):
        
        """ Retorna o conteúdo interno de um XML se encontrado, caso contrário, retorna None
        
            xml_string: str - XML para manipulação 
            nome_elemento: str - Nome da TAG para a procura
            erro: bool = False - Permite ou não a recursão de mais de uma tags no caso de um xml de erro 
            
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
        
        elif len(elementos) == 0 and erro:

            nome_elemento = "faultcode" if nome_elemento == "sf:exceptionCode" else "faultstring"
            valores_elemento = Utilidades.retorna_valorelemento_pornome(xml_string, nome_elemento, erro=erro)

        return valores_elemento if len(elementos) > 0 else None
    
    @staticmethod
    def valores_campos_xml(xml_string, nome_elemento, objeto, case_insensitive=True):
            
        """ Retorna uma lista contendo o conteúdo interno de um XML se encontrado, caso contrário, retorna uma lista vazia
        
            xml_string: str - XML para manipulação 
            nome_elemento: str - Nome da TAG para a procura
            case_insensitive: bool = False - Normaliza as variáveis xml_string e nome_elemento para caixa-baixa, assim permitindo o parser adequadamente
            
        """

        # TRANSFORMA EM CAIXA-BAIXA QUANDO QUANDO A VARIÁVEL case_insensitive FOR VERDADEIRA
        # ASSIM PERMITINDO O PARSER ADEQUADAMENTE
        xml_string = xml_string.lower() if case_insensitive else xml_string
        objeto = objeto.lower()
        nome_elemento = nome_elemento.lower() if case_insensitive else nome_elemento
        nome_elemento = "sf:" + nome_elemento

        xmlDom = xml.dom.minidom.parseString(xml_string)
        # VARIÁVEIS DESTINADAS A ARMAZENAR RESPECTIVAMENTE O PRIMEIRO NOME DE CAMPOS COMPOSTOS (NOME BASE)
        # EX: PROFILE, DE PROFILE.LICENCE.USER
        # E O ÚLTIMO NOME DE CAMPOS COMPOSTOS (NOME ALVO) DESTINADO AO FILTRO FINAL PARA COLETA DO VALOR
        nome_elemento_base, nome_elemento_alvo = nome_elemento, nome_elemento
        campo_composto = False

        if "." in nome_elemento:

            nome_elemento_base, nome_elemento_alvo = nome_elemento.split(".")[0], "sf:" + nome_elemento.split(".")[-1]
            campo_composto = True

        if nome_elemento == "sf:id":

            elementos = [id.split("</sf:id>")[0] for id in xml_string.split(f"<sf:type>{objeto}</sf:type><sf:id>")[1:]]

        elif nome_elemento == "sf:name":

            name_regex = regex.compile("<sf:type>{}(.*?)<sf:name>(.*?)<\/sf:name>".format(objeto))
            elementos = [elemento[-1] for elemento in name_regex.findall(xml_string)]

        else:

            elementos = xmlDom.getElementsByTagName(nome_elemento_base)
            elementos = [elemento.toxml() for elemento in elementos]
      
        valores_elemento = []

        # SE A QUANTIDADE DE ELEMENTOS FOR MAIOR QUE ZERO
        # ITERA A LITA E ADICIONA O VALOR DE CADA UM NA LISTA valores_elemento
        if len(elementos) > 0:      

            for elemento in elementos:

                if campo_composto:
                    
                    padrao_regex = "<" + nome_elemento_alvo + ">" +".*"+ "</" + nome_elemento_alvo + ">"
                    elemento = regex.compile(padrao_regex).findall(elemento)    
                    elemento =  np.nan if len(elemento) == 0 else elemento[0].replace('<' + nome_elemento_alvo + '>', '').replace('</' + nome_elemento_alvo + '>', '')
                    
                    valores_elemento.append(
                        elemento
                    )
                    continue

                elemento = elemento.replace('<' + nome_elemento + '>', '').replace('</' + nome_elemento + '>', '')
                elemento = np.nan if 'xsi:nil="true"' in elemento else elemento 
                
                valores_elemento.append(
                    elemento
                )

        return valores_elemento