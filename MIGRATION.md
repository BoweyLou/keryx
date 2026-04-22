# Migration Notes

## Existing Vaults

You can point `Keryx` at an existing Obsidian vault immediately. The gateway does not require a proprietary export step.

## Recommended Migration Order

1. Add `08 System/Templates/` and copy the starter templates from [`templates/`](templates).
2. Standardize machine-managed notes on the frontmatter fields used by this project:
   - `title`
   - `type`
   - `created`
   - `updated`
   - `tags`
   - `project`
   - `area`
   - `status`
   - `source`
   - `source_type`
   - `related`
   - `aliases`
   - `confidence`
   - `agent_origin`
   - `write_policy`
3. Add managed regions to notes you want agents to patch safely.
4. Run an initial `keryx index --config local.config.yaml`.

## Safe Adoption Strategy

- Start with read-only use: search, open, project context.
- Enable Class A write targets first: inbox, daily notes, session logs.
- Enable Class B writes only for notes with explicit managed sections.
- Keep Class C disabled unless you intentionally want rename/move/delete style mutations.
