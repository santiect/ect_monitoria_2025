from src.sim import Simulator
from src.data_loaders import Data
from src.sim import Indexes

weights = {
    "docente_NE":              0.0,
    "laboratorio":             0.0,
    "pre_requisito":           0.0,
    "razao_discente_docente":  0.0,
    "ch":                      0.0,                  
}

data = Data(curriculum_file_path="data/study/curriculo.xlsx",
            demand_file_path="data/study/demanda.xlsx",
            projects_file_path="data/study/projetos.xlsx",
            camaras_file_path="data/study/camaras.xlsx"
)
s = Simulator(data, weights)

s.simulate_by_component(Indexes.IP_COMPONENTE,
                        total=80, 
                        use_elective=False,
                        min_by_project=1,
                        xlsx_output_file="data/study/results/bolsas_por_componente.xlsx")

s.simulate_by_area(Indexes.IP_COMPONENTE,
                   total=80,
                   use_elective=False,
                   min_by_project=1,
                   xlsx_output_file="data/study/results/bolsas_por_camara.xlsx")

s.simulate_by_component_and_practice(Indexes.IP_TEORICA,
                                total=80,
                                min_by_project=1,
                                xlsx_output_file="data/study/results/bolsas_por_componente_praticas.xlsx")


s.simulate_by_area_and_practice(Indexes.IP_TEORICA,
                                total=80,
                                min_by_project=1,
                                xlsx_output_file="data/study/results/bolsas_por_camara_praticas.xlsx")
    
