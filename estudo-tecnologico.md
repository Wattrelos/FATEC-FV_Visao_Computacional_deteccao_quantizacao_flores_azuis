# Estudo Tecnológico e Metodológico: Pipeline Óptico e Cromático (RAW $\to$ CIELAB)

> **Documento de Engenharia e Pesquisa Aplicada**  
> **Autor:** Josias Sobrinho | **Orientação:** Profa. Márcia Bissaco  
> **Projeto:** Segmentação e Quantificação de Flores Azuis em Imagens de Alta Resolução  

---

## 1. Resumo Executivo e Justificativa Científica

O processamento digital de imagens (PDI) em ambientes agrícolas abertos enfrenta três desafios óptico-físicos fundamentais:
1. **Flutuações de Iluminação:** A alternância entre radiação solar direta, difusa e sombreamento (folhagens e nuvens) altera drasticamente as intensidades dos canais RGB;
2. **Compressão Destrutiva (JPEG de 8 bits):** Arquivos JPEG sofrem compressão por perda (DCT e subamostragem cromática 4:2:0) e aplicação forçada de curva gama ($\gamma \approx 2.2$), destruindo a linearidade dos fótons capturados pelo sensor;
3. **Complexidade Morfológica Botânica:** Pétalas com inclinação angular em relação ao plano do sensor projetam formas elípticas e sofrem efeitos de oclusão parcial e desfoque de profundidade de campo (*bokeh*).

Para solucionar esses gargalos, este projeto estabelece um pipeline estruturado a partir da decodificação linear de arquivos **RAW (Canon `.cr3`)** e migração para o espaço de cor **CIELAB ($L^*a^*b^*$)**, garantindo estabilidade métrica invariante à iluminação.

---

## 2. Fundamentação Teórica dos Espaços de Cor

### 2.1 Limitações do Espaço BGR/RGB
No espaço RGB (ou BGR adotado pelo OpenCV), a informação cromática está matematicamente correlacionada com a intensidade luminosa:

$$I = \frac{R + G + B}{3}$$

Quando uma pétala azul entra na sombra de uma folha, tanto o canal Azul quanto os canais Vermelho e Verde decaem proporcionalmente. Um limiar estático em BGR falha ao classificar a flor sombreada como fundo ou ao confundir folhas claras com tons não-alvo.

### 2.2 O Espaço CIELAB ($L^*a^*b^*$)
Normalizado pela Comissão Internacional de Iluminação (CIE, 2018), o sistema CIELAB é projetado para replicar a percepção visual humana com **uniformidade perceptual**:

```mermaid
flowchart TD
    RAW["Sensor RAW (14-bit Linear)"] -->|rawpy (use_camera_wb=True)| RGB16["RGB Linear (16-bit)"]
    RGB16 -->|OpenCV cvtColor| BGR16["BGR"]
    BGR16 -->|CIE XYZ Transform| LAB["CIELAB (L*, a*, b*)"]
    LAB --> L["Canal L* (Luminosidade: 0 a 100)"]
    LAB --> A["Canal a* (Verde (-) <--> Vermelho (+))"]
    LAB --> B["Canal b* (Azul (-) <--> Amarelo (+))"]
```

- **Canal $L^*$ (Luminância):** Varia de 0 (preto absoluto) a 100 (branco difuso). Absorve variações de sombras e iluminação solar.
- **Canal $a^*$ (Eixo Verde-Vermelho):** Valores negativos indicam tons esverdeados (típicos de folhagens e caules); valores positivos indicam tons magenta/vermelhos.
- **Canal $b^*$ (Eixo Azul-Amarelo):** Valores fortemente negativos indicam comprimentos de onda curtos (azuis); valores positivos indicam amarelos.

> [!NOTE]
> **Mapeamento no OpenCV (uint8):**  
> Para matrizes de 8 bits no OpenCV:
> - $L \in [0, 255]$ (mapeado de $L^* \times \frac{255}{100}$)
> - $a \in [0, 255]$ (onde 128 representa o zero cromático; $< 128$ é verde, $> 128$ é magenta/vermelho)
> - $b \in [0, 255]$ (onde 128 representa o zero cromático; $< 128$ é **azul**, $> 128$ é amarelo)

---

## 3. Pipeline de Processamento Linear

### 3.1 Etapas do Fluxo
1. **Decodificação Linear de Alta Resolução (`rawpy`):**
   O sensor da câmera (Canon EOS R5 C) fornece 14 bits por canal (45 megapixels). A decodificação via `rawpy.imread()` com `bit_depth=16` preserva a relação linear entre fótons incidentes e valores numéricos sem achatamento de realces.
2. **Conversão de Ordem de Canais:**
   A matriz fornecida pelo decodificador linear está em padrão RGB e é invertida para BGR (`cv2.COLOR_RGB2BGR`) para compatibilidade nativa com o OpenCV.
3. **Mapeamento Perceptual para CIELAB:**
   Conversão via `cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab)`.
4. **Isolamento Cromático e Limiarização:**
   Como as flores azuis na base de dados apresentam tonalidades azul-violáceas (com reflexos de antocianina), a segmentação explora a condição conjunta:
   - Baixo valor no canal $b^*$ ($b < 115$), garantindo a componente azul;
   - Valor controlado no canal $a^*$ ($a > 125$), abrangendo o matiz violáceo característico das pétalas;
   - Rejeição de ruídos de sombra profunda no canal $L^*$ ($L > 25$).

---

## 4. Implementação de Referência (Código-Base)

```python
import cv2
import numpy as np
import rawpy

def carregar_raw_para_lab(caminho_raw: str, downscale_factor: int = 2) -> tuple[np.ndarray, np.ndarray]:
    """
    Decodifica o arquivo RAW (.cr3) preservando fidelidade cromática
    e realiza a conversão para o espaço CIELAB.
    """
    with rawpy.imread(caminho_raw) as raw:
        # Decodificação com balanço de branco da câmera
        rgb = raw.postprocess(
            use_camera_wb=True,
            half_size=(downscale_factor == 2),
            no_auto_bright=True,
            output_bps=8
        )
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab)
    return bgr, lab

def segmentar_flores_azuis(lab_img: np.ndarray) -> np.ndarray:
    """
    Aplica limiarização nos canais cromáticos b* (azul) e a* (magenta)
    e pós-processamento com operadores morfológicos.
    """
    L, a, b = cv2.split(lab_img)
    
    # Critério cromático: b* baixo (azul) e a* ligeiramente elevado (violáceo)
    mascara_azul = (b < 112) & (a > 120) & (L > 30)
    mascara_uint8 = (mascara_azul.astype(np.uint8)) * 255
    
    # Filtragem morfológica: abertura (elimina ruído isolado) e fechamento (preenche lacunas internas)
    kernel_elipse = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mascara_limpa = cv2.morphologyEx(mascara_uint8, cv2.MORPH_OPEN, kernel_elipse)
    mascara_final = cv2.morphologyEx(mascara_limpa, cv2.MORPH_CLOSE, kernel_elipse)
    
    return mascara_final
```

---

## 5. Desafios Ópticos e Morfológicos Identificados

| Desafio Identificado | Causa Física / Botânica | Impacto no Algoritmo | Solução Implementada |
| :--- | :--- | :--- | :--- |
| **Distorção Elíptica de Pétalas** | Ângulo de inclinação do eixo da flor em relação ao plano normal do sensor. | Pétalas deixam de ser circulares e projetam elipses com excentricidade variável. | Adoção de elementos estruturantes elípticos (`cv2.MORPH_ELLIPSE`) nas operações morfológicas. |
| **Pétalas a 90° (Vista Lateral)** | Eixo floral paralelo ao plano focal da câmera. | Redução drástica da área visível e sobreposição com sépalas verdes. | Análise conjunta do canal $a^*$ para diferenciar a base do cálice da pétala azul. |
| **Sombras Próprias e Projetadas** | Iluminação zenital direta projetando sombra de folhas superiores sobre as flores. | Variação extrema de brilho nas mesmas pétalas. | Supressão completa do canal $L^*$ no cálculo da distância cromática. |
| **Efeito de Borda (*Antialiasing*)** | Transição suave de pixels na fronteira entre a pétala e o fundo. | Pixels de borda com valores intermediários de azul e verde. | Ajuste do threshold com suíte sintética de referência calibrada para medir o erro relativo. |
| **Reflexos Especulares** | Superfície cerosa da flor refletindo diretamente a luz solar (*glare*). | Pixels saturados com perda de cromaticidade ($L^* \approx 255$, $a^*, b^* \approx 128$). | Interpolação morfológica por fechamento (`MORPH_CLOSE`) das regiões de reflexo interno. |

---

## 6. Conclusões e Próximos Passos

O desacoplamento luminância/crominância através do espaço CIELAB, aliado à precisão de decodificação de 16 bits do LibRaw/rawpy, fornece um alicerce estável para a segmentação de espécimes florais azuis em condições reais de campo. 

O próximo passo é a consolidação do módulo executável de linha de comando (`segmentar_flores.py`) e a bateria de testes de aceitação com imagens sintéticas (`validar_sinteticos.py`).
