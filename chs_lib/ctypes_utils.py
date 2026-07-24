import ctypes
import os
import psutil
import sys
import wmi


# ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)  # this will prevent the screen saver or sleep.

# ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)  # set the setting back to normal

def hide_console():
    """Méthode permettant de masquer la fenêtre de la console en mode GUI. Nécessaire pour une application 'frozen',
    si cette application prend en charge à la fois le traitement en ligne de commande et le mode GUI .
    """

    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)
        # if you wanted to close the handles...
        # ctypes.windll.kernel32.CloseHandle(whnd)


def show_console():
    """
    Méthode permettant de montrer la console.
    """
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 1)


def from_cmd():
    """
    Focntion permettant d'identifier si le proccesus parent est Windows ou CMD.
    """
    cwmi = wmi.WMI()
    if getattr(sys, 'frozen', False):
        pid = os.getpid()
        name = ''
        for x in range(3):
            for process in cwmi.Win32_Process(ProcessId=pid):
                name = process.name
                pid = process.ParentProcessId
                if 'explorer' in name.lower():
                    return False
    return True


def get_process():
    for proc in psutil.process_iter():
        try:
            # this returns the list of opened files by the current process
            flist = proc.open_files()
            if flist:
                print(proc.pid, proc.name)
                for nt in flist:
                    print("\t", nt.path)

        # This catches a race condition where a process ends
        # before we can examine its files
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print("****", e)


if __name__ == "__main__":
    get_process()
