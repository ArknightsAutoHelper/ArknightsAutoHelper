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
    signal.signal(signal.SIGUSR2, _usr1_handler)
    signal.siginterrupt(signal.SIGUSR1, True)
    signal.siginterrupt(signal.SIGUSR2, True)
    def interrupt_native_thread(thread: threading.Thread):
        ident = thread.ident
        signal.pthread_kill(ident, signal.SIGUSR1)
        # signal.pthread_kill(threading.main_thread().ident, signal.SIGUSR2)
        os.kill(os.getpid(), signal.SIGCHLD)
    def set_interruptible():
        signal.pthread_sigmask(signal.SIG_UNBLOCK, [signal.SIGUSR1])        
    sleep = time.sleep
elif os.name == 'nt':
    ctypes.windll.kernel32.OpenThread.restype = ctypes.c_void_p
    def interrupt_native_thread(thread: threading.Thread):
        tid = thread.native_id
        THREAD_ALL_ACCESS = 0x001f03ff
        hThread = ctypes.c_void_p(ctypes.windll.kernel32.OpenThread(THREAD_ALL_ACCESS, 0, tid))
        if hThread:
            try:
                ctypes.windll.kernel32.SuspendThread(hThread)
                io = ctypes.windll.kernel32.CancelSynchronousIo(hThread)
                apc = ctypes.windll.kernel32.QueueUserAPC(ctypes.cast(ctypes.windll.kernel32.SetHandleCount, ctypes.c_void_p), hThread, 0)
                print("io:", io, "apc:", apc)
                ctypes.windll.kernel32.ResumeThread(hThread)
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
    def set_interruptible():
        pass
def interrupt_thread(thread: threading.Thread):
    ident = thread.ident
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(ident), ctypes.py_object(KeyboardInterrupt))
    interrupt_native_thread(thread)



def test():
    import time
    def worker():
        while True:
            print("worker sleep 5s")
            sleep(5)
            print("worker sleep done")
    thr = threading.Thread(target=worker)
    thr.start()
    print("main sleep 2s")
    sleep(2)
    print("interrupt thread in main")
    interrupt_thread(thr)
    thr.join()

if __name__ == '__main__':
    test()
