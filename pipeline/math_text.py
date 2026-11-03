"""Normalize JSON-escaped math delimiters and common author macro aliases."""
import re

ALIASES = {'bm': 'boldsymbol', 'mathds': 'mathbb', 'mathbbm': 'mathbb', 'mbox': 'text', 'dddot': 'overset{\\cdots}', 'cm': 'mathrm{cm}', 'Bar': 'overline'}

def normalize_math(text):
    slash = chr(92)
    # Some structured model responses escape both JSON and TeX twice. Decode
    # only expressions whose delimiters are doubled, never ordinary prose.
    for left, right in [('(', ')'), ('[', ']')]:
        pattern = re.escape(slash * 2 + left) + '(.*?)' + re.escape(slash * 2 + right)
        text = re.sub(pattern, lambda m: slash + left + m[1].replace(slash * 2, slash)
                      + slash + right, text, flags=re.S)
    def aliases(match):
        value = match[0]
        for original, standard in ALIASES.items():
            value = re.sub(re.escape(slash + original) + r'(?![A-Za-z])',
                           lambda _: slash + standard, value)
        value = re.sub(r'\\(big(?:g)?[lr]?|Big(?:g)?[lr]?|left|right)\{(\\[{}]|[()[\]|.])\}',
                       lambda m: slash + m[1] + m[2], value)
        value = convert_units(value)
        return value
    return re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]', aliases, text, flags=re.S)


UNITS = {
    'cm': r'\mathrm{cm}', 'kilogram': r'\mathrm{kg}', 'gram': r'\mathrm{g}',
    'metre': r'\mathrm{m}', 'meter': r'\mathrm{m}',
    'second': r'\mathrm{s}', 'ms': r'\mathrm{ms}', 's': r'\mathrm{s}',
    'hertz': r'\mathrm{Hz}', 'radian': r'\mathrm{rad}',
    'degree': r'{}^\circ', 'percent': r'\%', 'watt': r'\mathrm{W}',
    'hour': r'\mathrm{h}', 'minute': r'\mathrm{min}', 'joule': r'\mathrm{J}',
    'decibel': r'\mathrm{dB}', 'newton': r'\mathrm{N}', 'volt': r'\mathrm{V}', 'ampere': r'\mathrm{A}',
    'kilo': r'\mathrm{k}', 'milli': r'\mathrm{m}', 'micro': r'\mu',
    'centi': r'\mathrm{c}', 'nano': r'\mathrm{n}',
    'squared': '^{2}', 'cubed': '^{3}', 'per': '/',
}

def braced_argument(text, start):
    while start < len(text) and text[start].isspace():
        start += 1
    if start == len(text) or text[start] != '{':
        return None
    level = 1
    for end in range(start + 1, len(text)):
        if text[end] == '{':
            level += 1
        elif text[end] == '}':
            level -= 1
            if not level:
                return text[start + 1:end], end + 1
    return None

def scientific_number(number):
    match = re.fullmatch(r'([+-]?[\d.]+)[eE]([+-]?\d+)', number.strip())
    if not match:
        return number
    return match[1] + r'\times10^{' + str(int(match[2])) + '}'

def unit_expression(unit):
    return re.sub(r'\\([A-Za-z]+)', lambda m: UNITS.get(m[1], m[0]), unit)

def convert_units(text):
    """Expand siunitx quantities without executing any author TeX macros."""
    pattern = re.compile(r'\\(qtyrange|SIrange|numrange|qty|SI|num|unit|si)(?![A-Za-z])')
    output = []
    offset = 0
    for match in pattern.finditer(text):
        if match.start() < offset:
            continue
        command = match[1]
        count = 3 if command in ('qtyrange', 'SIrange') else 2 if command in ('qty', 'SI', 'numrange') else 1
        arguments = []
        end = match.end()
        if end < len(text) and text[end] == '[':
            options_end = text.find(']', end + 1)
            if options_end == -1:
                continue
            end = options_end + 1
        for _ in range(count):
            argument = braced_argument(text, end)
            if argument is None:
                break
            value, end = argument
            arguments.append(value)
        if len(arguments) != count:
            continue
        if command in ('unit', 'si'):
            replacement = unit_expression(arguments[0])
        else:
            replacement = scientific_number(arguments[0])
            if 'range' in command:
                replacement += r'\text{–}' + scientific_number(arguments[1])
            if command not in ('num', 'numrange'):
                replacement += r'\,' + unit_expression(arguments[-1])
        output.extend((text[offset:match.start()], replacement))
        offset = end
    return ''.join(output) + text[offset:]
