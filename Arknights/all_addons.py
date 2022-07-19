from contextlib import contextmanager
import logging
logger = logging.getLogger(__name__)
@contextmanager
def guard():
    try:
        yield
    except:
        logger.exception('Exception occurred during loading addon')


with guard(): from .addons.common import CommonAddon
with guard(): from .addons.combat import CombatAddon
with guard(): from .addons.stage_navigator import StageNavigator
with guard(): from .addons.recruit import RecruitAddon
with guard(): from .addons.quest import QuestAddon
with guard(): from .addons.record import RecordAddon
with guard(): from .addons.riic import RIICAddon

with guard(): from .addons.contrib.grass_on_aog import GrassAddOn

with guard(): from .addons.contrib.activity import ActivityAddOn


with guard(): from .addons.contrib.start_sp_stage import StartSpStageAddon

with guard(): from .addons.contrib.plan import PlannerAddOn

with guard(): from .addons import sof_nav
