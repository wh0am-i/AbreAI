"""
optical character recognition (OCR) 

Afazeres:  
Colocar tolerância de caracter, se 90% dos caracteres da placa tiverem...
ou treinamento da AI
em questão do horário, fazer o mesmo dos minutos só que pra caso horas seja 00 ou 24
incluir abertura do portão via arduino ou esp
tirar os prints como o de atual OCR e do intervalo_horarios

Instalações:
apt-get install python3
apt-get install python3-pip
pip install opencv-python
pip install pandas
pip install gspread
pip install tesseract
pip install pytesseract-ocr

Author: https://github.com/wh0am-i
"""


# ========BIBLIOTECAS========
from types import NoneType
import numpy as np
import datetime
import time
import cv2
import gspread as gs
import pytesseract as tsr
import pandas as pd
from mss import mss
from PIL import Image

# ========aquisição do horário========
localtime = datetime.datetime.now()

localhour = localtime.hour  # pega o horário atual
localminute = localtime.minute  # pega os minutos atuais

# se tiver no linux tira o path do tesseract
# path do tesseract após instalação do .exe; pode não ser necessário
tsr.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# ========parte sheets========
# acessando o sheets pela url e autenticando via google api key
planilha = 'https://docs.google.com/spreadsheets/d/1cos1cXdS9GwxIkrsiEFyscnYl3L1J7gVWr6YA4gE-I8/edit?usp=sharing'
id_planilha = '1cos1cXdS9GwxIkrsiEFyscnYl3L1J7gVWr6YA4gE-I8'
gc = gs.service_account(filename='sa_key.json')
sh = gc.open_by_url(planilha).sheet1


# Adding custom options
custom_config = r'--oem 3 --psm 6'


# ======preparação pro loop=======

def captura_tela():  # function para capturar tela
    sct = mss()

    box = {'top': 100, 'left': 0, 'width': 1500, 'height': 1000}

    sct_img = sct.grab(box)

    # parte do capture
    imagecont = 0
    image = np.array(sct_img)
    cv2.imwrite('frames/tela.jpg', image)
    imagecont += 1


def atualiza_bd():  # function para atualizar bd
    bd_import = pd.read_csv(
        f"https://docs.google.com/spreadsheets/d/{id_planilha}/export?format=csv")
    df = pd.DataFrame(bd_import)  # importação do bd interno
    df.to_csv('bd_interno.csv')


# usado no intervalo_horarios, armazena o intervalo de certo horário
horarios_disponiveis = []


def intervalo_horarios(horario_name):
    horarios_disponiveis.clear()
    horario = horario_name
    w = -10  # criar lista de horários, começando pelo horario -10min até o horario +10min
    while len(horarios_disponiveis) < 21:
        dividir = horario.split(":")
        horas = int(dividir[0])
        minutos = int(dividir[1])
        if (minutos + w) < 0:
            # var para transformar horário arrumar isso **********
            minutos = (minutos + w) + 60
            horas -= 1
            horarios_disponiveis.append(str(horas)+":"+str(minutos))
            horas += 1

        elif (minutos + w) > 60:
            # var para transformar horário arrumar isso **********
            minutos = (minutos + w) - 60
            horas += 1
            horarios_disponiveis.append(str(horas)+":0"+str(minutos))
            horas -= 1

        elif (minutos + w) < 10 and (minutos + w) > -1:  # só pra não deixar números como 23:4
            horarios_disponiveis.append(str(horas)+":0"+str(minutos+w))

        else:
            horarios_disponiveis.append(str(horas)+":"+str(minutos+w))
        w += 1


timer = 0
confirm = False

atualiza_bd()
print("Iniciando BD...")
# ========loop leitura========
# looping para verificar se a placa está no bd
print("Iniciando leitura de placas...")
while True:  # enquanto n houver break (ctrl+c no terminal)
    # "%H:%M:%S" para horas, minutos e segundos
    localhourandminute = time.strftime("%H:%M", time.localtime())
    # no github dá de ver como fica o bd.csv direito
    tabela = pd.read_csv(r"bd_interno.csv")

    # definição dos headers das placas e horários atorizados
    placas = tabela[['Placas autorizadas']]
    horarios = tabela[['Horários']]

    captura_tela()
    img = cv2.imread("frames/tela.jpg")  # definição de leitura de imagem
    print("Next Frame...")
    
    # início das functions e consulta do bd externo
    if timer >= 15:  # se bater 15 segundos de delay ele puxa a planilha online
        confirm = False  # reseta o confirm;
        print("Atualizando BD...")
        atualiza_bd()
        timer = 0
    else:
        timer += 1
    y = 0
    while y < len(placas):  #aq tá de boa
        intervalo_horarios(horarios.loc[y]["Horários"])
        if localhourandminute in horarios_disponiveis:  # adicionar aqui dentro a abertura do portão #isso aq tá de boa
            imgfinal = tsr.image_to_string(img, config=custom_config)
            timer += 2 #agiliza o timer pq a leitura demora mais
            if placas.loc[y]["Placas autorizadas"] in imgfinal: 
                print("Placa autorizada!") 
                if confirm == False: #aq tá de boa
                    print("Registrando acesso...")
                    sh.update("E"+str(y+2), placas.loc[y]["Placas autorizadas"])
                    sh.update("G"+str(y+2), localhourandminute)
                    confirm = True
                y += 1
            else:
                print("Aguardando leitura de placa...")
                y += 1
        else:
            print("Sem placas para o horário atual!")
            y += 1
