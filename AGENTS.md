# openapi-to-sila2 guidance

## Role

`openapi-to-sila2` is QPillars' public open-source conversion engine from OpenAPI specifications to
SiLA 2 Feature Definition Language and generated proxy scaffolding. It is a credibility and adoption
asset, and it is the technical foundation used by `sila2-studio`.

## Start here

- `README.md` for public behavior and CLI usage.
- `docs/` for specifications and decisions.
- `examples/` for supported workflows.
- `../engineering-reference/AGENTS.md` for shared engineering guidance.

## Boundaries

- Preserve a clean library and CLI surface independent of any hosted product.
- Put reusable conversion logic here, not in `sila2-studio`.
- Do not introduce product analytics, lead capture, hosting assumptions, or private dependencies.
- Treat generated FDL, validation fidelity, compatibility, and deterministic output as core quality.
- Preserve public API and CLI compatibility or document deliberate breaking changes.
- Keep the repository free of private customer and business information.

## Working expectations

- Use specs and fixtures that are safe to publish.
- Add regression coverage for mapping defects and edge cases.
- Be precise about what generated output does and does not provide.
- Avoid claims of full SiLA 2 support unless the support surface is measured and documented.

## Verification

- Run `just lint` and `just test`.
- Run `just build` for packaging or release-facing changes.
- Exercise the relevant example or fixture for mapping changes.
- Confirm public documentation matches the current CLI and package behavior.
