## ADDED Requirements

### Requirement: OKLCH Color Tokens — Light and Dark Mode
The system SHALL define all colors using OKLCH CSS variables in `:root` (light mode) and `.dark` (dark mode) selectors. The following semantic tokens MUST be defined with exact values:

| Token | Light Mode | Dark Mode |
|---|---|---|
| `--background` | `oklch(100% 0 0)` | `oklch(18% .005 285.823)` |
| `--foreground` | `oklch(14.1% .005 285.823)` | `oklch(98.5% 0 0)` |
| `--card` | `oklch(100% 0 0)` | `oklch(21% .006 285.885)` |
| `--muted` | `oklch(96.7% .001 286.375)` | `oklch(27.4% .006 286.033)` |
| `--muted-foreground` | `oklch(55.2% .016 285.938)` | `oklch(70.5% .015 286.067)` |
| `--border` | `oklch(92% .004 286.32)` | `oklch(100% 0 0/.1)` |
| `--brand` | `oklch(55% .16 255)` | `oklch(65% .16 255)` |
| `--success` | `oklch(55% .16 145)` | `oklch(65% .15 145)` |
| `--warning` | `oklch(75% .16 85)` | `oklch(70% .16 85)` |
| `--destructive` | `oklch(57.7% .245 27.325)` | `oklch(70.4% .191 22.216)` |

All color decisions in component development MUST reference hex values derived from these OKLCH tokens (for communication and design alignment purposes).

#### Scenario: Dark mode toggle
- **WHEN** user selects "Dark" theme in Preferences
- **THEN** the `.dark` class is applied to the `<html>` element via next-themes
- **THEN** all OKLCH variables resolve to their dark mode values within one paint cycle

### Requirement: Typography Scale
The system SHALL use three font families: `Inter` (UI/default), `Source Serif 4` (editorial/landing), `Geist Mono` (code/runtimes). Font sizes SHALL follow the rem scale: `xs` (.75rem), `sm` (.875rem), `base` (1rem), `lg` (1.125rem), `xl` (1.25rem), `2xl` (1.5rem), `3xl` (1.875rem), `4xl` (2.25rem), `5xl` (3rem), `6xl` (3.75rem). Font weights: normal (400), medium (500), semibold (600), bold (700).

#### Scenario: Code editor renders in Geist Mono
- **WHEN** user views the Skill Detail editor or Execution Log
- **THEN** the editor content renders with `font-family: 'Geist Mono', ui-monospace, monospace`

### Requirement: Border Radius and Spacing
Border radii SHALL be: `--radius: .625rem` (10px, buttons/inputs) and `--radius-md: calc(.625rem * .8)` (8px, sub-components). Spacing SHALL follow Tailwind's 4px base unit (`--spacing: .25rem`). Container max-widths: `xs`→20rem through `6xl`→72rem.

### Requirement: Animations and Micro-interactions
The system SHALL implement: skeleton pulse (`animate-pulse`) on loading states, ping indicator (`animate-ping`) on live activity buttons (WebSocket updates), smooth page transitions (opacity fade), and spinning dot on "In Progress" status icon when agent is active.

#### Scenario: Skeleton loading state
- **WHEN** an issue list is loading
- **THEN** skeleton placeholder rows animate with `animate-pulse` (opacity 0.5 → 1 loop)
- **THEN** skeletons are replaced by real data within the same DOM nodes to avoid layout shift
