To build the installer:
pyinstaller your_file.py --add-data ".venv\Lib\site-packages\tabula\tabula-1.0.5-jar-with-dependencies.jar;tabula"