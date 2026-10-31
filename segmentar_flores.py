#!/usr/bin/env python3
"""
segmentar_flores.py
===================
Módulo de processamento digital de imagens para identificação, segmentação
e quantificação de flores azuis em imagens digitais (incluindo RAW .cr3 e formatos convencionais).

Projeto: Mensuração da Área Ocupada por Flores Azuis
Instituição: FATEC Ferraz de Vasconcelos
Disciplina: Visão Computacional
Orientadora: Profa. Márcia Bissaco
Desenvolvedor: Josias Sobrinho
"""

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

try:
    import rawpy
    HAS_RAWPY = True
except ImportError:
    HAS_RAWPY = False


@dataclass
class SegmentacaoResultado:
    """Estrutura com os resultados e métricas da segmentação."""
    caminho_imagem: str
    largura: int
    altura: int
    total_pixels: int
    pixels_flor: int
    taxa_ocupacao_percentual: float
    num_clusters: int
    espaco_cor: str


class SegmentadorFlores:
    """
    Segmentador de flores azuis baseado em análise cromática
    nos espaços CIELAB e HSV com filtragem morfológica.
    """

    def __init__(
        self,
        espaco_cor: str = "lab",
        limiar_b_max: int = 112,
        limiar_a_min: int = 118,
        limiar_L_min: int = 30,
        limiar_L_max: int = 245,
        min_cluster_area: int = 25,
    ):
        """
        Inicializa os parâmetros do segmentador.

        :param espaco_cor: 'lab', 'hsv' ou 'combinado'.
        :param limiar_b_max: Teto do canal b* (valores < 128 indicam azul no CIELAB do OpenCV).
        :param limiar_a_min: Piso do canal a* (valores > 118 incluem nuances violáceas/pétalas).
        :param limiar_L_min: Piso de luminância L* (evita falsos positivos em sombras profundas).
        :param limiar_L_max: Teto de luminância L* (evita reflexos especulares extremos).
        :param min_cluster_area: Área mínima em pixels para descartar ruídos pontuais.
        """
        self.espaco_cor = espaco_cor.lower()
        self.limiar_b_max = limiar_b_max
        self.limiar_a_min = limiar_a_min
        self.limiar_L_min = limiar_L_min
        self.limiar_L_max = limiar_L_max
        self.min_cluster_area = min_cluster_area

    @staticmethod
    def carregar_imagem(caminho: str | Path, half_size_raw: bool = False) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Carrega imagem a partir do disco, suportando arquivos RAW (.cr3) e convencionais (.png, .jpg, .tif).

        :param caminho: Caminho do arquivo de imagem.
        :param half_size_raw: Se True, decodifica RAW em meia-resolução (muito mais rápido para prévias).
        :return: Tupla com matriz BGR uint8 e dimensões originais (altura, largura).
        """
        caminho_p = Path(caminho)
        if not caminho_p.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        ext = caminho_p.suffix.lower()

        if ext in [".cr3", ".cr2", ".nef", ".arw", ".dng"]:
            if not HAS_RAWPY:
                raise ImportError("O pacote 'rawpy' é necessário para decodificar arquivos RAW.")
            with rawpy.imread(str(caminho_p)) as raw:
                # Decodificação linear com balanço de branco do sensor
                rgb = raw.postprocess(
                    use_camera_wb=True,
                    half_size=half_size_raw,
                    no_auto_bright=True,
                    output_bps=8
                )
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            return bgr, (bgr.shape[0], bgr.shape[1])

        # Formatos convencionais
        bgr = cv2.imread(str(caminho_p))
        if bgr is None:
            raise ValueError(f"Não foi possível decodificar a imagem: {caminho}")
        return bgr, (bgr.shape[0], bgr.shape[1])

    def _mascara_lab(self, bgr: np.ndarray) -> np.ndarray:
        """Gera máscara binária baseada no espaço CIELAB."""
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab)
        L, a, b = cv2.split(lab)

        # No OpenCV:
        # L: [0, 255]
        # a: [0, 255] (128 = neutro, <128 verde, >128 vermelho/magenta)
        # b: [0, 255] (128 = neutro, <128 azul, >128 amarelo)
        cond_azul = (b <= self.limiar_b_max)
        cond_tom = (a >= self.limiar_a_min)
        cond_luz = (L >= self.limiar_L_min) & (L <= self.limiar_L_max)

        mascara = cond_azul & cond_tom & cond_luz
        return (mascara.astype(np.uint8)) * 255

    def _mascara_hsv(self, bgr: np.ndarray) -> np.ndarray:
        """Gera máscara binária baseada no espaço HSV."""
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
        # Faixa azul-violeta em escala OpenCV (H: 0-180, S: 0-255, V: 0-255)
        # 100 a 140 cobre de azul puro (120) até violeta (135-140)
        limite_inf = np.array([100, 45, 40], dtype=np.uint8)
        limite_sup = np.array([140, 255, 250], dtype=np.uint8)
        return cv2.inRange(hsv, limite_inf, limite_sup)

    def segmentar(self, bgr: np.ndarray) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Executa a segmentação completa: limiarização cromática + filtragem morfológica + descarte de ruído.

        :param bgr: Matriz da imagem em formato BGR.
        :return: Tupla (mascara_binaria, mascara_limpa_com_contornos, contagem_pixels_flores).
        """
        if self.espaco_cor == "lab":
            mascara_crua = self._mascara_lab(bgr)
        elif self.espaco_cor == "hsv":
            mascara_crua = self._mascara_hsv(bgr)
        elif self.espaco_cor == "combinado":
            m_lab = self._mascara_lab(bgr)
            m_hsv = self._mascara_hsv(bgr)
            mascara_crua = cv2.bitwise_and(m_lab, m_hsv)
        else:
            raise ValueError(f"Espaço de cor desconhecido: {self.espaco_cor}")

        # Operações Morfológicas com elemento estruturante elíptico (adaptado ao contorno de pétalas)
        kernel_abertura = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        kernel_fechamento = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

        # 1. Abertura: remove ruído salpicado e pixels isolados
        m_aberta = cv2.morphologyEx(mascara_crua, cv2.MORPH_OPEN, kernel_abertura)
        # 2. Fechamento: preenche pequenas fissuras e reflexos internos das pétalas
        m_fechada = cv2.morphologyEx(m_aberta, cv2.MORPH_CLOSE, kernel_fechamento)

        # Filtro de conectividade por área de contorno
        contornos, _ = cv2.findContours(m_fechada, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        mascara_final = np.zeros_like(m_fechada)

        num_clusters = 0
        for cnt in contornos:
            area = cv2.contourArea(cnt)
            if area >= self.min_cluster_area:
                cv2.drawContours(mascara_final, [cnt], -1, 255, thickness=cv2.FILLED)
                num_clusters += 1

        pixels_flores = int(np.count_nonzero(mascara_final))
        return mascara_final, contornos, pixels_flores

    def processar(self, caminho_img: str | Path, half_size_raw: bool = False) -> Tuple[SegmentacaoResultado, np.ndarray, np.ndarray]:
        """
        Processa completamente um arquivo de imagem e calcula as métricas exigidas.
        """
        bgr, (altura, largura) = self.carregar_imagem(caminho_img, half_size_raw=half_size_raw)
        mascara, contornos, pixels_flor = self.segmentar(bgr)

        total_pixels = altura * largura
        taxa_ocupacao = (pixels_flor / total_pixels) * 100.0 if total_pixels > 0 else 0.0

        num_clusters = sum(1 for c in contornos if cv2.contourArea(c) >= self.min_cluster_area)

        resultado = SegmentacaoResultado(
            caminho_imagem=str(caminho_img),
            largura=largura,
            altura=altura,
            total_pixels=total_pixels,
            pixels_flor=pixels_flor,
            taxa_ocupacao_percentual=round(taxa_ocupacao, 4),
            num_clusters=num_clusters,
            espaco_cor=self.espaco_cor.upper(),
        )

        return resultado, bgr, mascara

    @staticmethod
    def gerar_painel_visual(
        bgr_original: np.ndarray,
        mascara: np.ndarray,
        resultado: SegmentacaoResultado,
        max_dim: int = 1400,
    ) -> np.ndarray:
        """
        Gera um painel comparativo de altíssima qualidade visual contendo:
        1. Imagem Original com contornos e máscara sobreposta translúcida
        2. Máscara Binária pura de segmentação
        3. Recorte isolado das flores com cor original
        4. Cabeçalho com métricas formais (área, pixels, percentual de ocupação)
        """
        h, w = bgr_original.shape[:2]

        # Redimensionamento proporcional para visualização sem perda de aspecto
        escala = min(1.0, max_dim / max(h, w))
        if escala < 1.0:
            novo_w = int(w * escala)
            novo_h = int(h * escala)
            bgr_disp = cv2.resize(bgr_original, (novo_w, novo_h), interpolation=cv2.INTER_AREA)
            masc_disp = cv2.resize(mascara, (novo_w, novo_h), interpolation=cv2.INTER_NEAREST)
        else:
            bgr_disp = bgr_original.copy()
            masc_disp = mascara.copy()

        disp_h, disp_w = bgr_disp.shape[:2]

        # 1. Sobreposição Translúcida (Overlay Ciano/Verde fluorescente)
        overlay = bgr_disp.copy()
        regiao_flor = masc_disp > 0
        cor_destaque = np.array([0, 255, 128], dtype=np.uint8)  # Verde-água vibrante
        overlay[regiao_flor] = cv2.addWeighted(
            bgr_disp[regiao_flor], 0.45,
            np.tile(cor_destaque, (np.count_nonzero(regiao_flor), 1)), 0.55,
            0
        )

        # Delinear contornos em vermelho para precisão analítica
        contornos, _ = cv2.findContours(masc_disp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(overlay, contornos, -1, (0, 0, 255), 1)

        # 2. Máscara binária BGR
        masc_bgr = cv2.cvtColor(masc_disp, cv2.COLOR_GRAY2BGR)

        # 3. Flores isoladas (fundo preto)
        flores_isoladas = cv2.bitwise_and(bgr_disp, bgr_disp, mask=masc_disp)

        # Compor painel triplo lado a lado
        painel_corpo = np.hstack([bgr_disp, overlay, flores_isoladas])
        painel_w = painel_corpo.shape[1]

        # Criar faixa superior de cabeçalho informativo
        altura_banner = 90
        banner = np.full((altura_banner, painel_w, 3), 25, dtype=np.uint8)

        # Textos informativos no banner
        linha1 = f"FATEC-FV | Visao Computacional - Deteccao de Flores Azuis ({resultado.espaco_cor})"
        linha2 = (
            f"Arquivo: {Path(resultado.caminho_imagem).name} | "
            f"Dimensoes: {resultado.largura}x{resultado.altura} px | "
            f"Total: {resultado.total_pixels:,} px"
        )
        linha3 = (
            f"Pixels Flor: {resultado.pixels_flor:,} px | "
            f"Taxa de Ocupacao: {resultado.taxa_ocupacao_percentual:.4f}% | "
            f"Clusters Detectados: {resultado.num_clusters}"
        )

        fonte = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(banner, linha1, (20, 25), fonte, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(banner, linha2, (20, 52), fonte, 0.55, (200, 200, 200), 1, cv2.LINE_AA)
        cv2.putText(banner, linha3, (20, 78), fonte, 0.60, (0, 255, 128), 2, cv2.LINE_AA)

        # Subtítulos das colunas
        def adicionar_rotulo(img, texto):
            cv2.rectangle(img, (10, 10), (10 + len(texto) * 11, 35), (0, 0, 0), -1)
            cv2.putText(img, texto, (15, 28), fonte, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        adicionar_rotulo(bgr_disp, "1. Imagem Original")
        adicionar_rotulo(overlay, "2. Segmentacao (Overlay)")
        adicionar_rotulo(flores_isoladas, "3. Flores Isoladas")

        painel_final = np.vstack([banner, np.hstack([bgr_disp, overlay, flores_isoladas])])
        return painel_final


def main():
    parser = argparse.ArgumentParser(
        description="Segmentação e Quantificação de Flores Azuis em Imagens Digitais"
    )
    parser.add_argument(
        "-i", "--input", required=True, help="Caminho do arquivo de imagem ou pasta de imagens"
    )
    parser.add_argument(
        "-o", "--output", default="output", help="Diretório para salvar os resultados (padrão: output)"
    )
    parser.add_argument(
        "--space", default="lab", choices=["lab", "hsv", "combinado"],
        help="Espaço de cor a utilizar (padrão: lab)"
    )
    parser.add_argument(
        "--half-raw", action="store_true",
        help="Se informado para arquivos RAW (.cr3), processa em meia-resolução acelerada"
    )
    parser.add_argument(
        "--min-area", type=int, default=30,
        help="Área mínima de cluster em pixels para filtrar ruído (padrão: 30)"
    )
    parser.add_argument(
        "--save-mask-only", action="store_true",
        help="Salva também o arquivo PNG binário da máscara"
    )

    args = parser.parse_args()

    caminho_entrada = Path(args.input)
    diretorio_saida = Path(args.output)
    diretorio_saida.mkdir(parents=True, exist_ok=True)

    arquivos = []
    if caminho_entrada.is_dir():
        for ext in ("*.cr3", "*.CR3", "*.jpg", "*.jpeg", "*.png", "*.tif"):
            arquivos.extend(caminho_entrada.glob(ext))
    else:
        arquivos = [caminho_entrada]

    if not arquivos:
        print(f"Nenhum arquivo de imagem encontrado em: {caminho_entrada}")
        sys.exit(1)

    print(f"\n==================================================================")
    print(f"  FATEC-FV - Pipeline de Segmentacao de Flores Azuis")
    print(f"  Modo: {args.space.upper()} | Imagens a processar: {len(arquivos)}")
    print(f"==================================================================\n")

    segmentador = SegmentadorFlores(espaco_cor=args.space, min_cluster_area=args.min_area)
    resultados = []

    for arq in arquivos:
        print(f"[*] Processando: {arq.name}...")
        try:
            resultado, bgr, mascara = segmentador.processar(arq, half_size_raw=args.half_raw)
            resultados.append(asdict(resultado))

            stem = arq.stem
            # 1. Salvar painel visual comparativo
            caminho_painel = diretorio_saida / f"{stem}_painel_segmentacao.jpg"
            painel = segmentador.gerar_painel_visual(bgr, mascara, resultado)
            cv2.imwrite(str(caminho_painel), painel)

            # 2. Salvar máscara binária se solicitado
            if args.save_mask_only:
                caminho_mascara = diretorio_saida / f"{stem}_mascara_binaria.png"
                cv2.imwrite(str(caminho_mascara), mascara)

            print(f"    -> Dimensoes: {resultado.largura}x{resultado.altura} px")
            print(f"    -> Pixels flor detectados: {resultado.pixels_flor:,} px")
            print(f"    -> Taxa de ocupacao: {resultado.taxa_ocupacao_percentual:.4f}%")
            print(f"    -> Painel salvo em: {caminho_painel}\n")

        except Exception as e:
            print(f"    [ERRO] Falha ao processar {arq.name}: {e}\n")

    # Salvar relatório consolidado em JSON
    caminho_json = diretorio_saida / "metricas_segmentacao.json"
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)

    print(f"[+] Relatório consolidado em JSON salvo em: {caminho_json}")
    print(f"[+] Processamento concluído com sucesso.\n")


if __name__ == "__main__":
    main()

