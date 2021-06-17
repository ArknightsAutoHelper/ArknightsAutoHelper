import numpy as np
import urllib.request, json, time, os, copy, sys
from scipy.optimize import linprog
from . import arkplanner


global penguin_url, headers, LanguageMap
penguin_url = 'https://penguin-stats.io/PenguinStats/api/v2/'
headers = {'User-Agent': 'ArkPlanner'}
LanguageMap = {'CN': 'zh', 'US': 'en', 'JP': 'ja', 'KR': 'ko'}

path_stats = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'matrix_cache.json')
path_rules = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'formula_cache.json')
path_aog_stages = os.path.join(os.path.realpath(os.path.dirname(__file__)), 'aog_stages_cache.json')


class MaterialPlanning(object):
    def __init__(self,
                 update=False,
                 banned_stages={},
                 ConvertionDR=0.18,
                 display_main_only=True):
        """
        Object initialization.
        Args:
            filter_freq: int or None. The lowest frequence that we consider.
                No filter will be applied if None.
            url_stats: string. url to the dropping rate stats data.
            url_rules: string. url to the composing rules data.
            path_stats: string. local path to the dropping rate stats data.
            path_rules: string. local path to the composing rules data.
        """
        self.banned_stages = banned_stages  # for debugging
        self.display_main_only = display_main_only
        self.ConvertionDR = ConvertionDR
        self.aog_stages = []

        self.update(force=update)

    def get_item_id(self):
        items = arkplanner.get_all_items()
        item_array, item_id_to_name = [], {}
        item_name_to_id = {'id': {},
                           'zh': {},
                           'en': {},
                           'ja': {},
                           'ko': {}}

        additional_items = [
            {'itemId': '4001', 'name_i18n': {'ko': '용문폐', 'ja': '龍門幣', 'en': 'LMD', 'zh': '龙门币'}},
            {'itemId': '0010', 'name_i18n': {'ko': '작전기록', 'ja': '作戦記録', 'en': 'Battle Record', 'zh': '作战记录'}}
        ]
        for x in items + additional_items:
            item_array.append(x['itemId'])
            item_id_to_name.update({x['itemId']: {'id': x['itemId'],
                                                  'zh': x['name_i18n']['zh'],
                                                  'en': x['name_i18n']['en'],
                                                  'ja': x['name_i18n']['ja'],
                                                  'ko': x['name_i18n']['ko']}})
            item_name_to_id['id'].update({x['itemId']: x['itemId']})
            item_name_to_id['zh'].update({x['name_i18n']['zh']: x['itemId']})
            item_name_to_id['en'].update({x['name_i18n']['en']: x['itemId']})
            item_name_to_id['ja'].update({x['name_i18n']['ja']: x['itemId']})
            item_name_to_id['ko'].update({x['name_i18n']['ko']: x['itemId']})

        self.item_array = item_array
        self.item_id_to_name = item_id_to_name
        self.item_name_to_id = item_name_to_id
        self.item_dct_rv = {v: k for k, v in enumerate(item_array)}  # from id to idx
        self.item_name_rv = {item_id_to_name[v]['zh']: k for k, v in enumerate(item_array)}  # from (zh) name to idx

    def _pre_processing(self, material_probs):
        """
        Compute costs, convertion rules and items probabilities from requested dictionaries.
        Args:
            material_probs: List of dictionaries recording the dropping info per stage per item.
                Keys of instances: ["itemID", "times", "itemName", "quantity", "apCost", "stageCode", "stageID"].
            convertion_rules: List of dictionaries recording the rules of composing.
                Keys of instances: ["id", "name", "level", "source", "madeof"].
        """
        # construct item id projections.
        # construct stage id projections.
        stage_array = []
        for drop in material_probs['matrix']:
            if drop['stageId'] not in stage_array:
                stage_array.append(drop['stageId'])
        stage_dct_rv = {v: k for k, v in enumerate(stage_array)}
        servers = ['CN']    # ['CN', 'US', 'JP', 'KR']
        languages = ['zh']  # ['zh', 'en', 'ja', 'ko']

        valid_stages = {server: [False] * len(stage_array) for server in servers}
        stage_code = {server: ['' for _ in stage_array] for server in servers}
        stages = {}
        stage_name_rv = {lang: {} for lang in languages}
        stage_id_to_name = {}
        for server in servers:
            try:
                if server == 'CN':
                    stages[server] = arkplanner.get_all_stages()
                else:
                    stages[server] = get_json(f'stages?server={server}')
            except Exception as e:
                print(f'Failed to load server {server}, Error: {e}')
                return -1
            for stage in stages[server]:
                if stage['stageId'] not in stage_dct_rv or 'dropInfos' not in stage:
                    continue
                valid_stages[server][stage_dct_rv[stage['stageId']]] = True
                stage_code[server][stage_dct_rv[stage['stageId']]] = stage['code_i18n'][LanguageMap[server]]
                for lang in languages: stage_name_rv[lang][stage['code_i18n'][lang]] = stage_dct_rv[stage['stageId']]
                stage_id_to_name[stage['stageId']] = {lang: stage['code_i18n'][lang] for lang in languages}
                # Fix KeyError('id')
                stage_id_to_name[stage['stageId']]["id"] = stage['stageId']

        try:
            self.get_item_id()
        except Exception as e:
            print(f'Failed to load item list, Error: {e}')
            return -1

        self.stage_array = stage_array
        self.stage_dct_rv = stage_dct_rv
        self.stage_code = stage_code
        self.valid_stages = valid_stages
        self.stage_name_rv = stage_name_rv
        self.stage_id_to_name = stage_id_to_name

        # To format dropping records into sparse probability matrix
        self.cost_lst = np.zeros(len(self.stage_array))

        for server in servers:
            for stage in stages[server]:
                if stage['stageId'] in self.stage_dct_rv:
                    self.cost_lst[self.stage_dct_rv[stage['stageId']]] = stage['apCost']

        self.update_stage()
        self.stage_array = np.array(self.stage_array)
        self.probs_matrix = np.zeros([len(self.stage_array), len(self.item_array)])

        for drop in material_probs['matrix']:
            try:
                self.probs_matrix[self.stage_dct_rv[drop['stageId']], self.item_dct_rv[drop['itemId']]] = drop[
                                                                                                              'quantity'] / float(
                    drop['times'])
            except:
                print(f'Failed to parse {drop}. (出现此条请带报错信息联系根派)')

        # 添加LS, CE, S4-6, S5-2等的掉落 及 默认龙门币掉落
        for k, stage in enumerate(self.stage_array):
            self.probs_matrix[k, self.item_name_rv['龙门币']] = self.cost_lst[k] * 12
        self.update_droprate()

        # To build equavalence relationship from convert_rule_dct.
        self.update_convertion()
        self.convertions_dct = {}
        convertion_matrix = []
        convertion_outc_matrix = []
        convertion_cost_lst = []
        for rule in self.convertion_rules:
            convertion = np.zeros(len(self.item_array))
            convertion[self.item_name_rv[rule['name']]] = 1

            comp_dct = {comp['name']: comp['count'] for comp in rule['costs']}
            self.convertions_dct[rule['name']] = comp_dct
            for iname in comp_dct:
                convertion[self.item_name_rv[iname]] -= comp_dct[iname]
            convertion[self.item_name_rv['龙门币']] -= rule['goldCost']
            convertion_matrix.append(copy.deepcopy(convertion))

            outc_dct = {outc['name']: outc['count'] for outc in rule['extraOutcome']}
            outc_wgh = {outc['name']: outc['weight'] for outc in rule['extraOutcome']}
            weight_sum = float(rule['totalWeight'])
            for iname in outc_dct:
                convertion[self.item_name_rv[iname]] += outc_dct[iname] * self.ConvertionDR * outc_wgh[
                    iname] / weight_sum
            convertion_outc_matrix.append(convertion)
            convertion_cost_lst.append(0)

        self.convertion_matrix = np.array(convertion_matrix)
        self.convertion_outc_matrix = np.array(convertion_outc_matrix)
        self.convertion_cost_lst = convertion_cost_lst

    def _set_lp_parameters(self):
        """
        Object initialization.
        Args:
            convertion_matrix: matrix of shape [n_rules, n_items].
                Each row represent a rule.
            convertion_cost_lst: list. Cost in equal value to the currency spent in convertion.
            probs_matrix: sparse matrix of shape [n_stages, n_items].
                Items per clear (probabilities) at each stage.
            cost_lst: list. Costs per clear at each stage.
        """
        assert len(self.probs_matrix) == len(self.cost_lst)
        assert len(self.convertion_matrix) == len(self.convertion_cost_lst)
        assert self.probs_matrix.shape[1] == self.convertion_matrix.shape[1]

    def update(self,
               filter_freq=200,
               filter_stages=[],
               url_stats='result/matrix?show_closed_zone=true',
               url_rules='formula',
               path_stats=path_stats,
               path_rules=path_rules,
               force=True):
        """
        To update parameters when probabilities change or new items added.
        Args:
            url_stats: string. url to the dropping rate stats data.
            url_rules: string. url to the composing rules data.
            path_stats: string. local path to the dropping rate stats data.
            path_rules: string. local path to the composing rules data.
        """
        print(f'Start to update data {time.asctime(time.localtime(time.time()))}.')
        if not force:  # if not force to update, try loading data from file.
            try:
                material_probs, self.convertion_rules, aog_stages = \
                    load_data(path_stats, path_rules, path_aog_stages)
                self.aog_stages = set(aog_stages)
                # print(self.aog_stages)
            except:  # loading failed, try loading from server.
                force = True
        if force:  # load from server.
            try:
                print('Requesting data from web resources (i.e., penguin-stats.io)...', end=' ')
                arkplanner.update_cache()
                material_probs, self.convertion_rules, self.aog_stages = request_data(penguin_url + url_stats,
                                                                                      penguin_url + url_rules,
                                                                                      path_stats, path_rules)
                print('done.')
            except Exception as e:
                raise e
                # return

        if filter_freq:
            filtered_probs = []
            for drop in material_probs['matrix']:
                if drop['times'] >= filter_freq and drop['stageId'] not in filter_stages:
                    filtered_probs.append(drop)
            material_probs['matrix'] = filtered_probs

        if self._pre_processing(material_probs) != -1:
            self._set_lp_parameters()

    def _get_plan_no_prioties(self, demand_lst, outcome, gold_demand, exp_demand, convertion_dr, probs_matrix,
                              convertion_matrix, convertion_outc_matrix, cost_lst, convertion_cost_lst):
        """
        To solve linear programming problem without prioties.
        Args:
            demand_lst: list of materials demand. Should include all items (zero if not required).
        Returns:
            strategy: list of required clear times for each stage.
            fun: estimated total cost.
        """
        if convertion_dr != 0.18:
            convertion_outc_matrix = (
                                                 convertion_outc_matrix - convertion_matrix) / 0.18 * convertion_dr + convertion_matrix
        A_ub = (np.vstack([probs_matrix, convertion_outc_matrix])
                if outcome else np.vstack([probs_matrix, convertion_matrix])).T
        cost = (np.hstack([cost_lst, convertion_cost_lst]))
        assert np.any(cost_lst >= 0)

        excp_factor = 1.0
        dual_factor = 1.0

        while excp_factor > 1e-7:
            solution = linprog(c=cost,
                               A_ub=-A_ub,
                               b_ub=-np.array(demand_lst) * excp_factor,
                               method='interior-point')
            if solution.status != 4:
                break

            excp_factor /= 10.0

        while dual_factor > 1e-7:
            dual_solution = linprog(c=-np.array(demand_lst) * excp_factor * dual_factor,
                                    A_ub=A_ub.T,
                                    b_ub=cost,
                                    method='interior-point')
            if solution.status != 4:
                break

            dual_factor /= 10.0

        return solution, dual_solution, excp_factor

    def get_plan(self, requirement_dct={}, deposited_dct={}, input_item_id=True,
                 print_output=False, outcome=False, gold_demand=False, exp_demand=False, exclude=[],
                 store=False, convertion_dr=0.18, input_lang='zh', output_lang='zh', server='CN'):
        """
        User API. Computing the material plan given requirements and owned items.
        Args:
                requirement_dct: dictionary. Contain only required items with their numbers.
                deposit_dct: dictionary. Contain only owned items with their numbers.
        """
        status_dct = {0: 'Optimization terminated successfully. ',
                      1: 'Iteration limit reached. ',
                      2: 'Problem appears to be infeasible. ',
                      3: 'Problem appears to be unbounded. ',
                      4: 'Numerical difficulties encountered.'}

        demand_lst = np.zeros(len(self.item_array))
        for k, v in requirement_dct.items():
            if input_item_id:
                demand_lst[self.item_dct_rv[k]] = v
            else:
                demand_lst[self.item_dct_rv[self.item_name_to_id[input_lang][k]]] = v
        if gold_demand:
            try:
                demand_lst[self.item_name_rv['龙门币']] = 1e9 if gold_demand is True else int(gold_demand)
            except:
                demand_lst[self.item_name_rv['龙门币']] = 1e9
        if exp_demand:
            try:
                demand_lst[self.item_name_rv['作战记录']] = 1e9 if exp_demand is True else int(exp_demand)
            except:
                demand_lst[self.item_name_rv['作战记录']] = 1e9
        for k, v in deposited_dct.items():
            if input_item_id:
                demand_lst[self.item_dct_rv[k]] -= v
            else:
                demand_lst[self.item_dct_rv[self.item_name_to_id[input_lang][k]]] -= v

        if gold_demand == False and exp_demand == True:
            # 如果不需要龙门币 并 需要经验, 就删掉赤金到经验的转化
            convertion_matrix = self.convertion_matrix[:-1]
            convertion_outc_matrix = self.convertion_outc_matrix[:-1]
            convertion_cost_lst = self.convertion_cost_lst[:-1]
        else:
            convertion_matrix = self.convertion_matrix
            convertion_outc_matrix = self.convertion_outc_matrix
            convertion_cost_lst = self.convertion_cost_lst

        def alive(stage):
            if self.aog_stages and self.stage_code[server][self.stage_dct_rv[stage]] not in self.aog_stages:
                return False
            if stage in exclude:
                return False
            if self.stage_code[server][self.stage_dct_rv[stage]] in exclude:
                return False
            return self.valid_stages[server][self.stage_dct_rv[stage]]

        is_stage_alive = [alive(stage) for stage in self.stage_array]
        stage_array = self.stage_array[is_stage_alive]
        cost_lst = self.cost_lst[is_stage_alive]
        probs_matrix = self.probs_matrix[is_stage_alive]
        stage_dct_rv = {v: k for k, v in enumerate(stage_array)}

        solution, dual_solution, excp_factor = self._get_plan_no_prioties(
            demand_lst, outcome, gold_demand, exp_demand, convertion_dr, probs_matrix,
            convertion_matrix, convertion_outc_matrix, cost_lst, convertion_cost_lst)
        x, status = solution.x / excp_factor, solution.status
        y, slack = dual_solution.x, dual_solution.slack
        n_looting, n_convertion = x[:len(cost_lst)], x[len(cost_lst):]

        if status != 0:
            raise ValueError(status_dct[status])

        values = [{"level": '1', "items": []},
                  {"level": '2', "items": []},
                  {"level": '3', "items": []},
                  {"level": '4', "items": []},
                  {"level": '5', "items": []}]

        item_values = dict()

        for i, item in enumerate(self.item_array):
            if y[i] >= 0 and '作战记录' not in self.item_id_to_name[item]['zh'] and \
                    self.item_id_to_name[item]['zh'] not in ['龙门币', '赤金', '碳', '碳素', '碳素组', '经验', '家具'] and \
                    '技巧概要' not in self.item_id_to_name[item]['zh']:
                if y[i] > 0.1:
                    item_value = {
                        "name": self.item_id_to_name[item][output_lang],
                        "value": '%.2f' % y[i]
                    }
                else:
                    item_value = {
                        "name": self.item_id_to_name[item][output_lang],
                        "value": '%.5f' % (y[i])
                    }
                if self.item_array[i][-1] in '12345' and len(self.item_array[i]) == 5:
                    values[int(self.item_array[i][-1]) - 1]['items'].append(item_value)
            item_values[item] = y[i]

        for group in values:
            group["items"] = sorted(group["items"], key=lambda k: float(k['value']), reverse=True)

        cost = np.dot(x[:len(cost_lst)], cost_lst)
        gcost = -np.dot(x[len(cost_lst):], convertion_matrix[:, self.item_name_rv['龙门币']])
        gold = np.dot(n_looting, probs_matrix[:, self.item_name_rv['龙门币']])
        exp = np.dot(n_looting, probs_matrix[:, self.item_name_rv['基础作战记录']]) * 200 + \
              np.dot(n_looting, probs_matrix[:, self.item_name_rv['初级作战记录']]) * 400 + \
              np.dot(n_looting, probs_matrix[:, self.item_name_rv['中级作战记录']]) * 1000 + \
              np.dot(n_looting, probs_matrix[:, self.item_name_rv['作战记录']])

        stages = []
        for i, t in enumerate(n_looting):
            if t >= 0.1:
                stage_name = stage_array[i]
                if self.is_gold_or_exp(stage_name):
                    cost -= t * cost_lst[i]
                    gold -= t * probs_matrix[i, self.item_name_rv['龙门币']]
                    exp -= t * (probs_matrix[i, self.item_name_rv['基础作战记录']] * 200 +
                                probs_matrix[i, self.item_name_rv['初级作战记录']] * 400 +
                                probs_matrix[i, self.item_name_rv['中级作战记录']] * 1000 +
                                probs_matrix[i, self.item_name_rv['作战记录']])
                if self.stage_code['CN'][self.stage_dct_rv[stage_name]][:2] in ['SK', 'AP', 'CE', 'LS', 'PR'] and \
                        self.display_main_only:
                    continue
                target_items = np.where(probs_matrix[i] > 0.02)[0]
                items = {self.item_id_to_name[self.item_array[idx]][output_lang]: float2str(probs_matrix[i, idx] * t)
                         for idx in target_items if len(self.item_array[idx]) == 5 and self.item_array[idx] != 'furni'}
                stage = {
                    "stage": self.stage_id_to_name[stage_array[i]][output_lang],
                    "count": float2str(t),
                    "items": items
                }
                stages.append(stage)

        syntheses = []
        for i, t in enumerate(n_convertion):
            if t >= 0.1:
                target_item = self.item_array[np.argmax(convertion_matrix[i])]
                if self.item_id_to_name[target_item]['zh'] in ['作战记录', '龙门币']:
                    # 不显示经验和龙门币的转化
                    continue
                materials = {self.item_id_to_name[self.item_name_to_id['zh'][k]][output_lang]: f'{v * t:.1f}'
                             for k, v in self.convertions_dct[self.item_id_to_name[target_item]['zh']].items()}
                synthesis = {
                    "target": self.item_id_to_name[target_item][output_lang],
                    "count": str(int(t + 0.9)),
                    "materials": materials
                }
                syntheses.append(synthesis)

        res = {
            "cost": int(cost),
            "gcost": int(gcost),
            'gold': int(gold),
            'exp': int(exp),
            "stages": stages,
            "syntheses": syntheses,
            "values": list(reversed(values))
        }

        # if store:
        #     green = {item['name']: '%.3f' % (float(item['value']) / Price[
        #         self.item_id_to_name[self.item_name_to_id[output_lang][item['name']]]['zh']]) for item in
        #              values[2]['items']}
        #     yellow = {item['name']: '%.3f' % (float(item['value']) / Price[
        #         self.item_id_to_name[self.item_name_to_id[output_lang][item['name']]]['zh']]) for item in
        #               values[3]['items']}
        #
        #     res.update({'green': green,
        #                 'yellow': yellow})

        if print_output:
            print('Estimated total cost: %d, gold: %d, exp: %d.' % (res['cost'], res['gold'], res['exp']))
            print('Loot at following stages:')
            for stage in stages:
                display_lst = [k + '(%s) ' % stage['items'][k] for k in stage['items']]
                print('Stage ' + self.stage_code[server][self.stage_name_rv[output_lang][stage['stage']]]
                      + '(%s times) ===> ' % stage['count'] + ', '.join(display_lst))

            print('\nSynthesize following items:')
            for synthesis in syntheses:
                display_lst = [k + '(%s) ' % synthesis['materials'][k] for k in synthesis['materials']]
                print(synthesis['target'] + '(%s) <=== ' % synthesis['count']
                      + ', '.join(display_lst))

            print('\nItems Values:')
            for i, group in reversed(list(enumerate(values))):
                display_lst = ['%s:%s' % (item['name'], item['value']) for item in group['items']]
                print('Level %d items: ' % (i + 1))
                print(', '.join(display_lst))
        return res

    def is_gold_or_exp(self, stage_name):
        return self.stage_code['CN'][self.stage_dct_rv[stage_name]][:2] in ['LS', 'CE']

    def update_droprate(self):
        self.update_droprate_processing('S4-6', '龙门币', 3228)
        self.update_droprate_processing('S5-2', '龙门币', 2484)
        self.update_droprate_processing('S6-4', '龙门币', 2700, 'update')
        self.update_droprate_processing('CE-1', '龙门币', 1700, 'update')
        self.update_droprate_processing('CE-2', '龙门币', 2800, 'update')
        self.update_droprate_processing('CE-3', '龙门币', 4100, 'update')
        self.update_droprate_processing('CE-4', '龙门币', 5700, 'update')
        self.update_droprate_processing('CE-5', '龙门币', 7500, 'update')
        self.update_droprate_processing('LS-1', '作战记录', 1600, 'update')
        self.update_droprate_processing('LS-2', '作战记录', 2800, 'update')
        self.update_droprate_processing('LS-3', '作战记录', 3900, 'update')
        self.update_droprate_processing('LS-4', '作战记录', 5900, 'update')
        self.update_droprate_processing('LS-5', '作战记录', 7400, 'update')

    def update_convertion_processing(self, target_item: tuple, cost: int, source_item: dict, extraOutcome: dict):
        '''
            target_item: (item, itemCount)
            cost: number of 龙门币
            source_item: {item: itemCount}
            extraOutcome: {outcome: {item: weight}, rate, totalWeight}
        '''
        toAppend = dict()
        Outcome, rate, totalWeight = extraOutcome
        toAppend['costs'] = [{'count': x[1] / target_item[1], 'id': self.item_name_rv[x[0]], 'name': x[0]} for x in
                             source_item.items()]
        toAppend['extraOutcome'] = [
            {'count': rate, 'id': self.item_name_rv[x[0]], 'name': x[0], 'weight': x[1] / target_item[1]} for x in
            Outcome.items()]
        toAppend['goldCost'] = cost / target_item[1]
        toAppend['id'] = self.item_name_to_id['zh'][target_item[0]]
        toAppend['name'] = target_item[0]
        toAppend['totalWeight'] = totalWeight
        self.convertion_rules.append(toAppend)

    def update_convertion(self):
        # 之前的TODO: 考虑芯片/基建材料的不同副产物掉落 <- 不做了, 一般人不用planner做芯片规划
        self.update_convertion_processing(('作战记录', 200), 0, {'基础作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('作战记录', 400), 0, {'初级作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('作战记录', 1000), 0, {'中级作战记录': 1}, ({}, 0, 1))
        self.update_convertion_processing(('作战记录', 1000), 0, {'高级作战记录': 1}, ({}, 0, 1))
        # 这里一定保证这一条在最后!
        # ENSURE THIS LINE IS THE LAST LINE!
        self.update_convertion_processing(('作战记录', 400), 0, {'赤金': 1}, ({}, 0, 1))

    def update_stage(self):
        self.update_stage_processing('LS-1', 10, 'wk_kc_1')
        self.update_stage_processing('LS-2', 15, 'wk_kc_2')
        self.update_stage_processing('LS-3', 20, 'wk_kc_3')
        self.update_stage_processing('LS-4', 25, 'wk_kc_4')
        self.update_stage_processing('LS-5', 30, 'wk_kc_5')
        self.update_stage_processing('CE-1', 10, 'wk_melee_1')
        self.update_stage_processing('CE-2', 15, 'wk_melee_2')
        self.update_stage_processing('CE-3', 20, 'wk_melee_3')
        self.update_stage_processing('CE-4', 25, 'wk_melee_4')
        self.update_stage_processing('CE-5', 30, 'wk_melee_5')

    def update_stage_processing(self, stage_name: str, cost: int, code: str) -> None:
        self.stage_array.append(code)
        self.stage_dct_rv.update({code: len(self.stage_array) - 1})
        self.cost_lst = np.append(self.cost_lst, cost)
        servers = ['CN']    # ['CN', 'US', 'JP', 'KR']
        for server in servers:
            self.stage_code[server].append(stage_name)
            self.valid_stages[server].append(True)

    def update_droprate_processing(self, stage, item, droprate, mode='add'):
        if stage not in self.stage_name_rv['zh']:
            print(f'stage {stage} not found')
            return
        if item not in self.item_name_rv:
            print(f'item {item} not found')
            return
        stageid = self.stage_name_rv['zh'][stage]
        itemid = self.item_name_rv[item]
        if mode == 'add':
            self.probs_matrix[stageid][itemid] += droprate
        elif mode == 'update':
            self.probs_matrix[stageid][itemid] = droprate


def get_json(s):
    req = urllib.request.Request(penguin_url + s, None, headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())


def Cartesian_sum(arr1, arr2):
    arr_r = []
    for arr in arr1:
        arr_r.append(arr + arr2)
    arr_r = np.vstack(arr_r)
    return arr_r


def float2str(x, offset=0.5):
    if x < 1.0:
        out = '%.1f' % x
    else:
        out = '%d' % (int(x + offset))
    return out


def request_data(url_stats, url_rules, save_path_stats, save_path_rules):
    """
    To request probability and convertion rules from web resources and store at local.
    Args:
        url_stats: string. url to the dropping rate stats data.
        url_rules: string. url to the composing rules data.
        save_path_stats: string. local path for storing the stats data.
        save_path_rules: string. local path for storing the composing rules data.
    Returns:
        material_probs: dictionary. Content of the stats json file.
        convertion_rules: dictionary. Content of the rules json file.
    """
    try:
        os.mkdir(os.path.dirname(save_path_stats))
    except:
        pass
    try:
        os.mkdir(os.path.dirname(save_path_rules))
    except:
        pass

    req = urllib.request.Request(url_stats, None, headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        material_probs = json.loads(response.read().decode())
        with open(save_path_stats, 'w') as outfile:
            json.dump(material_probs, outfile)

    req = urllib.request.Request(url_rules, None, headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        response = urllib.request.urlopen(req)
        convertion_rules = json.loads(response.read().decode())
        with open(save_path_rules, 'w') as outfile:
            json.dump(convertion_rules, outfile)

    url_aog = 'https://arkonegraph.herokuapp.com/total/CN'
    req = urllib.request.Request(url_aog, None, headers)
    with urllib.request.urlopen(req, timeout=5) as response:
        response = urllib.request.urlopen(req)
        aog_data = json.loads(response.read().decode())
        tier = aog_data['tier']
        aog_stages = set()
        for i in range(1, 6):
            t = tier['t%d' % i]
            for item in t:
                if item['lowest_ap_stages']:
                    aog_stages.update([x['code'] for x in item['lowest_ap_stages']['normal']])
                if item['balanced_stages']:
                    aog_stages.update([x['code'] for x in item['balanced_stages']['normal']])
                if item['drop_rate_first_stages']:
                    aog_stages.update([x['code'] for x in item['drop_rate_first_stages']['normal']])
        with open(path_aog_stages, 'w') as outfile:
            json.dump(list(aog_stages), outfile)

    return material_probs, convertion_rules, aog_stages


def load_data(path_stats, path_rules, path_aog_stages):
    """
    To load stats and rules data from local directories.
    Args:
        path_stats: string. local path to the stats data.
        path_rules: string. local path to the composing rules data.
    Returns:
        material_probs: dictionary. Content of the stats json file.
        convertion_rules: dictionary. Content of the rules json file.
    """
    with open(path_stats) as json_file:
        material_probs = json.load(json_file)
    with open(path_rules) as json_file:
        convertion_rules = json.load(json_file)
    with open(path_aog_stages) as json_file:
        aog_stages = json.load(json_file)

    return material_probs, convertion_rules, aog_stages