import atexit
import math
import random
import sys
import termios
import tty
from datetime import datetime

COLOR_RED = 1
COLOR_GREEN = 2
COLOR_YELLOW = 3


class Context(object):
    def __init__(self, phrase):
        self.phrase = phrase
        self.state = None
        self.set_state(FastMode())

    def on_input(self, char):
        self.state.on_input(self, char)

    def set_state(self, new_state):
        new_state.on_enter(self, self.state)
        self.state = new_state


class Mode(object):
    label = None
    color = None
    next_mode = None

    def __init__(self):
        self.offset = 0
        self.errors = 0
        sys.stdout.write('\x1b[3{}m{:>6}: '.format(self.color, self.label))

    def on_enter(self, context, prev_mode):
        pass

    def on_input(self, context, char):
        if not self.offset:
            self.start = datetime.now()

        if char == context.phrase[self.offset]:
            if char != '\r':
                sys.stdout.write(char)
            self.offset += 1
        else:
            self.errors += 1
            self._on_error(context)

        if self.offset == len(context.phrase):
            self.time = (datetime.now() - self.start).total_seconds()
            if self._get_stats():
                sys.stdout.write('  ')
                sys.stdout.write(self._get_stats())
            sys.stdout.write('\r\n')

            context.set_state(self.next_mode())

    def _on_error(self, context):
        pass

    def _get_stats(self):
        return '{:.2f}s'.format(self.time)


class FastMode(Mode):
    label = 'fast'
    color = COLOR_GREEN


class SlowMode(Mode):
    label = 'slow'
    color = COLOR_RED

    def on_enter(self, context, prev_mode):
        if isinstance(prev_mode, SlowMode):
            # keep the error count from previous attempt
            self.errors = prev_mode.errors

    def _on_error(self, context):
        sys.stdout.write('\r\n')
        sys.stdout.write('FAIL!\r\n')
        context.set_state(SlowMode())

    def _get_stats(self):
        return None


class MediumMode(Mode):
    label = 'medium'
    color = COLOR_YELLOW

    def _get_stats(self):
        return '{}, {} errors'.format(
            super(MediumMode, self)._get_stats(), self.errors)


FastMode.next_mode = SlowMode
SlowMode.next_mode = MediumMode
MediumMode.next_mode = FastMode


def at_exit(settings):
    sys.stdout.write('\r\n')
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
    sys.stdout.write('\x1b[0m')


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


def char_range(from_char, to_char):
    return [chr(c) for c in range(ord(from_char), ord(to_char) + 1)]


def gen_phrase(alphabet, min_len):
    words = []
    while sum(map(len, words)) < min_len:
        l = 1 + poisson(4)
        words.append(''.join((random.choice(alphabet) for j in xrange(l))))

    return ' '.join(words)


def run():
    if len(sys.argv) > 1:
        phrase = ' '.join(sys.argv[1:]) + '\r'
    else:
        phrase = gen_phrase(char_range('a', 'z'), 30)

    print('type this phrase: {}'.format(phrase))

    settings = termios.tcgetattr(sys.stdin.fileno())
    tty.setraw(sys.stdin.fileno())
    atexit.register(at_exit, settings)

    context = Context(phrase)

    while True:
        char = sys.stdin.read(1)
        if ord(char) == 3:
            sys.exit(0)
        else:
            context.on_input(char)


if __name__ == '__main__':
    run()
