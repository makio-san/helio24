# dashboard-qa

You check that the local Streamlit dashboard still works on the current `main`.
Follow [RULES.md](RULES.md).

## Each run

1. `bash agents/bin/evidence.sh seed`, then run the app headless on a free port:
   `$PY -m streamlit run app.py --server.address 127.0.0.1 --server.port <port> --server.headless true`
   in the background. Check every tab loads without an exception (use
   `streamlit.testing.v1.AppTest` and `tests/test_app.py` patterns), that the replay,
   evaluation and experiment progress tabs show data, and that no local path or model input
   appears in a CSV download. Stop the server.
2. Fix bugs in `helio24/*_views.py`, `helio24/experiment_monitor.py` or helper modules with
   a test. `app.py` is never changed by an agent: the owner keeps local branding changes
   there. A bug that needs an `app.py` change becomes an `agents:bug` issue with the exact
   lines.
3. Never change what a tab shows by default (models, thresholds, operating point).
4. One PR per run, label `agents:dashboard-qa`. Nothing broken: one line.
