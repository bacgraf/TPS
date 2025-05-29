# build.py
import PyInstaller.__main__
import os
import shutil

# Configurações do build
APP_NAME = "MonitorTekpowerTPS"
MAIN_SCRIPT = "main.py"
ICON_PATH = None  # Caminho para um arquivo .ico se quiser um ícone personalizado
ADDITIONAL_FILES = [
    ("config.py", "."),
    ("modbus_client.py", "."),
    ("ui.py", ".")
]


def build_executable():
    # Configura os argumentos do PyInstaller
    pyinstaller_args = [
        "--name", APP_NAME,
        "--onefile",
        "--windowed",
        "--add-data", f"{';'.join([f'{src}:{dest}' for src, dest in ADDITIONAL_FILES])}",
        MAIN_SCRIPT
    ]

    if ICON_PATH:
        pyinstaller_args += ["--icon", ICON_PATH]

    # Executa o PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)

    # Move o executável para a pasta raiz
    dist_dir = os.path.join("dist")
    if os.path.exists(dist_dir):
        for file in os.listdir(dist_dir):
            if file.endswith(".exe"):
                shutil.move(os.path.join(dist_dir, file), ".")
        print("Executável criado com sucesso!")
    else:
        print("Erro: Pasta dist não encontrada")


if __name__ == "__main__":
    build_executable()