# Example script to remove duplicate lines from a text file
# and write the unique lines to a new file.

import sys


def remove_duplicates(input_path: str, output_path: str) -> None:
    """Read lines from input_path, filter out duplicates, and write unique lines to output_path."""
    seen = set()
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        for line in infile:
            if line not in seen:
                seen.add(line)
                outfile.write(line)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python duplicate_filter_example.py <input.txt> <output.txt>')
        sys.exit(1)
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    remove_duplicates(in_file, out_file)
    print(f'Filtered duplicates from {in_file} into {out_file}')
