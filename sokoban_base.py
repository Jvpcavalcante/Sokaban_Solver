import pygame as pg
import heapq
from collections import deque
import time

WINDOW_HEIGHT = 800
WINDOW_WIDTH = 1366
ALT_X = 60
ALT_Y = 60

"""
FUNCOES UTILITARIAS
"""

def vira_mat(n_arq):
    dic = {" ":0,"&":1,"B":2,".":3,"X":4,"#":5,}
    mat = []
    best = -1
    with open(n_arq,"r") as arq:
        for line in arq:
            temp = []
            best = max(best,len(line))
            for j in range(len(line)):
                if line[j] == "\n":break
                temp.append(dic[line[j]])
            mat.append(temp)
    
    for i in range(len(mat)):
        dif = best - len(mat[i])
        for j in range(dif):
            mat[i].append(0)

    return mat

def mostra(mat):
    for i in range(len(mat)):
        for j in range(len(mat[i])):
            print(mat[i][j],end=" ")
        print()



def desenha_board():
    f0 = pg.image.load("sprites/0.png").convert()
    f1 = pg.image.load("sprites/1.png").convert()
    f2 = pg.image.load("sprites/2.png").convert()
    f3 = pg.image.load("sprites/3.png").convert()
    f4 = pg.image.load("sprites/4.png").convert()
    f5 = pg.image.load("sprites/5.png").convert()
    f6 = pg.image.load("sprites/6.png").convert()

    imgs = [f0,f1,f2,f3,f4,f5,f6]

    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            Janela.blit(imgs[Jogo[i][j]],(j*ALT_X,i*ALT_Y))

    Janela.blit(f0,(0,0))

    pg.display.flip()

def kd_caixas():
    tupla = ()
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 2 or Jogo[i][j] == 4: tupla += (i,j),
    
    return tupla

def kd_player():
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 1 or Jogo[i][j] == 6: return (i,j)

def kd_paredes():
    tupla = ()
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 5: tupla += (i,j),
    
    return tupla

def kd_objetivos():
    tupla = ()
    for i in range(len(Jogo)):
        for j in range(len(Jogo[i])):
            if Jogo[i][j] == 3 or Jogo[i][j] == 4: tupla += (i,j),
    
    return tupla

def vencemo(pos_caixas):
    flag = True
    for caixa in pos_caixas:
        if Jogo[caixa[0]][caixa[1]] == 3 or Jogo[caixa[0]][caixa[1]] == 4: pass
        else: flag = False

    return flag

"""
FUNCOES PARA O SOLVER
"""

def auto_movimento_permitido(mov, pos_player, pos_caixas):
    xp, yp = pos_player
    if mov[2].isupper(): xf, yf = xp + (2*mov[0]), yp + (2*mov[1])
    else: xf, yf = xp + mov[0], yp + mov[1]

    return True if ((xf,yf) not in pos_caixas and Jogo[xf][yf] != 5) else False

def auto_gerar_movimentos(pos_player, pos_caixas):
    mx = [-1,1,0,0]
    my = [0,0,1,-1]
    letra = ["W","S","D","A"]

    xp,yp = pos_player
    movs_permitidos = ()

    for i in range(4):
        xf,yf = xp + mx[i], yp + my[i]
        if (xf,yf) in pos_caixas:
            temp = (mx[i],my[i],letra[i])
            if (auto_movimento_permitido(temp, pos_player, pos_caixas)):
                movs_permitidos += (temp),
        else:
            temp = (mx[i],my[i],letra[i].lower())
            if (auto_movimento_permitido(temp, pos_player, pos_caixas)):
                movs_permitidos += (temp),

    return movs_permitidos

def auto_atualiza_estado(pos_player,pos_caixas, mov):
    xp, yp = pos_player
    nova_pos_player = (xp + mov[0], yp + mov[1])
    lis_pos_caixas = list(pos_caixas)
    if mov[2].isupper():
        lis_pos_caixas.remove(nova_pos_player)
        lis_pos_caixas.append( (xp + (2*mov[0]), yp + (2*mov[1])) )

    return nova_pos_player,tuple(lis_pos_caixas)

"""
Rescrever daqui pra baixo ate a main
"""

def perdemo(pos_caixas,pos_objetivos,pos_paredes):
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
    distance = 0
    lugar_certo = set(pos_objetivos) & set(pos_caixas)
    dif_caixas = list(set(pos_caixas).difference(lugar_certo))
    dif_objetivos = list(set(pos_objetivos).difference(lugar_certo))
    for i in range(len(dif_caixas)):
        distance += (abs(dif_caixas[i][0] - dif_objetivos[i][0])) + (abs(dif_caixas[i][1] - dif_objetivos[i][1]))
    return distance

def movs_sem_andar(movs):
    cnt = 0
    for i in range(len(movs)):
        if movs[i][2].islower(): cnt += 1

    return cnt

def bfs(pos_objetivos,pos_paredes):
    t1 = time.time()
    player_start = kd_player()
    caixas_start = kd_caixas()
    
    ini_estado = (player_start,caixas_start)
    st = deque([[ini_estado]])
    movs = deque([[0]])
    visto = set()

    while st:
        estado = st.popleft()
        acao_ate_aq = movs.popleft()

        if vencemo(estado[-1][-1]):
            print("\ntempo: %.2f s" % (time.time() - t1))
            return str(acao_ate_aq)[5:-2].replace("', '"," ")
        
        if estado[-1] not in visto:
            visto.add(estado[-1])
            for movimento in auto_gerar_movimentos(estado[-1][0],estado[-1][1]):
                novo_player, novo_caixas = auto_atualiza_estado(estado[-1][0],estado[-1][1],movimento)
                
                if perdemo(novo_caixas,pos_objetivos,pos_paredes):
                    continue

                st.append(estado + [(novo_player,novo_caixas)])
                movs.append(acao_ate_aq + [movimento[2]])

"""
FUNCOES PARA O PLAYER
"""


def norm_movimento_permitido(pos_player,mov):
    xp, yp = pos_player
    if mov[2].isupper(): xf, yf = xp + (2*mov[0]), yp + (2*mov[1])
    else: xf, yf = xp + mov[0], yp + mov[1]

    return True if (Jogo[xf][yf] not in [2,4,5]) else False

def norm_faz_movimento(pos_player,mov):
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
    xp, yp = kd_player()
    dx, dy = direc

    dic = {(-1,0): "w", (1,0): "s", (0,1): "d", (0,-1): "a"}

    if Jogo[xp+dx][yp+dy] == 2 or Jogo[xp+dx][yp+dy] == 4:
        mov = (dx,dy,dic[(dx,dy)].upper())
        print(mov)
        if norm_movimento_permitido((xp,yp),mov):
            norm_faz_movimento((xp,yp),mov)
            return mov[2]
    else:
        mov = (dx,dy,dic[(dx,dy)])
        print(mov)
        if norm_movimento_permitido((xp,yp),mov):
            norm_faz_movimento((xp,yp),mov)
            return mov[2]



"""
A GRANDE E PODEROSA MAIN
"""

def main():
    global Janela, Tempo, Jogo
    
    pg.init()
    Janela = pg.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    Tempo = pg.time.Clock()

    Jogo = vira_mat("lvls/lvl1.txt")
    mostra(Jogo)

    pos_paredes = kd_paredes()
    pos_objetivos = kd_objetivos()

    movs_ate_agr = []
    done = False
    while not done:
        Janela.fill((0,0,0))
        Tempo.tick(60)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True

            elif event.type == pg.MOUSEBUTTONDOWN:
                print(movs_ate_agr)

            elif event.type == pg.KEYDOWN:

                if event.key == pg.K_w:
                    carac = norm_tenta_mov((-1,0))
                    if carac: movs_ate_agr.append(carac)

                    if vencemo(kd_caixas()):
                        print("deu bom")

                elif event.key == pg.K_s: 
                    carac = norm_tenta_mov((1,0))
                    if carac: movs_ate_agr.append(carac)

                    if vencemo(kd_caixas()):
                        print("deu bom")
                
                elif event.key == pg.K_a: 
                    carac = norm_tenta_mov((0,-1))
                    if carac: movs_ate_agr.append(carac)

                    if vencemo(kd_caixas()):
                        print("deu bom")

                elif event.key == pg.K_d:
                    carac = norm_tenta_mov((0,1))
                    if carac: movs_ate_agr.append(carac)

                    if vencemo(kd_caixas()):
                        print("deu bom")

                elif event.key == pg.K_r:
                    movs_ate_agr = []
                    Jogo = vira_mat("lvls/lvl1.txt")

                elif event.key == pg.K_z:
                    print(bfs(pos_objetivos,pos_paredes))

        desenha_board()
                
main()