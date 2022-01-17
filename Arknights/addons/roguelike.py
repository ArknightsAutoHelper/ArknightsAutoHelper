from random import randint

from transitions import Machine, State

import imgreco.roguelike
from Arknights.addons.common import CommonAddon
from Arknights.flags import SMALL_WAIT, TINY_WAIT, MEDIUM_WAIT, BIG_WAIT
from automator import AddonBase


class RoguelikeStageMachine:
    def __init__(self, addon):
        self._initialize_machine()
        self.addon = addon

    def _initialize_machine(self):
        self.states = ["dummy",
                       State(name='stage_unknown', on_enter=['_enter_stage_unknown']),
                       State(name='stage_battle_prepare', on_enter=['_enter_stage_battle_prepare']),
                       State(name='stage_accident', on_enter=['_enter_stage_accident']),
                       State(name='stage_interlude', on_enter=['_enter_stage_interlude']),
                       State(name='place_operator', on_enter=['_enter_place_operator']),
                       State(name='in_battle', on_enter=['_enter_in_battle']),
                       ]
        self.machine = Machine(model=self, states=self.states, initial='dummy')

        # dummy
        self.machine.add_transition('start', 'dummy', 'stage_unknown')

        # stage_unknown
        self.machine.add_transition('do_battle', 'stage_unknown', 'stage_battle_prepare')
        self.machine.add_transition('do_accident', 'stage_unknown', 'stage_accident')
        self.machine.add_transition('do_interlude', 'stage_unknown', 'stage_interlude')

        # battle
        self.machine.add_transition('battle_prepare_done', 'stage_battle_prepare', 'place_operator')
        self.machine.add_transition('place_operator_done', 'place_operator', 'in_battle')
        self.machine.add_transition('battle_end', 'in_battle', 'stage_unknown')

    def _enter_stage_unknown(self):
        self.addon.delay(MEDIUM_WAIT)

        # 选择节点
        screenshot = self.addon.device.screenshot().convert('RGB')
        w, h = screenshot.width, screenshot.height
        subarea = (0, h * 0.2, w, h * 0.8)
        screenshot = screenshot.crop(subarea)
        stage = self.addon.ocr.check_current_stage(screenshot)
        if stage == 0:
            return

        self.addon.ocr.CURRENT_STAGE = (self.addon.ocr.CURRENT_STAGE[0] + subarea[0],
                                        self.addon.ocr.CURRENT_STAGE[1] + subarea[1],
                                        self.addon.ocr.CURRENT_STAGE[2] + subarea[0],
                                        self.addon.ocr.CURRENT_STAGE[3] + subarea[1])
        self.addon.tap_rect(self.addon.ocr.CURRENT_STAGE)
        self.addon.delay(TINY_WAIT)
        self.addon.tap_rect(self.addon.ocr.ENTER_STAGE)

        if stage == 1:
            self.addon.logger.info("作战")
            self.trigger('do_battle')
        elif stage == 2:
            self.addon.logger.info("不期而遇")
        elif stage == 3:
            self.addon.logger.info("幕间余兴")

    def _enter_stage_battle_prepare(self):
        """
        战斗准备
          检测编队是否存在干员
        """
        screenshot = self.addon.device.screenshot().convert('RGB')
        if not self.addon.ocr.check_mountain_exist_in_troop(screenshot):
            self.addon.tap_rect(self.addon.ocr.TROOP_BUTTON)
            for i in range(3):
                self.addon.tap_rect(self.addon.ocr.TROOP_CHOOSE_MOUNTAIN[i])
        self.trigger("battle_prepare_done")

    def _enter_place_operator(self):
        self.addon.tap_rect(self.addon.ocr.START_BATTLE_BUTTON)

        self.addon.delay(SMALL_WAIT)
        screenshot = self.addon.device.screenshot().convert('RGB')
        map = self.addon.ocr.check_battle_map(screenshot)
        self.addon.logger.info(self.addon.ocr.get_map_name(map))

        ((origin1, move1), (origin2, move2)) = self.addon.ocr.get_map_action(map)
        self.addon.logger.info("放置")
        self.addon.swipe_screen_from_origin_to_target(origin1, move1)
        self.addon.delay(TINY_WAIT)
        self.addon.logger.info("朝向")
        self.addon.swipe_screen_from_origin_to_target(origin2, move2)

        self.addon.logger.info("两倍速")
        self.addon.tap_rect(self.addon.ocr.SPEED_UP_BUTTON)

        self.addon.delay(MEDIUM_WAIT)
        screenshot = self.addon.device.screenshot().convert('RGB')
        if not self.addon.ocr.check_skill_available(screenshot):
            return
        self.addon.tap_point(self.addon.ocr.get_operator(map), post_delay=0.0, randomness=(0, 0))
        self.addon.delay(SMALL_WAIT)
        screenshot = self.addon.device.screenshot().convert('RGB')
        if not self.addon.ocr.check_skill_position(screenshot):
            return

        self.addon.logger.info("开启技能")
        self.addon.tap_rect(self.addon.ocr.SKILL_BUTTON)

        self.trigger("place_operator_done")

    def _enter_in_battle(self):
        count = 0
        while True:
            count += 1
            if count % 3 == 0:
                self.addon.logger.info("战斗未结束")

            self.addon.delay(BIG_WAIT)
            screenshot = self.addon.device.screenshot().convert('RGB')
            if self.addon.ocr.check_battle_end(screenshot):
                self.addon.logger.info("战斗完成")
                self.addon.tap_rect(self.addon.ocr.BATTLE_END)
                self.addon.delay(TINY_WAIT)

                move = -randint(self.addon.viewport[0] // 4, self.addon.viewport[0] // 3)
                self.addon.swipe_screen(move)
                self.addon.delay(TINY_WAIT)

                screenshot = self.addon.device.screenshot().convert('RGB')
                if not self.addon.ocr.check_battle_end_run(screenshot):
                    return
                self.addon.tap_rect(self.addon.ocr.BATTLE_END_RUN)

                screenshot = self.addon.device.screenshot().convert('RGB')
                if not self.addon.ocr.check_battle_end_run_ok(screenshot):
                    return
                self.addon.logger.info("什么都不要，走了")
                self.addon.tap_rect(self.addon.ocr.BATTLE_END_RUN_OK)
                self.trigger("battle_end")
                break


class RoguelikeStateMachine:
    def __init__(self, addon):
        self._initialize_machine()
        self.addon = addon

        self.prepare_count = 0
        self.refresh_count = 0
        self.refresh_gap_count = 0

    def _initialize_machine(self):
        self.states = ["dummy",
                       State(name='prepare', on_enter=['_enter_prepare']),
                       State(name='assault', on_enter=['_enter_assault']),
                       State(name="find_mountain", on_enter=['_enter_find_mountain']),
                       State(name="refresh_mountain", on_enter=['_enter_refresh_mountain']),
                       State(name="recruit", on_enter=['_enter_recruit']),
                       State(name="stage", on_enter=['_enter_stage']),
                       "stop"]
        self.machine = Machine(model=self, states=self.states, initial='dummy')
        # dummy
        self.machine.add_transition('start', 'dummy', 'prepare')

        # prepare
        self.machine.add_transition('explore_done', 'prepare', 'assault')
        self.machine.add_transition('explore_fail', 'prepare', 'prepare')
        self.machine.add_transition('stop', 'prepare', 'stop')

        # assult
        self.machine.add_transition('assault_done', 'assault', 'find_mountain')
        self.machine.add_transition('stop', 'assault', 'stop')

        # find mountain
        self.machine.add_transition('find_done', 'find_mountain', 'recruit')
        self.machine.add_transition('find_fail', 'find_mountain', 'refresh_mountain')
        self.machine.add_transition('stop', 'find_mountain', 'stop')
        self.machine.add_transition('refresh', 'refresh_mountain', 'find_mountain')

        # recruit
        self.machine.add_transition('recruit_done', 'recruit', 'stage')
        self.machine.add_transition('stop', 'recruit', 'stop')

    def _enter_prepare(self):
        """
        就绪状态
        1. Explore 开始选择分队
        2. 未找到 Explore 重复3次
        3. 结束
        """
        screenshot = self.addon.device.screenshot()
        if not self.addon.ocr.check_explore_button_exist(screenshot):
            if self.prepare_count >= 3:
                self.trigger('stop')
                return

            self.addon.logger.error("不在肉鸽开始界面")
            self.prepare_count += 1
            self.addon.delay(MEDIUM_WAIT)
            self.trigger("explore_fail")
            return
        self.prepare_count = 0
        self.addon.tap_rect(self.addon.ocr.EXPLORE_BUTTON)
        self.addon.delay(SMALL_WAIT)
        self.trigger("explore_done")

    def _enter_assault(self):
        self.addon.logger.info("突击战术分队")
        move = -randint(self.addon.viewport[0] // 4, self.addon.viewport[0] // 3)
        self.addon.swipe_screen(move)
        self.addon.delay(TINY_WAIT)
        screenshot = self.addon.device.screenshot()
        if not self.addon.ocr.check_assault_detachment(screenshot):
            self.addon.logger.error("未找到突击战术分队")
            self.trigger('stop')
            return
        self.addon.tap_rect(self.addon.ocr.ASSAULT_BUTTON)

        screenshot = self.addon.device.screenshot()
        if not self.addon.ocr.check_assault_ok(screenshot):
            self.addon.logger.error("未找到突击战术分队确认按钮")
            self.trigger('stop')
            return
        self.addon.tap_rect(self.addon.ocr.ASSAULT_OK_BUTTON)

        self.addon.logger.info("取长补短")
        self.addon.tap_rect(self.addon.ocr.STRENGTHS_MAKE_UP_WEAKNESS_BUTTON)
        self.addon.tap_rect(self.addon.ocr.STRENGTHS_MAKE_UP_WEAKNESS_BUTTON)

        self.addon.logger.info("近卫招募")
        self.addon.tap_rect(self.addon.ocr.INITIAL_RECRUIT_BUTTON[0])
        self.addon.delay(TINY_WAIT)
        self.addon.logger.info("好友助战")
        self.addon.tap_rect(self.addon.ocr.SUPPORT_UNITS_BUTTON)
        self.addon.delay(TINY_WAIT)

        self.trigger("assault_done")

    def _enter_find_mountain(self):
        # 左半屏幕
        screenshot = self.addon.device.screenshot().convert('RGB')
        subarea1 = (0, 0, screenshot.width * 0.8, screenshot.height)
        cropped_img = screenshot.crop(subarea1)
        if not self.addon.ocr.check_mountain_exist(cropped_img):
            move = -randint(self.addon.viewport[0] // 4, self.addon.viewport[0] // 3)
            self.addon.swipe_screen(move)
            self.addon.delay(TINY_WAIT)
            # 右半屏幕
            screenshot = self.addon.device.screenshot().convert('RGB')
            if not self.addon.ocr.check_mountain_exist(screenshot):
                self.addon.logger.error("山未找到")
                self.trigger('find_fail')
                return

        self.refresh_count = 0
        self.trigger("find_done")

    def _enter_refresh_mountain(self):
        self.refresh_count += 1
        if self.refresh_count > 5:
            self.trigger('stop')
            return

        self.addon.logger.info('刷新助战列表')
        move = randint(self.addon.viewport[0] // 4, self.addon.viewport[0] // 3)
        self.addon.swipe_screen(move)
        screenshot = self.addon.device.screenshot()
        while not self.addon.ocr.check_refresh_button_exist(screenshot):
            if self.refresh_gap_count >= 3:
                self.trigger('stop')
                return

            self.refresh_gap_count += 1
            self.addon.delay(MEDIUM_WAIT)
            return

        self.refresh_gap_count = 0
        self.addon.tap_rect(self.addon.ocr.REFRESH_BUTTON)
        self.trigger('refresh')

    def _enter_recruit(self):
        screenshot = self.addon.device.screenshot().convert('RGB')
        self.addon.logger.info("山")
        mountain_position = self.addon.ocr.MOUNTAIN
        w, h = mountain_position[2] - mountain_position[0], mountain_position[3] - mountain_position[1]
        click_area = (mountain_position[0] + w * 2.0, mountain_position[1],
                      mountain_position[0] + w * 2.5, mountain_position[3])
        cropped_img = screenshot.crop(click_area)
        if not self.addon.ocr.check_mountain_ok(cropped_img):
            self.trigger('stop')
            return
        self.addon.ocr.MOUNTAIN_OK = (self.addon.ocr.MOUNTAIN_OK[0] + click_area[0],
                                      self.addon.ocr.MOUNTAIN_OK[1] + click_area[1],
                                      self.addon.ocr.MOUNTAIN_OK[2] + click_area[0],
                                      self.addon.ocr.MOUNTAIN_OK[3] + click_area[1])

        # 招募
        self.addon.tap_rect(self.addon.ocr.MOUNTAIN_OK)
        self.addon.delay(TINY_WAIT)
        self.addon.tap_rect((772, 499, 933, 544))
        self.addon.delay(MEDIUM_WAIT)
        self.addon.tap_rect((772, 499, 933, 544))

        self.addon.logger.info("辅助招募")
        self.addon.tap_rect(self.addon.ocr.INITIAL_RECRUIT_BUTTON[1])
        self.addon.delay(TINY_WAIT)
        self.addon.tap_rect(self.addon.ocr.RECRUIT_CONFIRM)
        self.addon.tap_rect(self.addon.ocr.RECRUIT_CONFIRM2)
        self.addon.delay(TINY_WAIT)

        self.addon.logger.info("医疗招募")
        self.addon.tap_rect(self.addon.ocr.INITIAL_RECRUIT_BUTTON[2])
        self.addon.delay(TINY_WAIT)
        self.addon.tap_rect(self.addon.ocr.RECRUIT_CONFIRM)
        self.addon.tap_rect(self.addon.ocr.RECRUIT_CONFIRM2)
        self.addon.delay(TINY_WAIT)

        # 进入古堡
        screenshot = self.addon.device.screenshot().convert('RGB')
        if not self.addon.ocr.check_enter_castle_exist(screenshot):
            self.trigger('stop')
            return
        self.addon.tap_rect(self.addon.ocr.ENTER_CASTLE)
        self.addon.delay(MEDIUM_WAIT)

        self.trigger("recruit_done")

    def _enter_stage(self):
        stage_machine = RoguelikeStageMachine(self.addon)
        stage_machine.start()

    def _enter_stop(self):
        self.addon.logger.error("行动结束")


class RoguelikeAddon(AddonBase):
    def on_attach(self):
        self.ocr = imgreco.roguelike.RoguelikeOCR()
        self.register_cli_command('roguelike', self.cli_roguelike, self.cli_roguelike.__doc__)

    def cli_roguelike(self, argv) -> int:
        """
        roguelike
        集成战略
        """
        with self.helper.frontend.context:
            self.logger.info("前瞻性投资")

            self.machine = RoguelikeStateMachine(self)
            self.machine.start()
        return 0
