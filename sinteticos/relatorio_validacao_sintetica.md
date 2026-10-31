# Relatório de Validação Experimental com Imagens Sintéticas

> **Atividade Prática:** Processamento e Quantificação de Flores Azuis  
> **Instituição:** Faculdade de Tecnologia de Ferraz de Vasconcelos (FATEC-FV)  
> **Disciplina:** Visão Computacional | **Orientadora:** Profa. Márcia Bissaco  
> **Pesquisador:** Josias Sobrinho  

---

## 1. Resumo Executivo da Validação

Em conformidade com a **Etapa 5** do plano de atividades, foram desenvolvidas **3 imagens sintéticas de referência** com quantidades exatas de pixels florais conhecidas previamente (*Ground Truth*). O objetivo desta validação é calcular o erro percentual entre a área real e a área detectada pelo mesmo algoritmo aplicado às imagens reais.

$$E_{\mathbin{\%}} = \left( \frac{|N_{\text{detectado}} - N_{\text{real}}|}{N_{\text{real}}} \right) \times 100\%$$

---

## 2. Tabela Comparativa de Precisão

| Cenário | Descrição | Pixels Reais (GT) | Pixels Detectados | Erro Absoluto | **Erro Percentual** | Ocupação Real | Ocupação Det. | IoU (Jaccard) | F1-Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `CENARIO_01` | Cenario 1 - Geometria regular, flores circulares e fundo verde uniforme | 69,884 | 69,957 | 73 | **0.10%** | 7.28% | 7.29% | 99.90% | 99.95% |
| `CENARIO_02` | Cenario 2 - Eixo floral inclinado (elipses) e fundo gradiente solo/folhagem | 90,980 | 90,971 | 9 | **0.01%** | 9.48% | 9.48% | 99.99% | 99.99% |
| `CENARIO_03` | Cenario 3 - Heterogeneidade cromatica (matizes azul/violeta) e sobreposicao | 40,132 | 40,162 | 30 | **0.07%** | 4.18% | 4.18% | 99.93% | 99.96% |

---

## 3. Discussão Técnica e Análise de Limitações

1. **Comportamento em Formas Regulares (Cenário 1):**
   - Apresentou erro mínimo, confirmando que a calibração cromática no canal $b^*$ do CIELAB isola perfeitamente os comprimentos de onda de azul sem vazamento para o fundo verde.

2. **Impacto da Inclinação Elíptica (Cenário 2):**
   - As flores representadas por elipses oblíquas mantiveram estabilidade com erro percentual muito reduzido, demonstrando a adequação do elemento estruturante elíptico (`MORPH_ELLIPSE`) nas etapas de abertura e fechamento.

3. **Heterogeneidade Cromática e Sobreposição (Cenário 3):**
   - Mesmo sob variação de matizes (de azul celeste até nuances violáceas) e fundo complexo com textura, o índice de IoU permaneceu elevado, comprovando a tolerância do intervalo $a^* \in [118, 255]$ e $b^* \le 112$.

---

## 4. Conclusão

O método demonstrou excelente acurácia e repetibilidade matemática, satisfazendo plenamente todos os critérios normativos de avaliação estabelecidos para a disciplina.
