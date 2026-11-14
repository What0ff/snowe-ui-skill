# Data Visualization and Dashboards

Use when choosing, building or reviewing a chart, KPI tile, sparkline or dashboard. Start from the viewer's question; styling comes last. Filters and collections live in [app-patterns.md](app-patterns.md).

## Choose the Form by the Question

| Question | Default | Deviate when |
|---|---|---|
| Compare categories | Horizontal bars sorted by value | Natural order (months, sizes): keep it, use columns |
| Change over time | Line; columns for counts per period | Under about 4 points: columns or numbers |
| Distribution | Histogram; box or strip plots across groups | Under about 30 values: a dot plot |
| Part of a whole | One stacked bar, or sorted bars of shares | Shares over time: 100% stacked columns, 5 parts at most |
| Two measures related | Scatter plot | Thousands of points: hexbin or low opacity |
| Exact lookup | Table with [aligned tabular numbers](design-foundations.md#starting-points) | The shape is the answer: chart plus table |

Prefer a table when people read exact values, compare more than about three measures per item, or there are fewer than about five values.

## Encode Accurately

Put the main comparison on position or length; angle, area and color intensity read less accurately (Cleveland and McGill).

| Pattern | Default | Deviate when |
|---|---|---|
| Bar baseline | Zero, because length is the value | Never truncate bars; use dots or a line, which may fit the data range |
| 3D or perspective | Flat 2D marks | The third dimension is real spatial data |
| Pie or donut | Sorted bars | Two or three parts, and share of the whole is the only message |
| Dual y-axes | Two charts aligned on one x-axis, or series indexed to 100 | An established pairing (temperature and rainfall climate charts), each axis in its series color |

Use 4–6 round ticks and gridlines lighter than the marks.

## Label and Color

- **Direct labels** at line and bar ends, up to about five series; a legend only when labels collide, ordered like the marks.
- **Categorical**: distinct hues, 6–8 at most; beyond that, group an "Other" or split into small multiples.
- **Sequential**: one hue light to dark, or a perceptually uniform ramp.
- **Diverging**: two hues around a meaningful midpoint (zero, target, neutral answer).
- **Highlight**: the message series in the accent, the rest gray. Default when the chart makes one point.
- A series keeps its color across charts; status colors stay reserved for status.
- **Never color alone**: add labels, marker shapes, dashes or position, and check a color-vision simulation. Marks that must be told apart need 3:1 against background and neighbors ([WCAG 1.4.11](quality-gates.md#accessibility-and-interaction)).
- **Dark mode**: re-pick series colors for the dark surface rather than inverting, then recheck 3:1.

## Numbers and Periods

- Format with `Intl.NumberFormat` ([localization](localization-and-rtl.md)). Axes may abbreviate (1.2K); tooltips and tables show full values.
- State units once, in the axis title or label ("Revenue, USD").
- Name the comparison basis ("vs previous 7 days"); mark an incomplete period "to date".
- From 4% to 5% is +1 percentage point, or +25%; say which.

## KPI Tiles and Sparklines

- A tile holds a label with unit, the value as its largest text, a signed delta with arrow (▲ +4.2%) and its comparison period.
- Delta color follows meaning, not direction: a rising return rate is bad. Sign and arrow carry direction without color. With a zero or tiny base, show the absolute change or "New".
- A sparkline has no axes, spans the tile's period and marks its last point. Tiles meant for comparison share one scale and say so.
- Tiles keep their size as values change ([stable geometry](design-foundations.md#stable-geometry-across-states)).

## Dashboard Layout and Scope

- Order by the question: KPIs that answer "is anything off?", then charts that explain why, then detail tables. Past about 5–9 views, add a tab.
- One time range and filter bar at the top governs everything beneath it. A panel with its own range, or one a filter does not reach, says so in its header ("Last 12 months · all regions"). Exports and shared links carry the active range.
- Align charts that share a time axis; prefer small multiples over one crowded chart. Show "Updated 14:02".

## States

Loading shows the frame and axes at final size. Empty names the cause ("No orders in this range") and offers to widen the range. Zero is data: draw the zero bar. Missing data is a gap with a note, never interpolated or drawn as zero. Errors stay in the failing panel, with retry and the last good data marked stale ([collection states](app-patterns.md#states-every-collection-needs)).

## Interaction and Accessibility

- Key numbers are visible without hover. A tooltip shows series, exact value, unit and period, finished like any [overlay](overlays-and-selection.md).
- Touch: tap a mark or scrub the axis to pin a readout; tap outside to dismiss. Hit areas are at least 24×24 px.
- Keyboard: arrow keys step through points; the readout is announced.
- Give each chart a takeaway title, a one-sentence summary ("Orders rose 18% in March") and a reachable data table. A static SVG uses `role="img"` with a name and description.
- Transitions respect [reduced motion](motion-and-interaction.md#reduced-motion-is-a-design-variant).

## Check

- The form answers the question; a table was considered.
- Bars start at zero; no 3D, crowded pie or unconventional dual axis.
- At most 8 stable categorical colors; marks 3:1; meaning survives without color.
- Every panel shows units, comparison basis, range and filters.
- Loading, empty, zero, missing and error states keep final geometry.
- Values are reachable without hover; a summary and data table exist.
