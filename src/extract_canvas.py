import requests
import certifi
from dotenv import load_dotenv
import os

# Config Globais
CANVAS_API_URL = 'https://famonline.instructure.com'
load_dotenv()
token = os.getenv('canvas_token')
headers = {'Authorization': f'Bearer {token}'}
cert = certifi.where()
course_id = 15812
api_assignment = f'/api/v1/courses/{course_id}/assignments'
api_report = f'/api/v1/courses/{course_id}/quizzes/{quiz_id}/reports'


# Extrai assignment_id com base no período buscado
ano = str(input('Qual o ano do report? ').strip())
mes = str(input('Qual o mês do report? ').strip().capitalize())
search_conc = mes +' '+ ano


# utilizar API para descobrir o quizzes correto com base no nome do assignment
#"report_type": "student_analysis",55049
