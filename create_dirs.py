import os

# Create directory structure
base_path = r'd:\Kidney Detection\frontend\src'
directories = ['api', 'components', 'pages', 'types']

for dir_name in directories:
    dir_path = os.path.join(base_path, dir_name)
    os.makedirs(dir_path, exist_ok=True)
    print(f'✓ Created: {dir_path}')

print('\n✓ All directories created successfully')
