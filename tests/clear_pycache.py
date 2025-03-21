import os
import shutil

def clear_cache(directory: str = 'pyweber'):
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            shutil.rmtree(path=pycache_path, ignore_errors=True)
        
        for file in files:
            if file.endswith('.pyc'):
                pyc_file = os.path.join(root, file)
                os.remove(pyc_file)