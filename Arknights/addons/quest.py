import logging

logger = logging.getLogger(__name__)

class QuestAddon:
    def clear_task(self):
        import imgreco.main
        logger.debug("helper.clear_task")
        logger.info("领取每日任务")
        self.back_to_main()
        screenshot = self.adb.screenshot()
        logger.info('进入任务界面')
        self.tap_quadrilateral(imgreco.main.get_task_corners(screenshot))
        self.__wait(SMALL_WAIT)
        screenshot = self.adb.screenshot()

        hasbeginner = imgreco.task.check_beginners_task(screenshot)
        if hasbeginner:
            logger.info('发现见习任务，切换到每日任务')
            self.tap_rect(imgreco.task.get_daily_task_rect(screenshot, hasbeginner))
            self.__wait(TINY_WAIT)
            screenshot = self.adb.screenshot()
        self.clear_task_worker()
        logger.info('切换到每周任务') #默认进入见习任务或每日任务，因此无需检测，直接切换即可
        self.tap_rect(imgreco.task.get_weekly_task_rect(screenshot, hasbeginner))
        self.clear_task_worker()

    def clear_task_worker(self):
        import imgreco.common
        screenshot = self.adb.screenshot()
        kickoff = True
        while True:
            if imgreco.common.check_nav_button(screenshot) and not imgreco.task.check_collectable_reward(screenshot):
                logger.info("奖励已领取完毕")
                break
            if kickoff:
                logger.info('开始领取奖励')
                kickoff = False
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            screenshot = self.adb.screenshot(cached=False)
