from random import randint
from automator import AddonBase
from .common import CommonAddon

class InventoryAddon(AddonBase):
    def get_inventory_items(self, show_item_name=False, only_normal_items=True):
        import imgreco.inventory

        self.addon(CommonAddon).back_to_main()
        self.logger.info("进入仓库")
        self.tap_rect(imgreco.inventory.get_inventory_rect(self.viewport))

        items = []
        last_screen_items = None
        move = -randint(self.viewport[0] // 4, self.viewport[0] // 3)
        self.swipe_screen(move)
        screenshot = self.screenshot()
        extra_move = randint(self.viewport[0] // 5, self.viewport[0] // 4) \
            if self.control.device_config.screenshot_method == 'aah-agent' else 0
        while True:
            move = -randint(self.viewport[0] // 4, self.viewport[0] // 3) - extra_move
            self.swipe_screen(move)
            screen_items = imgreco.inventory.get_all_item_details_in_screen(
                screenshot, only_normal_items=only_normal_items)
            screen_item_ids = set([item['itemId'] for item in screen_items])
            screen_items_map = {item['itemId']: item['quantity'] for item in screen_items}
            if last_screen_items is not None and not screen_item_ids - last_screen_items:
                self.logger.info("读取完毕")
                break
            if show_item_name:
                name_map = {item['itemName']: item['quantity'] for item in screen_items}
                self.logger.info('name_map: %s' % name_map)
            else:
                self.logger.info('screen_items_map: %s' % screen_items_map)
            last_screen_items = screen_item_ids
            items += screen_items
            # break
            screenshot = self.screenshot()
        if show_item_name:
            self.logger.info('items_map: %s' % {item['itemName']: item['quantity'] for item in items})
        return {item['itemId']: item['quantity'] for item in items}
