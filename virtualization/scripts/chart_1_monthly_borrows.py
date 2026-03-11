"""
Chart 1 — Monthly Borrow Activity (2024–2026)
Insight: How library usage trends change across months and years.
"""

import os, sys, django, calendar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()

from librarian.models import BorrowRecord

# ── Data ──────────────────────────────────────────────────────────────────────
records = BorrowRecord.objects.values_list('start_date', flat=True).order_by('start_date')

monthly = defaultdict(int)
for date in records:
    monthly[(date.year, date.month)] += 1

sorted_keys = sorted(monthly.keys())
values = [monthly[k] for k in sorted_keys]

# Short month + year label, mark year boundaries
xlabels = []
year_group_starts = {}
for i, (y, m) in enumerate(sorted_keys):
    xlabels.append(calendar.month_abbr[m])
    if m == 1 or i == 0:
        year_group_starts[i] = y

year_colours = {2024: '#C4A882', 2025: '#5C3D2E', 2026: '#8B5E52'}
bar_colours  = [year_colours.get(y, '#888') for y, m in sorted_keys]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(18, 6))
fig.patch.set_facecolor('#FAF7F2')
ax.set_facecolor('#FAF7F2')

x = list(range(len(sorted_keys)))
bars = ax.bar(x, values, color=bar_colours, width=0.72, edgecolor='white', linewidth=0.6, zorder=3)

# Trend line (rolling average 3)
import statistics
rolling = []
for i in range(len(values)):
    window = values[max(0, i-1):i+2]
    rolling.append(statistics.mean(window))
ax.plot(x, rolling, color='#2C1F14', linewidth=1.8, linestyle='--', alpha=0.55,
        zorder=4, label='Trend (3-month avg)')

# Annotate peak and lowest
peak_i = values.index(max(values))
low_i  = values.index(min(values))
for idx, label, yoff, colour in [(peak_i, f'Peak\n{max(values)} borrows', 4, '#5C3D2E'),
                                   (low_i,  f'Low\n{min(values)} borrows', 4, '#9E7E6A')]:
    ax.annotate(label,
        xy=(idx, values[idx]), xytext=(idx, values[idx] + yoff),
        ha='center', va='bottom', fontsize=7.5, color=colour, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=colour, lw=1),
    )

# Year dividers and labels
prev_y = None
for i, (y, m) in enumerate(sorted_keys):
    if y != prev_y:
        if i > 0:
            ax.axvline(i - 0.5, color='#D5C9BC', linewidth=1.2, linestyle='-', zorder=2)
        # Year label centred over its group
        group_indices = [j for j, (yy, mm) in enumerate(sorted_keys) if yy == y]
        mid = (group_indices[0] + group_indices[-1]) / 2
        ax.text(mid, -9, str(y), ha='center', va='top', fontsize=10,
                fontweight='bold', color=year_colours[y], transform=ax.transData)
        prev_y = y

ax.set_xticks(x)
ax.set_xticklabels(xlabels, fontsize=8, color='#6B5446')
ax.set_ylabel('Number of Borrows', fontsize=10, color='#5C3D2E', labelpad=10)
ax.set_title('Monthly Borrow Activity  (2024 - 2026)', fontsize=14,
             fontweight='bold', color='#2C1F14', pad=16)
ax.set_ylim(0, max(values) * 1.22)
ax.tick_params(axis='y', colors='#6B5446')
ax.tick_params(axis='x', length=0)
ax.grid(axis='y', color='#E8DDD0', linewidth=0.8, linestyle='--', zorder=0)
ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)

# Legend
legend_patches = [mpatches.Patch(color=c, label=str(y)) for y, c in year_colours.items()]
trend_line = mlines.Line2D([], [], color='#2C1F14', linewidth=1.8,
                           linestyle='--', alpha=0.55, label='3-month trend')
ax.legend(handles=legend_patches + [trend_line], loc='upper right',
          frameon=True, fontsize=9, facecolor='#FAF7F2', edgecolor='#E8DDD0',
          labelcolor='#2C1F14')

fig.text(0.5, -0.02, f'Total borrows: {sum(values)}  |  {len(sorted_keys)} months of data',
         ha='center', fontsize=8.5, color='#9E7E6A')

plt.tight_layout()
out_path = os.path.join(os.path.dirname(__file__), '..', 'charts', 'chart_1_monthly_borrows.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#FAF7F2')
print(f'Saved → {os.path.abspath(out_path)}')
