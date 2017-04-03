import os, pip, subprocess, sys, traceback
import tkinter as tk
from threading import Thread
from tkinter import messagebox
from tkinter.filedialog import askdirectory
from io import StringIO
from os import path

info = sys.version_info
curr_dir = os.path.abspath(os.curdir)

# folders required to be in a folder to consider it a
# valid install target if specifying an install location
# The HBOC is pretty much the only thing that could be
# expected to be required to complete the install
mek_required_folders = (
    "hboc",
    )

if info[0] < 3:
    input(
        "You must have python 3 or higher installed to run the MEK.\n" +
        "You currently have %s.%s.%s installed instead." % info[:3])
    raise SystemExit(0)


class IORedirecter(StringIO):
    def __init__(self, text_out, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)
        self.text_out = text_out

    def write(self, string):
        self.text_out.config(state='normal')
        self.text_out.insert('end', string)
        self.text_out.see('end')
        self.text_out.config(state='disabled')


def _do_subprocess(exec_str, action="Action", stdout=None):
    result = 0
    try:
        print("Executing:  %s" % exec_str)
        #print(subprocess.call(exec_str))
        result = subprocess.call(exec_str, stdout=stdout)
    except Exception:
        print(traceback.format_exc())
        print("    %s failed. Trying again with different parameters." % action)

        try:
            print("Executing:  python -m %s" % exec_str)
            #print(subprocess.call("python -m " + exec_str))
            result = subprocess.call("python -m " + exec_str, stdout=stdout)
            print("    %s succeeded." % action)
        except Exception:
            print(traceback.format_exc())
            result = 1
    if result:
        print("    %s failed." % action)
    else:
        print("    %s succeeded." % action)
    return result


def install(install_path=None, app=None, stdout=None):
    result = 1
    try:
        exec_str = "pip install mozzarilla"
        if install_path is not None:
            exec_str += ' --target="%s"' % install_path
        result = _do_subprocess(exec_str, "Install", stdout=stdout)

        exec_str = "pip install arbytmap"
        if install_path is not None:
            exec_str += ' --target="%s"' % install_path
        result &= _do_subprocess(exec_str, "Install", stdout=stdout)
    except Exception:
        print(traceback.format_exc())

    try: app._running_thread = None
    except Exception: pass

    print("-"*10 + " Finished " + "-"*10 + "\n")
    return result


def uninstall(partial_uninstall=True, app=None, stdout=None):
    result = 1
    try:
        # by default we wont uninstall supyr_struct, arbtmap, or
        # binilla since they may be needed by other applications
        modules = ("reclaimer", "mozzarilla")
        if not partial_uninstall:
            modules.extend(("arbytmap", "supyr_struct", "binilla"))

        for mod in modules:
            result &= _do_subprocess("pip uninstall %s -y" % mod,
                                     "Uninstall", stdout=stdout)
    except Exception:
        print(traceback.format_exc())

    try: app._running_thread = None
    except Exception: pass

    print("-"*10 + " Finished " + "-"*10 + "\n")
    return result


def upgrade(install_path=None, force_reinstall=False, app=None, stdout=None):
    result = 1
    try:
        exec_str = "pip install mozzarilla --upgrade"
        if install_path is not None:
            exec_str += ' --target="%s"' % install_path
        result = _do_subprocess(exec_str, "Upgrade", stdout=stdout)

        exec_str = "pip install arbytmap --upgrade"
        if install_path is not None:
            exec_str += ' --target="%s"' % install_path
        result &= _do_subprocess(exec_str, "Upgrade", stdout=stdout)
    except Exception:
        print(traceback.format_exc())

    try: app._running_thread = None
    except Exception: pass

    print("-"*10 + " Finished " + "-"*10 + "\n")
    return result


def run():
    try:
        installer = MekInstaller()
        installer.mainloop()
    except Exception:
        print(traceback.format_exc())
        input()


class MekInstaller(tk.Tk):
    '''
    This class provides an interface for installing, uninstalling,
    and upgrading the libraries and programs that the MEK relies on.
    '''
    _running_thread = None
    terminal_out = None

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("MEK installer v1.0")
        self.geometry("400x260+0+0")
        self.minsize(400, 260)
        
        self.install_dir = tk.StringVar(self)
        self.portable = tk.IntVar(self)
        self.force_reinstall = tk.IntVar(self)
        self.partial_uninstall = tk.IntVar(self)

        self.install_dir.set(curr_dir)

        # make the frames
        self.install_dir_frame = tk.LabelFrame(self, text="MEK directory")
        self.settings_frame = tk.LabelFrame(self, text="Settings")
        self.actions_frame  = tk.LabelFrame(self, text="Action to perform")

        self.inner_settings0 = tk.Frame(self.settings_frame)
        self.inner_settings1 = tk.Frame(self.settings_frame)
        self.inner_settings2 = tk.Frame(self.settings_frame)

        # add the filepath box
        self.install_dir_entry = tk.Entry(
            self.install_dir_frame, textvariable=self.install_dir)
        self.install_dir_entry.config(width=55, state='disabled')

        # add the buttons
        self.install_dir_browse_btn = tk.Button(
            self.install_dir_frame, text="Browse",
            width=6, command=self.install_dir_browse)
        
        self.install_btn = tk.Button(
            self.actions_frame, text="Install",
            width=10, command=self.install)
        self.uninstall_btn = tk.Button(
            self.actions_frame, text="Uninstall",
            width=10, command=self.uninstall)
        self.upgrade_btn = tk.Button(
            self.actions_frame, text="Upgrade",
            width=10, command=self.upgrade)

        # add the checkboxes
        self.force_reinstall_checkbox = tk.Checkbutton(
            self.inner_settings0, variable=self.force_reinstall,
            text="force reinstall when upgrading (for recompiling components)")
        self.portable_checkbox = tk.Checkbutton(
            self.inner_settings1, variable=self.portable,
            text='portable install (upgrades/installs to the "MEK directory" above)')
        self.partial_uninstall_checkbox = tk.Checkbutton(
            self.inner_settings2, variable=self.partial_uninstall,
            text="partial uninstall (remove only Mozzarilla and Reclaimer)")

        self.make_io_text()

        # pack everything
        self.install_dir_entry.pack(side='left', fill='x', expand=True)
        self.install_dir_browse_btn.pack(side='left', fill='both')

        self.portable_checkbox.pack(side='left', fill='both')
        self.force_reinstall_checkbox.pack(side='left', fill='both')
        self.partial_uninstall_checkbox.pack(side='left', fill='both')

        self.install_btn.pack(side='left', fill='x', padx=10)
        self.upgrade_btn.pack(side='left', fill='x', padx=10)
        self.uninstall_btn.pack(side='right', fill='x', padx=10)

        self.install_dir_frame.pack(fill='x')
        self.settings_frame.pack(fill='both')
        self.actions_frame.pack(fill='both')

        self.inner_settings0.pack(fill='both')
        self.inner_settings1.pack(fill='both')
        self.inner_settings2.pack(fill='both')

        self.io_frame.pack(fill='both', expand=True)

    def make_io_text(self):
        self.io_frame = tk.Frame(self, highlightthickness=0)
        self.io_text = tk.Text(self.io_frame, state='disabled')
        self.io_scroll_y = tk.Scrollbar(self.io_frame, orient='vertical')

        self.io_scroll_y.config(command=self.io_text.yview)
        self.io_text.config(yscrollcommand=self.io_scroll_y.set)

        self.io_scroll_y.pack(fill='y', side='right')
        self.io_text.pack(fill='both', expand=True)

        self.terminal_out = sys.stdout = IORedirecter(self.io_text)

    def start_thread(self, func, *args, **kwargs):
        kwargs.update(app=self, stdout=None)#self.terminal_out)
        new_thread = Thread(target=lambda a=args, kw=kwargs: func(*a, **kw))
        self._running_thread = new_thread
        new_thread.daemon = True
        new_thread.start()

    def install_dir_browse(self):
        if self._running_thread is not None:
            return
        dirpath = askdirectory(initialdir=self.install_dir.get())
        if dirpath:
            self.install_dir.set(path.normpath(dirpath))

    def install(self):
        if self._running_thread is not None:
            return

        install_dir = None
        valid_dir = True
        if self.portable.get():
            install_dir = self.install_dir.get()
            for req_path in mek_required_folders:
                valid_dir &= path.isdir(path.join(install_dir, req_path))

        if valid_dir:
            return self.start_thread(uninstall)

        print(str(install_dir) + "\n" +
              "    The above is not a valid directory to install to.\n" +
              "    Required folders couldn't be detected in it.\n" +
              "    Pick the folder that contains all the programs in\n" +
              "    the MEK, as that is where it must be installed.")

    def uninstall(self):
        if self._running_thread is not None:
            return
        if messagebox.askyesno(
            "Uninstall warning",
            "Are you sure you want to uninstall all the libraries\n" +
            "and components that the MEK depends on?"):
            return self.start_thread(uninstall, self.partial_uninstall.get())

    def upgrade(self):
        if self._running_thread is not None:
            return
        install_dir = None
        if self.portable.get():
            install_dir = self.install_dir.get()
        return self.start_thread(upgrade, install_dir,
                                 self.force_reinstall.get())


if __name__ == "__main__":
    run()
