#!/usr/bin/env python3

import importlib
import os
import subprocess
import sys
import traceback

from argparse import ArgumentParser
from io import StringIO
from os import path
from sys import platform
from threading import Thread
from urllib import request
from zipfile import ZipFile

PYTHON_MIN_MAJOR_VER = 3
PYTHON_MIN_MINOR_VER = 6

try:
    import tkinter as tk
    from tkinter import messagebox
    from tkinter.filedialog import askdirectory
except:
    try:
        import Tkinter as tk
        from Tkinter import messagebox
        from Tkinter.filedialog import askdirectory
    except:
        # Try as hard as inhumanly possible to tell the user that tkinter isn't on their system.
        NO_TK_ERR = "You cannot run the installer without having tkinter installed system wide"
        print(NO_TK_ERR)
        res = subprocess.run(["kdialog", "--msgbox", NO_TK_ERR])
        if res.returncode != 0:
            res = subprocess.run(["msg", os.getlogin(), NO_TK_ERR])
        if res.returncode != 0:
            res = subprocess.run(["zenity", "--info", "--text="+NO_TK_ERR])
        if res.returncode != 0:
            res = subprocess.run(["toilet", "-F", "gay", NO_TK_ERR])
        if res.returncode != 0:
            res = subprocess.run(["whiptail", "--msgbox", NO_TK_ERR, 0, 0])
        if res.returncode != 0:
            res = subprocess.run(["dialog", "--msgbox", NO_TK_ERR, 0, 0])
        if res.returncode != 0:
            input()
        SystemExit(-1)

MEK_LIB_DIRNAME = "mek_lib"
MEK_DOWNLOAD_URL = "https://github.com/Sigmmma/mek/archive/master.zip"
VERSION = (2,3,2)
VERSION_STR = "v%s.%s.%s" % VERSION

global installer_updated
installer_updated = False

# refinery requires mozzarilla(tag preview features and such), so we dont
# need to specify it here as it will be installed anyway when refinery is.
mek_program_package_names = ("refinery", "hek_pool", ) # "mozzarilla")
mek_library_package_names = ("reclaimer", )
program_package_names     = ("binilla", )
library_package_names     = ("supyr_struct", "arbytmap", "tatsu", )

if "linux" in platform.lower():
    platform = "linux"

PY_EXE = sys.executable

#####################################################
# Windows hack
# You can't run pip from pythonw, only from python.
#####################################################

parent_dir = path.dirname(PY_EXE)
basename = path.basename(PY_EXE)

if basename.lower() == "pythonw.exe":
    PY_EXE = path.join(parent_dir, "python.exe")

del parent_dir, basename


# This makes sure we install the MEK with the same Python as the installer was run.
pip_exec_name = [PY_EXE, "-m", "pip"]

#####################################################
# Embedded installer initialization
#####################################################

parser = ArgumentParser(description='The installer/updater for the MEK. Version %s' % VERSION_STR)
parser.add_argument('--version', action='version', version=VERSION_STR)
parser.add_argument('--install-dir', help='Enforce what directory we download the MEK to.')
parser.add_argument('--disable-uninstall-btn', action='store_true', help='Disable the uninstall button.')
parser.add_argument('--essentials-version', help='The version of the MEK Essentials that launched the installer.')
parser.add_argument('--meke-dir', help='The directory where the MEKe files are located.') # For the future.
cmd_args = parser.parse_args()

INSTALL_DIR          = path.abspath(cmd_args.install_dir or os.curdir)
CAN_PICK_INSTALL_DIR = not bool(cmd_args.install_dir)
HIDE_UNINSTALL_BTN   = cmd_args.disable_uninstall_btn
ESSENTIALS_VERSION   = cmd_args.essentials_version or None

# This is for the embedded updater. We disable certain features if we detect
# that we are embedded.
IS_ESSENTIALS = ESSENTIALS_VERSION is not None
# The version string is currently unused. But it might become useful in the
# future to signal that the whole essentials install needs to be removed
# and updated.

#####################################################
# Utility functions
#####################################################
def _do_subprocess(exec_strs, action="Action", app=None, printout=True):
    '''
    Run a subprocess and print the output.
    '''
    exec_strs = tuple(exec_strs)
    if app is not None and getattr(app, "_running_thread", 1) is None:
        raise SystemExit(0)

    result = 1
    try:
        if printout:
            print("-"*80)
            print("%s "*len(exec_strs) % exec_strs)

        p = subprocess.Popen(exec_strs,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)
        if printout:
            for stdout_line in iter(p.stdout.readline, ""):
                print(stdout_line)
            for stdout_line in iter(p.stderr.readline, ""):
                print(stdout_line)
        p.stdout.close()
        p.stderr.close()
        result = p.wait()

    except Exception:
        if printout:
            print(traceback.format_exc())

    if result:
        print("  %s failed.\n" % action)
        print("  Error code: %02x" % result)
    else:
        print("  %s succeeded.\n" % action)

    return result


def download_mek_to_folder(install_dir, src_url=None):
    '''
    Downloads the mek scripts from the mek repo master and extracts them into
    install_dir.
    '''
    global installer_updated

    if src_url is None:
        src_url = MEK_DOWNLOAD_URL
    print('Downloading newest version of MEK from: "%s"' % src_url)

    mek_zipfile_path, _ = request.urlretrieve(src_url)
    if not mek_zipfile_path:
        print("  Could not download.\n")
        return
    else:
        print("  Finished.\n")

    setup_filepath = '' if "__file__" not in globals() else __file__
    setup_filepath = setup_filepath.lower()
    setup_filename = setup_filepath.split(os.sep)[-1]

    try:
        with open(__file__, 'rb') as f:
            setup_file_data = f.read()
    except Exception:
        setup_file_data = None

    new_installer_path = None

    print('Unpacking MEK to "%s"' % install_dir)
    with ZipFile(mek_zipfile_path) as mek_zipfile:
        for zip_name in mek_zipfile.namelist():
            # ignore the root directory of the zipfile
            filepath = zip_name.split("/", 1)[-1]
            if filepath[:1] == '.' or zip_name[-1:] == "/":
                continue

            try:
                filepath = path.join(install_dir, filepath)

                os.makedirs(path.dirname(filepath), exist_ok=True)

                with mek_zipfile.open(zip_name) as zf, open(filepath, "wb+") as f:
                    filedata = zf.read()
                    if filepath.lower().endswith(setup_filename) and filedata != setup_file_data:
                        # NOTE: Comment out the next line if testing installer
                        installer_updated = True
                        new_installer_path = filepath
                    f.write(filedata)
            except Exception:
                print(traceback.format_exc())

    print("  Finished.\n")

    try: os.remove(mek_zipfile_path)
    except Exception: pass

    if installer_updated:
        messagebox.showinfo(
        "MEK Installer was updated",
        "The MEK installer that was downloaded differs from this one.\n"
        "Please close this installer and run:\n    %s" % new_installer_path
        )


def ensure_setuptools_installed(app):
    '''
    Ensure that setuptools is installed by simply installing it.
    '''
    print("Ensuring setuptools is installed")
    return _do_subprocess(
        (*pip_exec_name, "install", "setuptools"),
        "Ensure setuptools", app)


def is_pip_installed(app):
    '''
    Check if pip is installed by seeing the return code from trying to execute it.
    '''
    global pip_exec_name
    global IS_ESSENTIALS

    if platform == "linux":
        return True
    print("Picking a pip executable")

    try:
        from pip import __file__ as f
        f = path.join(path.dirname(f), "__main__.py")
    except Exception:
        f = "NOT FOUND"

    # Because life isn't fair.

    if not IS_ESSENTIALS:
        pip_patterns = (
            pip_exec_name,
            [PY_EXE, "-m", "pip"],
            [PY_EXE, f],
            ["python3", "-m", "pip"],
            ["python3", f],
            ["pip3"],
            ["python", "-m", "pip"],
            ["python", f],
            ["pip"],
        )
    else:
        # MEK Essentials comes with its own python install which should work
        # properly.
        pip_patterns = (pip_exec_name,)

    for pattern in pip_patterns:
        print("Trying:", pattern, "...", end="")
        if not bool(subprocess.run(pattern).returncode):
            print("success!")
            pip_exec_name = pattern
            return True
        else:
            print("fail.")

    return False


def is_module_fully_installed(mod_path, attrs):
    if isinstance(attrs, str):
        attrs = (attrs, )

    mods = list(mod_path.split("."))
    mod_name = mod_path.replace(".", "_")
    glob = globals()
    if mod_name not in glob:
        import_str = ""
        if len(mods) > 1:
            for mod in mods[: -1]:
                import_str += "%s." % mod
            import_str = "from %s " % import_str[:-1]
        import_str += "import %s as %s" % (mods.pop(-1), mod_name)
        exec("global %s" % mod_name, glob)
        try:
            exec(import_str, glob)
        except Exception:
            return False
    else:
        importlib.reload(glob[mod_name])
    mod = glob[mod_name]

    result = True
    for attr in attrs:
        result &= hasattr(mod, attr)
    return result

def print_diagnostics():
    not_found = "NOT FOUND"
    error = "ERROR"
    print("----- Diagnostic Info -----")
    print("Python:", sys.version_info)
    print("64-bit:", sys.maxsize > 2**32)
    print("Python executable:", sys.executable)
    print("Chosen executable:", PY_EXE)
    print("Mek Installer version:", VERSION_STR)
    try:
        from pip import __version__ as v
    except ImportError:
        v = not_found
    except Exception:
        v = error
    print("pip:", v)
    try:
        from setuptools import __version__ as v
    except ImportError:
        v = not_found
    except Exception:
        v = error
    print("setuptools:", v)
    print("--------------------------")


#####################################################
# Main installer functions
# NOTE: You should be able to call these functions
#       directly just fine(MekInstaller isnt needed)
#####################################################
def uninstall(partial_uninstall=True, show_verbose=False, app=None):
    result = 1
    if not is_pip_installed(app):
        print("Pip doesnt appear to be installed for your version of Python.\n"
              "Cannot uninstall without Pip.")
        return

    try:
        # by default we wont uninstall supyr_struct, arbytmap, or
        # binilla since they may be needed by other applications
        modules = list(mek_program_package_names + mek_library_package_names)
        if not partial_uninstall:
            modules.extend(program_package_names + library_package_names)

        for mod_name in modules:
            exec_strs = [*pip_exec_name, "uninstall", mod_name, "-y"]
            if show_verbose:
                exec_strs += ['--verbose']
            result &= _do_subprocess(exec_strs, "Uninstall", app)
    except Exception:
        print(traceback.format_exc())

    print("-"*10 + " Finished " + "-"*10 + "\n")
    return result


def install(install_path=None, force_reinstall=False,
            install_mek_programs=False, show_verbose=False, app=None):
    global installer_updated
    if not is_pip_installed(app):
        print("Pip doesnt appear to be installed for your version of Python.\n"
              "You can install it using get_pip.py in the MEK directory.\n\n"
              "You can also run your Python installer again, and make sure "
              "'Install Pip' is checked, and complete the installation.\n"
              "If this doesnt help, consult the Google senpai.")
        return

    result = 0
    try:
        if install_mek_programs:
            install_dir = install_path if install_path else INSTALL_DIR
            try:
                download_mek_to_folder(install_dir)
            except Exception:
                print(traceback.format_exc())

            if installer_updated:
                return

        if install_path is not None:
            install_path = path.join(install_path, MEK_LIB_DIRNAME)

        ensure_setuptools_installed(app)
        for mod in mek_program_package_names:
            exec_strs = [*pip_exec_name, "install", mod,
                         "--upgrade", "--no-cache-dir"]
            if install_path is not None:
                exec_strs += ['--target=%s' % install_path]
            if show_verbose:
                exec_strs += ['--verbose']
            if force_reinstall:
                exec_strs += ['--force-reinstall']
            print(" ".join(exec_strs))
            result |= _do_subprocess(exec_strs, "Install/Update", app)

    except Exception:
        print(traceback.format_exc())

    print("-"*10 + " Finished " + "-"*10 + "\n")
    return result


#####################################################
# Installer GUI classes
#####################################################
class IORedirecter(StringIO):
    # Text widget to output text to
    text_out = None

    def __init__(self, text_out, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)
        self.text_out = text_out

    def write(self, string):
        self.text_out.config(state=tk.NORMAL)
        self.text_out.insert(tk.END, string)
        self.text_out.see(tk.END)
        self.text_out.config(state=tk.DISABLED)


class MekInstaller(tk.Tk):
    '''
    This class provides a graphical interface for installing, uninstalling,
    and updating the libraries and programs that the MEK relies on.
    '''
    _running_thread = None
    alive = False

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        title = "MEK installer "+VERSION_STR
        if ESSENTIALS_VERSION:
            title = "MEK Essentials Updater %s - Essentials %s" % (VERSION_STR, ESSENTIALS_VERSION)
        self.title(title)
        # Default scale == 1.333
        self.tk.call("tk", "scaling", "1.666")
        self.minsize(480, 300)

        if ((sys.version_info[0] == PYTHON_MIN_MAJOR_VER and sys.version_info[1] < PYTHON_MIN_MINOR_VER) or
            sys.version_info[0] < PYTHON_MIN_MAJOR_VER):
            messagebox.showinfo(
            "Your version of Python is too old",
            "The minimum required version of Python for the MEK is %d.%d.\n"
            "You have version %d.%d, which is behind that by %d major versions and %d minor versions.\n\n"
            "Get a newer version at www.python.org if you're on Windows, or your package manager if you are on Linux.\n\n"
            "If you believe you have a new enough version then make sure that you're running the right Python on your system."
            % (PYTHON_MIN_MAJOR_VER, PYTHON_MIN_MINOR_VER, sys.version_info[0], sys.version_info[1], PYTHON_MIN_MAJOR_VER - sys.version_info[0], PYTHON_MIN_MINOR_VER - sys.version_info[1])
            )
            sys.exit(1)

        self.install_dir = tk.StringVar(self, INSTALL_DIR)
        self.force_reinstall   = tk.BooleanVar(self, 1)
        self.update_programs   = tk.BooleanVar(self, 1)
        self.portable          = tk.BooleanVar(self)
        self.partial_uninstall = tk.BooleanVar(self)
        self.show_error_info   = tk.BooleanVar(self)

        # make the frames
        self.install_dir_frame = tk.LabelFrame(self, text="MEK directory")
        self.settings_frame    = tk.LabelFrame(self, text="Settings")
        self.actions_frame     = tk.LabelFrame(self, text="Action to perform")

        self.inner_settings0 = tk.Frame(self.settings_frame)
        self.inner_settings1 = tk.Frame(self.settings_frame)
        self.inner_settings2 = tk.Frame(self.settings_frame)
        self.inner_settings3 = tk.Frame(self.settings_frame)
        self.inner_settings4 = tk.Frame(self.settings_frame)

        # add the filepath box
        self.install_dir_entry = tk.Entry(
            self.install_dir_frame, textvariable=self.install_dir)
        self.install_dir_entry.config(width=55, state='disabled')

        # add the buttons
        if CAN_PICK_INSTALL_DIR:
            self.install_dir_browse_btn = tk.Button(
                self.install_dir_frame, text="Browse",
                width=6, command=self.install_dir_browse)

        self.install_btn = tk.Button(
            self.actions_frame, text=(
            "Install/Update" if not IS_ESSENTIALS else "Update/Repair"),
            width=20, command=self.install)
        if not HIDE_UNINSTALL_BTN:
            self.uninstall_btn = tk.Button(
                self.actions_frame, text="Uninstall",
                width=20, command=self.uninstall)

        # add the checkboxes
        self.force_reinstall_checkbox = tk.Checkbutton(
            self.inner_settings0, variable=self.force_reinstall,
            text="force reinstall when updating libraries")
        if not IS_ESSENTIALS:
            self.update_programs_checkbox = tk.Checkbutton(
                self.inner_settings1, variable=self.update_programs,
                command=self.validate_mek_dir, text="install up-to-date MEK")
            self.portable_checkbox = tk.Checkbutton(
                self.inner_settings2, variable=self.portable,
                command=self.validate_mek_dir,
                text="portable install (installs to/updates the 'MEK directory' above)")
            self.partial_uninstall_checkbox = tk.Checkbutton(
                self.inner_settings3, variable=self.partial_uninstall,
                text="partial uninstall (remove only MEK related libraries and programs)")
        self.show_error_info_checkbox = tk.Checkbutton(
            self.inner_settings4, variable=self.show_error_info,
            text="show detailed information")

        self.make_io_text()

        # pack everything

        self.install_dir_entry.pack(side='left', fill='x', expand=True)
        if CAN_PICK_INSTALL_DIR:
            self.install_dir_browse_btn.pack(side='left', fill='both')

        self.force_reinstall_checkbox.pack(side='left', fill='both')
        if not IS_ESSENTIALS:
            self.update_programs_checkbox.pack(side='left', fill='both')
            self.portable_checkbox.pack(side='left', fill='both')
        if not HIDE_UNINSTALL_BTN:
            self.partial_uninstall_checkbox.pack(side='left', fill='both')
        self.show_error_info_checkbox.pack(side='left', fill='both')

        self.install_btn.pack(side='left', fill='x', padx=10)
        if not HIDE_UNINSTALL_BTN:
            self.uninstall_btn.pack(side='right', fill='x', padx=10)

        self.install_dir_frame.pack(fill='x')
        self.settings_frame.pack(fill='both')
        self.actions_frame.pack(fill='both')

        self.inner_settings0.pack(fill='both')
        self.inner_settings1.pack(fill='both')
        self.inner_settings2.pack(fill='both')
        self.inner_settings3.pack(fill='both')
        self.inner_settings4.pack(fill='both')

        self.io_frame.pack(fill='both', expand=True)
        print_diagnostics()
        self.alive = True
        self.validate_mek_dir()

    def validate_mek_dir(self, e=None):
        is_empty_dir = True
        try:
            install_dir = self.install_dir.get() if self.portable.get() else INSTALL_DIR
            if path.isdir(path.join(install_dir, MEK_LIB_DIRNAME)):
                is_empty_dir = False
        except Exception:
            pass

        if is_empty_dir:
            self.update_programs.set(1)

    def destroy(self):
        sys.stdout = sys.orig_stdout
        self._running_thread = None
        tk.Tk.destroy(self)
        self.alive = False
        raise SystemExit(0)

    def make_io_text(self):
        self.io_frame = tk.Frame(self, highlightthickness=0)
        self.io_text = tk.Text(self.io_frame, state='disabled')
        self.io_scroll_y = tk.Scrollbar(self.io_frame, orient='vertical')

        self.io_scroll_y.config(command=self.io_text.yview)
        self.io_text.config(yscrollcommand=self.io_scroll_y.set)

        self.io_scroll_y.pack(fill='y', side='right')
        self.io_text.pack(fill='both', expand=True)
        sys.orig_stdout = sys.stdout
        sys.stdout = IORedirecter(self.io_text)

    def start_thread(self, func, *args, **kwargs):
        def wrapper(app=self, func_to_call=func, a=args, kw=kwargs):
            try:
                kw['app'] = app
                func_to_call(*a, **kw)
            except Exception:
                print(traceback.format_exc())

            app._running_thread = None

        new_thread = Thread(target=wrapper)
        self._running_thread = new_thread
        new_thread.daemon = True
        new_thread.start()

    def install_dir_browse(self):
        if self._running_thread is not None:
            return
        dirpath = askdirectory(initialdir=self.install_dir.get())
        if dirpath:
            self.install_dir.set(path.normpath(dirpath))
            self.validate_mek_dir()
            self.portable.set(1)

    def uninstall(self):
        if self._running_thread is not None:
            return
        if self.portable.get():
            names_str = ""
            package_ct = 0
            for name in (mek_program_package_names + program_package_names +
                         mek_library_package_names + library_package_names):
                names_str = "%s%s\n" % (names_str, name)
                package_ct += 1

            return messagebox.showinfo(
                "Uninstall not necessary",
                "Portable installations do not require any special procedures\n"
                "to uninstall. Just delete the MEK folder to delete the MEK."
                )
        if messagebox.askyesno(
            "Uninstall warning",
            "Are you sure you want to uninstall all the libraries\n"
            "and components that the MEK depends on?"):
            return self.start_thread(uninstall,
                                     self.partial_uninstall.get(),
                                     self.show_error_info.get())

    def install(self):
        if self._running_thread is not None:
            return
        install_dir = None
        if self.portable.get():
            install_dir = self.install_dir.get()
        return self.start_thread(install, install_dir,
                                 self.force_reinstall.get(),
                                 self.update_programs.get(),
                                 self.show_error_info.get())


def run():
    try:
        installer = MekInstaller()
        installer.mainloop()
    except Exception:
        print(traceback.format_exc())
        input()


if __name__ == "__main__":
    run()
