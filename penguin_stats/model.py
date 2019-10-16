def struct(*keys):
    class _structBase:
        # __slots__ = keys
        def __init__(self, **kwargs):
            self.__dict__.update((k, None) for k in keys if k not in kwargs)
            self.__dict__.update(kwargs)

    return _structBase


class StageInfo(struct('code', 'id', 'normal_drop', 'special_drop', 'extra_drop')):
    def __str__(self):
        return self.id


class RangeWithException:
    def __init__(self, lower, upper, exceptions=()):
        self.lower = lower
        self.upper = upper
        self.exceptions = exceptions

    def __contains__(self, item):
        if self.lower <= item <= self.upper:
            return True
        return item in self.exceptions


class ItemInfo(struct('name', 'id', 'type')):
    def __repr__(self):
        return '%s(%s)' % (self.id, self.name)

    def __str__(self):
        return self.id


class ItemModel:
    def __init__(self, items):
        self.namemap = {}
        self.idmap = {}
        for obj in items:
            item = ItemInfo(id=obj['itemId'], name=obj['name'], type=obj['itemType'])
            self.namemap[item.name] = item
            self.idmap[item.id] = item

    def get_by_name(self, name):
        if name in self.namemap:
            return self.namemap[name]
        return None

    def get_by_id(self, itemid):
        if itemid in self.idmap:
            return self.idmap[itemid]
        return None


class StageModel:
    def __init__(self, stages):
        self.codemap = {}
        self.idmap = {}
        for obj in stages:
            stage = StageInfo(code=obj['code'], id=obj['stageId'])
            self.codemap[stage.code] = stage
            self.idmap[stage.id] = stage

    def get_by_code(self, code):
        if code in self.codemap:
            return self.codemap[code]
        return None

    def get_by_id(self, id):
        if id in self.idmap:
            return self.idmap[id]
        return None


class StageValidator:
    def __init__(self, grouprange, itemranges):
        self.grouprange = grouprange
        self.itemranges = itemranges

    def validate_group_count(self, count):
        return count in self.grouprange

    def validate_item_quantity(self, item, qty):
        item = str(item)
        if item not in self.itemranges:
            return False
        return qty in self.itemranges[item]


class ValidationModel:
    def __init__(self, constraints):
        self.constraints = {}
        for obj in constraints:
            name = obj['name']
            groupcon = RangeWithException(**obj['itemTypeBounds'])
            itemcons = {}
            for obj2 in obj['itemQuantityBounds']:
                itemcons[obj2['itemId']] = RangeWithException(**obj2['bounds'])
            self.constraints[name] = StageValidator(groupcon, itemcons)

    def get_validator_for_stage(self, stage):
        stage = str(stage)
        if stage in self.constraints:
            return self.constraints[stage]
        return None
