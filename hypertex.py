import hexchat
import time
import re
import threading
import queue
import subprocess
import sys
import datetime
import os
import tempfile

import matplotlib
matplotlib.use("Agg")

if sys.platform == "win32": # this might also be an issue on linux. not sure.
    _orig_popen = subprocess.Popen

    def _hidden_popen(*args, **kwargs):
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
        return _orig_popen(*args, **kwargs)

    subprocess.Popen = _hidden_popen

import matplotlib.pyplot as plt
plt.rcParams['text.usetex'] = True

__module_name__ = "HyperTeX"
__module_version__ = "1.1"
__module_description__ = "Detect and render TeX and hyperlink to its output."

hexchat.prnt(f"Loading HyperTeX {time.time()}")

render_queue = queue.Queue()

def render_tex(author: str, code: str, i: int) -> str:
    try:
        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')

        text = ax.text(0, 0, code, fontsize=18, ha='left', va='bottom')

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox = text.get_window_extent(renderer=renderer)

        px = 2
        py = 6
        bbox = bbox.expanded((bbox.width+2*px) / bbox.width, (bbox.height+2*py) / bbox.height)

        fig.set_size_inches(bbox.width / fig.dpi,bbox.height / fig.dpi)
        text.set_position(-bbox.x0 / fig.dpi, -bbox.y0 / fig.dpi)

        timestamp = datetime.datetime.now().strftime('%y_%d_%H%M%S')
        png_name = f"{author}_{timestamp}_{i}.png"
        save_path = os.path.join(tempfile.gettempdir(), png_name)

        plt.savefig(save_path, dpi=300, transparent=False, pad_inches=0)
        plt.close(fig)

        return save_path

    except Exception:
        return "INVALID_TEX"

def render_worker():
    while True:
        job = render_queue.get()
        if job is None:
            break

        author, code, index = job
        path = render_tex(author, code, index)

        def ui_print(userdata=None):
            if path == "INVALID_TEX":
                hexchat.prnt("\x02HyperTeX\x02: Failed to render.")
            else:
                hexchat.prnt(f"\x02[tex]\x02  file://{path}")
            return False

        hexchat.hook_timer(0, ui_print)
        render_queue.task_done()

threading.Thread(target=render_worker, daemon=True).start()

pattern = re.compile(
    r'\$\$.*?\$\$|\$.*?\$', re.VERBOSE|re.DOTALL
)

def preprint(words, word_eol, userdata):
    message = word_eol[1]
    author = words[0]

    for i, match in enumerate(pattern.findall(message)):
        render_queue.put((author, match, i))

    return hexchat.EAT_NONE

hexchat.hook_print("Channel Message", preprint)
hexchat.hook_print("Your Message", preprint)
