from src.sim import Simulator
from src.data_loaders import Data
from src.sim import Indexes

data = Data(
    curriculum_file_path="data/cleaned/study2/curriculo.xlsx",
    demand_file_path="data/cleaned/study2/demanda.xlsx",
    camaras_file_path="data/cleaned/study2/camaras.xlsx"
)

s = Simulator(data)

df_component = s.simulate_by_component_and_practice(
    Indexes.IP_TEORICA,
    total=80,
    min_by_compulsory=1,
    min_by_project=0,
    xlsx_output_file="results/study2/bolsas_por_componente.xlsx"
)


df_area = s.simulate_by_area_and_practice(
    Indexes.IP_TEORICA,
    total=80,
    min_by_compulsory=1,
    min_by_project=0,
    xlsx_output_file="results/study2/bolsas_por_camara.xlsx"
)

print(data.curriculum_df.to_string())

data.get_demand_by_component().to_excel('teste.xlsx')

print("\n\n\n")
print("SIMULAÇÃO POR COMPONENTE: ")
print(df_component.to_string())

print("\n\n\n")
print("SIMULAÇÃO POR ÁREA: ")
print(df_area.to_string())