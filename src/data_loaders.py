import pandas as pd
from io import StringIO
import re
import numpy as np
import camelot

class Data:
    
    def __init__(self, demand_file_path, curriculum_file_path, camaras_file_path):
        self.demand_file_path = demand_file_path
        self.curriculum_file_path = curriculum_file_path
        self.camaras_file_path = camaras_file_path
        self.load_data()

    def load_data(self):
        self.demand_df = self.load_df_from_xlsx(self.demand_file_path)
        self.curriculum_df = self.load_df_from_xlsx(self.curriculum_file_path)
        self.camaras_df = self.load_df_from_xlsx(self.camaras_file_path)
        assert self.curriculum_df is not None, "ERRO: Currículo não carregado"
        assert self.demand_df is not None, "ERRO: Demanda não carregada"
        assert self.camaras_df is not None, "ERRO: Câmaras não carregadas"
        self.pre_process_curriculum()
        self.pre_process_demand()
        self.pre_process_camaras()

    def pre_process_camaras(self):
        pass

    def pre_process_curriculum(self):
        df = self.curriculum_df
        df[['ch_total', 'ch_pratica']] = df[['ch_total', 'ch_pratica']].fillna(0)
        all_prereqs_list = df[~df['pre_requisitos'].isna()]['pre_requisitos'].str.cat(sep=';').split(';')
        unique_prereqs = set(all_prereqs_list)
        df['eh_pre_requisito'] = df['codigo'].isin(unique_prereqs)
        df['pratica'] = df['ch_pratica'] > 0
        df['ch_teorica'] = df['ch_total']-df['ch_pratica']
        

    def pre_process_demand(self):
        df = self.demand_df

    def load_df_from_xlsx(self, file_path):
        try:
            df = pd.read_excel(file_path)
            return df
        except FileNotFoundError:
            print(f"ERRO: O arquivo '{file_path}' não foi encontrado.")
            print("Por favor, verifique se o nome e o caminho do arquivo estão corretos.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado durante o processamento: {e}")
        return None

    def get_demand_by_area(self, use_elective=False):
        df_per_component = self.get_demand_by_component(use_elective=use_elective)
        numeric_columns_to_sum = [
            'matriculados', 'n_turmas', 'n_subturmas',
            'ch_teorica', 'ch_pratica', 'ch_total', 'pre_requisito', "n_componentes",
            'obrigatorio_generalista', 'obrigatorio_enfase'
        ]
        agg_dict = {col: 'sum' for col in numeric_columns_to_sum if col in df_per_component.columns}
        if 'n_professores' in df_per_component.columns:
            agg_dict['n_professores'] = 'first'

        df_by_area = df_per_component.groupby('camara').agg(agg_dict).reset_index()
        df_by_area = df_by_area.rename(columns={'camara': 'titulo'})
        self.__add_proportions(df_by_area)
        df_by_area = df_by_area.sort_values(by='matriculados', ascending=False)
        return df_by_area

    def __add_proportions(self, df):
        global_demand = df['matriculados'].sum()
        if global_demand > 0:
            df['prop_matriculados'] = df['matriculados'] / global_demand
        else:
            df['prop_matriculados'] = 0
        global_ch= df['ch_total'].sum()
        if global_ch > 0:
            df['prop_ch_total'] = df['ch_total'] / global_ch
        else:
            df['prop_ch_total'] = 0
        df['prop_pre_requisito'] = df['pre_requisito']/self.curriculum_df['codigo'].count()
        df['prop_forca_trabalho'] = df['n_professores']/self.camaras_df['n_professores'].sum()
        df['prop_obrigatorio'] = (df['obrigatorio_generalista']+df['obrigatorio_enfase'])/(df['obrigatorio_enfase'].max()+1)

    def get_demand_by_component(self, use_elective=False):
        demand_df = self.demand_df.copy()
        demand_df['turma_principal'] = demand_df['turma'].astype(str).str.extract(r'(\d+)').fillna('0')
        target_demand_df = demand_df
        if not use_elective:
            curriculum_codes = self.curriculum_df['codigo'].unique()
            target_demand_df = demand_df[demand_df['codigo'].isin(curriculum_codes)].copy()
        curriculum_info = self.curriculum_df[[
            'codigo', 'nome', 'camara', 'ch_teorica', 'ch_pratica', 
            'obrigatorio_generalista', 'obrigatorio_enfase'
        ]].drop_duplicates(subset=['codigo']).rename(columns={'ch_pratica': 'carga_horaria_pratica_base'}) 
        
        demand_with_info = pd.merge(
            target_demand_df,
            curriculum_info,
            on='codigo',
            how='left'
        )

        #print(demand_with_info)
        demand_with_info['nome'] = np.where(
            demand_with_info['nome_y'].notna(),
            demand_with_info['nome_y'],
            demand_with_info['nome_x']
        )
        demand_with_info.drop(columns=['nome_x', 'nome_y'], inplace=True)
        demand_with_info[['ch_teorica', 'carga_horaria_pratica_base', 'obrigatorio_generalista', 'obrigatorio_enfase']] = \
            demand_with_info[['ch_teorica', 'carga_horaria_pratica_base', 'obrigatorio_generalista', 'obrigatorio_enfase']].fillna(0)
        demand_with_info['camara'] = demand_with_info['camara'].fillna('Não definida')
        def aggregate_component(group):
            matriculados = group['matriculados'].sum()
            n_turmas = group.drop_duplicates(subset=['periodo', 'turma_principal']).shape[0]
            grupo_pratico = group[group['carga_horaria_pratica_base'] > 0]
            n_subturmas = grupo_pratico.drop_duplicates(subset=['periodo', 'turma']).shape[0]
            ch_teorica_base = group['ch_teorica'].iloc[0] if not group.empty else 0
            carga_horaria_pratica_base = group['carga_horaria_pratica_base'].iloc[0] if not group.empty else 0
            obrigatorio_generalista = group['obrigatorio_generalista'].iloc[0] if not group.empty else 0
            obrigatorio_enfase = group['obrigatorio_enfase'].iloc[0] if not group.empty else 0

            ch_teorica_total = n_turmas * ch_teorica_base
            ch_pratica_total = n_subturmas * carga_horaria_pratica_base 
            return pd.Series({
                'matriculados': matriculados,
                'n_turmas': n_turmas,
                'n_subturmas': n_subturmas,
                'ch_teorica': ch_teorica_total,
                'ch_pratica': ch_pratica_total,
                'obrigatorio_generalista': obrigatorio_generalista,
                'obrigatorio_enfase': obrigatorio_enfase,
                'ch_pratica_base': carga_horaria_pratica_base
            })
        summary_df = demand_with_info.groupby(
            ['codigo', 'nome', 'camara'],
        ).apply(aggregate_component,  include_groups=False).reset_index()
        summary_df = summary_df.rename(columns={'nome': 'titulo'})
        int_columns = ['matriculados', 'n_turmas', 'n_subturmas', 'ch_teorica', 'ch_pratica', 'ch_pratica_base','obrigatorio_generalista', 'obrigatorio_enfase']
        summary_df[int_columns] = summary_df[int_columns].astype(int)
        summary_df.loc[summary_df['ch_teorica'] == 0, 'n_turmas'] = 0
        summary_df = summary_df.sort_values(by='matriculados', ascending=False)
        summary_df['ch_total'] = summary_df['ch_teorica'] + summary_df['ch_pratica']
        summary_df = summary_df.sort_values(by='matriculados', ascending=False)
        all_prereqs = self.curriculum_df['pre_requisitos'].dropna().str.split(';').explode()
        prereq_counts = all_prereqs.value_counts()
        summary_df['pre_requisito'] = summary_df['codigo'].map(prereq_counts).fillna(0).astype(int)
        summary_df = pd.merge(summary_df, self.camaras_df, on='camara', how='left')
        summary_df['n_professores'] = summary_df['n_professores'].fillna(0).astype(int)
        summary_df['n_componentes'] = 1
        #print(summary_df.to_string())
        self.__add_proportions(summary_df)
        return summary_df

class Components:

    def __init__(self, *files):
        self.files = files
        self.df_list = []
        self.stacked_df = None
        self.load_data()
        self.stack_dataframes()

    def load_data(self):
        for file in self.files:
            self.read_file(file)

    def stack_dataframes(self):
        self.stacked_df = pd.concat(self.df_list, ignore_index=True)
        return self.stacked_df
    
    def get_unique_stacked_df(self):
        return self.stacked_df[['codigo', 'nome']].drop_duplicates().reset_index(drop=True)

    def get_electives(self, curriculum_df):
        df = self.get_unique_stacked_df()
        df = df[~df['codigo'].isin(curriculum_df['codigo'].unique())]
        return df


    def save_to_excel(self, output_filename):
        if self.stacked_df is None:
            self.stack_dataframes()
        if self.stacked_df is None or self.stacked_df.empty:
            return
        try:
            self.stacked_df.to_excel(output_filename, index=False)
        except Exception as e:
            print(f"Ocorreu um erro ao salvar o arquivo Excel: {e}")

    def read_file(self, file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            lista_de_dataframes = pd.read_html(StringIO(html_content), header=0)
            tabelas_de_disciplinas = []
            for df_tabela in lista_de_dataframes:
                if 'Cod. Comp.' in df_tabela.columns:
                    tabelas_de_disciplinas.append(df_tabela)
            df_completo = pd.concat(tabelas_de_disciplinas, ignore_index=True)
            column_mapping = {
                'Cod. Comp.': 'codigo',
                'Nome Componente': 'nome',
                'Turma': 'turma',
                'Horário': 'horario',
                'Cap': 'capacidade',
                'Mat': 'matriculados'
            }
            df_selecionado = df_completo[list(column_mapping.keys())].copy()
            df_selecionado['Cap'] = pd.to_numeric(df_selecionado['Cap'], errors='coerce').fillna(0).astype(int)
            df_selecionado['Mat'] = pd.to_numeric(df_selecionado['Mat'], errors='coerce').fillna(0).astype(int)
            df_selecionado['Horário'] = df_selecionado['Horário'].fillna('')
            periodo = re.search(r'(\d{4}-\d)', file).group(1) if re.search(r'(\d{4}-\d)', file) else 'unknown'
            df_selecionado['periodo'] = periodo
            df_renomeado = df_selecionado.rename(columns=column_mapping)
            df_final = df_renomeado[df_renomeado['codigo'].str.startswith('ECT')].copy()
            self.df_list.append(df_final)
        except FileNotFoundError:
            print(f"ERRO: O arquivo '{file}' não foi encontrado.")
            print("Por favor, verifique se o nome e o caminho do arquivo estão corretos.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado durante o processamento: {e}")

class Curriculum(Components):
    def read_file(self, file):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                text_content = f.read()
            blocos_periodo = re.split(r'\n(?=\d+°? PERÍODO)', text_content.strip())
            lista_de_disciplinas = []
            for bloco in blocos_periodo:
                if not bloco.strip():
                    continue
                match_periodo = re.search(r'(\d+)°? PERÍODO', bloco)
                if not match_periodo:
                    continue
                periodo = int(match_periodo.group(1))
                linhas_disciplina = re.findall(r'^(ECT\d{4})\s+(.+?)\s+(\d+)$', bloco, re.MULTILINE)
                for codigo, nome, carga_horaria in linhas_disciplina:
                    lista_de_disciplinas.append({
                        'periodo': periodo,
                        'codigo': codigo,
                        'nome': nome.strip(),
                        'carga_horaria': int(carga_horaria)
                    })
            if not lista_de_disciplinas:
                return
            df_final = pd.DataFrame(lista_de_disciplinas)
            self.df_list.append(df_final)
        except FileNotFoundError:
            print(f"ERRO: O arquivo '{file}' não foi encontrado.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado ao processar o currículo de texto: {e}")


def extrair_tabela_pdf_robusto(caminho_pdf):
    """
    Extrai tabelas de um PDF usando o modo 'stream' com guias manuais para
    colunas e área da tabela, garantindo alta precisão em layouts complexos.

    Args:
        caminho_pdf (str): O caminho para o arquivo PDF.

    Returns:
        pandas.DataFrame: Um DataFrame limpo e corrigido.
    """
    try:
        # 1. Definir a área da tabela na página [x1, y1, x2, y2]
        # (canto inferior esquerdo, canto superior direito)
        # Isso ajuda a ignorar texto fora da área da tabela (cabeçalhos/rodapés).
        # As coordenadas são: x1, y1 (canto superior esquerdo), x2, y2 (canto inferior direito)
        # Formato: [esquerda, cima, direita, baixo]
        area_da_tabela = ['60,720,940,50']

        # 2. Definir as coordenadas X para a divisão das colunas
        # (Mesma lógica da tentativa anterior)
        coordenadas_colunas = [
            '85,270,300,375,420,550,575,600,635,660,685,710,735,760,785,810,835,860,885,910,935'
        ]

        print(f"Lendo o arquivo PDF: {caminho_pdf} com modo 'stream' e guias manuais.")
        tables = camelot.read_pdf(
            caminho_pdf,
            flavor='stream',  # <--- MUDANÇA PRINCIPAL
            pages='all',
            table_areas=area_da_tabela,
            columns=coordenadas_colunas,
            split_text=True
        )
        print(f"Encontrado {tables.n} tabelas no documento.")

        if tables.n == 0:
            print("Nenhuma tabela foi encontrada no PDF com as configurações fornecidas.")
            return None

        # Combina os DataFrames de todas as páginas em um só
        df_completo = pd.concat([table.df for table in tables], ignore_index=True)
        
        print("Tabelas combinadas. Iniciando a limpeza dos dados...")

        # --- Limpeza do DataFrame ---

        # 1. Definir o cabeçalho manualmente, pois o 'stream' pode não pegá-lo
        nomes_colunas = [
            'Código', 'Componente Curricular', 'CH (h)', 'Pré-requisito', 'Correquisito', 'Equivalência',
            'Generalista Diurno', 'Generalista Noturno', 'Aeroespacial e astronomia',
            'Computação Aplicada', 'Negócios Tecnológicos', 'Neurociências',
            'Soluções e tecnologias sustentáveis', 'Tecnologia Ambiental', 'Tecnologia Biomédica',
            'Tecnologia de Computação', 'Tecnologia de Materiais Diurno',
            'Tecnologia de Materiais Noturno', 'Tecnologia Mecânica', 'Tecnologia Mecatrônica',
            'Tecnologia de Petróleo', 'Tecnologia de Telecomunicações'
        ]
        
        # O número de colunas extraídas deve ser igual ao número de nomes definidos
        if len(df_completo.columns) != len(nomes_colunas):
             print(f"Alerta: O número de colunas extraídas ({len(df_completo.columns)}) não corresponde ao esperado ({len(nomes_colunas)}).")
             # Mesmo com o alerta, tentaremos aplicar os nomes que correspondem
             df_completo.columns = nomes_colunas[:len(df_completo.columns)]
        else:
            df_completo.columns = nomes_colunas

        # 2. Limpar o conteúdo das células (remover quebras de linha)
        for col in df_completo.columns:
            # Garante que a coluna é do tipo string antes de usar .str
            df_completo[col] = df_completo[col].astype(str).str.replace('\n', ' ', regex=False).str.strip()

        # 3. Remover linhas de cabeçalho repetidas e linhas vazias
        df_completo = df_completo[df_completo['Código'] != 'Código']
        df_completo.replace(['', 'nan'], np.nan, inplace=True) # Substitui strings vazias e 'nan' por NaN
        df_completo.dropna(how='all', inplace=True) # Remove linhas onde TODAS as colunas são NaN

        df_completo.reset_index(drop=True, inplace=True)
        
        print("Limpeza concluída com sucesso!")
        return df_completo

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return None



if __name__ == "__main__":
    #components = Components("data/raw/2024-2.html", "data/raw/2025-1.html")
    #components.save_to_excel("data/tests/demanda.xlsx")
    #components.stacked_df.info()
    #components.get_unique_stacked_df()
    data = Data(curriculum_file_path="data/cleaned/study1/curriculo.xlsx",
                demand_file_path="data/cleaned/study1/demanda.xlsx",
                camaras_file_path="data/cleaned/study1/camaras.xlsx"
    )
    #df_electives = components.get_electives(data.curriculum_df)
    #print(df_electives.to_string())
    #df_electives.to_excel("data/tests/eletivas.xlsx")
    #curriculum = Curriculum("data/curriculo.txt")
    #curriculum.save_to_excel("data/tests/curriculo.xlsx")
    #curriculum.stacked_df.info()

    # --- Execução do Script ---
    # Substitua 'seu_arquivo.pdf' pelo nome do seu arquivo
    nome_arquivo_pdf = 'data/raw/obrigatorias.pdf' # <--- COLOQUE O NOME DO SEU ARQUIVO AQUI
    df_final = extrair_tabela_pdf_robusto(nome_arquivo_pdf)

    if df_final is not None:
        print("\n### Amostra do DataFrame Final ###")
        print(df_final.head())
        
        print("\n### Informações do DataFrame ###")
        df_final.info()
        print(df_final.to_string())

    # Opcional: Salvar o DataFrame em um arquivo CSV para fácil acesso
    #    nome_arquivo_csv = 'componentes_curriculares.csv'
    #    df_final.to_excell("data/tests/eletivas_enfases.xlsx/", index=False)
    #    print(f"\nDataFrame salvo com sucesso em '{nome_arquivo_csv}'")