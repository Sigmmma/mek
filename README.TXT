The MEK(Mozz Editing Kit) is a collection of tools made for editing Halo.
Originally created by MosesOfEgypt and now maintained by Sigmma.


Installation:

1. Install a Python version of 3.6 or higher. You can get it on Windows by
    opening the "get_python_3.8" shortcut in the install folder.

2. Run MEK_Installer.pyw

3. Choose whether or not to install the MEK's libraries in a portable fashion
    (to a local directory) or to the machine you are running. Make sure that
    "install up-to-date MEK" is checked so it will download the rest of the
    MEK to the current directory.

4. Click "Install/Update"

5. If the installer fails because it says pip is not installed, close it and
    run get-pip.py to install pip. When it finishes, go back to step 2.



Updating:

1. Run MEK_Installer.pyw
2. Click "Install/Update"



Troubleshooting:

* If you encounter an error while running the MEK installer, make sure to check the
"show detailed information" box and run it again. Send me a message with the output
and your system's information so I can fix it.

    * If the error is “ERROR: Can not combine '--user' and '--target'”, you might be
      using the Microsoft Store version of Python, which is incompatible with the MEK
      installer (check for “AppData\Local\Microsoft\WindowsApps” in your output). Try
      uninstalling that Python and installing one from <https://www.python.org>.

* If programs wont run at all, Python might not have been added to your system's PATH
environment variable. Google how to fix this, or run the python installer again to
uninstall it and re-install it with at least the options specified above ticked.

* If programs wont load or save tags then you have a permissions issue where python
isn't being allowed to modify/make files in the directory you are in.

The way to fix this is to move your modding folder out of program files, or by
updating the permissions for the folder to be editable by non-admin users.
Window's User Account Control is very picky and mean about how things get edited
in protected folders.

* If you changed config settings and now a program wont load or the gui is too messed up
up to easily use, delete the config files. Config files for Refinery, Mozzarilla, and Pool
are located in: mek_config
