from automator import AddonBase, cli_command, task_sched
from Arknights.flags import *
from .common import CommonAddon
class QuestAddon(AddonBase):
    def clear_task(self):
        import imgreco.main
        import imgreco.task
        self.logger.debug("helper.clear_task")
        self.logger.info("领取每日任务")
        self.addon(CommonAddon).back_to_main()
        screenshot = self.device.screenshot()
        self.logger.info('进入任务界面')
        self.tap_quadrilateral(imgreco.main.get_task_corners(screenshot))
        self.delay(SMALL_WAIT)
        screenshot = self.device.screenshot()

        hasbeginner = imgreco.task.check_beginners_task(screenshot)
        if hasbeginner:
            self.logger.info('发现见习任务，切换到每日任务')
            self.tap_rect(imgreco.task.get_daily_task_rect(screenshot, hasbeginner))
            self.delay(TINY_WAIT)
            screenshot = self.device.screenshot()
        self.clear_task_worker()
        self.logger.info('切换到每周任务') #默认进入见习任务或每日任务，因此无需检测，直接切换即可
        self.tap_rect(imgreco.task.get_weekly_task_rect(screenshot, hasbeginner))
        self.clear_task_worker()

    def clear_task_worker(self):
        import imgreco.common
        import imgreco.task
        screenshot = self.device.screenshot()
        kickoff = True
        while True:
            if imgreco.common.check_nav_button(screenshot) and not imgreco.task.check_collectable_reward(screenshot):
                self.logger.info("奖励已领取完毕")
                break
            if kickoff:
                self.logger.info('开始领取奖励')
                kickoff = False
            self.tap_rect(imgreco.task.get_collect_reward_button_rect(self.viewport))
            screenshot = self.device.screenshot(cached=False)

    @cli_command('collect')
    def cli_collect(self, argv):
        """
        collect
        收集每日任务和每周任务奖励
        """
        with self.helper.frontend.context:
            self.clear_task()
        return 0

    @task_sched.task(category='日常收菜', title='领取任务奖励')
    class CollectQuestTask(task_sched.Schema):
        pass

    @CollectQuestTask.handler
    def handle_task(self, task: CollectQuestTask):
        self.cli_collect([])
