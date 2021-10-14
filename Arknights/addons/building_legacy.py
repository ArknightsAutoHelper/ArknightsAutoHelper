import logging
logger = logging.getLogger(__name__)

class BuildingLegacyAddon:
    def get_credit(self):
        import imgreco.main
        logger.debug("helper.get_credit")
        logger.info("领取信赖")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入好友列表')
        self.tap_quadrilateral(imgreco.main.get_friend_corners(screenshot))
        self.__wait(SMALL_WAIT)
        self.tap_quadrilateral(imgreco.main.get_friend_list(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('访问好友基建')
        self.tap_quadrilateral(imgreco.main.get_friend_build(screenshot))
        self.__wait(MEDIUM_WAIT)
        building_count = 0
        while building_count <= 11:
            screenshot = self.adb.screenshot()
            self.tap_quadrilateral(imgreco.main.get_next_friend_build(screenshot))
            self.__wait(MEDIUM_WAIT)
            building_count = building_count + 1
            logger.info('访问第 %s 位好友', building_count)
        logger.info('信赖领取完毕')

    def get_building(self):
        import imgreco.main
        logger.debug("helper.get_building")
        logger.info("清空基建")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入我的基建')
        self.tap_quadrilateral(imgreco.main.get_back_my_build(screenshot))
        self.__wait(MEDIUM_WAIT + 3)
        self.tap_quadrilateral(imgreco.main.get_my_build_task(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('收取制造产物')
        self.tap_quadrilateral(imgreco.main.get_my_build_task_clear(screenshot))
        self.__wait(SMALL_WAIT)
        logger.info('清理贸易订单')
        self.tap_quadrilateral(imgreco.main.get_my_sell_task_1(screenshot))
        self.__wait(SMALL_WAIT + 1)
        self.tap_quadrilateral(imgreco.main.get_my_sell_tasklist(screenshot))
        self.__wait(SMALL_WAIT -1 )
        sell_count = 0
        while sell_count <= 6:
            screenshot = self.adb.screenshot()
            self.tap_quadrilateral(imgreco.main.get_my_sell_task_main(screenshot))
            self.__wait(TINY_WAIT)
            sell_count = sell_count + 1
        self.tap_quadrilateral(imgreco.main.get_my_sell_task_2(screenshot))
        self.__wait(SMALL_WAIT - 1)
        sell_count = 0
        while sell_count <= 6:
            screenshot = self.adb.screenshot()
            self.tap_quadrilateral(imgreco.main.get_my_sell_task_main(screenshot))
            self.__wait(TINY_WAIT)
            sell_count = sell_count + 1
        self.back_to_main()
        logger.info("基建领取完毕")
