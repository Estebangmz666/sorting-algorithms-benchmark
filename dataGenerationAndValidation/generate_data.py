from pathlib import Path
import random

SIZES = (1_000, 10_000, 100_000, 1_000_000)
MIN_VALUE = 10_000_000
MAX_VALUE = 99_999_999
SEED = 20261015
DATA_DIR = Path(__file__).resolve().parent / 'data'


def save_numbers(path: Path, values: list[int]) -> None:
    with path.open('w', encoding='utf-8', newline='\n') as file:
        file.writelines(f'{value}\n' for value in values)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)

    for size in SIZES:
        values = [rng.randint(MIN_VALUE, MAX_VALUE) for _ in range(size)]
        ascending = sorted(values)
        variants = {
            'random': values,
            'ascending': ascending,
            'descending': ascending[::-1],
        }
        for name, array in variants.items():
            destination = DATA_DIR / f'{name}_{size}.txt'
            if destination.exists():
                raise FileExistsError(f'Refusing to overwrite: {destination}')
            save_numbers(destination, array)
            print(f'Created: {destination.name} ({len(array)} numbers)')


if __name__ == '__main__':
    main()
