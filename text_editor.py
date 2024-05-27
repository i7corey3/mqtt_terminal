#!/usr/bin/env python
"""
A Dumb full-screen editor.

This example program makes use of many context manager methods:
:meth:`~.Terminal.hidden_cursor`, :meth:`~.Terminal.raw`,
:meth:`~.Terminal.location`, :meth:`~.Terminal.fullscreen`, and
:meth:`~.Terminal.keypad`.

Early curses work focused namely around writing screen editors, naturally
any serious editor would make liberal use of special modes.

``Ctrl - L``
  refresh

``Ctrl - C``
  quit

``Ctrl - S``
  save
"""
from __future__ import division, print_function

# std imports
import functools
import collections

# local
from blessed import Terminal

import sys

class TextEditor:
    def __init__(self):

        self.file_path = None
        self.Cursor = collections.namedtuple('Cursor', ('y', 'x', 'term'))

    def echo(self, text):
        """Display ``text`` and flush output."""
        sys.stdout.write(u'{}'.format(text))
        sys.stdout.flush()

        
    def input_filter(self, keystroke):
        """
        For given keystroke, return whether it should be allowed as input.

        This somewhat requires that the interface use special application keys to perform functions, as
        alphanumeric input intended for persisting could otherwise be interpreted as a command sequence.
        """
        if keystroke.is_sequence:
            # Namely, deny multi-byte sequences (such as '\x1b[A'),
            return False
        if ord(keystroke) < ord(u' '):
            # or control characters (such as ^L),
            return False
        return True


    def echo_yx(self, cursor, text):
        """Move to ``cursor`` and display ``text``."""
        self.echo(cursor.term.move_yx(cursor.y, cursor.x) + text)

    def readline(self, term, width=20):
        """A rudimentary readline implementation."""
        text = u''
        while True:
            inp = term.inkey()
            if inp.code == term.KEY_ENTER:
                break
            elif inp.code == term.KEY_ESCAPE or inp == chr(3):
                text = None
                break
            elif not inp.is_sequence and len(text) < width:
                text += inp
                self.echo(inp)
            elif inp.code in (term.KEY_BACKSPACE, term.KEY_DELETE):
                text = text[:-1]
                # https://utcc.utoronto.ca/~cks/space/blog/unix/HowUnixBackspaces
                #
                # "When you hit backspace, the kernel tty line discipline rubs out
                # your previous character by printing (in the simple case)
                # Ctrl-H, a space, and then another Ctrl-H."
                self.echo(u'\b \b')
        return text
    
    def open_file(self, file):
        self.screen = {}
        x = 0
        y = 0
        y_flip = False
        with open(file, 'r') as f:
            term = Terminal()
            csr = self.Cursor(0, 0, term)
            for lines in f.read():
                if y_flip:
                    x = 0
                    y += 1
                    y_flip = False
                if lines == '\n':
                    y_flip = True
                
                self.screen[(y, x)] = lines
                csr = self.Cursor(y,
                        x,
                        csr.term)
                self.echo_yx(csr, self.screen.get((csr.y, csr.x)))
                x += 1
                
        return self.screen

    def save(self, screen, fname):
        """Save screen contents to file."""
        if not fname:
            return
        with open(fname, 'w') as fout:
            cur_row = cur_col = 0
            for (row, col) in sorted(screen):
                char = screen[(row, col)]
                while row != cur_row:
                    cur_row += 1
                    cur_col = 0
                    fout.write(u'\n')
                while col > cur_col:
                    cur_col += 1
                    fout.write(u' ')
                fout.write(char)
                cur_col += 1
            fout.write(u'\n')


    def redraw(self, term, screen, start=None, end=None):
        """Redraw the screen."""
        if start is None and end is None:
            self.echo(term.clear)
            start, end = (self.Cursor(y=min(y for (y, x) in screen or [(0, 0)]),
                                x=min(x for (y, x) in screen or [(0, 0)]),
                                term=term),
                        self.Cursor(y=max(y for (y, x) in screen or [(0, 0)]),
                                x=max(x for (y, x) in screen or [(0, 0)]),
                                term=term))
        lastcol, lastrow = -1, -1
        for row, col in sorted(screen):
            if start.y <= row <= end.y and start.x <= col <= end.x:
                if col >= term.width or row >= term.height:
                    # out of bounds
                    continue
                if row != lastrow or col != lastcol + 1:
                    # use cursor movement
                    self.echo_yx(self.Cursor(row, col, term), screen[row, col])
                else:
                    # just write past last one
                    self.echo(screen[row, col])


    def main(self):
        """Program entry point."""
        def above(csr, offset):
            return self.Cursor(y=max(0, csr.y - offset),
                        x=csr.x,
                        term=csr.term)

        def below(csr, offset):
            return self.Cursor(y=min(csr.term.height - 1, csr.y + offset),
                        x=csr.x,
                        term=csr.term)

        def right_of(csr, offset):
            return self.Cursor(y=csr.y,
                        x=min(csr.term.width - 1, csr.x + offset),
                        term=csr.term)

        def left_of(csr, offset):
            return self.Cursor(y=csr.y,
                        x=max(0, csr.x - offset),
                        term=csr.term)

        def home(csr):
            return self.Cursor(y=csr.y,
                        x=0,
                        term=csr.term)

        def end(csr):
            return self.Cursor(y=csr.y,
                        x=csr.term.width - 1,
                        term=csr.term)

        def bottom(csr):
            return self.Cursor(y=csr.term.height - 1,
                        x=csr.x,
                        term=csr.term)

        def center(csr):
            return self.Cursor(csr.term.height // 2,
                        csr.term.width // 2,
                        csr.term)
        
        def backspace(csr): 
            
            return left_of(csr, 1)
        
        def delete(csr):

            return right_of(csr, 1)
        
        def deleteHome(csr):
            
            l = list(col for col in self.screen.keys() if col[0] == csr.y-1)
            return min(i for i in l if self.screen[i] != ' ')[1]-1
           
        
        def backspaceHome(csr):

            l = list(col for col in self.screen.keys() if col[0] == csr.y-1)
            return max(i for i in l if self.screen[i] != ' ')[1]+1

        def enterKeyPressed(csr):
            # self.echo(term.clear)
            s = {}
            for row, col in sorted(self.screen):
             
                if csr.y <= row:
                    s[(row+1, col)] = self.screen[row, col]
                    self.echo_yx(csr, s[(row+1, col)])
                else:
                    s[(row, col)] = self.screen[(row, col)]
            self.screen = s
            self.redraw(term=term, screen=self.screen)
           

        def lookup_move(inp_code, csr):
            return {
                # arrows, including angled directionals
                csr.term.KEY_END: below(left_of(csr, 1), 1),
                csr.term.KEY_KP_1: below(left_of(csr, 1), 1),

                csr.term.KEY_DOWN: below(csr, 1),
                csr.term.KEY_KP_2: below(csr, 1),

                csr.term.KEY_PGDOWN: below(right_of(csr, 1), 1),
                csr.term.KEY_LR: below(right_of(csr, 1), 1),
                csr.term.KEY_KP_3: below(right_of(csr, 1), 1),

                csr.term.KEY_LEFT: left_of(csr, 1),
                csr.term.KEY_KP_4: left_of(csr, 1),

                csr.term.KEY_CENTER: center(csr),
                csr.term.KEY_KP_5: center(csr),

                csr.term.KEY_RIGHT: right_of(csr, 1),
                csr.term.KEY_KP_6: right_of(csr, 1),

                csr.term.KEY_HOME: above(left_of(csr, 1), 1),
                csr.term.KEY_KP_7: above(left_of(csr, 1), 1),

                csr.term.KEY_UP: above(csr, 1),
                csr.term.KEY_KP_8: above(csr, 1),

                csr.term.KEY_PGUP: above(right_of(csr, 1), 1),
                csr.term.KEY_KP_9: above(right_of(csr, 1), 1),

                csr.term.KEY_BACKSPACE: backspace(csr),
                csr.term.KEY_DELETE: delete(csr),

                # shift + arrows
                csr.term.KEY_SLEFT: left_of(csr, 10),
                csr.term.KEY_SRIGHT: right_of(csr, 10),
                csr.term.KEY_SDOWN: below(csr, 10),
                csr.term.KEY_SUP: above(csr, 10),

                # carriage return
                csr.term.KEY_ENTER: home(below(csr, 1)),
            }.get(inp_code, csr)

        term = Terminal()
        
        
        with term.hidden_cursor(), \
                term.raw(), \
                term.location(), \
                term.fullscreen(), \
                term.keypad():
            inp = None
            self.screen = self.open_file("text.txt")
            csr = self.Cursor(0, 0, term)
            while True:
                self.echo_yx(csr, term.reverse(self.screen.get((csr.y, csr.x), u' ')))
                inp = term.inkey()

                if inp == chr(3):
                    # ^c exits
                    break

                elif inp == chr(19):
                    # ^s saves
                    self.echo_yx(home(bottom(csr)),
                            term.ljust(term.bold_white(u'Filename: ')))
                    self.echo_yx(right_of(home(bottom(csr)), len(u'Filename: ')), u'')
                    self.save(self.screen, self.readline(term))
                    self.echo_yx(home(bottom(csr)), term.clear_eol)
                    self.redraw(term=term, screen=self.screen,
                        start=home(bottom(csr)),
                        end=end(bottom(csr)))
                    continue

                elif inp == chr(12):
                    # ^l refreshes
                    self.redraw(term=term, screen=self.screen)
                   
                else:
                    n_csr = lookup_move(inp.code, csr)

                if n_csr != csr:
                    if inp.code == term.KEY_BACKSPACE:
                        
                        n_csr = left_of(csr, 1)
                        self.screen[(csr.y, csr.x)] = u' '
                        self.screen[(n_csr.y, n_csr.x)] = u' '
                        self.echo_yx(csr, self.screen.get((csr.y, csr.x), u'\b \b'))
                        self.redraw(term=term, screen=self.screen)
                        
                        csr = n_csr
                    elif inp.code == term.KEY_DELETE:
                        n_csr = right_of(csr, 1)
                        self.screen[(csr.y, csr.x)] = u' '
                        self.echo_yx(csr, self.screen.get((csr.y, csr.x), u'\b \b'))
                        self.redraw(term=term, screen=self.screen)
                        csr = n_csr
                    elif inp.code == term.KEY_ENTER:
                        n_csr = home(below(csr, 1))
                        enterKeyPressed(csr)
                        csr = n_csr
                        
                    else:
                        # erase old cursor,
                        self.echo_yx(csr, self.screen.get((csr.y, csr.x), u' '))
                        csr = n_csr

                elif self.input_filter(inp):
                    self.echo_yx(csr, inp)
                    self.screen[(csr.y, csr.x)] = inp.__str__()
                    n_csr = right_of(csr, 1)
                    self.redraw(term=term, screen=self.screen)
                    if n_csr == csr:
                        # wrap around margin
                        n_csr = home(below(csr, 1))
                    csr = n_csr
                
                else:
                    if inp.code == term.KEY_BACKSPACE:
                        if csr.x == 0 and csr.y > 0:
                            try:
                                n_csr = above(right_of(csr, backspaceHome(csr)), 1)
                                
                                self.screen[(n_csr.y, n_csr.x)] = u' '
                                self.echo_yx(csr, self.screen.get((csr.y, csr.x), u'\b \b'))
                                self.redraw(term=term, screen=self.screen)
                                
                                csr = n_csr
                            except:
                                n_csr = above(csr, 1)
                                self.echo_yx(csr, self.screen.get((n_csr.y-1, n_csr.x), u'\b \b'))
                                self.redraw(term=term, screen=self.screen)
                                csr = n_csr
                            
                    elif inp.code == term.KEY_DELETE:
                        if csr.x == 0 and csr.y > 0:

                            n_csr = below(right_of(csr, deleteHome(csr)), 1)
                            
                            self.screen[(n_csr.y, n_csr.x)] = u' '
                            self.echo_yx(csr, self.screen.get((csr.y, csr.x), u'\b \b'))
                            self.redraw(term=term, screen=self.screen)
                            
                            csr = n_csr
                            
                
                
                

if __name__ == '__main__':
    t = TextEditor()
    t.main()