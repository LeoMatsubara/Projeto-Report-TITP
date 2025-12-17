#Adicionar uma coluna do mês de referencia do arquivo
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_clean_report(data_path):
    try:
        df = pd.read_csv(data_path, usecols=[0,2,6,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35],dtype={'sis_id': str})
        logging.info(f'Arquivo carregado com {len(df)} linhas e {len(df.columns)} colunas.')

        logging.info('Transformação dos dados em processamento...')
        df.columns = [col.strip() for col in df.columns]
        df.fillna('',inplace=True)
        cols_to_change = range(3,18)
        new_names = {df.columns[i]: df.columns[i][9:].strip() for i in cols_to_change}
        df.rename(columns=new_names, inplace=True)
        df['submitted'] = pd.to_datetime(df['submitted'], errors='coerce')
        df['submitted'] = df['submitted'].dt.strftime('%d/%m/%Y')
        df['name'] = [n.strip().title() for n in df['name']]
        logging.info('Arquivo tratado! Salvando novo arquivo...')

        return df

    except Exception as e:
        logging.error(f'Erro ao processar arquivo: {e}')

def save_data_processed(df_clean,path_data_p,name_data_p):
    save_path = f'{path_data_p}/{name_data_p}'
    df = pd.DataFrame(df_clean)
    if os.path.exists(save_path):
        logging.info(f'Arquivo tratado ja existente em: {save_path}')
        return
    try:
        df.to_csv(path_or_buf=save_path,sep=';',index=False)
        logging.info(f'Arquivo tratado salvo com sucesso em: {save_path}')
        return save_path
    except Exception as e:
        logging.error(f'Erro ao tentar salvar o arquivo: {e}')