import argparse
import json

from bs4 import BeautifulSoup
import requests

parser = argparse.ArgumentParser(description="Downloads Azure Lane data.", add_help=False)

outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", help="Path to a folder where output should be saved")

helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


output_dir = args.output_dir

BASE_URL = 'https://azurlane.koumakan.jp'
ships_url = '{}/List_of_Ships'.format(BASE_URL)
soup = BeautifulSoup(requests.get(ships_url).text, 'lxml')


def process_image(full_url, title, item):
    page = BeautifulSoup(requests.get(full_url).text, 'lxml')
    original_image_link = page.find('a', text=lambda x: x == 'Original file')
    if original_image_link:
        item['images'][title] = {
            'order': len(item['images']),
            'title': title,
            'file_name': original_image_link['title'],
            'url': '{}{}'.format(BASE_URL, original_image_link['href']),
        }
    else:
        print('failed to find image for ' + title)


def process_tab(tab, item):
    title = tab['title']
    url_ref = tab.find('a')['href']
    full_url = '{}{}'.format(BASE_URL, url_ref)
    process_image(full_url, title, item)


def process_sub_row(full_url, item):
    page = BeautifulSoup(requests.get(full_url).text, 'lxml')

    tables = page.findAll('table')
    for table in tables:
        if table.find('th').text.strip() == 'Ship Stats':
            tabs = table.findAll('div', {'class': 'tabbertab'})
            for tab in tabs:
                process_tab(tab, item)
            return
    print('failed to find ship stats')


def process_row(row):
    cols = row.findAll('td')
    ship_id = int(cols[0].text.strip())
    name_en = cols[1].text.strip()
    url_ref = cols[1].find('a')['href']
    full_url = '{}{}'.format(BASE_URL, url_ref)
    item = {
        'id': ship_id,
        'name_en': name_en,
        'url': full_url,
        'images': {},
    }
    process_sub_row(full_url, item)
    return item


def process_table(table):
    headers = table.findAll('th')
    if len(headers) < 5 or headers[0].text.strip() != 'ID' or headers[1].text.strip() != 'Name':
        print('skipping table')
        return
    rows = table.findAll('tr')[1:]
    items = []
    for row in rows:
        items.append(process_row(row))
    return items


tables = soup.findAll('table')
items = []
for table in tables:
    items.extend(process_table(table))


if len(items) < 100:
    print('Grossly unexpected number of items found, bailing')
    exit()

os.makedirs(output_dir, exist_ok=True)

output_json = {'items': items}
output_json_file = os.path.join(output_dir, 'azure_lane.json')
with open(file_path, "wb") as f:
    json.dump(output_json, output_json_file)


def download_file(url, file_path):
    print('downloading {} to {}'.format(url, file_path))
    response_object = urllib.request.urlopen(url)
    with response_object as response:
        file_data = response.read()
        with open(file_path, "wb") as f:
            f.write(file_data)


for item in items:
    for image in item['images']:
        url = image['url']
        filename = url[url.rfind("/") + 1:]
        image_path = os.file.join(output_dir, filename)
        if not os.path.exists(image_path):
            download_file(url, image_path)
