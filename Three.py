import os

def generate_tree(root_dir, exclude_dirs, output_file):
    with open(output_file, 'w') as f:
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]  # Exclude dirs
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write('{}{}/\n'.format(indent, os.path.basename(root)))
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                f.write('{}{}\n'.format(sub_indent, file))

generate_tree('.', ['venv', '.venv',
                    'static','.git',
                    'migrations', '.mypy_cache', '.idea'], 'arborescence.txt')

