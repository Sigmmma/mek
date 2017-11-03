'''
This is a thread-safe version of Tkinter for Python3.
Import this where you would normally import tkinter.


Copyright (c) 2017 Devin Bobadilla

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
'''
try:
    from tkinter import *
except ImportError:
    from Tkinter import *
from queue import Queue as _Queue
from time import sleep as _sleep
from threading import currentThread as _curr_thread, _DummyThread


class TkWrapper:
    # process ~66 times per second(aiming for 60Hz with some wiggle room)
    idle_time = 15  # process requests every 15 milliseconds
    after_call_id = None

    def __init__(self, tk_widget=None):
        self.tk_widget     = tk_widget
        self.request_queue = self.create_queue()
        self.tk_thread     = self.get_curr_thread()
        self.after_call_id = None

    # change these if your application uses a different threading framework.
    def get_curr_thread(self): return _curr_thread()
    def create_queue(self):    return _Queue()

    def __getattr__(self, attr_name):
        if self.tk_widget is None:
            raise AttributeError(
                "self.tk_widget is None. Not hooked into a Tk instance.")

        return (lambda *a, _f=getattr(self.tk_widget._tk, attr_name), **kw:
                self.call_tk_attr_threadsafe(_f, *a, **kw))

    def call_tk_attr_threadsafe(self, tk_attr, *a, **kw):
        thread = self.get_curr_thread()
        if thread == self.tk_thread or isinstance(thread, _DummyThread):
            # it is either safe to call from the thread the tkinter widget
            # is running on, or a dummy thread is running which is also safe
            return tk_attr(*a, **kw)

        # add a request to the requests queue to call this attribute
        result, raise_result = response = [None, None]
        self.request_queue.put((response, tk_attr, a, kw))
        while raise_result is None and self.tk_widget is not None:
            _sleep(0.0001)
            result, raise_result = response

        if raise_result:
            raise result
        return result

    def hook(self, tk_widget=None):
        if tk_widget is None:
            tk_widget = self.tk_widget
        if tk_widget is None or hasattr(tk_widget, "_tk"):
            return

        self.tk_widget = tk_widget
        tk_widget._tk  = tk_widget.tk
        tk_widget.tk   = self
        self.after_call_id = tk_widget.after(0, self.process_requests)

    def unhook(self):
        if not hasattr(self.tk_widget, "_tk"): return
        self.tk_widget.tk = self.tk_widget._tk
        del self.tk_widget._tk

        # make sure to cancel any after calls since we are unhooking
        if self.after_call_id is not None:
            self.tk_widget.after_cancel(self.after_call_id)

        self.after_call_id = None
        self.tk_widget = None

    def process_requests(self):
        while self.tk_widget is not None:
            try:
                response, func, a, kw = self.request_queue.get_nowait()
            except Exception:
                break

            try:
                response[:] = (func(*a, **kw), False)
            except Exception as e:
                response[:] = (e, True)

        if self.tk_widget is not None:
            self.after_call_id = self.tk_widget.after(
                self.idle_time, self.process_requests)


def _tk_init_override(self, *a, **kw):
    self._orig_init(*a, **kw)
    # replace the underlying tk object with the wrapper 
    TkWrapper().hook(self)


# dont hook twice or we'll end up with an infinite loop
if not hasattr(Tk, "_orig_init"):
    Tk._orig_init = Tk.__init__
    Tk.__init__   = _tk_init_override
