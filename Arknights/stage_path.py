from resources.imgreco.map_vectors import stage_maps_linear, is_invalid_stage
known_stages_ocr = [x for v in stage_maps_linear.values() for x in v]


def _isnumchar(ch):
    return len(ch) == 1 and '0' <= ch <= '9'

def get_stage_path(stage):
    parts = stage.split('-')
    part0 = parts[0]
    if _isnumchar(part0[-1]):  # '1-7', 'S4-1', etc
        return ['main', 'ep0' + parts[0][-1], stage]
    elif part0 in ('LS', 'AP', 'SK', 'CE', 'CA'):
        return ['material', part0, stage]
    elif part0 == 'PR' and parts[1] in ('A', 'B', 'C', 'D'):
        return ['soc', 'PR-' + parts[1], stage]
    return None


def is_stage_supported(stage):
    path = get_stage_path(stage)
    if path is None:
        return False
    if path[0] in ('main', 'material', 'soc'):
        partition = path[1]
        import resources.imgreco.map_vectors as map_vectors
        if partition in map_vectors.stage_maps:
            return path[2] in map_vectors.stage_maps[partition]
        return False
    else:
        # FIXME: support for material and soc stages
        return False


def is_stage_supported_ocr(stage):
    return stage in known_stages_ocr and not is_invalid_stage(stage)
