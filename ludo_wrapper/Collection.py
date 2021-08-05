from math import ceil
import requests
import json
# from requests.api import get
from ludopedia_wrapper.Connection import Connection


def fetch_all_games(conexao):
    collection = get_collection(conexao)
    total_pages = ceil(collection["total"]/20)
    jogos = collection["colecao"]
    for pg in range(2, total_pages+1):
        next_page = get_collection(conexao, pg=pg)
        jogos += next_page["colecao"]
    return jogos


def get_collection(conexao, pg=1):
    url = f"https://ludopedia.com.br/api/v1/colecao?lista=colecao&page={pg}"
    headers = {
        "Content-type": "aplication-json",
        "Authorization": f"Bearer {conexao.ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)
    return json.loads(response.text)


if __name__ == '__main__':
    conector = Connection()
    games = fetch_all_games(conector)
    print(len(games))
