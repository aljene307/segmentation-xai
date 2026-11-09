"""Mesures de mémoire sous Windows (sans dépendance supplémentaire)."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys


def memoire_libre_go() -> float | None:
    """Mémoire physique disponible, en Go (None hors de Windows)."""
    if sys.platform != "win32":
        return None

    class Etat(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.wintypes.DWORD), ("dwMemoryLoad", ctypes.wintypes.DWORD),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    e = Etat()
    e.dwLength = ctypes.sizeof(e)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e)):
        return None
    return e.ullAvailPhys / 1024**3


def pic_processus_go() -> float | None:
    """Pic de mémoire vive du processus Python courant, en Go."""
    if sys.platform != "win32":
        return None

    class Compteurs(ctypes.Structure):
        _fields_ = [("cb", ctypes.wintypes.DWORD), ("PageFaultCount", ctypes.wintypes.DWORD)]
        _fields_ += [(n, ctypes.c_size_t) for n in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
            "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    processus = ctypes.windll.kernel32.GetCurrentProcess
    processus.restype = ctypes.wintypes.HANDLE
    lire = ctypes.windll.psapi.GetProcessMemoryInfo
    lire.argtypes = [ctypes.wintypes.HANDLE, ctypes.POINTER(Compteurs), ctypes.wintypes.DWORD]
    lire.restype = ctypes.wintypes.BOOL
    c = Compteurs()
    c.cb = ctypes.sizeof(c)
    if not lire(processus(), ctypes.byref(c), c.cb):
        return None
    return c.PeakWorkingSetSize / 1024**3


def exiger_memoire_libre(minimum_go: float) -> float | None:
    """Arrête le programme avec un message clair si la mémoire libre est insuffisante."""
    libre = memoire_libre_go()
    if libre is not None and libre < minimum_go:
        raise SystemExit(
            f"Mémoire libre insuffisante : {libre:.2f} Go, il en faut au moins {minimum_go:.1f} Go.\n"
            "Fermez des programmes (onglets de Chrome, autres applications) puis relancez.\n"
            "La taille de l'échantillon de la CAH n'est pas modifiée (règle fixe : 6 000 clients)."
        )
    return libre
