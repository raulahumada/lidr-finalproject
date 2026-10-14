"""``python -m app.ingestion`` entry — delegates to ``run_ingest``."""

from app.ingestion.run_ingest import main

raise SystemExit(main())
