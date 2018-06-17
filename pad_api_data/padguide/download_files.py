import argparse
import json
import os
import time

import padguide_api


parser = argparse.ArgumentParser(description="Downloads PadGuide API data.", add_help=False)
outputGroup = parser.add_argument_group("Output")
outputGroup.add_argument("--output_dir", required=True,
                         help="Path to a folder where output should be saved")
helpGroup = parser.add_argument_group("Help")
helpGroup.add_argument("-h", "--help", action="help", help="Displays this help message and exits.")
args = parser.parse_args()


files = [
    'eventList.jsp',
    'dungeonTypeList.jsp',
    'dungeonList.jsp',
    'skillList.jsp',
    'attributeList.jsp',
    'typeList.jsp',
    'expList.jsp',
    'monsterList.jsp',
    'evolutionList.jsp',
    'evoMaterialList.jsp',
    'subDungeonList.jsp',
    'dungeonMonsterList.jsp',
    'dungeonSkillList.jsp',
    'rssList.jsp',
    'newsList.jsp',
    'seriesList.jsp',
    'awokenSkillList.jsp',
    'monsterInfoList.jsp',
    'getSkillCondition.jsp',
    'getAdsList.jsp',
    'subDungeonScoreList.jsp',
    'collectionCategoryList.jsp',
    'collectionTitleList.jsp',
    'collectionMonsterList.jsp',
    'dungeonSkillDamageList.jsp',
    'eggCategoryList.jsp',
    'eggCategoryNameList.jsp',
    'eggTitleList.jsp',
    'eggTitleNameList.jsp',
    'eggMonsterList.jsp',
    'skillDataList.jsp',
    'iconList.jsp',
    'skillLeaderDataList.jsp',
    'dungeonMonsterDropList.jsp',
    'coinRotationList.jsp',
    'monsterPriceList.jsp',
    'subDungeonPointList.jsp',
    'shopList.jsp',
    'shopLineupList.jsp',
    'monsterAddInfoList.jsp',
    'skillRotationList.jsp',
    'skillRotationListList.jsp',
    'subDungeonRewardList.jsp',
    'subDungeonAliasList.jsp',
    'subDungeonMaliasList.jsp',
    'serverSettingList.jsp',
    'rankList.jsp',
]

schedule_jsp = 'scheduleList.jsp'


def writeJsonFile(ep, js_data):
    file_path = '{}.json'.format(ep)
    with open(os.path.join(args.output_dir, file_path), "w") as f:
        json.dump(js_data, f, sort_keys=True, indent=4)


def writeItemsJsonFile(ep, js_data):
    ep = ep.replace('.jsp', '')
    ep = 'stripped_{}'.format(ep)
    if 'items' in js_data:
        items_json = js_data['items']
        writeJsonFile(ep, items_json)
    else:
        print('no stripped format for', ep)


for ep in files:
    ep_json = padguide_api.makePadguideTsRequest(0, ep)
    writeJsonFile(ep, ep_json)
    writeItemsJsonFile(ep, ep_json)


cur_time = int(round(time.time() * 1000))
three_weeks_ago = cur_time - 3 * 7 * 24 * 60 * 60 * 1000
ep_json = padguide_api.makePadguideTsRequest(three_weeks_ago, schedule_jsp)
writeJsonFile(schedule_jsp, ep_json)
writeItemsJsonFile(schedule_jsp, ep_json)
