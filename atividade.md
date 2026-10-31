# TASK SPEC: Segmentação e Quantificação de Flores Azuis

## 1. Parameters & Metadata
```yaml
task_id: "pdi_deteccao_flores_azuis"
academic_metadata:
  institution: "Faculdade de Tecnologia de Ferraz de Vasconcelos (FATEC-FV)"
  course: "Graduação em Análise e Desenvolvimento de Sistemas (ADS)"
  subject: "Visão Computacional"
  advisor: "Profa. Márcia Bissaco"
  author: "Josias Sobrinho"

target_domain:
  class_name: "blue_flower"
  raw_sensor: "Canon EOS R5 C (45 MP, .cr3, 14-bit linear)"
  color_space_primary: "CIELAB"
  color_space_auxiliary: ["HSV", "BGR"]
  
thresholds_cielab_opencv_uint8:
  b_channel_max: 112     # Eixo Azul-Amarelo (neutro=128, <128 azul, >128 amarelo)
  a_channel_min: 118     # Eixo Verde-Vermelho (captura nuances violáceas/pétalas)
  L_channel_min: 30      # Piso de luminosidade (rejeita sombras profundas)
  L_channel_max: 245     # Teto de luminosidade (rejeita reflexos especulares)
  min_cluster_area: 25   # Filtro de conectividade (descarte de ruído pontual)

morphology:
  kernel_shape: "MORPH_ELLIPSE"
  opening_ksize: [3, 3]  # Elimina ruído salpicado e pixels isolados
  closing_ksize: [5, 5]  # Preenche fissuras internas e reflexos em pétalas

validation_suite:
  synthetic_samples: 3
  scenarios:
    - id: "CENARIO_01"
      name: "Geometria regular e simetria radial"
      variations: ["5x flores circulares", "fundo folhagem uniforme"]
    - id: "CENARIO_02"
      name: "Eixo floral inclinado"
      variations: ["pétalas elípticas rotacionadas", "fundo gradiente solo/folha"]
    - id: "CENARIO_03"
      name: "Heterogeneidade cromática"
      variations: ["matizes azul a violeta", "sobreposição", "fundo texturizado"]

metrics_schema:
  absolute_flower_pixels: int
  total_image_pixels: int
  occupancy_ratio_pct: float    # (flower_pixels / total_pixels) * 100
  percentage_error_pct: float   # (|detected - ground_truth| / ground_truth) * 100
  iou_jaccard_pct: float        # (intersection / union) * 100
  dice_f1_score_pct: float      # (2 * intersection / (gt + det)) * 100
```

## 2. Functional Pipeline & Type Contracts
```python
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import numpy as np

@dataclass
class SegmentacaoResultado:
    caminho_imagem: str
    largura: int
    altura: int
    total_pixels: int
    pixels_flor: int
    taxa_ocupacao_percentual: float
    num_clusters: int
    espaco_cor: str

@dataclass
class MetricasValidacao:
    id_cenario: str
    descricao: str
    largura: int
    altura: int
    total_pixels: int
    pixels_real_gt: int
    pixels_detectados: int
    erro_absoluto: int
    erro_percentual: float
    taxa_ocupacao_real: float
    taxa_ocupacao_detectada: float
    iou_jaccard: float
    dice_f1: float

class FlowerSegmentationInterface:
    def segmentar(self, bgr: np.ndarray) -> Tuple[np.ndarray, List, int]:
        """
        Executa a segmentação completa: limiarização cromática no CIELAB,
        filtragem morfológica elíptica e descarte de ruído por conectividade.
        Retorno: (mascara_binaria, contornos, pixels_flor)
        """
        ...

    def processar(self, caminho_img: str | Path, half_size_raw: bool = False) -> Tuple[SegmentacaoResultado, np.ndarray, np.ndarray]:
        """
        Carrega imagem RAW (.cr3) ou convencional, aplica a segmentação
        e calcula métricas de área absoluta e taxa de ocupação global.
        """
        ...
```

## 3. Strict Mathematical Constraints & Rules
- [x] **Normalização Global da Área**:
  $$\tau = \left( \frac{N_{\text{flores}}}{W \times H} \right) \times 100\%$$
  O denominador **deve ser** a área total da imagem ($W \times H$), e não o subconjunto de vegetação.
- [x] **Ground Truth Determinístico a Priori**:
  Imagens sintéticas de referência devem possuir contagem exata prévia de pixels ($N_{\text{real}}$), gravada diretamente a partir de máscaras binárias discretas antes da renderização cromática.
- [x] **Fórmula do Erro Relativo Percentual**:
  $$E_{\%} = \left( \frac{|N_{\text{detectado}} - N_{\text{real}}|}{N_{\text{real}}} \right) \times 100\%$$
- [x] **Consistência do Método**:
  O procedimento algorítmico e os limiares cromáticos aplicados às imagens sintéticas devem ser rigorosamente idênticos aos aplicados às imagens reais.

## 4. Execution Artifacts & Benchmark Results
- [x] **Processamento das Imagens Reais (`output/`)**:
  - `R5C_4430.cr3`: $760.539$ pixels de flor detectados | Taxa de Ocupação: **$6,7964\%$**
  - `R5C_4431.cr3`: $603.809$ pixels de flor detectados | Taxa de Ocupação: **$5,3958\%$**
- [x] **Suíte de Validação Sintética (`sinteticos/`)**:
  - `CENARIO_01`: Real: $69.884$ px | Detectado: $69.957$ px | $E_{\%} = \mathbf{0,10\%}$ | IoU: $99,90\%$
  - `CENARIO_02`: Real: $90.980$ px | Detectado: $90.971$ px | $E_{\%} = \mathbf{0,01\%}$ | IoU: $99,99\%$
  - `CENARIO_03`: Real: $40.132$ px | Detectado: $40.162$ px | $E_{\%} = \mathbf{0,07\%}$ | IoU: $99,93\%$
- [x] **Painéis Visuais e Relatórios**:
  - `output/*_painel_segmentacao.jpg` (Visualização lado a lado: Original, Overlay, Isolada)
  - `output/metricas_segmentacao.json` (Consolidação estruturada de métricas reais)
  - `sinteticos/relatorio_validacao_sintetica.md` (Relatório analítico das limitações e precisão)
  - `sinteticos/resultados_validacao.json` (Métricas tabuladas de validação com Ground Truth)

        ...
```

## 3. Strict Mathematical Constraints & Rules
- [x] **Normalização Global da Área**:
  $$\tau = \left( \frac{N_{\text{flores}}}{W \times H} \right) \times 100\%$$
  O denominador **deve ser** a área total da imagem ($W \times H$), e não o subconjunto de vegetação.
- [x] **Ground Truth Determinístico a Priori**:
  Imagens sintéticas de referência devem possuir contagem exata prévia de pixels ($N_{\text{real}}$), gravada diretamente a partir de máscaras binárias discretas antes da renderização cromática.
- [x] **Fórmula do Erro Relativo Percentual**:
  $$E_{\%} = \left( \frac{|N_{\text{detectado}} - N_{\text{real}}|}{N_{\text{real}}} \right) \times 100\%$$
- [x] **Consistência do Método**:
  O procedimento algorítmico e os limiares cromáticos aplicados às imagens sintéticas devem ser rigorosamente idênticos aos aplicados às imagens reais.

## 4. Execution Artifacts & Benchmark Results
- [x] **Processamento das Imagens Reais (`output/`)**:
  - `R5C_4430.cr3`: $760.539$ pixels de flor detectados | Taxa de Ocupação: **$6,7964\%$**
  - `R5C_4431.cr3`: $603.809$ pixels de flor detectados | Taxa de Ocupação: **$5,3958\%$**
- [x] **Suíte de Validação Sintética (`sinteticos/`)**:
  - `CENARIO_01`: Real: $69.884$ px | Detectado: $69.957$ px | $E_{\%} = \mathbf{0,10\%}$ | IoU: $99,90\%$
  - `CENARIO_02`: Real: $90.980$ px | Detectado: $90.971$ px | $E_{\%} = \mathbf{0,01\%}$ | IoU: $99,99\%$
  - `CENARIO_03`: Real: $40.132$ px | Detectado: $40.162$ px | $E_{\%} = \mathbf{0,07\%}$ | IoU: $99,93\%$
- [x] **Painéis Visuais e Relatórios**:
  - `output/*_painel_segmentacao.jpg` (Visualização lado a lado: Original, Overlay, Isolada)
  - `output/metricas_segmentacao.json` (Consolidação estruturada de métricas reais)
  - `sinteticos/relatorio_validacao_sintetica.md` (Relatório analítico das limitações e precisão)
  - `sinteticos/resultados_validacao.json` (Métricas tabuladas de validação com Ground Truth)