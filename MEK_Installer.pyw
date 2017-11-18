#!/usr/bin/env python3

import importlib
import os
import subprocess
import sys
import traceback
import zipfile
try:    import tkinter as tk
except: import Tkinter as tk
from threading import Thread
from tkinter import messagebox
from tkinter.filedialog import askdirectory
from io import StringIO
from os import path
from sys import platform
from urllib import request

global installer_updated
installer_updated = False

mek_lib_dirname = "mek_lib"
curr_dir = os.path.abspath(os.curdir)
mek_download_url = "https://bitbucket.org/Moses_of_Egypt/mek/get/default.zip"

# refinery requires mozzarilla(tag preview features and such), so we dont
# need to specify it here as it will be installed anyway when refinery is.
mek_program_package_names = ("refinery", ) # "mozzarilla")
mek_library_package_names = ("reclaimer", )
program_package_names     = ("binilla", )
library_package_names     = ("supyr_struct", "arbytmap", )

required_module_extensions = {
    "arbytmap.ext": ("arbytmap_ext",   "bitmap_io_ext",    "dds_defs_ext",
                     "raw_packer_ext", "raw_unpacker_ext", "swizzler_ext")
    }

if "linux" in platform.lower():
    platform = "linux"

if platform == "linux":
    pip_exec_name = "pip3"
else:
    pip_exec_name = "pip"


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


def _do_subprocess(exec_strs, action="Action", app=None, printout=True):
    exec_strs = tuple(exec_strs)
    while True:
        if app is not None and getattr(app, "_running_thread", 1) is None:
            raise SystemExit(0)

        result = 1
        try:
            if printout:
                print("-"*80)
                print("%s "*len(exec_strs) % exec_strs)

            with subprocess.Popen(exec_strs, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, shell=True) as p:
                if app is not None:
                    try:
                        for line in p.stdout:
                            if printout:
                                print(line.decode("latin-1"), end='')
                    except:
                        p.kill()
                        p.wait()
                        raise
                else:
                    while p.poll() is None:
                        # wait until the process has finished
                        pass

            result = p.wait()
        except Exception:
            if printout:
                print(traceback.format_exc())

        if app is not None and getattr(app, "_running_thread", 1) is None:
            raise SystemExit(0)

        if result:
            print("  Error code: %02x" % result)

        if result and exec_strs[0] != "python":
            print("  %s failed. Trying with different arguments." % action)
            exec_strs = ("python", "-m") + exec_strs
        else:
            break

    if result:
        print("  %s failed.\n" % action)
    else:
        print("  %s succeeded.\n" % action)
    return result


def uninstall(partial_uninstall=True, show_verbose=False, app=None):
    result = 1
    if not is_pip_installed(app):
        print("Pip doesnt appear to be installed for your version of Python.\n"
              "Cannot uninstall without Pip.")
        return

    try:
        # by default we wont uninstall supyr_struct, arbtmap, or
        # binilla since they may be needed by other applications
        modules = list(mek_program_package_names + mek_library_package_names)
        if not partial_uninstall:
            modules.extend(program_package_names + library_package_names)

        for mod_name in modules:
            exec_strs = [pip_exec_name, "uninstall", mod_name, "-y"]
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
              "Run your Python installer again, make sure 'Install Pip' is "
              "checked, and complete the installation.\n"
              "If this doesnt help, consult the Google senpai.")
        return

    result = 0
    try:
        if install_mek_programs:
            install_dir = install_path if install_path else curr_dir
            download_mek_to_folder(install_dir)
            if installer_updated:
                return

        if install_path is not None:
            install_path = os.path.join(install_path, mek_lib_dirname)

        ensure_setuptools_installed(app)
        for mod in mek_program_package_names:
            exec_strs = [pip_exec_name, "install", mod,
                         "--upgrade", "--no-cache-dir"]
            if install_path is not None:
                exec_strs += ['--target=%s' % install_path]
            if show_verbose:
                exec_strs += ['--verbose']
            if force_reinstall:
                exec_strs += ['--force-reinstall']
            result |= _do_subprocess(exec_strs, "Install/Update", app)

    except Exception:
        print(traceback.format_exc())

    print("-"*10 + " Finished " + "-"*10 + "\n")
    if platform != "linux":
        successes = []

        for mod_path, attrs in required_module_extensions.items():
            successes.append(is_module_fully_installed(mod_path, attrs))
            if not successes[-1]:
                print("%s did not fully compile its C extensions." % mod_path)

        if sum(successes) != len(successes):
            warn_msvc_compile()

    return result


def ensure_setuptools_installed(app):
    print("Ensuring setuptools is installed")
    return _do_subprocess(
        (pip_exec_name, "install", "setuptools", "--no-cache-dir"),
        "Ensure setuptools", app)


def is_pip_installed(app):
    print("Checking that Pip is installed")
    return not _do_subprocess(
        (pip_exec_name, ),
        "Pip check", app, printout=False)


def download_mek_to_folder(install_dir, src_url=None):
    global installer_updated

    if src_url is None:
        src_url = mek_download_url
    print("Downloading newest version of MEK from:\n    %s\n    to:\n    %s\n" %
          (src_url, install_dir))

    mek_zipfile_path, _ = request.urlretrieve(src_url)
    if not mek_zipfile_path:
        print("    Could not download MEK zipfile.")
        return

    if os.sep == "/":
        find = "\\"
    elif os.sep == "\\":
        find = "/"

    setup_filepath = '' if "__file__" not in globals() else __file__
    setup_filepath = setup_filepath.lower().replace(find, os.sep)
    setup_filename = setup_filepath.split(os.sep)[-1]

    try:
        with open(__file__, 'rb') as f:
            setup_file_data = f.read()
    except Exception:
        setup_file_data = None

    new_installer_path = None

    with zipfile.ZipFile(mek_zipfile_path) as mek_zipfile:
        for zip_name in mek_zipfile.namelist():
            filepath = zip_name.split("/", 1)[-1]
            if filepath[:1] == '.':
                continue
            filepath = os.path.join(install_dir, filepath).replace(find, os.sep)
            filename = filepath.split(os.sep)[-1]
            dirpath = os.path.dirname(filepath)

            if not os.path.exists(dirpath):
                os.makedirs(dirpath)

            with mek_zipfile.open(zip_name) as zf, open(filepath, "wb+") as f:
                filedata = zf.read()
                if setup_filename == filename.lower() and filedata != setup_file_data:
                    installer_updated = True
                    new_installer_path = filepath
                f.write(filedata)

    try: os.remove(mek_zipfile_path)
    except Exception: pass

    if installer_updated:
        messagebox.showinfo(
        "MEK Installer was updated",
        "The MEK installer that was downloaded differs from this one.\n"
        "Please close this installer and run:\n    %s" % new_installer_path
        )


def run():
    try:
        installer = MekInstaller()
        installer.mainloop()
    except Exception:
        print(traceback.format_exc())
        input()


def warn_msvc_compile():
    if sys.version_info[0] != 3 or sys.version_info[1] < 3:
        pass
    elif sys.version_info[1] in (3, 4):
        messagebox.showinfo(
            "Accelerator modules were not compiled",
            "A properly set up environment is required for the accelerator "
            "modules these programs utilize to be compiled.\n\n"
            "These accelerators make certain things possible, like bitmap viewing.\n"
            "The MEK will still work fine without them, but anything that relies "
            "on their speedup will be significantly slower(sometimes by 100x).\n\n"

            "If possible, the easiest way to fix this problem is to run this program's "
            "uninstall command, uninstall your current version of python, download and "
            "install python 3.5 or higher, download and install the 2015 build tools "
            "from the link below(make sure to check Windows 8.1 SDK) and run the update "
            "function of this installer with 'force reinstall' checked.\n\n"

            "http://landinghub.visualstudio.com/visual-cpp-build-tools\n\n"

            "If you cannot change your python version, follow the directions from the "
            "link below to get your system configured to compile C extensions, then run "
            "the update function of this installer with 'force reinstall' checked.\n\n"

            "https://blog.ionelmc.ro/2014/12/21/compiling-python-extensions-on-windows/#for-python-3-4\n\n"

            "If you have already done all of these things and you still receive this "
            "message, please private message me on Halomaps.org so I can fix the problem.\n"
            )
    elif sys.version_info[1] > 4:
        messagebox.showinfo(
            "Accelerator modules were not compiled",
            "The Visual Studio 2015 build tools are required for the "
            "accelerator modules these programs utilize to be compiled.\n\n"
            "These accelerators make certain things possible, like bitmap viewing.\n"
            "The MEK will still work fine without them, but anything that relies "
            "on their speedup will be significantly slower(sometimes by 100x).\n\n"

            "To fix this, download and install the 2015 build tools from the link "
            "below(make sure to check Windows 8.1 SDK) and run the update function "
            "of this installer with 'force reinstall' checked.\n\n"

            "http://landinghub.visualstudio.com/visual-cpp-build-tools\n\n"

            "If you already have the build tools installed and you still receive this "
            "message, please private message me on Halomaps.org so I can fix the problem.\n"
            )


class MekInstaller(tk.Tk):
    '''
    This class provides an interface for installing, uninstalling,
    and updating the libraries and programs that the MEK relies on.
    '''
    _running_thread = None
    alive = False

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("MEK installer v2.1.3")
        self.geometry("480x400+0+0")
        self.minsize(480, 300)
        
        self.install_dir = tk.StringVar(self, curr_dir)
        self.force_reinstall   = tk.BooleanVar(self, 1)
        self.update_programs   = tk.BooleanVar(self)
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
        self.install_dir_browse_btn = tk.Button(
            self.install_dir_frame, text="Browse",
            width=6, command=self.install_dir_browse)
        
        self.install_btn = tk.Button(
            self.actions_frame, text="Install/Update",
            width=20, command=self.install)
        self.uninstall_btn = tk.Button(
            self.actions_frame, text="Uninstall",
            width=20, command=self.uninstall)

        # add the checkboxes
        self.force_reinstall_checkbox = tk.Checkbutton(
            self.inner_settings0, variable=self.force_reinstall,
            text="force reinstall when updating libraries")
        self.update_programs_checkbox = tk.Checkbutton(
            self.inner_settings1, variable=self.update_programs, command=self.validate_mek_dir,
            text="install up-to-date MEK")
        self.portable_checkbox = tk.Checkbutton(
            self.inner_settings2, variable=self.portable, command=self.validate_mek_dir,
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
        self.install_dir_browse_btn.pack(side='left', fill='both')

        self.force_reinstall_checkbox.pack(side='left', fill='both')
        self.update_programs_checkbox.pack(side='left', fill='both')
        self.portable_checkbox.pack(side='left', fill='both')
        self.partial_uninstall_checkbox.pack(side='left', fill='both')
        self.show_error_info_checkbox.pack(side='left', fill='both')

        self.install_btn.pack(side='left', fill='x', padx=10)
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
        if sys.version_info[0] < 3 or sys.version_info[1] < 3:
            messagebox.showinfo(
                "Incompatible python version",
                ("The MEK requires python 3.3.0 or higher to be installed.\n"
                "You are currently running version %s.%s.%s\n\n"
                "If you know you have python 3.3.0 or higher installed, then\n"
                "the version your operating system is defaulting to when\n"
                "running python files is %s.%s.%s\n\n") % tuple(sys.version_info[:3]) * 2
                )
            self.destroy()
        self.alive = True
        self.validate_mek_dir()

    def validate_mek_dir(self, e=None):
        is_empty_dir = True
        try:
            install_dir = self.install_dir.get() if self.portable.get() else curr_dir
            if os.path.isdir(os.path.join(install_dir, mek_lib_dirname)):
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

if __name__ == "__main__":
    run()
