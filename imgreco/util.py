def any_in(keys, collection):
    for k in keys:
        if k in collection:
            return True
    return False


def get_vwvh(size):
    if isinstance(size, tuple):
        return (size[0]/100, size[1]/100)
    return (size.width/100, size.height/100)
