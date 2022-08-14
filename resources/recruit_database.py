import re
from Arknights.addons.contrib.common_cache import load_game_data
import logging


logger = logging.getLogger(__name__)


recruit_database_bak = [
    ('Lancet-2', 0, ['医疗干员', '远程位', '治疗', '支援机械']),
    ('Castle-3', 0, ['近卫干员', '近战位', '支援', '支援机械']),
    ('夜刀', 1, ['先锋干员', '近战位', '新手']),
    ('黑角', 1, ['重装干员', '近战位', '新手']),
    ('巡林者', 1, ['狙击干员', '远程位', '新手']),
    ('杜林', 1, ['术师干员', '远程位', '新手']),
    ('12F', 1, ['术师干员', '远程位', '新手']),
    ('芬', 2, ['先锋干员', '近战位', '费用回复']),
    ('香草', 2, ['先锋干员', '近战位', '费用回复']),
    ('翎羽', 2, ['先锋干员', '近战位', '输出', '费用回复']),
    ('玫兰莎', 2, ['近卫干员', '近战位', '输出', '生存']),
    ('米格鲁', 2, ['重装干员', '近战位', '防护']),
    ('克洛丝', 2, ['狙击干员', '远程位', '输出']),
    ('安德切尔', 2, ['狙击干员', '远程位', '输出']),
    ('炎熔', 2, ['术师干员', '远程位', '群攻']),
    ('芙蓉', 2, ['医疗干员', '远程位', '治疗']),
    ('安赛尔', 2, ['医疗干员', '远程位', '治疗']),
    ('史都华德', 2, ['术师干员', '远程位', '输出']),
    ('梓兰', 2, ['辅助干员', '远程位', '减速']),
    ('夜烟', 3, ['术师干员', '远程位', '输出', '削弱']),
    ('远山', 3, ['术师干员', '远程位', '群攻']),
    ('杰西卡', 3, ['狙击干员', '远程位', '输出', '生存']),
    ('流星', 3, ['狙击干员', '远程位', '输出', '削弱']),
    ('白雪', 3, ['狙击干员', '远程位', '群攻', '减速']),
    ('清道夫', 3, ['先锋干员', '近战位', '费用回复', '输出']),
    ('红豆', 3, ['先锋干员', '近战位', '输出', '费用回复']),
    ('杜宾', 3, ['近卫干员', '近战位', '输出', '支援']),
    ('缠丸', 3, ['近卫干员', '近战位', '生存', '输出']),
    ('霜叶', 3, ['近卫干员', '近战位', '减速', '输出']),
    ('艾丝黛尔', 3, ['近卫干员', '近战位', '群攻', '生存']),
    ('慕斯', 3, ['近卫干员', '近战位', '输出']),
    ('砾', 3, ['特种干员', '近战位', '快速复活', '防护']),
    ('暗索', 3, ['特种干员', '近战位', '位移']),
    ('末药', 3, ['医疗干员', '远程位', '治疗']),
    ('调香师', 3, ['医疗干员', '远程位', '治疗']),
    ('角峰', 3, ['重装干员', '近战位', '防护']),
    ('蛇屠箱', 3, ['重装干员', '近战位', '防护']),
    ('古米', 3, ['重装干员', '近战位', '防护', '治疗']),
    ('地灵', 3, ['辅助干员', '远程位', '减速']),
    ('阿消', 3, ['特种干员', '近战位', '位移']),
    ('白面鸮', 4, ['医疗干员', '远程位', '治疗', '支援']),
    ('凛冬', 4, ['先锋干员', '近战位', '费用回复', '支援']),
    ('德克萨斯', 4, ['先锋干员', '近战位', '费用回复', '控场']),
    ('因陀罗', 4, ['近卫干员', '近战位', '输出', '生存']),
    ('幽灵鲨', 4, ['近卫干员', '近战位', '群攻', '生存']),
    ('蓝毒', 4, ['狙击干员', '远程位', '输出']),
    ('白金', 4, ['狙击干员', '远程位', '输出']),
    ('陨星', 4, ['狙击干员', '远程位', '群攻', '削弱']),
    ('梅尔', 4, ['辅助干员', '远程位', '召唤', '控场']),
    ('赫默', 4, ['医疗干员', '远程位', '治疗']),
    ('华法琳', 4, ['医疗干员', '远程位', '治疗', '支援']),
    ('临光', 4, ['重装干员', '近战位', '防护', '治疗']),
    ('红', 4, ['特种干员', '近战位', '快速复活', '控场']),
    ('雷蛇', 4, ['重装干员', '近战位', '防护', '输出']),
    ('可颂', 4, ['重装干员', '近战位', '防护', '位移']),
    ('火神', 4, ['重装干员', '近战位', '生存', '防护', '输出']),
    ('普罗旺斯', 4, ['狙击干员', '远程位', '输出']),
    ('守林人', 4, ['狙击干员', '远程位', '输出', '爆发']),
    ('崖心', 4, ['特种干员', '近战位', '位移', '输出']),
    ('初雪', 4, ['辅助干员', '远程位', '削弱']),
    ('真理', 4, ['辅助干员', '远程位', '减速', '输出']),
    ('狮蝎', 4, ['特种干员', '近战位', '输出', '生存']),
    ('食铁兽', 4, ['特种干员', '近战位', '位移', '减速']),
    ('能天使', 5, ['狙击干员', '远程位', '输出']),
    ('推进之王', 5, ['先锋干员', '近战位', '费用回复', '输出']),
    ('伊芙利特', 5, ['术师干员', '远程位', '群攻', '削弱']),
    ('闪灵', 5, ['医疗干员', '远程位', '治疗', '支援']),
    ('夜莺', 5, ['医疗干员', '远程位', '治疗', '支援']),
    ('星熊', 5, ['重装干员', '近战位', '防护', '输出']),
    ('塞雷娅', 5, ['重装干员', '近战位', '防护', '治疗', '支援']),
    ('银灰', 5, ['近卫干员', '近战位', '输出', '支援']),
    ('空爆', 2, ['狙击干员', '远程位', '群攻']),
    ('月见夜', 2, ['近卫干员', '近战位', '输出']),
    ('猎蜂', 3, ['近卫干员', '近战位', '输出']),
    ('夜魔', 4, ['术师干员', '远程位', '输出', '治疗', '减速']),
    ('斯卡蒂', 5, ['近卫干员', '近战位', '输出', '生存']),
    ('陈', 5, ['近卫干员', '近战位', '输出', '爆发']),
    ('诗怀雅', 4, ['近卫干员', '近战位', '输出', '支援']),
    ('格雷伊', 3, ['术师干员', '远程位', '群攻', '减速']),
    ('泡普卡', 2, ['近卫干员', '近战位', '群攻', '生存']),
    ('斑点', 2, ['重装干员', '近战位', '防护', '治疗']),
    ('THRM-EX', 0, ['特种干员', '近战位', '爆发', '支援机械']),
    ('黑', 5, ['狙击干员', '远程位', '输出']),
    ('赫拉格', 5, ['近卫干员', '近战位', '输出', '生存']),
    ('格劳克斯', 4, ['辅助干员', '远程位', '减速', '控场']),
    ('星极', 4, ['近卫干员', '近战位', '输出', '防护']),
    ('苏苏洛', 3, ['医疗干员', '远程位', '治疗']),
    ('桃金娘', 3, ['先锋干员', '近战位', '费用回复', '治疗']),
    ('麦哲伦', 5, ['辅助干员', '远程位', '支援', '减速', '输出']),
    ('送葬人', 4, ['狙击干员', '远程位', '群攻']),
    ('红云', 3, ['狙击干员', '远程位', '输出']),
    ('莫斯提马', 5, ['术师干员', '远程位', '群攻', '支援', '控场']),
    ('槐琥', 4, ['特种干员', '近战位', '快速复活', '削弱']),
    ('清流', 3, ['医疗干员', '远程位', '治疗', '支援']),
    ('梅', 3, ['狙击干员', '远程位', '输出', '减速']),
    ('煌', 5, ['近卫干员', '近战位', '输出', '生存']),
    ('灰喉', 4, ['狙击干员', '远程位', '输出']),
    ('苇草', 4, ['先锋干员', '近战位', '费用回复', '输出']),
    ('布洛卡', 4, ['近卫干员', '近战位', '群攻', '生存']),
    ('安比尔', 3, ['狙击干员', '远程位', '输出', '减速']),
    ('阿', 5, ['特种干员', '远程位', '支援', '输出']),
    ('吽', 4, ['重装干员', '近战位', '防护', '治疗']),
    ('正义骑士号', 0, ['狙击干员', '远程位', '支援', '支援机械']),
    ('刻俄柏', 5, ['术师干员', '远程位', '输出', '控场']),
    ('惊蛰', 4, ['术师干员', '远程位', '输出']),
    ('风笛', 5, ['先锋干员', '近战位', '费用回复', '输出']),
    ('慑砂', 4, ['狙击干员', '远程位', '群攻', '削弱']),
    ('宴', 3, ['近卫干员', '近战位', '输出', '生存']),
    ('刻刀', 3, ['近卫干员', '近战位', '爆发', '输出']),
    ('巫恋', 4, ['辅助干员', '远程位', '削弱']),
    ('傀影', 5, ['特种干员', '近战位', '快速复活', '控场', '输出']),
]


def get_all_recruit_characters():
    recruit_re = re.compile(r'(★+)\\n(.*?)(\n|$)')
    recruit_detail = load_game_data('gacha_table')['recruitDetail']
    # print(recruit_detail)
    result = recruit_re.findall(recruit_detail, re.MULTILINE)
    return parse_match_groups(result)


def parse_match_groups(groups):
    result = []
    for group in groups:
        # star_count = len(group[0])
        characters = []
        for character in group[1].split(' / '):
            characters.append(character.replace('<@rc.eml>', '').replace('</>', ''))
        result += characters
        # print(star_count, characters)
    return result


def get_character_name_map():
    characters = load_game_data('character_table').values()
    result = {}
    # position = set()
    # profession = set()
    for character in characters:
        result[character['name']] = character
    #     position.add(character['position'])
    #     profession.add(character['profession'])
    # print(position)
    # print(profession)
    return result


profession_map = {
    'MEDIC': '医疗干员',
    'WARRIOR': '近卫干员',
    'PIONEER': '先锋干员',
    'CASTER': '术师干员',
    'SPECIAL': '特种干员',
    'SUPPORT': '辅助干员',
    'TANK': '重装干员',
    'SNIPER': '狙击干员',
}
position_map = {
    'MELEE': ['近战位'],
    'RANGED': ['远程位'],
    'ALL': ['近战位', '远程位'],
}


def get_recruit_database_by_game_data():
    all_recruit_characters = get_all_recruit_characters()
    character_name_map = get_character_name_map()
    result = []
    for character_name in all_recruit_characters:
        character = character_name_map.get(character_name)
        if not character:
            logger.warning('character not found: %s', character_name)
            continue
        tag_list = [profession_map.get(character['profession'])]
        tag_list += position_map.get(character['position'], [])
        tag_list += character['tagList']
        # print((character_name, character['rarity'], tag_list))
        if character['rarity'] == 0:
            tag_list.append('支援机械')
        result.append((character_name, character['rarity'], tag_list))
    return result


def check_data():
    recruit_database = get_recruit_database_by_game_data()
    recruit_database_map = {}
    for character_name, rarity, tag_list in recruit_database:
        recruit_database_map[character_name] = (rarity, tag_list)
    old_recruit_database_map = {}
    for character_name, rarity, tag_list in recruit_database_bak:
        old_recruit_database_map[character_name] = (rarity, tag_list)
    print('=' * 20, 1)
    check_data_map(recruit_database_map, old_recruit_database_map)
    print('=' * 20, 2)
    check_data_map(old_recruit_database_map, recruit_database_map)


def check_data_map(data_map1, data_map2):
    for character_name in data_map1:
        data1 = data_map1[character_name]
        data2 = data_map2.get(character_name)
        if not data2:
            print('no backup data:', character_name, data1)
            continue
        if data1[0] != data2[0]:
            print('rarity not match:', character_name, data1, data2)
        if data1[1][:2] != data2[1][:2]:
            print('position/profession not match:', character_name, data1, data2)
        if sorted(data1[1][2:]) != sorted(data2[1][2:]):
            print('tag_list not match:', character_name, data1, data2)


try:
    recruit_database = get_recruit_database_by_game_data()
except Exception as e:
    logger.exception(e)
    recruit_database = recruit_database_bak


__all__ = ['recruit_database']


if __name__ == '__main__':
    check_data()
