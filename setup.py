"""py2app build configuration for the Rephrase menubar app.

Run via build_mac.sh, which pins the Python interpreter and build venv:
    ./build_mac.sh
"""

from setuptools import setup

from version import __version__

APP = ["rephrase.py"]

PLIST = {
    "CFBundleName": "Rephrase",
    "CFBundleDisplayName": "Rephrase",
    # Stable identifier so macOS TCC remembers Accessibility / Input
    # Monitoring grants per bundle id instead of re-asking after rebuilds.
    "CFBundleIdentifier": "com.gauravjiandani.rephrase",
    "CFBundleShortVersionString": __version__,
    "CFBundleVersion": __version__,
    # Menubar-only app: no Dock icon, no Cmd+Tab entry.
    "LSUIElement": True,
    # Required so the osascript "System Events" keystroke calls raise the
    # Automation permission prompt instead of failing silently.
    "NSAppleEventsUsageDescription": (
        "Rephrase simulates Cmd+C and Cmd+V keystrokes to copy your selected "
        "text and paste the rephrased result."
    ),
    "NSHumanReadableCopyright": "MIT License",
    "LSMinimumSystemVersion": "12.0",
}

OPTIONS = {
    "plist": PLIST,
    # Ship these as full packages: their submodules are loaded dynamically
    # (keyring backends, pynput platform backends, openai lazy imports,
    # certifi's bundled CA file) and would be missed by import analysis.
    "packages": [
        "rumps",
        "pynput",
        "keyring",
        "openai",
        "pyperclip",
        "certifi",
        "httpx",
        "httpcore",
        "anyio",
        "pydantic",
    ],
}

setup(
    name="Rephrase",
    app=APP,
    version=__version__,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
