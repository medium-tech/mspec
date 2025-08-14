#!/usr/bin/env python3
import timeit

from test_module.multi_model.model import MultiModel

# vars :: {"test_module": "module.name.snake_case", "multi_model": "model.name.snake_case", "MultiModel": "model.name.pascal_case"}

def perf_single_model_validate(repeat:int=5, number:int=10_000) -> float:
    test_multi_model = MultiModel.example()

    return timeit.repeat(test_multi_model.validate, repeat=repeat, number=number)

def perf_single_model_init_example(repeat:int=5, number:int=10_000) -> float:
    return timeit.repeat(MultiModel.example, repeat=repeat, number=number)


if __name__ == '__main__':
    import argparse
    
    default_number = 1_000_000
    default_repeat = 5

    parser = argparse.ArgumentParser(description='Run performance tests for MultiModel validation.')
    parser.add_argument('--number', type=int, default=default_number, help=f'Number of times to run the validation. Default is {default_number}.')
    parser.add_argument('--repeat', type=int, default=default_repeat, help=f'Number of times to repeat the test. Default is {default_repeat}.')
    args = parser.parse_args()

    perf_tests = [name for name in globals() if name.startswith('perf_') and callable(globals()[name])]
    report = {}

    for perf_test in perf_tests:
        test_result = globals()[perf_test](args.repeat, args.number)
        report[perf_test] = test_result

        minimun = min(test_result)
        print(f'{perf_test}:')
        for result in test_result:
            if result == minimun:
                print(f'  {result} <- min')
            else:
                print(f'  {result}')