import os
from dataclasses import dataclass
from pathlib import Path

import yaml


LINGO_DIR = Path(__file__).resolve().parents[1]
SHARED_DIR = LINGO_DIR / 'shared'
EXE_SCRIPT_DIR = SHARED_DIR / 'scripts' / 'exe'
EXE_CONTRACT_DIR = SHARED_DIR / 'tests' / 'exe'


@dataclass(frozen=True)
class ExeCaseExpectation:
    exit_code: int
    stdout: str


@dataclass(frozen=True)
class ExeContractCase:
    name: str
    params: dict
    expect: ExeCaseExpectation


@dataclass(frozen=True)
class ExeContract:
    file_path: Path
    script_path: Path
    tags: tuple[str, ...]
    cases: tuple[ExeContractCase, ...]


# helpers #

def _normalize_output(text: str) -> str:
    return text.rstrip('\n')


def _require_mapping(value, field_name: str, file_path: Path) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f'{file_path}: expected {field_name} to be a mapping')
    return value


def _require_list(value, field_name: str, file_path: Path) -> list:
    if not isinstance(value, list):
        raise ValueError(f'{file_path}: expected {field_name} to be a list')
    return value


def _parse_case(case_data: dict, file_path: Path) -> ExeContractCase:
    case_data = _require_mapping(case_data, 'cases[]', file_path)

    name = case_data.get('name')
    if not isinstance(name, str) or not name:
        raise ValueError(f'{file_path}: case name must be a non-empty string')

    params = case_data.get('params', {})
    params = _require_mapping(params, f'case {name}.params', file_path)

    expect_data = _require_mapping(case_data.get('expect'), f'case {name}.expect', file_path)

    exit_code = expect_data.get('exit_code')
    if not isinstance(exit_code, int):
        raise ValueError(f'{file_path}: case {name}.expect.exit_code must be an int')

    stdout = expect_data.get('stdout', '')
    if not isinstance(stdout, str):
        raise ValueError(f'{file_path}: case {name}.expect.stdout must be a string')

    return ExeContractCase(
        name=name,
        params=params,
        expect=ExeCaseExpectation(exit_code=exit_code, stdout=_normalize_output(stdout)),
    )


# public api #

def load_exe_contract(contract_file: Path) -> ExeContract:
    with contract_file.open('r') as f:
        doc = yaml.safe_load(f)

    doc = _require_mapping(doc, 'root', contract_file)

    envelope = _require_mapping(doc.get('lingo_test'), 'lingo_test', contract_file)
    if envelope.get('spec') != 'exe':
        raise ValueError(f"{contract_file}: expected lingo_test.spec='exe'")

    script_ref = doc.get('script')
    if not isinstance(script_ref, str) or not script_ref:
        raise ValueError(f'{contract_file}: script must be a non-empty string')

    script_path = SHARED_DIR / script_ref
    if not script_path.exists():
        raise ValueError(f'{contract_file}: script path does not exist: {script_path}')

    tags = _require_list(doc.get('tags', []), 'tags', contract_file)
    normalized_tags = []
    for tag in tags:
        if not isinstance(tag, str) or not tag:
            raise ValueError(f'{contract_file}: tags must contain only non-empty strings')
        normalized_tags.append(tag)

    case_docs = _require_list(doc.get('cases', []), 'cases', contract_file)
    if not case_docs:
        raise ValueError(f'{contract_file}: must define at least one case')

    cases = tuple(_parse_case(case_doc, contract_file) for case_doc in case_docs)

    return ExeContract(
        file_path=contract_file,
        script_path=script_path,
        tags=tuple(normalized_tags),
        cases=cases,
    )


def load_all_exe_contracts() -> list[ExeContract]:
    files = sorted(EXE_CONTRACT_DIR.glob('*.test.yaml'))
    return [load_exe_contract(file_path) for file_path in files]


def filter_contracts_by_tags(contracts: list[ExeContract], tags: set[str] | None) -> list[ExeContract]:
    if not tags:
        return contracts

    selected = []
    for contract in contracts:
        if set(contract.tags).intersection(tags):
            selected.append(contract)
    return selected


def parse_tag_filter_from_env(var_name: str = 'LINGO_TEST_TAGS') -> set[str] | None:
    raw = os.environ.get(var_name, '').strip()
    if not raw:
        return None

    return {tag.strip() for tag in raw.split(',') if tag.strip()}
