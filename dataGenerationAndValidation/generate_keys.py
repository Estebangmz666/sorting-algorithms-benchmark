"""Generate, once, the search keys used in Punto 2.

For every size it creates, next to the datasets of Punto 1:
- keys_<n>.txt: 1000 keys in random order, 500 present in ascending_<n>.txt
  and 500 absent (8-digit values that do not appear in the array).
- position_keys_<n>.txt: three keys taken from ascending_<n>.txt, one per
  line, located at the start (index 0), center (index n // 2) and end
  (index n - 1) of the array.
"""
from pathlib import Path
import random

SIZES = (1_000, 10_000, 100_000, 1_000_000)
MIN_VALUE = 10_000_000
MAX_VALUE = 99_999_999
KEY_COUNT = 1_000
PRESENT_COUNT = 500
SEED = 20261021
DATA_DIR = Path(__file__).resolve().parent / 'data'


def load_numbers(path: Path) -> list[int]:
    with path.open('r', encoding='utf-8') as file:
        return [int(line) for line in file]


def save_numbers(path: Path, values: list[int]) -> None:
    if path.exists():
        raise FileExistsError(f'Refusing to overwrite: {path}')
    with path.open('w', encoding='utf-8', newline='\n') as file:
        file.writelines(f'{value}\n' for value in values)


def main() -> None:
    rng = random.Random(SEED)

    for size in SIZES:
        folder = DATA_DIR / f'{size:,}'.replace(',', '_')
        ascending = load_numbers(folder / f'ascending_{size}.txt')
        if len(ascending) != size or ascending != sorted(ascending):
            raise ValueError(f'Invalid ascending dataset for n={size}')

        values = set(ascending)
        # Distinct present keys, so 500 different values are searched.
        present = rng.sample(sorted(values), PRESENT_COUNT)
        absent = set()
        while len(absent) < KEY_COUNT - PRESENT_COUNT:
            candidate = rng.randint(MIN_VALUE, MAX_VALUE)
            if candidate not in values:
                absent.add(candidate)

        keys = present + sorted(absent)
        rng.shuffle(keys)
        save_numbers(folder / f'keys_{size}.txt', keys)

        positions = [ascending[0], ascending[size // 2], ascending[size - 1]]
        save_numbers(folder / f'position_keys_{size}.txt', positions)
        print(f'Created: keys_{size}.txt ({len(keys)} keys) '
              f'and position_keys_{size}.txt {positions}')


if __name__ == '__main__':
    main()
