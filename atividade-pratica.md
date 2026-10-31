# Atividade prática — Processamento e quatificação das flores

## Instructions

Objetivo: Aplicar técnicas de processamento digital de imagens para identificar, segmentar e quantificar a área ocupada por flores azuis em imagens digitais, bem como avaliar a precisão do método utilizado por meio de testes com imagens sintéticas de referência.
Instruções

Realize o processamento da imagem fornecida, utilizando um software de processamento digital de imagens ou desenvolvendo sua própria solução computacional.


### A atividade deverá contemplar as seguintes etapas:


1. Identificação e segmentação das flores 

Identifique e segmente as regiões correspondentes às flores  presentes na imagem, diferenciando-as dos demais elementos e cores do fundo. Utilize critérios de identificação baseados nas características de cor, como tonalidade, saturação e brilho, ou outro método de segmentação que considere adequado.


2. Quantificação da área

Determine a quantidade absoluta de pixels correspondentes às flores. Com base nessa informação, calcule a área total ocupada pelas flores na imagem.


3. Cálculo do percentual de ocupação

Calcule o percentual da área ocupada pelas flores em relação à área total da imagem original.


4. Visualização dos resultados

Apresente a imagem processada, contendo as regiões identificadas como flores, destacadas por meio de uma máscara de segmentação ou mantendo sua cor original. A visualização deverá permitir verificar se a identificação das flores foi realizada corretamente.


5. Validação do método utilizando imagens sintéticas

Além de processar a imagem original, desenvolva ou gere imagens sintéticas contendo flores ou formas geométricas em diferentes tonalidades que representam a flor, com dimensões e quantidades de pixels previamente conhecidas.

Essas imagens deverão funcionar como padrões de referência para testar e validar o método de segmentação e quantificação desenvolvido.


Para essa etapa:

* Crie pelo menos três imagens sintéticas com diferentes configurações de flores, variando a quantidade, o tamanho, o formato e/ou a tonalidade da flor.

* Garanta que a quantidade exata de pixels com tonalidades da flor de cada imagem seja conhecida previamente, de modo que os valores reais possam ser utilizados como referência.

* Aplique às imagens sintéticas o mesmo método de processamento utilizado na imagem original.

* Compare a quantidade de pixels identificados pelo algoritmo com a quantidade real de pixels azuis previamente estabelecida.

* Calcule o erro percentual entre o valor obtido pelo processamento e o valor de referência, avaliando a precisão do método.

O objetivo dessa etapa é verificar se o método desenvolvido consegue identificar e quantificar corretamente regiões azuis em imagens nas quais a área real é conhecida.
Entrega

Apresente um relatório contendo:

* A imagem original e a respectiva imagem segmentada, destacando as flores identificadas.  

* A quantidade absoluta de pixels correspondente às flores .  
O percentual de ocupação das flores em relação à área total da imagem original.  

* A descrição do software, algoritmo ou método utilizado para realizar a segmentação.  
O critério adotado para identificar as tonalidades que correspondem à flor.  

* As imagens sintéticas utilizadas na validação, acompanhadas dos respectivos valores reais de pixels com tonalidades da flor.  
Os resultados obtidos pelo processamento das imagens sintéticas, incluindo a comparação entre os valores reais e os valores detectados.  
* O cálculo do erro percentual e uma breve discussão sobre a precisão e as possíveis limitações do método.  

Observações importantes

* Os percentuais de ocupação deverão ser calculados em relação ao total de pixels da imagem original, e não somente em relação aos pixels classificados como flores.

* Nas imagens sintéticas, a quantidade real de pixels azuis deverá ser conhecida e documentada antes da aplicação do algoritmo.

* Utilize o mesmo procedimento de segmentação nas imagens originais e sintéticas, permitindo uma avaliação consistente do método.

* Considere que variações de tonalidade, iluminação, antialiasing e características do fundo podem influenciar os resultados da segmentação.

Critério geral de avaliação: Serão considerados a qualidade da segmentação, a precisão da quantificação, a correta aplicação dos cálculos percentuais, a validação do algoritmo com imagens sintéticas e a capacidade de interpretar os resultados obtidos.