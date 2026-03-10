"""
Chart 2 — Top 10 Most Borrowed Categories
Insight: Which book categories dominate borrowing. Ranked with % share.
"""

import os, sys, django
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()

from librarian.models import BorrowRecord
from django.db.models import Count

# ── Data ──────────────────────────────────────────────────────────────────────
data = list(
    BorrowRecord.objects
    .values('book__category__name')
    .annotate(total=Count('id'))
    .order_by('-total')[:10]
)

total_all  = sum(d['total'] for d in data)
categories = [d['book__category__name'] or 'Uncategorised' for d in data]
totals     = [d['total'] for d in data]
pcts       = [round(t / total_all * 100, 1) for t in totals]

# Colours: gold/silver/bronze for top 3, then gradient
colours = ['#C4A82A', '#A0A0A0', '#C47A3A'] + ['#5C3D2E'] * 7
alphas  = [1.0, 1.0, 1.0] + [0.88 - i * 0.06 for i in range(7)]
final_colours = [(plt.matplotlib.colors.to_rgb(c) + (a,)) for c, a in zip(colours, alphas)]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6.5))
fig.patch.set_facecolor('#FAF7F2')
ax.set_facecolor('#FAF7F2')

y_pos = list(range(len(categories)))
bars  = ax.barh(y_pos, totals, color=final_colours, edgecolor='white',
                linewidth=0.8, height=0.65)

# Rank label left of bar
rank_labels = ['1st', '2nd', '3rd'] + [f'{i+1}th' for i in range(3, len(categories))]
for i, rank in enumerate(rank_labels):
    colour = '#C4A82A' if i == 0 else '#A0A0A0' if i == 1 else '#C47A3A' if i == 2 else '#9E7E6A'
    ax.text(-3, i, rank, va='center', ha='right', fontsize=8.5,
            color=colour, fontweight='bold')

# Count + % label at end of bar
for i, (bar, val, pct) in enumerate(zip(bars, totals, pcts)):
    w = bar.get_width()
    ax.text(w + 1.5, bar.get_y() + bar.get_height() / 2,
            f'{val}  ({pct}%)', va='center', fontsize=9,
            color='#2C1F14', fontweight='bold' if i < 3 else 'normal')
ax.set_xlim(-12, totals[0] * 1.28)
ax.set_yticks(y_pos)
ax.set_yticklabels(categories, fontsize=10.5, color='#2C1F14')
ax.invert_yaxis()
ax.tick_params(axis='x', colors='#6B5446', labelsize=9)
ax.tick_params(axis='y', length=0)
ax.set_xlabel('Total Borrows', fontsize=10, color='#5C3D2E', labelpad=8)
ax.set_title('Top 10 Most Borrowed Categories', fontsize=14,
             fontweight='bold', color='#2C1F14', pad=16)
ax.grid(axis='x', color='#E8DDD0', linewidth=0.8, linestyle='--', zorder=0)
ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)

fig.text(0.5, -0.01,
         f'{total_all} total borrows across top 10 categories | Library System 2024-2026',
         ha='center', fontsize=8.5, color='#9E7E6A')

plt.tight_layout(rect=[0, 0.02, 1, 1])
out_path = os.path.join(os.path.dirname(__file__), '..', 'charts', 'chart_2_top_categories.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#FAF7F2')
print(f'Saved → {os.path.abspath(out_path)}')
