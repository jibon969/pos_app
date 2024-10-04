
import os
import shutil

# Root directory of your Django project
# project_root = '/Users/j.ahmed/coding/webs/eBussness/eBussness'

project_root = '/Users/j.ahmed/coding/webs/eBussness/eBussness'

# List of directories to delete
directories_to_delete = ['__pycache__', 'migrations']

def delete_directories(root, directories):
    for dirpath, dirnames, filenames in os.walk(root):
        for dirname in dirnames:
            if dirname in directories:
                dir_to_delete = os.path.join(dirpath, dirname)
                print(f"Deleting directory: {dir_to_delete}")
                shutil.rmtree(dir_to_delete)

if __name__ == "__main__":
    delete_directories(project_root, directories_to_delete)
    print("Deletion completed.")
