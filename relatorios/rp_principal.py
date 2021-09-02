import pandas as pd
import datapane as dp
import matplotlib.pyplot as plt
from modules.database import Database
from modules.reports import Datapane


titulo_do_relatorio = 'colecao'

texto_de_apresentacao = """
Esta página foi gerada por um projeto de código aberto, destinado a apresentar 
insights sobre sua coleção de boardgames na [Ludopedia](www.ludopedia.com.br).  
Fazemos uso da API disponibilizada pela Ludopedia.  
Conheça mais ou colabore, [acesse o projeto](https://github.com/kelsensantos/boardgames_collection).
"""

# localização dos jogos
locais = Database.get_table(Database.tb_locais)
# monta um plot para visualização de jogos por local
x = locais['local'].value_counts().to_frame('Total')
y = round((locais['local'].value_counts(normalize=True).to_frame('%') * 100), 1)
locais_resumo = pd.concat([x, y], axis=1)
# gráficos para localização dos jogos
figsize = (21, 7)
# # figura 1
plt.figure()
locais_plot1 = locais_resumo[['Total']].T.plot(kind='bar', figsize=figsize, rot=0, fontsize=14)
# # figura 2
fig, locais_plot2 = plt.subplots(figsize=figsize, subplot_kw=dict(aspect='equal'))
dados = locais_resumo['%']
wedges, texts, autotexts = locais_plot2.pie(dados, autopct='%1.1f%%', textprops=dict(color='w'))
locais_plot2.legend(wedges, list(dados.index), loc='upper left', bbox_to_anchor=[1, 0, 0.5, 1])
plt.setp(autotexts, size=14, weight='bold')
locais_plot2.set_title('Distribuição de jogos por local')


# criação do relatório
report = dp.Report(

    "### Apresentação",
    texto_de_apresentacao,

    '### Localização dos boardgames',
    dp.Select(blocks=[
        dp.Plot(locais_plot1, label='Gráfico', caption='Quantidade por localização'),
        dp.Plot(locais_plot2, label='Pizza %', caption='Quantidade percentual'),
        dp.DataTable(locais_resumo, label='Tabela', caption='Resumo de jogos por localização'),
        dp.DataTable(locais, label='Jogos', caption="Jogos por localização")
    ]),
)

Datapane.atualizar_relatorio(report, titulo_do_relatorio)
