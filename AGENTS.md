# Contributor guidance

## Role

`openapi-to-sila2` converts OpenAPI specifications into SiLA 2 Feature Definition Language and
generated proxy scaffolding. Keep the library and CLI deterministic, testable, and usable as a
standalone open-source project.

## Start here

- `README.md` for public behavior and CLI usage.
- `docs/` for specifications and decisions.
- `examples/` for supported workflows.

## Boundaries

- Preserve a clean library and CLI surface independent of any hosted product.
- Treat generated FDL, validation fidelity, compatibility, and deterministic output as core quality.
- Preserve public API and CLI compatibility or document deliberate breaking changes.
- Keep all instructions, fixtures, examples, issue references, and documentation suitable for public
  distribution.
- Do not depend on private repositories, internal paths, unpublished specifications, or confidential
  data.

## Working expectations

- Use specs and fixtures that are safe to publish.
- Add regression coverage for mapping defects and edge cases.
- Be precise about what generated output does and does not provide.
- Avoid claims of full SiLA 2 support unless the support surface is measured and documented.
- Never include credentials, customer specifications, private URLs, or internal operational details.

## Verification

- Run `just lint` and `just test`.
- Run `just build` for packaging or release-facing changes.
- Exercise the relevant example or fixture for mapping changes.
- Confirm public documentation matches the current CLI and package behavior.
