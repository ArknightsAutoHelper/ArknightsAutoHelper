import logging

logger = logging.getLogger(__name__)

class RecruitAddon:
    def recruit(self):
        import imgreco.recruit
        from . import recruit_calc
        logger.info('识别招募标签')
        tags = imgreco.recruit.get_recruit_tags(self.adb.screenshot())
        logger.info('可选标签：%s', ' '.join(tags))
        result = recruit_calc.calculate(tags)
        logger.debug('计算结果：%s', repr(result))
        return result

