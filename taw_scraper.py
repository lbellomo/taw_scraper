import json
import argparse
from time import time, sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

parser = argparse.ArgumentParser(
    description='Simple tawdis.net scraper. Output a jsonline.',
    epilog='Example: python taw_scraper.py to_download.csv out_file.jsonl')
# path_firefox, path_gecko, to_download, out_file
parser.add_argument('download_list',
                    help='file with urls to evaluate, one url per line is expected')
parser.add_argument('out_file', help='name of the out file')

parser.add_argument('-f', '--firefox', help='path to firefox (if firefox is not in the path)')
parser.add_argument('-g', '--geckodriver', help='path to geckodriver (default: ./geckodriver)')
args = parser.parse_args()

def load_page(driver, page_url, first_load=False, timeout=60):
    url = 'https://www.tawdis.net/'

    driver.get(url)

    if first_load:
        # click in the "accept-cookies"
        elem = driver.find_element_by_id('aceptarCookiesLink')
        elem.send_keys(Keys.RETURN)

    elem = driver.find_element_by_id('direccionWebwcag2')
    elem.clear()
    elem.send_keys(page_url)
    elem.send_keys(Keys.RETURN)

    wait_to_load = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, "automaticos"))
        )

def scrape_source(page_source):
    '''Recive the page_source of tawdis.net and returna json with the info'''
    soup = BeautifulSoup(page_source, 'lxml')
    out = dict()

    automaticos = soup.find('div', attrs={'class': 'automaticos'})
    desconocidos = soup.find('div', attrs={'class', 'desconocidos'})
    no_revisados = soup.find('div', attrs={'class', 'no_revisados'})

    for div_name, div_class in zip(['problems', 'warnings', 'not_reviewed'],
                                   [automaticos, desconocidos, no_revisados]):

        detectado = div_class.find('p', attrs={'class': 'detectado'})
        count = detectado.find('strong').text.split()[0]
        success_criteria = detectado.find('span').text.split()[1]

        conclucion = div_class.find('p', attrs={'conclusion'}).find('strong').get_text(strip=True)

        principios = div_class.find('ul', attrs={'class': 'principios'}).findAllNext('li', limit=4)
        perceivable = principios[0].text.split()[-1]
        operable = principios[1].text.split()[-1]
        understandable = principios[2].text.split()[-1]
        robust = principios[3].text.split()[-1]

        out[div_name + '_count'] = count
        out[div_name + '_success_criteria'] = success_criteria
        out[div_name + '_conclucion'] = conclucion
        out[div_name + '_perceivable'] = perceivable
        out[div_name + '_operable'] = operable
        out[div_name + '_understandable'] = understandable
        out[div_name + '_robust'] = robust

    resume_info = soup.find('div', attrs={'class': 'resumen-info'}).findChildren('strong')

    out['resource'] = resume_info[0].next_sibling.strip()
    out['date'] = resume_info[1].next_sibling.strip()
    out['guidelines'] = resume_info[2].next_sibling.strip()
    out['analysis_level'] = resume_info[3].next_sibling.strip()
    out['technologies'] = resume_info[4].next_sibling.strip()

    perceivable = soup.find('div', attrs={'id': 'principio_1'}).find('table')
    operable = soup.find('div', attrs={'id': 'principio_2'}).find('table')
    understandable = soup.find('div', attrs={'id': 'principio_3'}).find('table')
    robust = soup.find('div', attrs={'id': 'principio_4'}).find('table')


    table_name = 'perceivable'
    table = perceivable.find('table')
    tables_names = ['perceivable', 'operable', 'understandable', 'robust']
    tables  = [perceivable, operable, understandable, robust]

    for table_name, table in zip(tables_names, tables):
        for i, row in enumerate(table.findChildren('tr')):
            # La primera linea
            if not i:
                continue

            if row.findChildren('th'):

                row_list = row.findChildren('th')
                temp_name = (
                    row_list[0].text
                    .split('-', maxsplit=1)[1]
                    .lower().replace(' ', '_')
                )
                row_name = table_name + '_' + temp_name + '_'
                #row_list[1].text
                out[row_name + 'problems'] =  row_list[1].text
                out[row_name + 'warnings'] = row_list[2].text
                out[row_name + 'not_reviewed'] =  row_list[3].text

            elif row.findChildren('td'):
                row_list = row.findChildren('td')
                temp_name = (
                    row_list[0].text
                    .split('-', maxsplit=1)[1]
                    .strip().lower().replace(' ', '_')
                    .replace('-', '_').replace(',','')
                )
                row_name = table_name + '_' + temp_name + '_'
                out[row_name + 'level'] = row_list[1].text
                if row_list[2].findChildren('img'):
                    out[row_name + 'result'] = row_list[2].img.attrs['alt']

                else:
                    out[row_name + 'result'] = row_list[2].text.strip()

                out[row_name + 'problems'] = row_list[3].text
                out[row_name + 'warnings'] = row_list[4].text
                out[row_name + 'not_reviewed'] = row_list[5].text

    return out

def main():
    download_list_path = args.download_list
    out_file_path = args.out_file
    if not args.firefox:
        firefox_path = None
    else:
        firefox_path = args.firefox


    if not args.geckodriver:
        geckodriver_path = './geckodriver'
    else:
        geckodriver_path = args.geckodriver


    driver = webdriver.Firefox(
        firefox_binary=firefox_path,
        executable_path=geckodriver_path
    )
    out_list = []

    with open(download_list_path, 'r') as to_download_file, \
         open(out_file_path, 'w') as out_file:

        for i, page_url in enumerate(to_download_file):
            # Miramos si ya esta bajado
            # if
            if not i:
                old_time = time()
                load_page(driver, page_url, first_load=True)
                out = scrape_source(driver.page_source)
            else:
                new_time = time()
                # Esperamos 5 segundos de mas
                while new_time - old_time < 25:
                    sleep(1)
                    new_time = time()

                old_time = time()
                load_page(driver, page_url)
                out = scrape_source(driver.page_source)
            # Salvamos lo bajado
            json.dump(out, out_file)
            out_file.write('\n')

        driver.close()

if __name__=='__main__':
    main()
