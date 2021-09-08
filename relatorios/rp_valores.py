# import pandas as pd
import datapane as dp
import matplotlib.pyplot as plt
# from modules.database import Database
from modules.reports import Datapane
from modules.classes import Colecao

titulo_do_relatorio = 'Análise de valor da coleção de boardgames'

texto_de_apresentacao = """
Esta página foi gerada por um projeto de código aberto, destinado a apresentar 
insights sobre sua coleção de boardgames na [Ludopedia](www.ludopedia.com.br).  
Fazemos uso da API disponibilizada pela Ludopedia.  
Conheça mais ou colabore, [acesse o projeto](https://github.com/kelsensantos/boardgames_collection).
"""

# variáveis genéricas
colecao = Colecao.buscar_colecao()
default_fig_size = (8, 5)

# Tabela com resumo de custos
metricas = ['mean', '50%', 'max', 'count']
custos_resumo = colecao.describe()[['vl_custo']].loc[metricas]
custos_resumo.loc['Total de jogos', :] = len(colecao)
custos_resumo.loc['Custo total', :] = colecao['vl_custo'].sum()
custos_resumo = custos_resumo.round(1)
custos_resumo.rename(
    index={
        'count': 'Jogos com custo definido',
        'mean': 'Média de valor pago',
        '50%': 'Mediana de valor pago',
        'max': 'Maior valor pago'
    },
    inplace=True
)
# custos_resumo.columns = ['']

# Histograma com custos dos jogos
plt.figure()
histograma_custos = colecao.vl_custo.plot.hist(
    bins=50,
    figsize=default_fig_size
)
histograma_custos.set_ylabel('Quantidade')
histograma_custos.set_xlabel('Custo')
histograma_custos.set_title('Frequência de jogos por custo\n', loc='left')

# Jogos sem custo definido
selecao = colecao['vl_custo'].isnull()
jogos_sem_custo = colecao[selecao].copy()
jogos_sem_custo_apresentacao = f'Existem {len(jogos_sem_custo)} jogos sem custo definido.'


def func1():
    """ Esta função serve para montar o relatório, caso o dataframe esteja vazio. """
    if len(jogos_sem_custo):
        return dp.DataTable(jogos_sem_custo),
    else:
        return 'Não existe.'


# criação do relatório
report = dp.Report(

    dp.Page(
        title='Custos',
        blocks=[
            "### Apresentação",
            texto_de_apresentacao,

            '### Análise de valor e custo de boardgames',
            dp.Group(
                dp.DataTable(custos_resumo, label='Resumo', caption="Resumo de principais métricas"),
                dp.Plot(histograma_custos, label='Histograma', caption='Histograma de custos'),
                columns=2
            )
        ]
    ),
    dp.Page(
        title='Jogos sem custo',
        blocks=[
            jogos_sem_custo_apresentacao,
            func1()
        ]
    )
)

Datapane.atualizar_relatorio(report, titulo_do_relatorio)
