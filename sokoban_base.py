import pygame as pg
import heapq
from collections import deque
import time

# variaveis globais para tamanho de tela e tamanho de cada tile
WINDOW_WIDTH = 1366
WINDOW_HEIGHT = 800

ALT_X = 60
ALT_Y = 60

"""
FUNCOES UTILITARIAS
"""

def vira_mat(entrada):
    """
    Como a maioria das fases vao ser encontradas na internet estou usando a formatacao
    mais popular para definir como sao mostradas as fases, estretanto trabalhar com isso para o grid
    ia ser bem ruim, entao converto para numeros.

    lista de significados:
    " " = espaco vazio -> 0
    "&" = player -> 1
    "B" = caixa -> 2
    "." = objetivo -> 3
    "X" = caixa no objetivo -> 4
    "#" = parede -> 5

    """
    dic = {" ":0,"&":1,"B":2,".":3,"X":4,"#":5,}
    mat = []
    best = -1
    
    for i in range(len(entrada)):
        temp = []
        best = max(best,len(entrada[i]))
        for j in range(len(entrada[i])):
            temp.append(dic[entrada[i][j]])
        
        mat.append(temp)

    # forca todas as linhas a terem o mesmo tamanha, completando com tiles de espaco vazio
    for i in range(len(mat)):
        dif = best - len(mat[i])
        for j in range(dif):
            mat[i].append(0)

    return mat

def desenha_board():
    """
    Funcao que atualiza a tela do jogo, como os tiles tem o mesmo tamanho basta
    que voce passe a posicao da quina superior esquerda e a funcao coloca a imagem a
    partir dali
    """
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            Janela.blit(imgs[Jogo[i][j]],(j*ALT_X,i*ALT_Y)) # aproveita que o grid usa numeros para descobrir qual imagem tem q ficar em cada posicao

    pg.display.flip() # atualiza a tela mostrando as mudancas

def kd_caixas():
    """
    Funcao auxiliar, retorna uma tupla com a posicao das caixas
    """
    tupla = ()
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 2 or Jogo[i][j] == 4: tupla += (i,j),
    
    return tupla

def kd_player():
    """
    Funcao auxiliar, retorna uma tupla com a posicao do player
    """
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 1 or Jogo[i][j] == 6: return (i,j)

def kd_paredes():
    """
    Funcao auxiliar, retorna uma tupla com a posicao das paredes
    """
    tupla = ()
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 5: tupla += (i,j),
    
    return tupla

def kd_objetivos():
    """
    Funcao auxiliar, retorna uma tupla com a posicao dos objetivos
    """
    tupla = ()
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 3 or Jogo[i][j] == 4: tupla += (i,j),
    
    return tupla

def vencemo(pos_caixas):
    """
    Funcao auxiliar pra ver se todas as caixas estao em uma posicao de objetivo
    """
    flag = True
    for caixa in pos_caixas: # loop que percorre a lista de caixas e ve se todas estao em 
        if Jogo[caixa[0]][caixa[1]] == 3 or Jogo[caixa[0]][caixa[1]] == 4: pass
        else: flag = False

    return flag

"""
FUNCOES PARA JOGAR ROUBANDO
"""

def auto_movimento_permitido(mov, pos_player, pos_caixas):
    """
    Verifica se uma tentativa de movimento feita pela arvore de busca e valida
    """
    xp, yp = pos_player
    if mov[2].isupper(): xf, yf = xp + (2*mov[0]), yp + (2*mov[1])
    else: xf, yf = xp + mov[0], yp + mov[1]

    return True if ((xf,yf) not in pos_caixas and Jogo[xf][yf] != 5) else False

def auto_gerar_movimentos(pos_player, pos_caixas):
    """
    Gera todos os movimentos que sao possiveis a partir de um certo estado
    """
    # define a matriz de movimento
    mx = [-1,1,0,0]
    my = [0,0,1,-1]
    letra = ["W","S","D","A"]

    xp,yp = pos_player
    movs_permitidos = ()

    for i in range(4): # loop para aplicar a matriz de movimento na posicao inicial
        xf,yf = xp + mx[i], yp + my[i] # nova posicao
        if (xf,yf) in pos_caixas: # se na posicao tinha uma caixa
            temp = (mx[i],my[i],letra[i])
            if (auto_movimento_permitido(temp, pos_player, pos_caixas)):
                movs_permitidos += (temp),
        else:
            temp = (mx[i],my[i],letra[i].lower()) # lower para passar pra proxima funcao a informacao que foi um movimento comum
            if (auto_movimento_permitido(temp, pos_player, pos_caixas)):
                movs_permitidos += (temp),

    return movs_permitidos

def auto_atualiza_estado(pos_player,pos_caixas, mov):
    """
    Essa serve pra atualizar o "vertice" da arvore de busca, e importante q o lis_pos_caixas e pos_player sejam tuplas
    pq nao da pra colocar uma lista na priority queue
    """
    nova_pos_player = (pos_player[0] + mov[0], pos_player[1] + mov[1])
    lis_pos_caixas = list(pos_caixas)
    if mov[2].isupper():
        lis_pos_caixas.remove(nova_pos_player)
        lis_pos_caixas.append( (pos_player[0] + (2*mov[0]), pos_player[1] + (2*mov[1])) )

    return nova_pos_player,tuple(lis_pos_caixas)

def perdemo(pos_caixas,pos_objetivos,pos_paredes):
    """
    A funcao dessa heuristica foi encontrada numa wiki.

    A ideia por tras dela e verificar por meio de varias rotacoes do board se existe
    alguma situacao que cria um deadlock imediato, essa funcao ainda assim e BEMM ruim
    existem modulos gigantes com mais de 800 linhas so pra verificar os deadlocks. 
    
    Todavia, essa funcao e desnecessario pro funcionamento do programa ela so poda um pouco
    a arvore de busca, dependendo da fase voce ganha muito desempenho, em outras nem tanto
    mas o algoritmo como um todo funciona perfeitamente sem ela.

    O resto da explicacao dessa funcao sera feito na apresentacao oral, visto que e muito mais
    facil explicar visualmente com os slides que quero usar.
    """
    rotatePattern = [[0,1,2,3,4,5,6,7,8],
                    [2,5,8,1,4,7,0,3,6],
                    [8,7,6,5,4,3,2,1,0],
                    [6,3,0,7,4,1,8,5,2]]
    
    flipPattern = [[2,1,0,5,4,3,8,7,6],
                    [0,3,6,1,4,7,2,5,8],
                    [6,7,8,3,4,5,0,1,2],
                    [8,5,2,7,4,1,6,3,0]]
    
    allPattern = rotatePattern + flipPattern

    for box in pos_caixas:
        if box not in pos_objetivos:
            board = [(box[0] - 1, box[1] - 1), (box[0] - 1, box[1]), (box[0] - 1, box[1] + 1), 
                    (box[0], box[1] - 1), (box[0], box[1]), (box[0], box[1] + 1), 
                    (box[0] + 1, box[1] - 1), (box[0] + 1, box[1]), (box[0] + 1, box[1] + 1)]
            
            for pattern in allPattern:
                newBoard = [board[i] for i in pattern]
                if newBoard[1] in pos_paredes and newBoard[5] in pos_paredes: return True
                elif newBoard[1] in pos_caixas and newBoard[2] in pos_paredes and newBoard[5] in pos_paredes: return True
                elif newBoard[1] in pos_caixas and newBoard[2] in pos_paredes and newBoard[5] in pos_caixas: return True
                elif newBoard[1] in pos_caixas and newBoard[2] in pos_caixas and newBoard[5] in pos_caixas: return True
                elif newBoard[1] in pos_caixas and newBoard[6] in pos_caixas and newBoard[2] in pos_paredes and newBoard[3] in pos_paredes and newBoard[8] in pos_paredes: return True
    return False

def heuristica(pos_objetivos, pos_caixas):
    """
    Funcao de heuristica do A*

    A ideia e calcular a distancia manhattan entre as caixas e os objetivos e retornar esse valor
    """
    distance = 0
    lugar_certo = set(pos_objetivos) & set(pos_caixas)
    dif_caixas = list(set(pos_caixas).difference(lugar_certo))
    dif_objetivos = list(set(pos_objetivos).difference(lugar_certo))
    for i in range(len(dif_caixas)):
        distance += (abs(dif_caixas[i][0] - dif_objetivos[i][0])) + (abs(dif_caixas[i][1] - dif_objetivos[i][1]))
    return distance

def heuristica1(obj,cax):
    """
    Funcao descontinuada

    Ignorar essa funcao, a de cima e bem mais eficiente ;-;
    Embora ambas façam basicamente a mesma coisa, vai ficar aqui por enqt, vai que a de cima da errado
    """
    dist = 0
    n_cax = []
    n_obj = []
    for i in range(len(obj)):
        if cax[i] in obj:
            n_cax.append(cax[i])
            n_obj.append(obj[i])

    n_cax.sort()
    n_obj.sort()

    for i in range(len(n_obj)): dist += (abs(n_cax[i][0]-n_obj[i][0]) + abs(n_cax[i][1]-n_obj[i][1]))

    return dist

def movs_sem_andar(movs):
    """
    Fator auxiliar da heuristica, pra reduzir a chance da busca fazer movimentos aleatorios
    so conta quantos movimentos ja foram feitos onde uma caixa nao foi empurrada e retorna esse valor
    """
    cnt = 0
    for i in range(len(movs)):
        if i == 0: continue
        if movs[i].islower(): cnt += 1

    return cnt

class fila_de_prioridade: # define uma classe pra lista de prioridade, ja que o python nao tem isso nativo \\ c++ >> python
    def  __init__(self):
        self.lista = []
        self.cnt = 0

    def bota(self, vertice, prior):
        heapq.heappush(self.lista, (prior, self.cnt, vertice))
        self.cnt += 1

    def tira(self): return heapq.heappop(self.lista)[2]

    def qnts_visitados(self): return self.cnt

def a_estrela(pos_obj,pos_par):
    """
    Esse algoritmo aqui e bem complicado, e explicar ele vai ser a maior parte da minha apresentacao.

    Um resumo curto da ideia é:

    No nosso tabuleiro a unica coisa que muda é a posicao do player e das caixas, entao vamos considerar isso como o vertice de um grafo.
    a partir desse vertice inicial, vamos contruindo o resto do grafo gerando novos vertices a partir do inicial, sabemos como fazer isso pq
    temos funcoes auxiliar ajustadas para as regras do jogo

    Usando a fila de prioridade podemos procurar nesse grafo indo sempre na direcao que a heuristica indica como a mais promissora, entao
    basta procurar ate que encontremos um vertice de indica uma posicao vitoriosa
    """
    t1 = time.time() # inicia o tempo para medir o desempenho do algoritmo

    pq_busca = fila_de_prioridade()
    pq_busca.bota((kd_player(),kd_caixas()), 0)
    
    visitados = set() # set que vai ser usado pra garantir que nao vamos passar duas vezes no mesmo
    
    movimentos_ate_agr = fila_de_prioridade()
    movimentos_ate_agr.bota([0], 0)
    
    while pq_busca:
        
        pg.event.pump() # Linha magica pra impedir que o windows ache o programa travou enquanto o algoritmo roda

        # tira da priority queue as informacoes do estado atual e dos movimentos feitos pra chegar ate aqui
        estado_atual = pq_busca.tira()
        movs_aq = movimentos_ate_agr.tira()
        
        if vencemo(estado_atual[1]): # se esse estado e vitorioso
            print("\ntempo: %.2f s" % (time.time() - t1)) # printa o tempo de execucao do algoritmo
            print("Foram gerados", pq_busca.qnts_visitados(), "vertices ate encontrar um vertice vitorioso")
            fim = str(movs_aq)[5:-2].replace("', '","") # tranforma a tupla de movimentos em string pra passar pra outra funcao
            auto_to_norm(fim) # chama a funcao que mostra os movimetos pro usuario
            break

        if estado_atual not in visitados: # se nunca passou por esse estado e ainda precisa expandir a arvore de busca
            visitados.add(estado_atual) # adiciona o estado atual nos estados visitados
            andei_qnt = movs_sem_andar(movs_aq[1:])

            for mov in auto_gerar_movimentos(estado_atual[0], estado_atual[1]):
                newPosPlayer, newPosBox = auto_atualiza_estado(estado_atual[0], estado_atual[1], mov)
                
                if perdemo(newPosBox,pos_obj,pos_par): continue # se for um estado perdido nem gera outros estados a partir dele

                dist_caixas = heuristica(pos_obj, newPosBox) # calcula a distancia manhattan pra heuristica

                pq_busca.bota((newPosPlayer, newPosBox), dist_caixas + andei_qnt) # adiciona um novo estado na priority queue
                movimentos_ate_agr.bota(movs_aq + [mov[-1]], dist_caixas + andei_qnt) # adiciona os movimentos pra chegar nesse estado na priority queue


"""
FUNCOES PARA JOGAR NORMALMENTE
"""

def norm_movimento_permitido(pos_player,mov):
    """
    Funcao auxiliar que verifica se o movimento e permitido
    """
    xp, yp = pos_player
    # verifica se o a posicao 2 quadrados pra frente esta livre, esse caso corrensponde a empurrar uma caixa
    if mov[2].isupper(): xf, yf = xp + (2*mov[0]), yp + (2*mov[1]) 
    #verifica se o quadrado da frente esta livre, corresponde a andar normalmente
    else: xf, yf = xp + mov[0], yp + mov[1]

    return True if (Jogo[xf][yf] not in [2,4,5]) else False

def norm_faz_movimento(pos_player,mov):
    """
    Atualiza o grid considerando que o movimento passado era valido
    """
    xp, yp = pos_player
    dx, dy = mov[0], mov[1]
    
    if Jogo[xp+dx][yp+dy] == 2:
        Jogo[xp+(2*dx)][yp+(2*dy)] = 4 if Jogo[xp+(2*dx)][yp+(2*dy)] == 3 else 2
        Jogo[xp+dx][yp+dy] = 1
        Jogo[xp][yp] = 0 if Jogo[xp][yp] == 1 else 3

    
    elif Jogo[xp+dx][yp+dy] == 4:
        Jogo[xp+(2*dx)][yp+(2*dy)] = 4 if Jogo[xp+(2*dx)][yp+(2*dy)] == 3 else 2
        Jogo[xp+dx][yp+dy] = 6
        Jogo[xp][yp] = 0 if Jogo[xp][yp] == 1 else 3

    else:
        Jogo[xp+dx][yp+dy] = 1 if Jogo[xp+dx][yp+dy] == 0 else 6
        Jogo[xp][yp] = 0 if Jogo[xp][yp] == 1 else 3

def norm_tenta_mov(direc):
    """
    Recebe o input do teclado e chama a funcao verificadora para saber se e valido
    caso seja valido chama a funcao que atualiza o grid
    """
    xp, yp = kd_player()
    dx, dy = direc

    #converte a matriz de movimento para as teclas
    dic = {(-1,0): "w", (1,0): "s", (0,1): "d", (0,-1): "a"}

    if Jogo[xp+dx][yp+dy] == 2 or Jogo[xp+dx][yp+dy] == 4:
        mov = (dx,dy,dic[(dx,dy)].upper())
        if norm_movimento_permitido((xp,yp),mov):
            norm_faz_movimento((xp,yp),mov)
            return mov[2]
    else:
        mov = (dx,dy,dic[(dx,dy)])
        if norm_movimento_permitido((xp,yp),mov):
            norm_faz_movimento((xp,yp),mov)
            return mov[2]


def auto_to_norm(s):
    """
    Funcao que faz os movimentos do solver para que o user veja a solucao 
    """
    dic = {"w":(-1,0),"s":(1,0),"a":(0,-1),"d":(0,1)}
    for carac in s:
        norm_faz_movimento(kd_player(),dic[carac.lower()])
        desenha_board()
        pg.time.wait(150)

        pg.event.pump()
        # comando do pygame que impede o windows de travar meu codigo todo hahahah windows maldito, perdi 2 dias ate descobrir isso
        

def recupera_fases_originais():
    """
    Recupera o dicionario que ficou salvo no arquivo txt
    """
    dic = {}
    try: # tenta abrir o arquivo
        with open("fases_originais.txt","r") as arq:
            for line in arq:
                dic = eval(line)
    except FileNotFoundError: # se nao achar o arquivo cria um e retorna um dicionario vazio
        novo = open("fases_originais.txt","w")
        novo.close()
    
    return dic

def salvar_fases_originais(fases):
    """
    Salva o dicionario no arquivo txt
    """
    with open("fases_originais.txt","w") as arq:
        arq.write(str(fases))

def mostra_vencemo():
    """
    Por favor, ganhe uma fase e veja essa maravilha de imagem que eu criei de madrugada depois de 3 redbulls
    """
    Janela.blit(imgs[7],(0,0)) # exibe minha obra prima
    pg.display.flip() # atualiza o display


"""
A GRANDE E PODEROSA MAIN
"""

def main():
    # desculpa pelas variaveis globais prof, mas tava dando erro sem elas
    global Janela, Tempo, Jogo, imgs

    # preenche a lista de fases com todas as fazes q o usuario criou
    fases = recupera_fases_originais()

    while 1:
        print("BEM VINDO AO SOKOBAN!!!")
        print("1 - Jogar")
        print("2 - Editar fases")
        print("3 - Sair")
        resp = -1

        #loop com try pra garantir que o usuario escolheu uma opcao valida
        while 1:
            try:
                resp = int(input("Escolha uma opcao: "))
                if not (0<resp<4):
                    raise ValueError
            except:
                print("ESCOLHA UM VALOR VALIDO!")
            else:
                break
        
        if resp == 1:
            #printa o nome de todas as fases q foram carregadas do arquivo txt
            nome_fases = list(fases.keys())
            print("Fases carregadas: ")
            for nome in nome_fases:
                print("-",nome)
            

            # loop com try pra garantir que foi escolhida uma fase que existe
            fase = ""
            while 1:
                try:
                    fase = input("Qual fase voce deseja jogar (digite sair para voltar ao menu): ")
                    if fase == "sair":break
                    if fase not in nome_fases: raise ValueError
                
                except: print("Por favor escolha um valor valido")
                else: break
            if fase != "" and fase != "sair":break

        if resp == 2:
            print("1 - Adicionar nova fase")
            print("2 - Excluir uma fase")
            print("3 - Voltar")

            #loop com try para garantir que o usuario escolheu uma opcao valida
            resp1 = -1
            while 1:
                try:
                    resp1 = int(input("Escolha uma opcao: "))
                    if not (0<resp1<4):
                        raise ValueError
                except:
                    print("ESCOLHA UM VALOR VALIDO!")
                else:
                    break

            if resp1 == 1:
                mat = []
                print("Insira a sua fase, quando tiver colocado todas as linhas digite -1")
                nome_fase = input("escolha o nome da sua fase: ")
                while 1:
                    entrada = input()
                    if entrada == "-1":break
                    mat.append(entrada)
                
                fases[nome_fase] = mat

            if resp1 == 2:
                while 1:
                    nome_fase = input("Qual o nome da fase que voce deseja excluir (digite sair para voltar ao menu): ")
                    if nome_fase == "sair": break
                    else:
                        try: fases.pop(nome_fase)
                        except: print("Essa fase nao existe colega.")
                        else: break
        
        if resp == 3:
            salvar_fases_originais(fases)
            return 

    
    #Inicia o pygame e cria as instancias da janela e do tempo
    pg.init()
    Janela = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    Tempo = pg.time.Clock()
    
    #cria o grid na memoria com base na fase escolhida acima
    Jogo = vira_mat(fases[fase])

    #inicializa as listas de paredes e objetivos, ja que essas nunca mudam
    pos_paredes = kd_paredes()
    pos_objetivos = kd_objetivos()

    # carrega todas as imagens que sao usando pelo programa
    f0 = pg.image.load("sprites/0.png").convert()
    f1 = pg.image.load("sprites/1.png").convert()
    f2 = pg.image.load("sprites/2.png").convert()
    f3 = pg.image.load("sprites/3.png").convert()
    f4 = pg.image.load("sprites/4.png").convert()
    f5 = pg.image.load("sprites/5.png").convert()
    f6 = pg.image.load("sprites/6.png").convert()
    banner = pg.image.load("sprites/vencemo.png").convert()

    # deixa as imagens numa lista global pra pode acessar, por algum motivo estava dando erro quando nao era global
    imgs = [f0,f1,f2,f3,f4,f5,f6,banner]

    movs_ate_agr = [] # lista dos movimentos que foram feitos pelo player
    done = False
    ja_vencemo = False
    while not done:
        Janela.fill((0,0,0)) # deixa o fundo da janela preto
        Tempo.tick(60) # define 60 fps pro jogo

        for event in pg.event.get(): # listener dos inputs do usuario
            if event.type == pg.QUIT:
                done = True
                salvar_fases_originais(fases) # garante que as fases sao salvas

            elif event.type == pg.MOUSEBUTTONDOWN:
                print(movs_ate_agr)

            elif event.type == pg.KEYDOWN: # se e um evento do tipo entrada do teclado

                if event.key == pg.K_w: # tenta andar pra cima
                    carac = norm_tenta_mov((-1,0))
                    if carac: movs_ate_agr.append(carac)

                elif event.key == pg.K_s: # tenta andar pra baixo
                    carac = norm_tenta_mov((1,0))
                    if carac: movs_ate_agr.append(carac)
                
                elif event.key == pg.K_a: # tenta andar pra esquerda
                    carac = norm_tenta_mov((0,-1))
                    if carac: movs_ate_agr.append(carac)

                elif event.key == pg.K_d: # tenta andar pra direita
                    carac = norm_tenta_mov((0,1))
                    if carac: movs_ate_agr.append(carac)

                elif event.key == pg.K_r: # reinicia a fase, vai ser bem util se vc fizer besteira
                    movs_ate_agr = []
                    Jogo = vira_mat(fases[fase])

                elif event.key == pg.K_z: # pede ajuda pro solver usando A*
                    print("Ta roubando ne danado kk")
                    a = [""]
                    a_estrela(pos_objetivos,pos_paredes)

        if ja_vencemo: mostra_vencemo() # chama minha maravilhosa tela da VITORIA HAHAHA
        else: 
            desenha_board() # atualiza o board depois do movimento
            temp = vencemo(kd_caixas()) # verifica se chegou num estado vitorioso
            ja_vencemo = temp
            if temp: pg.time.wait(2000) # da 2 seg pra poder apreciar sua bela vitoria
                
main()