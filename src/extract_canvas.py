import requests
import certifi
from dotenv import load_dotenv, find_dotenv
import os

# Config Globais
CANVAS_API_URL = 'https://famonline.instructure.com'
load_dotenv(find_dotenv(filename='canvas_tkn.env'))
token = os.getenv('canvas_token')
headers = {'Authorization': f'Bearer {token}'}
cert = certifi.where()
course_id = 15812
quiz_id = None
api_assignment = f'/api/v1/courses/{course_id}/assignments'
api_report = f'/api/v1/courses/{course_id}/quizzes/{quiz_id}/reports'

# Extrai quiz_id com base no período buscado, armazena input para parâmetro
ano = input('Qual o ano do report? ').strip()
mes = input('Qual o mês do report? ').strip().capitalize()
search_conc = f'{mes} {ano}'
params = {'search_term': search_conc}

# utilizar API para descobrir o quizzes correto com base no nome do assignment
def captura_assignment():   
    try:
        url_s1 = f'{CANVAS_API_URL}{api_assignment}'
        response = requests.get(headers=headers,
                                url=url_s1,
                                verify=cert,
                                params=params)
        if response.status_code == 200:
            result_assignment = response.json()
            quiz_id = result_assignment[0].get('quiz_id')
            print(quiz_id)
        else:
            print(f'{response.status_code}: {response.text}')

    except Exception as e:
        print(f'Ocorreu um erro ao capturar assignment: {e}')
    return quiz_id

#def dwl_teste():

#"report_type": "student_analysis",55049