import threading
import os
import ctypes
import time

if os.name == 'posix':
    import signal
    def _usr1_handler(signum, frame):
        if signum == signal.SIGUSR1:
            raise InterruptedError
    signal.signal(signal.SIGUSR1, _usr1_handler)
    signal.siginterrupt(signal.SIGUSR1, True)
    def interrupt_native_thread(thread: threading.Thread):
        ident = thread.ident
        signal.pthread_kill(ident, signal.SIGUSR1)
    sleep = time.sleep
elif os.name == 'nt':
    ctypes.windll.kernel32.OpenThread.restype = ctypes.c_void_p
    def interrupt_native_thread(thread: threading.Thread):
        tid = thread.native_id
        THREAD_ALL_ACCESS = 0x001f03ff
        hThread = ctypes.c_void_p(ctypes.windll.kernel32.OpenThread(THREAD_ALL_ACCESS, 0, tid))
        if hThread:
            try:
                io = ctypes.windll.kernel32.CancelSynchronousIo(hThread)
                apc = ctypes.windll.kernel32.QueueUserAPC(ctypes.cast(ctypes.windll.kernel32.SetHandleCount, ctypes.c_void_p), hThread, 0)
            except:
                pass
            finally:
                ctypes.windll.kernel32.CloseHandle(hThread)
    def sleep(t):
        ms = int(t * 1000)
        if ms < 0:
            ms = 0
        if ms > 0xffffffff:
            ms = 0xffffffff
        ctypes.windll.kernel32.SleepEx(ms, 1)
def interrupt_thread(thread: threading.Thread):
    ident = thread.ident
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(ident), ctypes.py_object(KeyboardInterrupt))
    # NOTE: no way to interrupt CPython-initated system call in non-main thread since PEP 475
    # NOTE: CancelSynchronousIo and QueueUserAPC/NtAlertThread on Windows are also unable to interrupt
    #       because CPython uses overlapped IO and unalertable WaitForMultipleObjects internally.
    # see https://bugs.python.org/issue21895
    # interrupt_native_thread(thread)



def test():
    import time
    def worker():
        while True:
            print("worker sleep 5s")
            time.sleep(5)
            # sleep(5)
            print("worker sleep done")
    thr = threading.Thread(target=worker)
    thr.start()
    print("main sleep 2s")
    sleep(2)
    print("interrupt thread in main")
    interrupt_thread(thr)
    while thr.is_alive():
        thr.join(1)

if __name__ == '__main__':
    test()
