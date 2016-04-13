import tty
import sys
import termios
import atexit
from datetime import datetime
import random
import math

MODE_FAST = 0
MODE_SLOW = 1
MODE_MEDIUM = 2
MODES = (MODE_FAST, MODE_SLOW, MODE_MEDIUM)
MODE_STR = ('fast', 'slow', 'medium')
MODE_COL = (2, 1, 3)

mode = MODE_FAST


def at_exit():
    sys.stdout.write('\r\n')
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
    sys.stdout.write('\x1b[0m')


def log_event(s):
    with file('stats', 'a') as f:
        f.write(s)
        f.write('\n')


def poisson(l):
    L = math.exp(-l)
    k = 0
    p = 1
    while True:
        k += 1
        p *= random.uniform(0, 1)
        if p <= L:
            break

    return k - 1


def gen_phrase(alphabet, min_len):
    words = []
    while sum(map(len, words)) < min_len:
        l = 1 + poisson(4)
        words.append(''.join((random.choice(alphabet) for j in xrange(l))))

    return ' '.join(words)


settings = termios.tcgetattr(sys.stdin.fileno())
tty.setraw(sys.stdin.fileno())
atexit.register(at_exit)
reference = ' '.join(sys.argv[1:]) + '\r'
errors = 0

while True:
    sys.stdout.write('\x1b[3{}m{:>6}: '.format(
        MODE_COL[mode], MODE_STR[mode]))
    offset = 0

    while True:
        ch = sys.stdin.read(1)
        if offset == 0:
            start = datetime.now()
        if ord(ch) == 3:
            sys.exit(-1)
        else:
            if ch == reference[offset]:
                if ch != '\r':
                    sys.stdout.write(ch)
                offset += 1
            else:
                errors += 1
                if mode == MODE_SLOW:
                    sys.stdout.write('\r\n')
                    sys.stdout.write('FAIL!\r\n')
                    break

        if offset == len(reference):
            time = (datetime.now() - start).total_seconds()
            if mode == MODE_FAST or mode == MODE_MEDIUM:
                sys.stdout.write('  {:.2f}s'.format(time))
                if mode == MODE_MEDIUM:
                    sys.stdout.write(', {} errors'.format(errors))
            sys.stdout.write('\r\n')
            log_event('{} {} {} {} {}'.format(
                datetime.now().isoformat(),
                MODE_STR[mode][0].upper(),
                time,
                errors,
                reference.strip()
            ))
            mode = (mode + 1) % len(MODES)
            errors = 0
            break
