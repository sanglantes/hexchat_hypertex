import hexchat
import time
import re

import subprocess
import sys

if sys.platform == "win32":
    _orig_popen = subprocess.Popen

    def _hidden_popen(*args, **kwargs):
        kwargs.setdefault(
            "creationflags",
            subprocess.CREATE_NO_WINDOW
        )
        return _orig_popen(*args, **kwargs)

    subprocess.Popen = _hidden_popen

import matplotlib.pyplot as plt
import datetime
import os
import tempfile

__module_name__ = "HyperTeX"
__module_version__ = "1.0"
__module_description__ = "Detect and render TeX and hyperlink to its output."

print (f"Loading HyperTeX {time.time()}")

def render_tex(author: str, code: str, i: int) -> str:
    try:
        plt.rcParams['text.usetex'] = True

        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis('off')

        text = ax.text(0, 0, code, fontsize=18, ha='left', va='bottom')

        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        bbox = text.get_window_extent(renderer=renderer)
        bbox = bbox.expanded(
            (bbox.width+2*2) / bbox.width,
            (bbox.height+2*5) / bbox.height
        )
        fig.set_size_inches((bbox.width)/fig.dpi, (bbox.height+1)/fig.dpi)
        text.set_position(((-bbox.x0)/fig.dpi, -bbox.y0/fig.dpi))

        x = datetime.datetime.now()
        png_name = f"{author}_{x.strftime('%y_%d_%H%M%S')}_{i}.png"
        save_path = os.path.join(tempfile.gettempdir(), png_name)
        plt.savefig(save_path, dpi=300, transparent=False)

        return save_path
    except Exception as e:
        return "INVALID_TEX"

pattern = re.compile(
    r'\$\$.*?\$\$|\$.*?\$', re.VERBOSE|re.DOTALL
)

def preprint(words, word_eol, userdata):
    message = word_eol[1]
    author = words[0]
    for e, m in enumerate(pattern.findall(message)):
        output = render_tex(author, m, e)
        if output == "INVALID_TEX":
            hexchat.prnt("\x02HyperTeX\x02: Failed to render.")
            continue
        hexchat.prnt(f"\x02[tex]\x02  file://{output}")
    return hexchat.EAT_NONE

hexchat.hook_print("Channel Message", preprint)
hexchat.hook_print("Your Message", preprint)
