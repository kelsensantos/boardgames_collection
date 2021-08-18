from math import ceil
import requests
import json
# from requests.api import get
from ludopedia_wrapper.Connection import Connection


class Ludopedia:
    """ Consome os métodos da API da Ludopedia. """

    def __init__(self, conn=Connection()):
        self.conexao = conn
        self.headers = {
                "Content-type": "aplication-json",
                "Authorization": f"Bearer {self.conexao.ACCESS_TOKEN}"
            }

    def _request_json(self, url):
        """ Realiza consulta e obtém resposta em formato json. """
        response = requests.get(url, headers=self.headers)
        response_json = json.loads(response.text)
        return response_json

    @staticmethod
    def _mount_url(url, first=True, **kwargs):
        """ Monta a URL para requisição a partir de dicinário com parâmetros.
        Todos os parâmetros precisam ser informados a partir do inicial,
        ou seja, a url de entrada não poder conter outros patrâmetros pré-definidos. """
        mounted_url = url
        for item in kwargs.keys():
            complemento = kwargs.get(item)
            if first:
                mounted_url = mounted_url + '?' + str(item) + '=' + str(complemento)
            else:
                mounted_url = mounted_url + '&' + str(item) + '=' + str(complemento)
            first = False
        return mounted_url

    @staticmethod
    def _modelar_kwargs(**kwargs):
        return kwargs

    def get_endpoint(self, url, **kwargs):
        """ Método genérico para consumir de qualquer endpoint via get. """
        url = Ludopedia._mount_url(url, **kwargs)
        response = self._request_json(url)
        return response

    def buscar_colecao(self, todos=True, lista='colecao', ordem='nome', pg=1, rows=100, **kwargs):
        """ Método para consumir do endpoint "colecao". """
        url = 'https://ludopedia.com.br/api/v1/colecao'
        url = Ludopedia._mount_url(
            url,
            lista=lista,
            rows=rows,
            ordem=ordem,
            pg=pg,
            **kwargs
        )
        print(f'Obtendo dados de {url} ...')
        response = self._request_json(url)
        # implementa atributo para buscar todos os jogos (default: true)
        if todos and pg == 1:
            total_de_paginas = ceil(response["total"] / rows)
            jogos = response["colecao"]
            print(f'Total de páginas: {total_de_paginas}')
            for page in range(2, total_de_paginas + 1):
                proxima_pagina = self.buscar_colecao(pg=page)
                jogos += proxima_pagina["colecao"]
            response = jogos
        return response
