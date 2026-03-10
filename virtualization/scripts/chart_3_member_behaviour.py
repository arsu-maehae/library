"""
Chart 3 — Member Borrow Behaviour: On-Time vs Late Returns
Insight: Identifies high-risk members who frequently return books late.
"""

import os, sys, django
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library.settings')
django.setup()

from librarian.models import BorrowRecord, Member
from django.db.models import F

#── Data ──────────────────────────────────────────────────────────────────────
data = []
for member in Member.objects.all():
    records = BorrowRecord.objects.filter(member=member, return_date__isnull=False)
    total = records.count()
    if total == 0:
        continue
    late    = records.filter(return_date__gt=F('due_date')).count()
    on_time = total - late
    data.append({
        'name':     member.name or member.ssid,
        'total':    total,
        'on_time':  on_time,
        'late':     late,
        'late_pct': round(late / total * 100),
    })

data.sort(key=lambda x: x['late_pct'], reverse=True)

names     = [d['name'] for d in data]
on_times  = [d['on_time'] for d in data]
lates     = [d['late'] for d in data]
late_pcts = [d['late_pct'] for d in data]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(13, max(7, len(names) * 0.38)))
fig.patch.set_facecolor('#FAF7F2')
ax.set_facecolor('#FAF7F2')

y     = list(range(len(names)))
bar_h = 0.62

# Highlight high-risk rows
for i, pct in enumerate(late_pcts):
    if pct >= 50:
        ax.barh(i, max(d['total'] for d in data) * 1.35, height=bar_h + 0.15,
                color='#FDF0EE', edgecolor='none', zorder=1)

ax.barh(y, on_times, height=bar_h, color='#4A7C59', label='On Time ✓', edgecolor='white', linewidth=0.5, zorder=3)
ax.barh(y, lates, height=bar_h, left=on_times, color='#A33A2E', label='Late ✗', edgecolor='white', linewidth=0.5, zorder=3)

# Count labels inside segments
for i, (ot, lt) in enumerate(zip(on_times, lates)):
    if ot >= 5:
        ax.text(ot / 2, i, str(ot), va='center', ha='center',
                fontsize=7.5, color='white', fontweight='bold', zorder=4)
    if lt >= 5:
        ax.text(ot + lt / 2, i, str(lt), va='center', ha='center',
                fontsize=7.5, color='white', fontweight='bold', zorder=4)

# Late % badge
max_total = max(d['total'] for d in data)
for i, (d, pct) in enumerate(zip(data, late_pcts)):
    is_high = pct >= 50
    bg_col  = '#A33A2E' if is_high else '#E8DDD0'
    txt_col = 'white'   if is_high else '#6B5446'
    ax.text(max_total + 2.5, i, f' {pct}% ',
            va='center', ha='left', fontsize=8,
            color=txt_col, fontweight='bold' if is_high else 'normal',
            bbox=dict(boxstyle='round,pad=0.3', facecolor=bg_col, edgecolor='none'))

ax.text(max_total + 2.5, -0.9, '! High Risk (>=50% late)',
        fontsize=8, color='#A33A2E', fontweight='bold', va='top')

ax.set_yticks(y)
ax.set_yticklabels(names, fontsize=9.5, color='#2C1F14')
ax.invert_yaxis()
ax.set_xlim(0, max_total * 1.38)
ax.set_xlabel('Number of Completed Borrows', fontsize=10, color='#5C3D2E', labelpad=8)
ax.set_title('Member Borrow Behaviour: On-Time vs Late Returns',
             fontsize=13, fontweight='bold', color='#2C1F14', pad=16)
ax.tick_params(axis='x', colors='#6B5446', labelsize=9)
ax.tick_params(axis='y', length=0)
ax.grid(axis='x', color='#E8DDD0', linewidth=0.8, linestyle='--', zorder=0)
ax.spines[['top', 'right', 'left', 'bottom']].set_visible(False)

on_patch   = mpatches.Patch(color='#4A7C59', label='On Time')
late_patch = mpatches.Patch(color='#A33A2E', label='Late')
high_patch = mpatches.Patch(color='#FDF0EE', edgecolor='#F5C4BC', label='High-risk member (>=50% late)')
ax.legend(handles=[on_patch, late_patch, high_patch], loc='lower right',
          frameon=True, fontsize=9, facecolor='#FAF7F2', edgecolor='#E8DDD0')

fig.text(0.5, -0.01,
         f'{len(data)} members  |  Badge = % of borrows returned late  |  Red badge = >=50% late',
         ha='center', fontsize=8, color='#9E7E6A')

plt.tight_layout(rect=[0, 0.02, 1, 1])
out_path = os.path.join(os.path.dirname(__file__), '..', 'charts', 'chart_3_member_behaviour.png')
plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor='#FAF7F2')
print(f'Saved → {os.path.abspath(out_path)}')
