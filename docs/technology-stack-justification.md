# Technology Stack Justification

## Project context
SmartSeg is a telecom customer segmentation platform that must:
- ingest and validate CSV datasets,
- preprocess tabular customer data,
- run K-Means clustering and evaluate segmentation quality,
- expose results through APIs,
- persist run history/results,
- present interactive dashboards and exports.

The selected stack is designed to meet these needs with fast development, reproducibility, and maintainability.

## Core backend and data stack

### Python
**Why chosen:**
- Strong ecosystem for data science and machine learning.
- Rapid prototyping with clean, readable syntax.
- Widely adopted in academia and industry, which reduces onboarding cost.

**Alignment with requirements:**
- Supports end-to-end pipeline development (data ingestion → preprocessing → clustering → reporting).
- Enables quick experimentation with segmentation parameters (`k`, normalization, imputation).

### SQL (SQLite currently)
**Why chosen:**
- Relational model fits run metadata, dataset references, and clustering outputs.
- SQLite is lightweight and file-based, ideal for prototype/development deployments.
- Easy migration path to PostgreSQL/MySQL for production scale.

**Alignment with requirements:**
- Persists clustering runs and results across backend restarts.
- Supports traceability/auditability of experiments (run IDs, timestamps, parameters).

### pandas
**Why chosen:**
- Best-in-class DataFrame API for tabular CSV workflows.
- Efficient feature selection, missing-value handling, filtering, and transformations.
- Integrates seamlessly with scikit-learn.

**Alignment with requirements:**
- Handles telecom customer tables with mixed numeric columns.
- Simplifies preprocessing steps needed before clustering (imputation, normalization input prep).

### scikit-learn
**Why chosen:**
- Reliable implementation of K-Means and standard ML utilities.
- Includes scaling, metrics, and model evaluation tooling.
- Stable API and extensive documentation.

**Alignment with requirements:**
- Directly addresses the core requirement: customer segmentation via K-Means.
- Supports reproducible clustering through controlled `random_state`.
- Enables quality checks (e.g., inertia/silhouette-style validation).

## API and application layer

### FastAPI
**Why chosen:**
- High-performance Python web framework with async support.
- Automatic OpenAPI/Swagger docs speed up testing and integration.
- Strong request/response validation through typed schemas.

**Alignment with requirements:**
- Exposes clear endpoints for upload, clustering, and result retrieval.
- Makes frontend-backend integration straightforward and testable.

### Pydantic (schemas)
**Why chosen:**
- Strict validation and serialization of API payloads.
- Reduces runtime errors from malformed requests.

**Alignment with requirements:**
- Ensures clustering parameters and response objects are consistent and safe.

## Frontend stack (delivery and usability)

### React + TypeScript
**Why chosen:**
- Component-based architecture for multi-page analytics UI.
- TypeScript improves reliability of API integration and state handling.

**Alignment with requirements:**
- Supports dashboards, segmentation flows, and report/export screens with maintainable code.

### Vite + Tailwind CSS + Recharts
**Why chosen:**
- Vite enables fast development iterations.
- Tailwind supports consistent UI styling.
- Recharts provides quick implementation of business-oriented visualizations.

**Alignment with requirements:**
- Delivers responsive, interactive result exploration for non-technical users.

## Why this stack is a good fit overall
- **End-to-end cohesion:** Python + pandas + scikit-learn minimizes friction from data prep to modeling.
- **Practical persistence:** SQL storage provides reliable run history and reproducibility.
- **Integration-ready:** FastAPI and TypeScript-based frontend communicate cleanly through documented REST contracts.
- **Scalable path:** The current prototype stack can evolve without major rewrites (SQLite → PostgreSQL, local deployment → cloud).
- **Academic and industry relevance:** Tools are standard, well-documented, and defensible in a PFE context.

## Conclusion
This technology stack is intentionally chosen to balance **implementation speed**, **analytical correctness**, **system reliability**, and **future scalability**. It aligns directly with SmartSeg’s requirements for telecom customer segmentation, from raw CSV ingestion to actionable, visualized clustering insights.
