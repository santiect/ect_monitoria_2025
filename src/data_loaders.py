import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
import re
import numpy as np

class Data:
    def __init__(self, demand_file_path, projects_file_path, curriculum_file_path, camaras_file_path):
        self.demand_file_path = demand_file_path
        self.projects_file_path = projects_file_path
        self.curriculum_file_path = curriculum_file_path
        self.camaras_file_path = camaras_file_path
        self.load_data()
    
    def load_data(self):
        self.demand_df = self.load_df_from_xlsx(self.demand_file_path)
        self.projects_df = self.load_df_from_xlsx(self.projects_file_path)
        self.curriculum_df = self.load_df_from_xlsx(self.curriculum_file_path)
        self.camaras_df = self.load_df_from_xlsx(self.camaras_file_path)
        assert self.curriculum_df is not None, "ERRO: Currículo não carregado"
        assert self.projects_df is not None, "ERRO: Projetos não carregados"
        assert self.demand_df is not None, "ERRO: Demanda não carregada"
        assert self.camaras_df is not None, "ERRO: Câmaras não carregadas"
        self.pre_process_curriculum()
        self.pre_process_demand()
        self.pre_process_projects()
        self.pre_process_camaras()

    def pre_process_camaras(self):
        df = self.camaras_df
        #print(df.to_string())

    def pre_process_curriculum(self):
        df = self.curriculum_df
        all_prereqs_list = df[~df['pre_requisitos'].isna()]['pre_requisitos'].str.cat(sep=';').split(';')
        unique_prereqs = set(all_prereqs_list)
        df['eh_pre_requisito'] = df['codigo'].isin(unique_prereqs)
        df['pratica'] = df['ch_pratica'] > 0
        df['ch_teorica'] = df['ch_total']-df['ch_pratica']
        #print(self.curriculum_df)

    def pre_process_projects(self):
        df = self.projects_df
        df['docente_ne'] = df['docente_ne']=="sim"
        #print(df)

    def pre_process_demand(self):
        df = self.demand_df
        #print(df)
    
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
            'ch_teorica', 'ch_pratica', 'ch_total', 'pre_requisito'
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
        if global_demand > 0:
            df['prop_ch_total'] = df['ch_total'] / global_ch
        else:
            df['prop_ch_total'] = 0
        df['prop_pre_requisito'] = df['pre_requisito']/self.curriculum_df['codigo'].count()
        df['prop_forca_trabalho'] = df['n_professores']/self.camaras_df['n_professores'].sum()
       

    def get_demand_by_component(self, use_elective=False):
        demand_df = self.demand_df.copy()
        demand_df['turma_principal'] = demand_df['turma'].astype(str).str.extract(r'(\d+)').fillna('0')
        target_demand_df = demand_df
        if not use_elective:
            curriculum_codes = self.curriculum_df['codigo'].unique()
            target_demand_df = demand_df[demand_df['codigo'].isin(curriculum_codes)].copy()
        curriculum_info = self.curriculum_df[['codigo', 'nome', 'camara', 'ch_teorica', 'ch_pratica']].drop_duplicates(subset=['codigo'])
        demand_with_info = pd.merge(
            target_demand_df, 
            curriculum_info, 
            on='codigo', 
            how='left'
        )
        demand_with_info['nome'] = np.where(
            demand_with_info['nome_y'].notna(), 
            demand_with_info['nome_y'], 
            demand_with_info['nome_x']
        )
        demand_with_info.drop(columns=['nome_x', 'nome_y'], inplace=True)
        demand_with_info[['ch_teorica', 'ch_pratica']] = demand_with_info[['ch_teorica', 'ch_pratica']].fillna(0)
        demand_with_info['camara'] = demand_with_info['camara'].fillna('Não definida')
        def aggregate_component(group):
            # ... (esta função interna permanece a mesma) ...
            matriculados = group['matriculados'].sum()
            n_turmas = group.drop_duplicates(subset=['periodo', 'turma_principal']).shape[0]
            grupo_pratico = group[group['ch_pratica'] > 0]
            n_subturmas = grupo_pratico.drop_duplicates(subset=['periodo', 'turma']).shape[0]
            ch_teorica_base = group['ch_teorica'].iloc[0] if not group.empty else 0
            ch_pratica_base = group['ch_pratica'].iloc[0] if not group.empty else 0
            ch_teorica_total = n_turmas * ch_teorica_base
            ch_pratica_total = n_subturmas * ch_pratica_base
            return pd.Series({
                'matriculados': matriculados,
                'n_turmas': n_turmas,
                'n_subturmas': n_subturmas,
                'ch_teorica': ch_teorica_total,
                'ch_pratica': ch_pratica_total
            })
        summary_df = demand_with_info.groupby(
            ['codigo', 'nome', 'camara'], 
        ).apply(aggregate_component,  include_groups=False).reset_index()
        summary_df = summary_df.rename(columns={'nome': 'titulo'})
        int_columns = ['matriculados', 'n_turmas', 'n_subturmas', 'ch_teorica', 'ch_pratica']
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
        #with np.errstate(divide='ignore', invalid='ignore'):
        #     summary_df['ch_por_prof'] = np.divide(summary_df['ch_total'], summary_df['n_professores'])
        #summary_df['ch_por_prof'] = summary_df['ch_por_prof'].replace([np.inf, -np.inf], 0)
        #summary_df['ch_por_prof'] = summary_df['ch_por_prof'].fillna(0).round(2)
        # --- FIM DO CÓDIGO ADICIONADO ---

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
            print(f"Lendo: {file}")
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
            print(f"Lendo: {file}")
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

if __name__ == "__main__":
    components = Components("data/raw/2024-2.html", "data/raw/2025-1.html")
    components.save_to_excel("data/tests/demanda.xlsx")
    #components.stacked_df.info()
    #curriculum = Curriculum("data/curriculo.txt")
    #curriculum.save_to_excel("data/tests/curriculo.xlsx")
    #curriculum.stacked_df.info()
