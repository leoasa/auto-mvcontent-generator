import os

def cleanup_files(files):
    """Remove temporary files after processing"""
    for file in files:
        if os.path.exists(file):
            os.remove(file) 
