from lograder import Grader
from lograder.io.tests import CxxExecutableConfig
import os
import random

ORDERS_OF_MAGNITUDE = [
    '',
    'thousand',
    'million',
    'billion',
    'trillion',
    'quadrillion',
    'quintillion'
]
def convert_ones_digit(number: int) -> str:
    match number:
        case 0: return ''
        case 1: return 'one'
        case 2: return 'two'
        case 3: return 'three'
        case 4: return 'four'
        case 5: return 'five'
        case 6: return 'six'
        case 7: return 'seven'
        case 8: return 'eight'
        case 9: return 'nine'
    return 'unknown'
def convert_tens_digit(number: int) -> str:
    match number:
        case 0: return ''
        case 1: return 'ten'
        case 2: return 'twenty'
        case 3: return 'thirty'
        case 4: return 'forty'
        case 5: return 'fifty'
        case 6: return 'sixty'
        case 7: return 'seventy'
        case 8: return 'eighty'
        case 9: return 'ninety'
    return 'unknown'
def convert_two_digit(number: int) -> str:
    ones_digit = convert_ones_digit(number % 10)
    tens_digit = convert_tens_digit(number // 10)
    if not ones_digit and not tens_digit:
        return ''
    if not ones_digit:
        return tens_digit
    if not tens_digit:
        return ones_digit
    combined = tens_digit + '-' + ones_digit
    match combined:
        case 'ten-one': return 'eleven'
        case 'ten-two': return 'twelve'
        case 'ten-three': return 'thirteen'
        case 'ten-four': return 'fourteen'
        case 'ten-five': return 'fifteen'
        case 'ten-six': return 'sixteen'
        case 'ten-seven': return 'seventeen'
        case 'ten-eight': return 'eighteen'
        case 'ten-nine': return 'nineteen'
    return combined
def convert_three_digit(number: int) -> str:
    hundreds_digit = convert_ones_digit(number // 100)
    two_digit = convert_two_digit(number % 100)
    if not hundreds_digit and not two_digit:
        return ''
    if not hundreds_digit:
        return two_digit
    hundreds_digit = hundreds_digit + ' hundred'
    if not two_digit:
        return hundreds_digit
    return hundreds_digit + ' ' + two_digit
def convert_number(number: int) -> str:
    names = []
    while number != 0:
        names.append(convert_three_digit(number % 1000))
        number //= 1000
    if not names:
        return 'zero'
    output = ''
    for name, order in zip(names, ORDERS_OF_MAGNITUDE):
        if name:
            output = name + ' ' + order + ', ' + output
    return output[:-3]

def check_output_generator():
    for i in range(101):
        yield CxxExecutableConfig(
            name=f"Check `{i}` (make sure all two-digit numbers are supported).",
            visibility="visible",
            expected_output_str=convert_number(i),
            input_str=str(i)
        )
    for i in range(20):
        for j in range(1, 10):
            if i == 19 and j > 1:
                break
            number = j * 10 ** i
            yield CxxExecutableConfig(
                name=f"Check `{number}` (make sure all pure multiples of powers of ten are supported).",
                visibility="visible",
                expected_output_str=convert_number(number),
                input_str=str(number)
            )
    for i in range(3, 20):
        for _ in range(10):
            number = random.randint(0, min(10**i, 18446744073709551615))
            yield CxxExecutableConfig(
                name=f"Check `{number}` (trying a bunch of random numbers).",
                visibility="visible",
                expected_output_str=convert_number(i),
                input_str=str(i)
            )

if __name__ == "__main__":
    grader = Grader()

    grader.add_cxx_executables_from_config('tests.json')
    grader.add_cxx_executables_from_generator(check_output_generator())
    grade_obj = grader.grade()
    os.makedirs('/autograder/results', exist_ok=True)
    with open('/autograder/results/results.json', 'w+') as f:
        f.write(grade_obj.model_dump_json())
