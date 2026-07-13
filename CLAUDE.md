## Design system reference

The project has a DESIGN.md at repo root defining "The Archive" design system. Key CSS custom properties and tokens are documented there. Before writing CSS, consult DESIGN.md for colors, spacing, shadows, and typography tokens.

Key tokens: `--accent` (brass #D4A857), `--font-ui` (Satoshi), `--font-body` (Instrument Serif), `--space-md` (16px base), `--radius-sm` (4px), `--radius-md` (8px).

3D depth effects (tilt, glass navbar, parallax) are gated behind `.no-js`, `prefers-reduced-motion`, and `@supports` guards. See `DESIGN.md §11` for the progressive enhancement chain.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec
