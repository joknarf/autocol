#!/usr/bin/env python
import os
import sys
import re
import shlex
from subprocess import run, Popen, PIPE, DEVNULL
from textwrap import indent
#from tabula import tabulatecol #WARN print ends with RESET COLORS
#from colorama import Back#, Fore

TITLE_SYMS = os.environ.get("autocol_syms") or "" #" " "   " "⎹" ⎥ ⎹   
TITLE_SYMS = os.environ.get("autocol_syms") or "⎹"
CSI = "\033["
COLORS = ('BLACK', 'RED', 'GREEN', 'YELLOW', 'BLUE', 'MAGENTA', 'CYAN', 'WHITE')

class Style:
    wrapoff = CSI + "?7l"
    wrapon = CSI + "?7h"

class ForeG:
    RESET = CSI + '39' + 'm'
    NONE = ''
    def __init__(self):
        for i,col in enumerate(COLORS):
            setattr(self, col, CSI + str(i+30) +'m')
            setattr(self, 'LIGHT' + col, CSI + str(i+90) +'m')

    def toback(self, color):
        col = int(color.split("[")[1][:-1])
        return CSI + str(col + 10) + "m"


class BackG:
    RESET = CSI + '49' + 'm'
    NONE = ''
    def __init__(self):
        for i,col in enumerate(COLORS):
            setattr(self, col, CSI + str(i+40) +'m')
            setattr(self, 'LIGHT' + col, CSI + str(i+100) +'m')
    
    def tofore(self, color):
        col = int(color.split("[")[1][:-1])
        return CSI + str(col - 10) + "m"


Fore = ForeG()
Back = BackG()

print(Style.wrapoff, end='')

class Autocol:
    """
    textcolors = {"text":"colors", "text":"colors}
    textccolors = {"colname": {text:colors, {text:colors} }
    """
    def __del__(self):
        global colors
        print(Style.wrapon, end='')

    def parsecmd(self, cmd, **kwargs):
        try:
            with Popen(cmd, stdout=PIPE, stdin=DEVNULL, encoding='utf-8', bufsize=0) as proc:
                kwargs['input'] = proc.stdout
                self.parse(**kwargs)
            return self
        except:
            #self.out.close()
            print("Error: ", cmd, file=sys.stderr)
            sys.exit(1)
            return self
    
    def parse(self,
              input=sys.stdin,
              cmd=None,
              out=sys.stdout, 
              separator=None,
              headers=None,
              live=False, 
              less=False, 
              parser=None, 
              python='',  
              titlecolors=(Fore.LIGHTWHITE, Back.LIGHTBLACK),
              align=None,
              textcolors=None,
              patterncolors=None,
              skipcolumns=None,
              padding=' ',
              fixcolumns=1,
    ):
        self.out = out
        self.titlecolors = titlecolors
        self.skipcolumns = skipcolumns or []
        self.textcolors = textcolors or {}
        self.patterncolors = patterncolors or {}
        if not separator:
            separator = r"[ \t]+"
        if headers:
            self.headers = headers
        else:
            self.headers = re.split(separator, input.readline().strip())
        self.hn = {h.strip():i for i,h in enumerate(self.headers)}
        self.cust_align = align or []
        self.align = [align[i] if len(self.cust_align)>i else '-' for i,h in enumerate(self.headers)]
        self.maxwidth = [len(c) for c in self.headers]
        self.linenum = 0
        self.linecolors = ["\033[48;5;234m", Back.BLACK]
        self.columncolors = ["\033[48;5;235m"]
        for i in range(len(self.columncolors), len(self.headers)):
            self.columncolors.append('')
        self.padding = padding
        self.live = live
        self.less = less
        self.fixcolumns = fixcolumns
        if isinstance(input, list):
            self.data = input
            for cells in self.data:
                self.setmaxwidth(cells)
            return self
        self.data = []
        py_code = f"""
for line in iter(input.readline, ''):
    line = line.strip()
    oline = line
    cells = re.split(separator, line, len(self.headers)-1)
{indent(python,"    ")}
    if line != oline:
        cells = re.split(separator, line, len(self.headers)-1)
    if parser:
        cells = parser(line, cells, self.headers, self.hn, live)
    if cells is None:
        continue
    self.setmaxwidth(cells)
    self.data.append(cells)
    if live:
        if self.linenum == 0:
            self.printline(self.headers, out)
            #if less: # bug less +F
            #    print('\\n' * os.get_terminal_size(sys.__stdout__.fileno()).lines, file=out)
        self.printline(cells, out)
"""
        if live and less:
            os.environ["LESS"] = ""
            os.environ["LESSCHARSET"] = "utf-8"
            cmd = './less -RSX +F --shift=10 -~ -j 2 --no-search-headers --header 1,'+str(sum(self.maxwidth[:fixcolumns])+(1+len(self.padding))*(fixcolumns))
            try:
                with Popen(shlex.split(cmd), encoding='utf-8', stdin=PIPE, bufsize=0, close_fds=True) as proc:
                    out = proc.stdin
                    exec(py_code)
            except KeyboardInterrupt:
                os.system("stty echo")
                return self
        else:
            exec(py_code)
        return self
            
    def setmaxwidth(self, cells):
        for i,c in enumerate(cells):
            self.maxwidth[i] = max(self.maxwidth[i], len(c))
            try:
                self.align = self.cust_align[i]
            except:
                if re.match('^[0-9]+([.][0-9]+)*%*$', c):
                    self.align[i] = "+"
                else:
                    self.align[i] = "-"
            
    def colorize(self, cell, linecolor, column):
        c = cell.strip()
        if self.headers[column] in self.textcolors and c in self.textcolors[self.headers[column]]:
            return self.textcolors[self.headers[column]][c] + cell + Fore.RESET + linecolor
        if c in self.textcolors:
            return self.textcolors[c] + cell + Fore.RESET + linecolor
        if self.headers[column] in self.patterncolors:
            patterncolors = self.patterncolors[self.headers[column]]
        else:
            patterncolors = self.patterncolors
        for p,pc in patterncolors.items():
            if isinstance(pc, str):
                cell = re.sub(f'({p})', pc + r'\1' + Fore.RESET + linecolor, cell)
        return cell
    
    def printline(self, cells, out=sys.stdout):
        print(self.linecolors[self.linenum%2], file=out, flush=True, end="")
        tcolors = "".join(self.titlecolors)
        symcolor = Back.tofore(self.titlecolors[1])
        syms = TITLE_SYMS
        symcol0 = tcolors if syms[0] == " " else symcolor
        symcol2 = tcolors if syms[2] == " " else symcolor + Back.RESET
        for i,cell in enumerate(cells):
            if i in self.skipcolumns:
                continue
            if self.linenum == 0:
                if i == 0:
                    cell = symcol0 + syms[0] + tcolors + self.padding[1:] + f"%{self.align[i]}{self.maxwidth[i]}s" % cell + Fore.BLACK + syms[1] # 
                elif i == len(self.headers)-1:
                    cell = tcolors + self.padding + f"%{self.align[i]}{self.maxwidth[i]}s" % cell + symcol2 + syms[2] #"" 
                else:    
                    cell = tcolors + self.padding + f"%{self.align[i]}{self.maxwidth[i]}s" % cell + Fore.BLACK + syms[1]
            else:
                cell = self.colorize(self.padding + f"%{self.align[i]}{self.maxwidth[i]}s " % cell, self.linecolors[self.linenum%2], i)
                if self.columncolors[i]:
                    cell = self.columncolors[i] + cell + self.linecolors[self.linenum%2]
            print(cell, end="", file=out, flush=True)
        print(Fore.RESET + Back.RESET, file=out, flush=True)
        self.linenum = self.linenum + 1

    def print(self, out=None):
        if self.live:
            return self.maxwidth
        out = out or self.out
        if self.less:
            return self.printless()
        return self.printout(out)

    def printout(self, out=None):
        self.printline(self.headers, out)
        for line in self.data:
            self.printline(line, out)
        return self.maxwidth
        #return tabulatecol(self.data, headers=self.headers)

    def printless(self):
        os.environ['LESS'] = ''
        os.environ['LESSCHARSET'] = "utf-8"
        cmd = './less -RSXKF --shift=10 -~ -j 2 --no-search-headers --header 1,'+str(sum(self.maxwidth[:self.fixcolumns])+(1+len(self.padding))*(self.fixcolumns))
        try:
            with Popen(shlex.split(cmd), encoding='utf-8', stdin=PIPE, close_fds=False) as proc:
                self.printout(out=proc.stdin)
        except KeyboardInterrupt:
            return
        

def initcolors(colors=None):
    if not colors:
        return {}
    tcolors = {}
    for tc in colors:
        tc = tc.encode('unicode_escape').decode()
        tcol = tc.split(':')
        if len(tcol)==4:
            item = tcol.pop(0)
            if not item in tcolors:
                tcolors[item] = {}
            col = eval("Back." + (tcol[1].upper() or 'NONE')) + eval("Fore."+ (tcol[2].upper() or 'NONE'))
            tcolors[item][tcol[0]] = col
        else:
            tcolors[tcol[0]] = eval("Back." + (tcol[1].upper() or 'NONE')) + eval("Fore."+ (tcol[2].upper() or 'NONE'))
    return tcolors

def autocol(args, out=sys.stdout, input=sys.stdin, parser=None):
    args.skipcolumns = [int(c) for c in args.skipcolumns]
    tcol = initcolors(args.textcolors)
    pcol = initcolors(args.patterncolors)
    auto = Autocol()
    if args.cmd:
        parse = auto.parsecmd
    else:
        parse = auto.parse
    try:
        parse(
            cmd=args.cmd,
            input=input,
            out=out,
            separator=args.separator,
            headers=args.headers,
            live=args.live,
            less=args.less,
            parser=parser,
            python=args.python,
            textcolors=tcol,
            patterncolors=pcol,
            align=args.align,
            skipcolumns=args.skipcolumns,
        ).print()
        #out.close()
    except (BrokenPipeError, KeyboardInterrupt):
        return

def main(args):
    parser = argparse.ArgumentParser(args)
    parser.add_argument('-F', '--separator')
    parser.add_argument('-L', '--less', action='store_true')
    parser.add_argument('-t', '--textcolors', nargs='*')
    parser.add_argument('-p', '--patterncolors', nargs='*')
    parser.add_argument('-P', '--python', default='')
    parser.add_argument('-s', '--skipcolumns', nargs='*', default=[])
    parser.add_argument('-a', '--align', nargs='*')
    parser.add_argument('-l', '--live', action='store_true')
    parser.add_argument('-H', '--headers', nargs='*')
    parser.add_argument('cmd', nargs="*")
    args = parser.parse_args()
    autocol(args, sys.stdout)
    sys.exit()

if __name__ == '__main__':
    import argparse
    main(sys.argv)
