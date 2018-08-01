import argparse
import json
import os
import urllib.request

import pymysql


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape existing icons from PadGuide.", add_help=False)

    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument("--db_config", required=True, help="JSON database info")

    outputGroup = parser.add_argument_group("Output")
    outputGroup.add_argument("--output_dir", required=True,
                             help="Path to a folder where output should be saved")

    helpGroup = parser.add_argument_group("Help")
    helpGroup.add_argument("-h", "--help", action="help",
                           help="Displays this help message and exits.")

    return parser.parse_args()


def scrape_images(args):
    with open(args.db_config) as f:
        db_config = json.load(f)

    output_dir = args.output_dir

    # Connect to the database
    connection = pymysql.connect(host=db_config['host'],
                                 user=db_config['user'],
                                 password=db_config['password'],
                                 db=db_config['db'],
                                 charset=db_config['charset'],
                                 cursorclass=pymysql.cursors.DictCursor)

    with connection.cursor() as cursor:
        sql = "SELECT icon_url FROM icon_list WHERE icon_url not like 'icon%' and icon_url not like 'port%'"
        cursor.execute(sql)
        icons = list(cursor.fetchall())

    for icon_row in icons:
        icon = icon_row['icon_url']
        image_url = 'http://pad.dnt7.com/images/icons/{}'.format(icon)
        output_file = os.path.join(output_dir, icon)
        urllib.request.urlretrieve(image_url, output_file)


if __name__ == '__main__':
    args = parse_args()
    scrape_images(args)
