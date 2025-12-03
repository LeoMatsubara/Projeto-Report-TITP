
import requests
import re
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def catch_assignments(api_url, course_id, headers, cert, ano):
    """Busca todas as assignments que contenham o ano informado."""
    params = {'search_term': ano}
    assignments = []

    try:
        url = f'{api_url}/api/v1/courses/{course_id}/assignments'
        response = requests.get(headers=headers, url=url, verify=cert, params=params, timeout=30)

        if response.status_code == 200:
            result = response.json()
            for item in result:
                if item.get('quiz_id'):
                    assignments.append({
                        'name': item.get('name'),
                        'quiz_id': item.get('quiz_id')
                    })
        else:
            logging.error(f'{response.status_code}: {response.text}')
    except Exception as e:
        logging.error(f'Erro ao buscar assignments: {e}')

    return assignments



def catch_link_report_by_id(api_url, course_id, headers, cert, quiz_id, max_wait=120, interval=5):
    import time
    params = {'quiz_report[report_type]': 'student_analysis', 'include': 'file'}
    logging.info('Solicitando geração do relatório...')

    try:
        url = f'{api_url}/api/v1/courses/{course_id}/quizzes/{quiz_id}/reports'
        response = requests.post(headers=headers, url=url, verify=cert, params=params, timeout=30)

        if response.status_code != 200:
            logging.error(f'{response.status_code}: {response.text}')
            return None, None

        report_id = response.json().get('id')
        if not report_id:
            logging.error('Não foi possível obter o ID do relatório.')
            return None, None

        # Polling
        logging.info('Relatório em processamento. Aguardando...')
        start_time = time.time()
        while time.time() - start_time < max_wait:
            status_url = f'{url}/{report_id}'
            status_resp = requests.get(headers=headers, url=status_url, verify=cert, timeout=30)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                if status_data.get('file'):
                    report_name = status_data['file']['display_name']
                    report_link = status_data['file']['url']
                    logging.info(f'Relatório pronto: {report_name}')
                    return report_name, report_link
                else:
                    logging.info('Ainda processando... aguardando...')
            else:
                logging.warning(f'Erro ao verificar status: {status_resp.status_code}')
            time.sleep(interval)

        logging.error('Tempo limite atingido. Relatório não ficou pronto.')
    except Exception as e:
        logging.error(f'Ocorreu um erro ao solicitar/verificar o relatório: {e}')

    return None, None


def download_save(report_name, report_link, headers, cert, path_download):
    safe_name = re.sub(r'[<>:"/\\|?*]', '-', report_name).strip()
    file_path = f'{path_download}/{safe_name}'

    if requests.get(report_link, headers=headers, verify=cert).status_code != 200:
        logging.error('Erro ao acessar o link do relatório.')
        return

    if os.path.exists(file_path):
        logging.warning(f'Arquivo já existente. Verifique em: {file_path}')
        return

    try:
        response = requests.get(report_link, headers=headers, verify=cert)
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(response.content)
            logging.info(f'Arquivo salvo em: {file_path}')
            return safe_name
        else:
            logging.error(f'{response.status_code}: {response.text}')
    except Exception as e:
        logging.error(f'Ocorreu um erro ao salvar o arquivo: {e}')
