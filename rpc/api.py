import app
import app.schemadef

from .context import session_var

def export(func):
    return func

@export
async def app_get_version():
    return app.version

@export
async def app_get_config():
    schema, values = app.schemadef.to_viewmodel(app.config)
    return dict(schema=schema, values=values)

@export
async def app_set_config_values(values):
    app.schemadef.set_flat_values(app.config, values)

@export
async def app_check_updates():
    pass

@export
async def sched_refresh_task_list():
    pass

@export
async def sched_add_task(defn):
    pass

@export
async def sched_update_task(task_id, defn):
    pass

@export
async def sched_remove_task(task_id):
    pass

@export
async def sched_reset_task_list():
    pass

@export
async def sched_start():
    pass

@export
async def sched_interrupt():
    pass

@export
async def sched_get_registered_tasks():
    pass


def _codegen():
    pass

if __name__ == '__main__':
    _codegen()
