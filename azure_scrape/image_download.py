import argparse
import json
import os

from bs4 import BeautifulSoup
import requests

parser = argparse.ArgumentParser(description="Downloads Azure Lane data.", add_help=False)

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


def process_list_of_ships_table(table, id_mod=None):
    headers = table.findAll('th')
    if len(headers) < 5 or headers[0].text.strip() != 'ID' or headers[1].text.strip() != 'Name':
        print('skipping table')
        return
    rows = table.findAll('tr')[1:]
    items = []
    for row in rows:
        try:
            items.append(process_list_of_ships_row(row, id_mod))
        except:
            print('processing failed')
    return items


def process_list_of_ships_row(row, id_mod):
    cols = row.findAll('td')
    ship_id = cols[0].text.strip()
    if id_mod:
        ship_id = id_mod(ship_id)

    name_en = cols[1].text.strip()
    url_ref = cols[1].find('a')['href']
    full_url = '{}{}{}'.format(BASE_URL, url_ref,'/Gallery')
    item = {
        'id': ship_id,
        'name_en': name_en,
        'url': full_url,
        'images': [],
    }
    print('processing {} {}'.format(ship_id, name_en))
    process_ship(full_url, item)
    return item


def process_ship(full_url, item):
    page = BeautifulSoup(requests.get(full_url).text, 'lxml')

    switcher = page.find('div', {'class': 'tabber'})

    tabs = switcher.findAll('div', {'class': 'tabbertab'})
    if tabs:
        for tab in tabs:
            title = tab['title']
            link = tab.find('div', {'class': 'shipskin-image'}).find('a', {'class': 'image'})
            link_target = link['href']
            full_url = '{}{}'.format(BASE_URL, link_target)
            process_image(full_url, title, item)
    else:
        header = page.find('div', {'class': 'azl_box_head'})
        title = header.find('div', {'class': 'azl_box_title'}).text
        body = page.find('div', {'class': 'azl_box_body'})
        link = body.find('a', {'class': 'image'})
        link_target = link['href']
        full_url = '{}{}'.format(BASE_URL, link_target)
        process_image(full_url, title, item)


def process_image(full_url, title, item):
    page = BeautifulSoup(requests.get(full_url).text, 'lxml')
    original_image_path = page.find('div', {'class': 'fullImageLink'}).find('a')['href']
    if original_image_path:
        file_name = os.path.basename(original_image_path)
        result = {
            'order': len(item['images']),
            'title': title,
            'file_name': file_name,
            'url': '{}{}'.format(BASE_URL, original_image_path),
        }
        print('adding', result)
        item['images'].append(result)
    else:
        print('failed to find image for ' + title)


def download_file(url, file_path):
    print('downloading {} to {}'.format(url, file_path))
    response = requests.get(url)
    with open(file_path, "wb") as f:
        f.write(response.content)


output_dir = args.output_dir

BASE_URL = 'https://azurlane.koumakan.jp'
SHIPS_URL = '{}/List_of_Ships'.format(BASE_URL)
soup = BeautifulSoup(requests.get(SHIPS_URL).text, 'lxml')

header = soup.find(id='Standard_List')
standard_table = header.findNext('table')

header = header.findNext(id='Research_Ships')
research_table = header.findNext('table')

header = header.findNext(id='Collab_Ships')
collab_table = header.findNext('table')

items = []
items.extend(process_list_of_ships_table(standard_table))
items.extend(process_list_of_ships_table(research_table))
items.extend(process_list_of_ships_table(collab_table))

if len(items) < 100:
    print('Grossly unexpected number of items found, bailing')
    exit()

os.makedirs(output_dir, exist_ok=True)

output_json = {'items': items}
output_json_file = os.path.join(output_dir, 'azure_lane.json')
with open(output_json_file, "w") as f:
    json.dump(output_json, f)

for item in items:
    for image in item['images']:
        url = image['url']
        filename = url[url.rfind("/") + 1:]
        image_path = os.path.join(output_dir, filename)
        if not os.path.exists(image_path):
            download_file(url, image_path)
