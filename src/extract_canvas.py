import requests
import certifi
from dotenv import load_dotenv, find_dotenv
import os
import re
from pathlib import Path

# Config Globais
CURRENT_DIR = Path(__file__).resolve().parent
CANVAS_API_URL = 'https://famonline.instructure.com'
load_dotenv(find_dotenv(filename='canvas_tkn.env'))
token = os.getenv('canvas_token')
headers = {'Authorization': f'Bearer {token}'}
cert = certifi.where()
course_id = 15812
path_download = rf'{CURRENT_DIR.parent}/data/raw'

# Extrai quiz_id com base no período buscado, armazena input para parâmetro
ano = input('Qual o ano do report? ').strip()
mes = input('Qual o mês do report? ').strip().capitalize()

# utilizar API para descobrir o quizzes correto com base no nome da assignment
def catch_assignment():
    search_conc = f'{mes} {ano}'
    params = {'search_term': search_conc} 
    try:
        url = f'{CANVAS_API_URL}/api/v1/courses/{course_id}/assignments'
        response = requests.get(headers=headers,
                                url=url,
                                verify=cert,
                                params=params)
        if response.status_code == 200:
            result_assignment = response.json()
            quiz_id = result_assignment[0].get('quiz_id')
        else:
            print(f'{response.status_code}: {response.text}')
    except Exception as e:
        print(f'Ocorreu um erro ao capturar assignment: {e}')
    return quiz_id

def catch_link_report():
    quiz_id = catch_assignment()
    params = {'quiz_report[report_type]':'student_analysis','include':'file'}
    print('\nRelatório em processamento...\n')
    try:
        url= f'{CANVAS_API_URL}/api/v1/courses/{course_id}/quizzes/{quiz_id}/reports'
        response = requests.post(headers=headers,
                                url=url,
                                verify=cert,
                                params=params)
        if response.status_code == 200:
            result = response.json()
            report_name = result['file']['display_name']
            report_link = result['file']['url']
            print(f'Relatório Gerado: {report_name}')
        else:
            print(f'{response.status_code}: {response.text}')
            return None, None
    except Exception as e:
        print(f'Ocorreu um erro ao realizar o download: {e}')
    return report_name, report_link

def download_save(report_name, report_link):
    safe_name = re.sub(r'[<>:"/\\|?*]', '-', report_name)
    response = requests.get(report_link,
                            headers=headers,
                            verify=cert)
    if response.status_code == 200:
        file_path = f'{path_download}/{safe_name}'
        with open(file_path, "wb") as file:    
            file.write(response.content)
        print(f'Arquivo salvo em: {file_path}')
    else:
            print(f'{response.status_code}: {response.text}')

#Teste

report_name, report_link = catch_link_report()
download_save(report_name, report_link)