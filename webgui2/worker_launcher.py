# we don't want the server process to load the helper logic
# this module is loaded by server and worker process

def worker_process(inq, outq):
    # ... but this function will be called in worker process only
    from . import worker
    worker.worker_process(inq, outq)
