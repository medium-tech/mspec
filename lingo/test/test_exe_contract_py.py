import unittest

from lingo.test.adapters import run_exe_with_python
from lingo.test.contracts import (
    filter_contracts_by_tags,
    list_exe_contract_files,
    load_exe_contracts,
    parse_tag_filter_from_env,
)


class TestExeContractPython(unittest.TestCase):
    """
    Contract tests for exe scripts executed by the Python interpreter.

    Use LINGO_TEST_TAGS=tag1,tag2 to run a subset by tag.
    """

    def test_exe_contracts(self):
        tag_filter = parse_tag_filter_from_env()

        all_contracts = []
        for contract_file in list_exe_contract_files():
            try:
                loaded = load_exe_contracts(contract_file)
            except Exception as e:
                self.fail(str(e))
            all_contracts.extend(loaded)

        all_contracts_len = len(all_contracts)
        filtered_contracts = filter_contracts_by_tags(all_contracts, tag_filter)
        filtered_contracts_len = len(filtered_contracts)

        if not filtered_contracts:
            self.fail('No exe contracts selected. Check lingo/shared/tests/exe and LINGO_TEST_TAGS.')

        for contract in filtered_contracts:
            for case in contract.cases:
                with self.subTest(contract=contract.file_path.name, entry=contract.entry_index, case=case.name):
                    result = run_exe_with_python(contract.script_path, case.params)

                    self.assertEqual(
                        result.exit_code,
                        case.expect.exit_code,
                        msg=(
                            f'Unexpected exit code for {contract.file_path.name}:{case.name}\n'
                            f'stdout:\n{result.stdout}\n'
                            f'stderr:\n{result.stderr}'
                        ),
                    )

                    self.assertEqual(
                        result.stdout,
                        case.expect.stdout,
                        msg=(
                            f'Unexpected stdout for {contract.file_path.name}:tests[{contract.entry_index}]:{case.name}\n'
                            f'expected:\n{case.expect.stdout}\n'
                            f'actual:\n{result.stdout}\n'
                            f'stderr:\n{result.stderr}'
                        ),
                    )

        print(f':: exe :: ran {filtered_contracts_len} of {all_contracts_len} exe contracts (tags: {tag_filter})')


if __name__ == '__main__':
    unittest.main()
