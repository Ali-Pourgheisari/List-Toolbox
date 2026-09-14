"""List Toolbox — entry point.

    streamlit run list_toolbox.py

The app itself lives in the exclusion_lists package:
    core/  pure logic — file reading, name matching, merging (no Streamlit)
    ui/    the Streamlit layer — session state, widgets, one module per tab
"""

from exclusion_lists.app import main

main()
