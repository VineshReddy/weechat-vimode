# -*- coding: utf-8 -*-
#
# Copyright (C) 2013-2014 Germain Z. <germanosz@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Add vi/vim-like modes to WeeChat.
# For the full help, type `/vimode` inside WeeChat.
#


import csv
import os
import re
import subprocess
from StringIO import StringIO
import time

import weechat


# Script info.
# ============

SCRIPT_NAME = "vimode"
SCRIPT_AUTHOR = "GermainZ <germanosz@gmail.com>"
SCRIPT_VERSION = "0.4"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = ("Add vi/vim-like modes and keybindings to WeeChat.")


# Halp!
# =====

# Type '/vimode' in WeeChat to view this help formatted text.
HELP_TEXT = """
GitHub repo: {url}https://github.com/GermainZ/weechat-vimode

{header}Description:
Add vi/vim-like modes and keybindings to WeeChat.

{header}Usage:
To switch to Normal mode, press Esc or Ctrl+Space.

Two bar items are provided:
    {bold}mode_indicator{reset}: shows the currently active mode \
(e.g. "NORMAL").
    {bold}vi_buffer{reset}: shows partial commands (e.g. "df").
You can add them to your input bar. For example, using iset.pl:
    /iset weechat.bar.input.items
    <Alt+Enter>
    Add {bold}[mode_indicator]+{reset} at the start, and \
{bold},[vi_buffer]{reset} at the end.
Final result example:
    "{bold}[mode_indicator]+{reset}[input_prompt]+(away),[input_search],\
[input_paste],input_text,{bold}[vi_buffer]{reset}"

To switch back to Insert mode, you can use i, a, A, etc.
To execute an Ex command, simply precede it with a ':' while in normal mode, \
for example: ":h" or ":s/foo/bar".

{header}Current key bindings:
{header2}Input line:
{header3}Operators:
d{com}{{motion}}{reset}   Delete text that {com}{{motion}}{reset} moves over.
c{com}{{motion}}{reset}   Delete {com}{{motion}}{reset} text and start insert.
y{com}{{motion}}{reset}   Yank {com}{{motion}}{reset} text to clipboard.
{header3}Motions:
h           {com}[count]{reset} characters to the left exclusive.
l           {com}[count]{reset} characters to the right exclusive.
w           {com}[count]{reset} words forward exclusive.
W           {com}[count]{reset} WORDS forward exclusive.
b           {com}[count]{reset} words backward.
B           {com}[count]{reset} WORDS backward.
ge          Backward to the end of word {com}[count]{reset} inclusive.
gE          Backward to the end of WORD {com}[count]{reset} inclusive.
e           Forward to the end of word {com}[count]{reset} inclusive.
E           Forward to the end of WORD {com}[count]{reset} inclusive.
0           To the first character of the line.
^           To the first non-blank character of the line exclusive.
$           To the end of the line exclusive.
f{com}{{char}}{reset}     To {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the right.
F{com}{{char}}{reset}     To {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the left.
t{com}{{char}}{reset}     Till before {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the right.
T{com}{{char}}{reset}     Till after {com}[count]{reset}'th occurence of \
{com}{{char}}{reset} to the left.
{header3}Other:
<Space>     {com}[count]{reset} characters to the right.
<BS>        {com}[count]{reset} characters to the left.
x           Delete {com}[count]{reset} characters under and after the cursor.
X           Delete {com}[count]{reset} characters before the cursor.
~           Switch case of the character under the cursor.
;           Repeat latest f, t, F or T {com}[count]{reset} times.
,           Repeat latest f, t, F or T in opposite direction \
{com}[count]{reset} in opposite times.
r{com}{{count}}{reset}    Replace {com}[count]{reset} characters with \
{com}{{count}}{reset} under and after the cursor.
R           Enter Replace mode. Counts are not supported.
dd          Delete line.
cc          Delete line and start insert.
yy          Yank line. Requires xsel.
I           Insert text before the first non-blank in the line.
p           Put the text from the clipboard after the cursor. Requires xsel.
{header2}Buffers:
j           Scroll buffer up. {note}
k           Scroll buffer down. {note}
^U          Scroll buffer page up. {note}
^D          Scroll buffer page down. {note}
gt          Go to the next buffer.
            (or K)
gT          Go to the previous buffer.
            (or J)
gg          Goto first line.
G           Goto line {com}[count]{reset}, default last line. {note}
/           Launch WeeChat search mode
^^          Jump to the last buffer.
{note} Counts may not work as intended, depending on the value of \
{bold}weechat.look.scroll_amount{reset} and \
{bold}weechat.look.scroll_page_percent{reset}.
{header2}Windows:
^Wh         Go to the window to the left.
^Wj         Go to the window below the current one.
^Wk         Go to the window above the current one.
^Wl         Go to the window to the right.
^W=         Balance windows' sizes.
^Wx         Swap window with the next one.
^Ws         Split current window in two.
^Wv         Split current window in two, but vertically.
^Wq         Quit current window.

{header}Current commands:
:h                  Help ({bold}/help{reset})
:q                  Closes current buffer ({bold}/close{reset})
:qall               Exits WeeChat ({bold}/exit{reset})
:w                  Saves settings ({bold}/save{reset})
:sp                 Split current window in two ({bold}/window splith{reset}).
:vsp                Split current window in two, but vertically \
({bold}/window splitv{reset}).
:!{com}{{cmd}}{reset}             Execute shell command ({bold}/exec -buffer \
shell{reset})
:s/pattern/repl
:s/pattern/repl/g   Search/Replace {note}
:command            All other commands will be passed to WeeChat \
(e.g. ':script …' is equivalent to '/script …').
{note} Supports regex (check docs for the Python re module for more \
information). '&' in the replacement is also substituted by the pattern. If \
the 'g' flag isn't present, only the first match will be substituted.

{header}History:
{header2}version 0.1:{reset}   initial release
{header2}version 0.2:{reset}   added esc to switch to normal mode, various \
key bindings and commands.
{header2}version 0.2.1:{reset} fixes/refactoring
{header2}version 0.3:{reset}   separate operators from motions and better \
handling. Added yank operator, I/p. Other fixes and improvements. The Escape \
key should work flawlessly on WeeChat ≥ 0.4.4.
{header2}version 0.4:{reset}   added: f, F, t, T, r, R, W, E, B, gt, gT, J, \
K, ge, gE, X, ~, ,, ;, ^^, ^Wh, ^Wj, ^Wk, ^Wl, ^W=, ^Wx, ^Ws, ^Wv, ^Wq, \
:!cmd, :sp, :vsp. \
Improved substitutions (:s/foo/bar). Rewrote key handling logic to take \
advantage of WeeChat API additions. Many fixes and improvements. \
WeeChat ≥ 1.0.0 required.
""".format(header=weechat.color("red"), header2=weechat.color("lightred"),
           header3=weechat.color("brown"), url=weechat.color("cyan"),
           note="%s*%s" % (weechat.color("red"), weechat.color("reset")),
           bold=weechat.color("bold"), reset=weechat.color("reset"),
           com=weechat.color("green"))


# Global variables.
# =================

# General.
# --------

# Holds the text of the command-line mode (currently only Ex commands ":").
cmd_text = ''
# Mode we're in. One of INSERT, NORMAL or REPLACE.
mode = "INSERT"
# Holds normal commands (e.g. 'dd').
vi_buffer = ''
# Buffer used to show help message (/vimode help).
help_buf = None
# See `cb_key_combo_default()`.
esc_pressed = 0
# See `cb_key_pressed()`.
last_signal_time = 0
# See `start_catching_keys()` for more info.
catching_keys_data = {'amount': 0}
# Used for ; and , to store the last f/F/t/T motion.
last_search_motion = {'motion': None, 'data': None}

# Script options.
vimode_settings = {'no_warn': ("off", "don't warn about problematic"
                               "keybindings and tmux/screen")}


# Regex patterns.
# ---------------

REGEX_MOTION_LOWERCASE_W = re.compile(r"\b\w|[^\w ]")
REGEX_MOTION_UPPERCASE_W = re.compile(r"(?<!\S)\b\w")
REGEX_MOTION_LOWERCASE_E = re.compile(r"\w\b|[^\w ]")
REGEX_MOTION_UPPERCASE_E = re.compile(r"\S(?!\S)")
REGEX_MOTION_LOWERCASE_B = re.compile(r"\w\b|[^\w ]")
REGEX_MOTION_UPPERCASE_B = re.compile(r"\w\b(?!\S)")
REGEX_MOTION_GE = re.compile(r"\b\w|[^\w ]")
REGEX_MOTION_CARRET = re.compile(r"\S")

# Regex used to detect problematic keybindings.
# For example: meta-wmeta-s is bound by default to ``/window swap``.
#    If the user pressed Esc-w, WeeChat will detect it as meta-w and will not
#    send any signal to `cb_key_combo_default()` just yet, since it's the
#    beginning of a known key combo.
#    Instead, `cb_key_combo_default()` will receive the Esc-ws signal, which
#    becomes "ws" after removing the Esc part, and won't know how to handle it.
REGEX_PROBLEMATIC_KEYBINDINGS = re.compile(r"meta-\w(meta|ctrl)")


# Vi commands.
# ------------

# See Also: `cb_exec_cmd()`.
VI_COMMANDS = {'h': "/help",
               'qall': "/exit",
               'q': "/close",
               'w': "/save",
               'set': "/set",
               'sp': "/window splith",
               'vsp': "/window splitv"}


# Vi operators.
# -------------

# Each operator must have a corresponding function, called "operator_X" where
# X is the operator. For example: `operator_c()`.
VI_OPERATORS = ['c', 'd', 'y']


# Vi motions.
# -----------

# Vi motions. Each motion must have a corresponding function, called
# "motion_X" where X is the motion (e.g. `motion_w()`).
# See Also: `SPECIAL_CHARS`.
VI_MOTIONS = ['w', 'e', 'b', '^', '$', 'h', 'l', 'W', 'E', 'B', 'f', 'F', 't',
              'T', 'ge', 'gE']

# Special characters for motions. The corresponding function's name is
# converted before calling. For example, '^' will call `motion_carret` instead
# of `motion_^` (which isn't allowed because of illegal characters).
SPECIAL_CHARS = {'^': "carret",
                 '$': "dollar"}


# Methods for vi operators, motions and key bindings.
# ===================================================

# Documented base examples:
# -------------------------

def operator_base(buf, input_line, pos1, pos2, overwrite):
    """Operator method example.

    Args:
        buf (str): pointer to the current WeeChat buffer.
        input_line (str): the content of the input line.
        pos1 (int): the starting position of the motion.
        pos2 (int): the ending position of the motion.
        overwrite (bool, optional): whether the character at the cursor's new
            position should be overwritten or not (for inclusive motions).
            Defaults to False.

    Notes:
        Should be called "operator_X", where X is the operator, and defined in
        `VI_OPERATORS`.
        Must perform actions (e.g. modifying the input line) on its own,
        using the WeeChat API.

    See Also:
        For additional examples, see `operator_d()` and
        `operator_y()`.
    """
    # Get start and end positions.
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    # Print the text the operator should go over.
    weechat.prnt('', "Selection: %s" % input_line[start:end])

def motion_base(input_line, cur, count):
    """Motion method example.

    Args:
        input_line (str): the content of the input line.
        cur (int): the position of the cursor.
        count (int): the amount of times to multiply or iterate the action.

    Returns:
        A tuple containing two values:
            int: the new position of the cursor.
            bool: True if the motion is inclusive, False otherwise.

    Notes:
        Should be called "motion_X", where X is the motion, and defined in
        `VI_MOTIONS`.
        Must not modify the input line directly.

    See Also:
        For additional examples, see `motion_w()` (normal motion) and
        `motion_f()` (catching motion).
    """
    # Find (relative to cur) position of next number.
    pos = get_pos(input_line, r"[0-9]", cur, True, count)
    # Return the new (absolute) cursor position.
    # This motion is exclusive, so overwrite is False.
    return cur + pos, False

def key_base(buf, input_line, cur, count):
    """Key method example.

    Args:
        buf (str): pointer to the current WeeChat buffer.
        input_line (str): the content of the input line.
        cur (int): the position of the cursor.
        count (int): the amount of times to multiply or iterate the action.

    Notes:
        Should be called `key_X`, where X represents the key(s), and defined
        in `VI_KEYS`.
        Must perform actions on its own (using the WeeChat API).

    See Also:
        For additional examples, see `key_a()` (normal key) and
        `key_r()` (catching key).
    """
    # Key was pressed. Go to Insert mode (similar to 'i').
    set_mode("INSERT")


# Operators:
# ----------

def operator_d(buf, input_line, pos1, pos2, overwrite=False):
    """Delete text from `pos1` to `pos2` from the input line.

    If `overwrite` is set to True, the character at the cursor's new position
    is removed as well (the motion is inclusive).

    See Also:
        `operator_base()`.
    """
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    if overwrite:
        end += 1
    input_line = list(input_line)
    del input_line[start:end]
    input_line = ''.join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    set_cur(buf, input_line, pos1)

def operator_c(buf, input_line, pos1, pos2, overwrite=False):
    """Delete text from `pos1` to `pos2` from the input and enter Insert mode.

    If `overwrite` is set to True, the character at the cursor's new position
    is removed as well (the motion is inclusive.)

    See Also:
        `operator_base()`.
    """
    operator_d(buf, input_line, pos1, pos2, overwrite)
    set_mode("INSERT")

def operator_y(buf, input_line, pos1, pos2, _):
    """Yank text from `pos1` to `pos2` from the input line.

    See Also:
        `operator_base()`.
    """
    start = min(pos1, pos2)
    end = max(pos1, pos2)
    proc = subprocess.Popen(['xsel', '-bi'], stdin=subprocess.PIPE)
    proc.communicate(input=input_line[start:end])


# Motions:
# --------

def motion_w(input_line, cur, count):
    """Go `count` words forward and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_LOWERCASE_W, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur + pos, False

def motion_W(input_line, cur, count):
    """Go `count` WORDS forward and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_UPPERCASE_W, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur + pos, False

def motion_e(input_line, cur, count):
    """Go to the end of `count` words and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_LOWERCASE_E, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur + pos, True

def motion_E(input_line, cur, count):
    """Go to the end of `count` WORDS and return cusor position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_UPPERCASE_E, cur, True, count)
    if not pos:
        return len(input_line), False
    return cur + pos, True

def motion_b(input_line, cur, count):
    """Go `count` words backwards and return position.

    See Also:
        `motion_base()`.
    """
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_LOWERCASE_B, new_cur,
                  count=count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_B(input_line, cur, count):
    """Go `count` WORDS backwards and return position.

    See Also:
        `motion_base()`.
    """
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_UPPERCASE_B, new_cur,
                  count=count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_ge(input_line, cur, count):
    """Go to end of `count` words backwards and return position.

    See Also:
        `motion_base()`.
    """
    new_cur = len(input_line) - cur - 1
    pos = get_pos(input_line[::-1], REGEX_MOTION_GE, new_cur,
                  count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_gE(input_line, cur, count):
    """Go to end of `count` WORDS backwards and return position.

    See Also:
        `motion_base()`.
    """
    new_cur = len(input_line) - cur
    pos = get_pos(input_line[::-1], REGEX_MOTION_GE, new_cur,
                  True, count)
    if not pos:
        return 0, False
    pos = len(input_line) - (pos + new_cur + 1)
    return pos, True

def motion_h(input_line, cur, count):
    """Go `count` characters to the left and return position.

    See Also:
        `motion_base()`.
    """
    return max(0, cur - count), False

def motion_l(input_line, cur, count):
    """Go `count` characters to the right and return position.

    See Also:
        `motion_base()`.
    """
    return cur + count, False

def motion_carret(input_line, cur, count):
    """Go to first non-blank character of line and return position.

    See Also:
        `motion_base()`.
    """
    pos = get_pos(input_line, REGEX_MOTION_CARRET, 0)
    return pos, False

def motion_dollar(input_line, cur, count):
    """Go to end of line and return position.

    See Also:
        `motion_base()`.
    """
    pos = len(input_line)
    return pos, False

def motion_f(input_line, cur, count):
    """Go to `count`'th occurence of character and return position.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_f", input_line, cur, count)

def cb_motion_f(update_last=True):
    """Callback for `motion_f()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'], re.escape(pattern),
                  catching_keys_data['cur'], True,
                  catching_keys_data['count'])
    catching_keys_data['new_cur'] = pos + catching_keys_data['cur']
    if update_last:
        last_search_motion = {'motion': 'f', 'data': pattern}
    cb_key_combo_default(None, None, '')

def motion_F(input_line, cur, count):
    """Go to `count`'th occurence of char to the right and return position.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_F", input_line, cur, count)

def cb_motion_F(update_last=True):
    """Callback for `motion_F()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    cur = len(catching_keys_data['input_line']) - catching_keys_data['cur'] + 1
    pos = get_pos(catching_keys_data['input_line'][::-1],
                  re.escape(pattern),
                  cur,
                  True,
                  catching_keys_data['count'])
    catching_keys_data['new_cur'] = catching_keys_data['cur'] - pos
    if update_last:
        last_search_motion = {'motion': 'F', 'data': pattern}
    cb_key_combo_default(None, None, '')

def motion_t(input_line, cur, count):
    """Go to `count`'th occurence of char and return position.

    The position returned is the position of the character to the left of char.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_t", input_line, cur, count)

def cb_motion_t(update_last=True):
    """Callback for `motion_t()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'], re.escape(pattern),
                  catching_keys_data['cur'] + 1,
                  True, catching_keys_data['count'])
    pos += 1
    if pos > 0:
        catching_keys_data['new_cur'] = pos + catching_keys_data['cur'] - 1
    else:
        catching_keys_data['new_cur'] = catching_keys_data['cur']
    if update_last:
        last_search_motion = {'motion': 't', 'data': pattern}
    cb_key_combo_default(None, None, '')

def motion_T(input_line, cur, count):
    """Go to `count`'th occurence of char to the left and return position.

    The position returned is the position of the character to the right of
    char.

    See Also:
        `motion_base()`.
    """
    return start_catching_keys(1, "cb_motion_T", input_line, cur, count)

def cb_motion_T(update_last=True):
    """Callback for `motion_T()`.

    Args:
        update_last (bool, optional): should `last_search_motion` be updated?
            Set to False when calling from `key_semicolon()` or `key_comma()`
            so that the last search motion isn't overwritten.
            Defaults to True.

    See Also:
        `start_catching_keys()`.
    """
    global last_search_motion
    pattern = catching_keys_data['keys']
    pos = get_pos(catching_keys_data['input_line'][::-1], re.escape(pattern),
                  (len(catching_keys_data['input_line']) -
                   (catching_keys_data['cur'] + 1)) + 1,
                  True, catching_keys_data['count'])
    pos += 1
    if pos > 0:
        catching_keys_data['new_cur'] = catching_keys_data['cur'] - pos + 1
    else:
        catching_keys_data['new_cur'] = catching_keys_data['cur']
    if update_last:
        last_search_motion = {'motion': 'T', 'data': pattern}
    cb_key_combo_default(None, None, '')


# Keys:
# -----

def key_cc(buf, input_line, cur, count):
    """Delete line and start Insert mode.

    See Also:
        `key_base()`.
    """
    weechat.command('', "/input delete_line")
    set_mode("INSERT")

def key_yy(buf, input_line, cur, count):
    """Yank line.

    See Also:
        `key_base()`.
    """
    proc = subprocess.Popen(['xsel', '-bi'], stdin=subprocess.PIPE)
    proc.communicate(input=input_line)

def key_i(buf, input_line, cur, count):
    """Start Insert mode.

    See Also:
        `key_base()`.
    """
    set_mode("INSERT")

def key_a(buf, input_line, cur, count):
    """Move cursor one character to the right and start Insert mode.

    See Also:
        `key_base()`.
    """
    set_cur(buf, input_line, cur + 1, False)
    set_mode("INSERT")

def key_A(buf, input_line, cur, count):
    """Move cursor to end of line and start Insert mode.

    See Also:
        `key_base()`.
    """
    set_cur(buf, input_line, len(input_line), False)
    set_mode("INSERT")

def key_I(buf, input_line, cur, count):
    """Move cursor to first non-blank character and start Insert mode.

    See Also:
        `key_base()`.
    """
    pos, _ = motion_carret(input_line, cur, 0)
    set_cur(buf, input_line, pos)
    set_mode("INSERT")

def key_G(buf, input_line, cur, count):
    """Scroll to specified line or bottom of buffer.

    See Also:
        `key_base()`.
    """
    if count > 0:
        # This is necessary to prevent weird scroll jumps.
        weechat.command('', "/window scroll_bottom")
        weechat.command('', "/window scroll %s" % count)
    else:
        weechat.command('', "/window scroll_bottom")

def key_r(buf, input_line, cur, count):
    """Replace `count` characters under the cursor.

    See Also:
        `key_base()`.
    """
    start_catching_keys(1, "cb_key_r", input_line, cur, count, buf)

def cb_key_r():
    """Callback for `key_r()`.

    See Also:
        `start_catching_keys()`.
    """
    global catching_keys_data
    input_line = list(catching_keys_data['input_line'])
    count = catching_keys_data['count']
    cur = catching_keys_data['cur']
    if cur + count <= len(input_line):
        for _ in range(count):
            input_line[cur] = catching_keys_data['keys']
            cur += 1
        input_line = ''.join(input_line)
        weechat.buffer_set(catching_keys_data['buf'], "input", input_line)
        set_cur(catching_keys_data['buf'], input_line, cur - 1)
    catching_keys_data = {'amount': 0}

def key_R(buf, input_line, cur, count):
    """Start Replace mode.

    See Also:
        `key_base()`.
    """
    set_mode("REPLACE")

def key_tilda(buf, input_line, cur, count):
    """Switch the case of `count` characters under the cursor.

    See Also:
        `key_base()`.
    """
    input_line = list(input_line)
    while count and cur < len(input_line):
        input_line[cur] = input_line[cur].swapcase()
        count -= 1
        cur += 1
    input_line = ''.join(input_line)
    weechat.buffer_set(buf, "input", input_line)
    set_cur(buf, input_line, cur)

def key_alt_j(buf, input_line, cur, count):
    """Go to WeeChat buffer.

    Called to preserve WeeChat's alt-j buffer switching.

    This is only called when alt-j<num> is pressed after pressing Esc, because
    \x01\x01j is received in key_combo_default which becomes \x01j after
    removing the detected Esc key.
    If Esc isn't the last pressed key, \x01j<num> is directly received in
    key_combo_default.
    """
    start_catching_keys(2, "cb_key_alt_j", input_line, cur, count)

def cb_key_alt_j():
    """Callback for `key_alt_j()`.

    See Also:
        `start_catching_keys()`.
    """
    global catching_keys_data
    weechat.command('', "/buffer " + catching_keys_data['keys'])
    catching_keys_data = {'amount': 0}

def key_semicolon(buf, input_line, cur, count, swap=False):
    """Repeat last f, t, F, T `count` times.

    Args:
        swap (bool, optional): if True, the last motion will be repeated in the
            opposite direction (e.g. 'f' instead of 'F'). Defaults to False.

    See Also:
        `key_base()`.
    """
    global catching_keys_data, vi_buffer
    catching_keys_data = ({'amount': 0,
                           'input_line': input_line,
                           'cur': cur,
                           'keys': last_search_motion['data'],
                           'count': count,
                           'new_cur': 0,
                           'buf': buf})
    # Swap the motion's case if called from key_comma.
    if swap:
        motion = last_search_motion['motion'].swapcase()
    else:
        motion = last_search_motion['motion']
    func = "cb_motion_%s" % motion
    vi_buffer = motion
    globals()[func](False)

def key_comma(buf, input_line, cur, count):
    """Repeat last f, t, F, T in opposite direction `count` times.

    See Also:
        `key_base()`.
    """
    key_semicolon(buf, input_line, cur, count, True)


# Vi key bindings.
# ================

# String values will be executed as normal WeeChat commands.
# For functions, see `key_base()` for reference.
VI_KEYS = {'j': "/window scroll_down",
           'k': "/window scroll_up",
           'G': key_G,
           'gg': "/window scroll_top",
           'x': "/input delete_next_char",
           'X': "/input delete_previous_char",
           'dd': "/input delete_line",
           'cc': key_cc,
           'i': key_i,
           'a': key_a,
           'A': key_A,
           'I': key_I,
           'yy': key_yy,
           'p': "/input clipboard_paste",
           '0': "/input move_beginning_of_line",
           '/': "/input search_text",
           'gt': "/buffer +1",
           'K': "/buffer +1",
           'gT': "/buffer -1",
           'J': "/buffer -1",
           'r': key_r,
           'R': key_R,
           '~': key_tilda,
           '\x01[[A': "/input history_previous",
           '\x01[[B': "/input history_next",
           '\x01[[C': "/input move_next_char",
           '\x01[[D': "/input move_previous_char",
           '\x01[[H': "/input move_beginning_of_line",
           '\x01[[F': "/input move_end_of_line",
           '\x01[[5~': "/window page_up",
           '\x01[[6~': "/window page_down",
           '\x01[[3~': "/input delete_next_char",
           '\x01[[2~': key_i,
           '\x01M': "/input return",
           '\x01?': "/input move_previous_char",
           ' ': "/input move_next_char",
           '\x01[j': key_alt_j,
           '\x01[1': "/buffer *1",
           '\x01[2': "/buffer *2",
           '\x01[3': "/buffer *3",
           '\x01[4': "/buffer *4",
           '\x01[5': "/buffer *5",
           '\x01[6': "/buffer *6",
           '\x01[7': "/buffer *7",
           '\x01[8': "/buffer *8",
           '\x01[9': "/buffer *9",
           '\x01[0': "/buffer *10",
           '\x01^': "/input jump_last_buffer",
           '\x01D': "/window page_down",
           '\x01U': "/window page_up",
           '\x01Wh': "/window left",
           '\x01Wj': "/window down",
           '\x01Wk': "/window up",
           '\x01Wl': "/window right",
           '\x01W=': "/window balance",
           '\x01Wx': "/window swap",
           '\x01Ws': "/window splith",
           '\x01Wv': "/window splitv",
           '\x01Wq': "/window merge",
           ';': key_semicolon,
           ',': key_comma}

# Add alt-j<number> bindings.
for i in range(10, 99):
    VI_KEYS['\x01[j%s' % i] = "/buffer %s" % i


# Key handling.
# =============

def cb_key_pressed(data, signal, signal_data):
    """Detect potential Esc presses.

    Alt and Esc are detected as the same key in most terminals. The difference
    is that Alt signal is sent just before the other pressed key's signal.
    We therefore use a timeout (50ms) to detect whether Alt or Esc was pressed.
    """
    global last_signal_time
    last_signal_time = time.time()
    if signal_data == "\x01[":
        # In 50ms, check if any other keys were pressed. If not, it's Esc!
        weechat.hook_timer(50, 0, 1, "cb_check_esc",
                           "{:f}".format(last_signal_time))
    return weechat.WEECHAT_RC_OK

def cb_check_esc(data, remaining_calls):
    """Check if the Esc key was pressed and change the mode accordingly."""
    global esc_pressed, vi_buffer, cmd_text, catching_keys_data
    if last_signal_time == float(data):
        esc_pressed += 1
        set_mode("NORMAL")
        # Cancel any current partial commands.
        vi_buffer = ''
        cmd_text = ''
        weechat.command('', "/bar hide vi_cmd")
        catching_keys_data = {'amount': 0}
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK

def cb_key_combo_default(data, signal, signal_data):
    """Eat and handle key events when in Normal mode, if needed.

    The key_combo_default signal is sent when a key combo is pressed. For
    example, alt-k will send the "\x01[k" signal.

    Esc is handled a bit differently to avoid delays, see `cb_key_pressed()`.
    """
    global esc_pressed, vi_buffer, cmd_text

    # If Esc was pressed, strip the Esc part from the pressed keys.
    # Example: user presses Esc followed by i. This is detected as "\x01[i",
    # but we only want to handle "i".
    keys = signal_data
    if esc_pressed and keys.startswith("\x01[" * esc_pressed):
        keys = keys[2 * esc_pressed:]
        # Multiples of 3 seem to "cancel" themselves,
        # e.g. Esc-Esc-Esc-Alt-j-11 is detected as "\x01[\x01[\x01" followed by
        # "\x01[j11" (two different signals).
        if signal_data == "\x01[" * 3:
            esc_pressed = -1  # Because cb_check_esc will increment it to 0.
        else:
            esc_pressed = 0
    # Ctrl-Space.
    elif keys == "\x01@":
        set_mode("NORMAL")
        return weechat.WEECHAT_RC_OK_EAT

    # Nothing to do here.
    if mode == "INSERT":
        return weechat.WEECHAT_RC_OK

    # We're in Replace mode — allow 'normal' key presses (e.g. 'a') and
    # overwrite the next character with them, but let the other key presses
    # pass normally (e.g. backspace, arrow keys, etc).
    if mode == "REPLACE":
        if len(keys) == 1:
            weechat.command('', "/input delete_next_char")
        elif keys == "\x01?":
            weechat.command('', "/input move_previous_char")
            return weechat.WEECHAT_RC_OK_EAT
        return weechat.WEECHAT_RC_OK

    # We're catching keys! Only 'normal' key presses interest us (e.g. 'a'),
    # not complex ones (e.g. backspace).
    if len(keys) == 1 and catching_keys_data['amount']:
        catching_keys_data['keys'] += keys
        catching_keys_data['amount'] -= 1
        # Done catching keys, execute the callback.
        if catching_keys_data['amount'] == 0:
            globals()[catching_keys_data['callback']]()
            vi_buffer = ''
            weechat.bar_item_update("vi_buffer")
        return weechat.WEECHAT_RC_OK_EAT

    # We're in command-line mode.
    if cmd_text:
        # Backspace key.
        if keys == "\x01?":
            # Remove the last character from our command line.
            cmd_text = list(cmd_text)
            del cmd_text[-1]
            cmd_text = ''.join(cmd_text)
        # Return key.
        elif keys == "\x01M":
            weechat.hook_timer(1, 0, 1, "cb_exec_cmd", cmd_text)
            cmd_text = ''
        # Input.
        elif len(keys) == 1:
            cmd_text += keys
        # Update (and maybe hide) the bar item.
        weechat.bar_item_update("cmd_text")
        if not cmd_text:
            weechat.command('', "/bar hide vi_cmd")
        return weechat.WEECHAT_RC_OK_EAT
    # Enter command mode.
    elif keys == ':':
        cmd_text += ':'
        weechat.command('', "/bar show vi_cmd")
        weechat.bar_item_update("cmd_text")
        return weechat.WEECHAT_RC_OK_EAT

    # Add key to the buffer.
    vi_buffer += keys
    weechat.bar_item_update("vi_buffer")
    if not vi_buffer:
        return weechat.WEECHAT_RC_OK

    # Keys without the count. These are the actual keys we should handle.
    # The count, if any, will be removed from vi_keys just below.
    # After that, vi_buffer is only used for display purposes — only vi_keys is
    # checked for all the handling.
    vi_keys = vi_buffer

    # Look for a potential match (e.g. 'd' might become 'dw' or 'dd' so we
    # accept it, but 'd9' is invalid).
    # If no matches are found, the keys buffer is cleared.
    match = False
    # Digits are allowed at the beginning (counts or '0').
    count = 1
    if vi_buffer.isdigit():
        match = True
    elif vi_buffer and vi_buffer[0].isdigit():
        count = ''
        for char in vi_buffer:
            if char.isdigit():
                count += char
            else:
                break
        vi_keys = vi_buffer.replace(count, '', 1)
        count = int(count)
    # Check against defined keys.
    if not match:
        for key in VI_KEYS:
            if key.startswith(vi_keys):
                match = True
                break
    # Check against defined motions.
    if not match:
        for motion in VI_MOTIONS:
            if motion.startswith(vi_keys):
                match = True
                break
    # Check against defined operators + motions.
    if not match:
        for operator in VI_OPERATORS:
            if vi_keys.startswith(operator):
                for motion in VI_MOTIONS:
                    if motion.startswith(vi_keys[1:]):
                        match = True
                        break
    # No match found — clear the keys buffer.
    if not match:
        vi_buffer = ''
        return weechat.WEECHAT_RC_OK_EAT

    buf = weechat.current_buffer()
    input_line = weechat.buffer_get_string(buf, 'input')
    cur = weechat.buffer_get_integer(buf, "input_pos")

    # It's a key. If the corresponding value is a string, we assume it's a
    # WeeChat command. Otherwise, it's a method we'll call.
    if vi_keys in VI_KEYS:
        if isinstance(VI_KEYS[vi_keys], str):
            for _ in range(count):
                # This is to avoid crashing WeeChat on script reloads/unloads,
                # because no hooks must still be running when a script is
                # reloaded or unloaded.
                if VI_KEYS[vi_keys] == "/input return":
                    return weechat.WEECHAT_RC_OK
                weechat.command('', VI_KEYS[vi_keys])
                current_cur = weechat.buffer_get_integer(buf, "input_pos")
                set_cur(buf, input_line, current_cur)
        else:
            VI_KEYS[vi_keys](buf, input_line, cur, count)
    # It's a motion (e.g. 'w') — call `motion_X()` where X is the motion, then
    # set the cursor's position to what that function returned.
    elif vi_keys in VI_MOTIONS:
        if vi_keys in SPECIAL_CHARS:
            func = "motion_%s" % SPECIAL_CHARS[vi_keys]
        else:
            func = "motion_%s" % vi_keys
        end, _ = globals()[func](input_line, cur, count)
        set_cur(buf, input_line, end)
    # It's an operator + motion (e.g. 'dw') — call `motion_X()` (where X is
    # the motion), then we call `operator_Y()` (where Y is the operator)
    # with the position `motion_X()` returned. `operator_Y()` should then
    # handle changing the input line.
    elif (len(vi_keys) > 1 and
          vi_keys[0] in VI_OPERATORS and
          vi_keys[1:] in VI_MOTIONS):
        if vi_keys[1:] in SPECIAL_CHARS:
            func = "motion_%s" % SPECIAL_CHARS[vi_keys[1:]]
        else:
            func = "motion_%s" % vi_keys[1:]
        pos, overwrite = globals()[func](input_line, cur, count)
        oper = "operator_%s" % vi_keys[0]
        globals()[oper](buf, input_line, cur, pos, overwrite)
    # The combo isn't completed yet (e.g. just 'd').
    else:
        return weechat.WEECHAT_RC_OK_EAT

    # We've already handled the key combo, so clear the keys buffer.
    if not catching_keys_data['amount']:
        vi_buffer = ''
        weechat.bar_item_update("vi_buffer")
    return weechat.WEECHAT_RC_OK_EAT


# Callbacks.
# ==========

# Bar items.
# ----------

def cb_vi_buffer(data, item, window):
    """Return the content of the vi buffer (pressed keys on hold)."""
    return vi_buffer

def cb_cmd_text(data, item, window):
    """Return the text of the command line."""
    return cmd_text

def cb_mode_indicator(data, item, window):
    """Return the current mode (INSERT/NORMAL/REPLACE)."""
    return mode


# Config.
# -------

def cb_config(data, option, value):
    """Script option changed, update our copy."""
    option_name = option.split('.')[-1]
    if option_name in vimode_settings:
        vimode_settings[option_name] = value
    return weechat.WEECHAT_RC_OK


# Command-line execution.
# -----------------------

def cb_exec_cmd(data, remaining_calls):
    """Translate and execute our custom commands to WeeChat command."""
    # Process the entered command.
    data = list(data)
    del data[0]
    data = ''.join(data)
    # s/foo/bar command.
    if data.startswith("s/"):
        cmd = data
        parsed_cmd = next(csv.reader(StringIO(cmd), delimiter='/',
                                     escapechar='\\'))
        pattern = re.escape(parsed_cmd[1])
        repl = parsed_cmd[2]
        repl = re.sub(r'([^\\])&', r'\1' + pattern, repl)
        flag = None
        if len(parsed_cmd) == 4:
            flag = parsed_cmd[3]
        count = 1
        if flag == 'g':
            count = 0
        buf = weechat.current_buffer()
        input_line = weechat.buffer_get_string(buf, 'input')
        input_line = re.sub(pattern, repl, input_line, count)
        weechat.buffer_set(buf, "input", input_line)
    # Shell command.
    elif data.startswith('!'):
        weechat.command('', "/exec -buffer shell %s" % data[1:])
    # Check againt defined commands.
    else:
        data = data.split(' ', 1)
        cmd = data[0]
        args = ''
        if len(data) == 2:
            args = data[1]
        if cmd in VI_COMMANDS:
            weechat.command('', "%s %s" % (VI_COMMANDS[cmd], args))
        # No vi commands defined, run the command as a WeeChat command.
        else:
            weechat.command('', "/{} {}".format(cmd, args))
    return weechat.WEECHAT_RC_OK

# Help buffer.
# ------------

def cb_help_closed(data, buf):
    """The help buffer has been closed."""
    global help_buf
    help_buf = None
    return weechat.WEECHAT_RC_OK

# Script commands.
# ----------------

def cb_vimode_cmd(data, buf, args):
    """Handle script commands (``/vimode <command>``)."""
    global help_buf
    # ``/vimode`` or ``/vimode help``
    if not args or args == "help":
        if help_buf is None:
            help_buf = weechat.buffer_new("vimode", '', '', "cb_help_closed",
                                          '')
            weechat.command(help_buf, "/buffer set time_for_each_line 0")
        buf_num = weechat.buffer_get_integer(help_buf, "number")
        weechat.command('', "/buffer %s" % buf_num)
        weechat.prnt(help_buf, HELP_TEXT)
        weechat.command(help_buf, "/window scroll_top")
    # ``/vimode bind_keys`` or ``/vimode bind_keys --list``
    elif args.startswith("bind_keys"):
        infolist = weechat.infolist_get("key", '', "default")
        weechat.infolist_reset_item_cursor(infolist)
        commands = ["/key unbind ctrl-W",
                    "/key bind ctrl-^ /input jump_last_buffer",
                    "/key bind ctrl-Wh /window left",
                    "/key bind ctrl-Wj /window down",
                    "/key bind ctrl-Wk /window up",
                    "/key bind ctrl-Wl /window right",
                    "/key bind ctrl-W= /window balance",
                    "/key bind ctrl-Wx /window swap",
                    "/key bind ctrl-Ws /window splith",
                    "/key bind ctrl-Wv /window splitv",
                    "/key bind ctrl-Wq /window merge"]
        while weechat.infolist_next(infolist):
            key = weechat.infolist_string(infolist, "key")
            if re.match(REGEX_PROBLEMATIC_KEYBINDINGS, key):
                commands.append("/key unbind %s" % key)
        if args == "bind_keys":
            weechat.prnt('', "Running commands:")
            for command in commands:
                weechat.command('', command)
            weechat.prnt('', "Done.")
        elif args == "bind_keys --list":
            weechat.prnt('', "Listing commands we'll run:")
            for command in commands:
                weechat.prnt('', "    %s" % command)
            weechat.prnt('', "Done.")
    return weechat.WEECHAT_RC_OK


# Helpers.
# ========

# Motions/keys helpers.
# ---------------------

def get_pos(data, regex, cur, ignore_cur=False, count=0):
    """Return the position of `regex` match in `data`, starting at `cur`.

    Args:
        data (str): the data to search in.
        regex (pattern): regex pattern to search for.
        cur (int): where to start the search.
        ignore_cur (bool, optional): should the first match be ignored if it's
            also the character at `cur`?
            Defaults to False.
        count (int, optional): the index of the match to return. Defaults to 0.

    Returns:
        int: position of the match. 0 if no matches are found.
    """
    # List of the *positions* of the found patterns.
    matches = [m.start() for m in re.finditer(regex, data[cur:])]
    pos = 0
    if count:
        if len(matches) > count - 1:
            if ignore_cur and matches[0] == 0:
                if len(matches) > count:
                    pos = matches[count]
            else:
                pos = matches[count - 1]
    elif matches:
        if ignore_cur and matches[0] == 0:
            if len(matches) > 1:
                pos = matches[1]
        else:
            pos = matches[0]
    return pos

def set_cur(buf, input_line, pos, cap=True):
    """Set the cursor's position.

    Args:
        buf (str): pointer to the current WeeChat buffer.
        input_line (str): the content of the input line.
        pos (int): the position to set the cursor to.
        cap (bool, optional): if True, the `pos` will shortened to the length
            of `input_line` if it's too long. Defaults to True.
    """
    if cap:
        pos = min(pos, len(input_line) - 1)
    weechat.buffer_set(buf, "input_pos", str(pos))

def start_catching_keys(amount, callback, input_line, cur, count, buf=None):
    """Start catching keys. Used for special commands (e.g. 'f', 'r').

    amount (int): amount of keys to catch.
    callback (str): name of method to call once all keys are caught.
    input_line (str): input line's content.
    cur (int): cursor's position.
    count (int): count, e.g. '2' for "2fs".
    buf (str, optional): pointer to the current WeeChat buffer.
        Defaults to None.

    `catching_keys_data` is a dict with the above arguments, as well as:
        keys (str): pressed keys will be added under this key.
        new_cur (int): the new cursor's position, set in the callback.

    When catching keys is active, normal pressed keys (e.g. 'a' but not arrows)
    will get added to `catching_keys_data` under the key 'keys', and will not
    be handled any further.
    Once all keys are caught, the method defined in the 'callback' key is
    called, and can use the data in `catching_keys_data` to perform its action.
    """
    global catching_keys_data
    if 'new_cur' in catching_keys_data:
        new_cur = catching_keys_data['new_cur']
        catching_keys_data = {'amount': 0}
        return new_cur, True
    catching_keys_data = ({'amount': amount,
                           'callback': callback,
                           'input_line': input_line,
                           'cur': cur,
                           'keys': '',
                           'count': count,
                           'new_cur': 0,
                           'buf': buf})
    return cur, False


# Other helpers.
# --------------

def set_mode(arg):
    """Set the current mode and update the bar mode indicator."""
    global mode
    mode = arg
    weechat.bar_item_update("mode_indicator")

def print_warning(text):
    """Print warning, in red, to the current buffer."""
    weechat.prnt('', ("%s[vimode.py] %s" % (weechat.color("red"), text)))

def check_warnings():
    """Warn the user about problematic key bindings and tmux/screen."""
    user_warned = False
    # Warn the user about problematic key bindings that may conflict with
    # vimode.
    # The solution is to remove these key bindings, but that's up to the user.
    infolist = weechat.infolist_get("key", '', "default")
    problematic_keybindings = []
    while weechat.infolist_next(infolist):
        key = weechat.infolist_string(infolist, "key")
        command = weechat.infolist_string(infolist, "command")
        if re.match(REGEX_PROBLEMATIC_KEYBINDINGS, key):
            problematic_keybindings.append("%s -> %s" % (key, command))
    if problematic_keybindings:
        user_warned = True
        print_warning("Problematic keybindings detected:")
        for keybinding in problematic_keybindings:
            print_warning("    %s" % keybinding)
        print_warning("These keybindings may conflict with vimode.")
        print_warning("You can remove problematic key bindings and add"
                      " recommended ones by using /vimode bind_keys, or only"
                      " list them with /vimode bind_keys --list")
        print_warning("For help, see: https://github.com/GermainZ/weechat"
                      "-vimode/blob/master/FAQ#problematic-key-bindings.md")
    del problematic_keybindings
    # Warn tmux/screen users about possible Esc detection delays.
    if "STY" in os.environ or "TMUX" in os.environ:
        if user_warned:
            weechat.prnt('', '')
        user_warned = True
        print_warning("tmux/screen users, see: https://github.com/GermainZ/"
                      "weechat-vimode/blob/master/FAQ.md#esc-key-not-being-"
                      "detected-instantly")
    if (user_warned and not
            weechat.config_string_to_boolean(vimode_settings['no_warn'])):
        if user_warned:
            weechat.prnt('', '')
        print_warning("To force disable warnings, you can set"
                      " plugins.var.python.vimode.no_warn to 'on'")


# Main script.
# ============

if __name__ == '__main__':
    weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION,
                     SCRIPT_LICENSE, SCRIPT_DESC, '', '')
    # Warn the user if he's using an unsupported WeeChat version.
    VERSION = weechat.info_get("version_number", '')
    if int(VERSION) < 0x01000000:
        print_warning("Please upgrade to WeeChat ≥ 1.0.0. Previous versions"
                      " are not supported.")
    # Set up script options.
    for option, value in vimode_settings.items():
        if weechat.config_is_set_plugin(option):
            vimode_settings[option] = weechat.config_get_plugin(option)
        else:
            weechat.config_set_plugin(option, value[0])
            vimode_settings[option] = value[0]
        weechat.config_set_desc_plugin(option,
                                       "%s (default: \"%s\")" % (value[1],
                                                                 value[0]))
    # Warn the user about possible problems if necessary.
    if not weechat.config_string_to_boolean(vimode_settings['no_warn']):
        check_warnings()
    # Create bar items and setup hooks.
    weechat.bar_item_new("mode_indicator", "cb_mode_indicator", '')
    weechat.bar_item_new("cmd_text", "cb_cmd_text", '')
    weechat.bar_item_new("vi_buffer", "cb_vi_buffer", '')
    vi_cmd = weechat.bar_new("vi_cmd", "off", "0", "root", '', "bottom",
                             "vertical", "vertical", "0", "0", "default",
                             "default", "default", "0", "cmd_text")
    weechat.hook_config('plugins.var.python.%s.*' % SCRIPT_NAME, 'cb_config',
                        '')
    weechat.hook_signal("key_pressed", "cb_key_pressed", '')
    weechat.hook_signal("key_combo_default", "cb_key_combo_default", '')
    weechat.hook_command("vimode", SCRIPT_DESC, "[help | bind_keys [--list]]",
                         "     help: show help\n"
                         "bind_keys: unbind problematic keys, and bind"
                         " recommended keys to use in WeeChat\n"
                         "          --list: only list changes",
                         "help || bind_keys |--list",
                         "cb_vimode_cmd", '')
