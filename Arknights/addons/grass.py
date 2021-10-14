import logging
from random import randint

logger = logging.getLogger(__name__)

class GrassAddon:
    def get_inventory_items(self, show_item_name=False):
        import imgreco.inventory

        self.back_to_main()
        logger.info("进入仓库")
        self.tap_rect(imgreco.inventory.get_inventory_rect(self.viewport))

        items = []
        last_screen_items = None
        move = -randint(self.viewport[0] // 4, self.viewport[0] // 3)
        self.__swipe_screen(move)
        screenshot = self.adb.screenshot()
        while True:
            move = -randint(self.viewport[0] // 4, self.viewport[0] // 3)
            self.__swipe_screen(move)
            screen_items = imgreco.inventory.get_all_item_details_in_screen(screenshot)
            screen_item_ids = set([item['itemId'] for item in screen_items])
            screen_items_map = {item['itemId']: item['quantity'] for item in screen_items}
            if last_screen_items == screen_item_ids:
                logger.info("读取完毕")
                break
            if show_item_name:
                name_map = {item['itemName']: item['quantity'] for item in screen_items}
                logger.info('name_map: %s' % name_map)
            else:
                logger.info('screen_items_map: %s' % screen_items_map)
            last_screen_items = screen_item_ids
            items += screen_items
            # break
            screenshot = self.adb.screenshot()
        if show_item_name:
            logger.info('items_map: %s' % {item['itemName']: item['quantity'] for item in items})
        return {item['itemId']: item['quantity'] for item in items}
