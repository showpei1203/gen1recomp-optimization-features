# Mobile / Google Colab workflow

When the user only has a phone, do not require the Windows `.bat` flow.

A Colab notebook can mount Google Drive and process the large game ZIP server-side, so the 600 MB source file never needs to be downloaded to the phone.

Current mobile notebook on Drive:
- `source_games/RMXP_POKEMON_ZH_TW_MOBILE_COLAB_v0.1.1.ipynb`

For Pokemon Anil DE 1.0.23 it locates:
- `Pokemon Anil DE 1.0.23 ENGLISH.zip`

and produces in the same Drive folder:
- `Pokemon Anil DE 1.0.23 ENGLISH_LOCALIZATION_SOURCE.zip`

The source pack includes translation-relevant content such as `Data/`, `PBS/`, `Plugins/`, `Fonts/`, `Graphics/Fonts/`, `Text_*`, `Game.ini`, `intl.txt`, and root-level Ruby/text/config files. The original ZIP is not modified.

Reason for this path: the Google Drive connector raw-download ceiling is smaller than large fangame archives, so Colab acts as the server-side extraction bridge.