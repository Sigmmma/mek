                        WHAT IS POOL
So first off, what is Pool and why should I use it? Pool is a wrapper
for tool.exe that allows you to batch process tool commands, run up to
64 tool commands in parallel, run tool on directories other than the
one it resides in, and more. Pool also allows you to save the list of
commands you've typed in to text files and load them up for later use.
Pool will load up whatever commands were typed in when it was closed.
Pool can do more, but it is basically an ease-of-use upgrade for tool.


                      GETTING STARTED
To use Pool at all, you first need to select the tool.exe to use.
Pool will try to detect your copies of tool when it loads if none
have been added. To add one, go to "File->Add Tool" and browse to
the tool.exe you want to use. To switch tools, click the menu to
the left of "Help". It will show you all tools it knows about.

Now you're all set, and you can just type commands into this text
box like you would normally when running tool in the command line.
A couple useful examples can be viewed by going to "File->Open"
and opening one of the text files in the command lists folder.


                      HOW TO USE POOL
Just enter commands like you would for running Tool in command line.
Once you've typed them in, hit "Process all" or "Process selected".
Lines starting with a or a / are considered disabled(they are
basically comments), and are ignored when processing. Lines that
begin with a # are considered directives and do special things.
For example, #cwd allows you to set the current working directory,
#k and #c make cmd windows stay open or close(respectively) when
the command finishes processing, and #w tells Pool to wait until
all commands currently processing are finished before continuing.
Combine #k with #w and you can pause processing at certain spots.

Commands currently processing will be surrounded in yellow, failed
commands will be surrounded in red, and finished ones in green.
Because Tool doesn't actually report any error information when it
returns, the only failures Pool can detect are mis-typed commands.
Go to "Help->Commands and Directives" to view an explaination of
each command, each directive, and each of their arguments.
    (NOTE: As of right now, most of the help is blank. Sorry!)


                       SMART-ASSIST
I personally prefer to type commands and parameters in rather than
using a GUI(like a file browser) to do it for me. There are others
like me, but there are also people who want/need the help. To make
everyone happy, I've come up with a smart-assist system that works
through the use of right-clicking. Right-click an empty line and a
menu will pop up that allows you to paste in a template for any
command or directive. Right-click a command to get a description
of it and what its arguments are. Right-click an argument to view
a description of the argument and/or bring up a GUI to edit it.
Smart-assist can be turned off at any time in the Settings menu.
Example:
    Right-click the <scenario> argument of build-cache-file and a
    browser will appear, letting you select the scenario to use.


          THESE COLORS HURT AND I HATE THE TEMPLATES!!!
If you don't like the text color scheme or the commands that appear
in the right-click menu, you can change them through the File menu.
The color scheme and menu options will be opened in notepad, and
will both be applied as soon as you save and close the text files.


             WAS IT REALLY NECESSARY TO CREATE THIS?
No, not at all lmao. I was REALLY bored and decided that it'd be
fun to add another tool(lul) to the MEK that sort-of replaces one
of Bungie's original hek programs. I'm not insane enough to write
an actual REPLACEMENT for tool.exe, so this is good enough for me.

