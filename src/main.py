
import certifi
import os
import logging
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import extract_canvas

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

CURRENT_DIR = Path(__file__).resolve().parent
CANVAS_API_URL = 'https://famonline.instructure.com'

load_dotenv(find_dotenv(filename='canvas_tkn.env'))
token = os.getenv('canvas_token')
if not token:
    raise RuntimeError('Token não encontrado. Verifique o arquivo .env e a variável.')

headers = {'Authorization': f'Bearer {token}'}
cert = certifi.where()
course_id = 15812
path_download = CURRENT_DIR.parent / 'data' / 'raw'


def main():
    ano = input('Qual o ano do report? ').strip()

    assignments = extract_canvas.catch_assignments(
        api_url=CANVAS_API_URL,
        course_id=course_id,
        headers=headers,
        cert=cert,
        ano=ano
    )

    if not assignments:
        logging.error('Nenhuma assignment encontrada para o ano informado.')
        return

    # Exibe lista para escolha
    print("\nAssignments encontradas:")
    for idx, a in enumerate(assignments, start=1):
        print(f"{idx}. {a['name']} (quiz_id: {a['quiz_id']})")

    escolha = input("\nDigite o número da assignment desejada: ").strip()
    try:
        escolha_idx = int(escolha) - 1
        if escolha_idx < 0 or escolha_idx >= len(assignments):
            logging.error('Opção inválida.')
            return
    except ValueError:
        logging.error('Entrada inválida. Digite um número.')
        return

    quiz_id = assignments[escolha_idx]['quiz_id']

    # Gera relatório com quiz_id escolhido
    report_name, report_link = extract_canvas.catch_link_report_by_id(
        api_url=CANVAS_API_URL,
        course_id=course_id,
        headers=headers,
        cert=cert,
        quiz_id=quiz_id
    )

    if report_name and report_link:
        extract_canvas.download_save(
            report_name=report_name,
            report_link=report_link,
            headers=headers,
            cert=cert,
            path_download=path_download
        )
    else:
        logging.error('Não foi possível gerar o relatório.')

if __name__ == '__main__':
    main()