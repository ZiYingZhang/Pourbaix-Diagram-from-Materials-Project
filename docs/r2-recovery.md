# R2 Recovery Record

Date: 2026-08-15

## Source

The R2.8 source was recovered from the historical working directory at `E:\Research Library\Data\materials project\pourbaix diagram`. The historical directory and its packaged artifacts were left unchanged.

## Integrity

| Item | SHA-256 |
|---|---|
| Historical `pourbaix_gui_R2.py` | `7ACEEDE9457AA7C85405F7034834B1B576DE228E37AA52B7E30F1551EC0458C0` |
| Recovered `legacy/R2/pourbaix_gui_R2.py` | `7ACEEDE9457AA7C85405F7034834B1B576DE228E37AA52B7E30F1551EC0458C0` |
| Initial `pourbaix_gui_R3.py` baseline | `7ACEEDE9457AA7C85405F7034834B1B576DE228E37AA52B7E30F1551EC0458C0` |
| Historical `pourbaix_gui_R2-win64.zip` | `2EAD2AE08AF432622350DE96876B28A25DB5B5A7DDACAFFF083EAA24290930AE` |

## Root-cause evidence

- `pourbaix_env\Scripts\python.exe` exits with `No Python at "D:\Software Installation Area\Python311\python.exe"`.
- `.venv\Scripts\python.exe` exits with `No Python at "D:\Software Installation Area\Python312\python.exe"`.
- The R2 requirements pin `mp-api==0.44.0`, predating the selected coherent R3 dependency set.
- The verified R3 runtime executable is `C:\Users\hp\AppData\Local\Python\bin\python3.13.exe`, version 3.13.15.

The recovery therefore preserves R2 as historical evidence while rebuilding R3 in a clean environment; neither broken virtual environment is repaired in place.

