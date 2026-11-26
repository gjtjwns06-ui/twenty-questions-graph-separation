"""Render README figures from preserved response tables, CSVs and exact bounds."""
from pathlib import Path
import csv
from fractions import Fraction
import hashlib
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle
from matplotlib.colors import LinearSegmentedColormap

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'assets'
INK, MUTED, TEAL, BLUE, ORANGE = '#122237','#64748b','#159b8c','#515bd4','#d5843f'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.labelcolor':MUTED,'xtick.color':MUTED,
                     'ytick.color':MUTED,'text.color':INK,'axes.titleweight':'bold',
                     'figure.facecolor':'white','savefig.facecolor':'white'})
SOURCES = {}


def read(name):
    p=ROOT/'research'/name
    SOURCES[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return json.loads(p.read_text(encoding='utf-8'))


def save(fig,name):
    fig.savefig(OUT/f'{name}.png',dpi=160,bbox_inches='tight',pad_inches=.18,facecolor=fig.get_facecolor())
    fig.savefig(OUT/f'{name}.svg',bbox_inches='tight',pad_inches=.18,facecolor=fig.get_facecolor())
    plt.close(fig)


def table(rows,m):
    a=np.zeros((len(rows),m),dtype=int)
    for i,r in enumerate(rows):a[i,list(r)]=1
    return a


def hero():
    best=read('runs/extremal_report_v1/best18.json')
    # The small response matrices are the actual saved 18-by-9 witness.
    ra=best['a']['rows'] if 'a' in best else None
    if ra is None:
        # Read the canonical hub-free witness instead, retaining exact row data.
        pair=read('runs/hubfree_search_v1/best.json')
        arrays=[table(pair[w]['graph']['rows'],18) for w in ['bad','good']]
    else:
        arrays=[table(best[w]['rows'],9) for w in ['a','b']]
    fig=plt.figure(figsize=(14,4.6),facecolor='#0b1427')
    bg=fig.add_axes([0,0,1,1]);bg.set_axis_off()
    fig.text(.045,.87,'TWENTY QUESTIONS  /  GRAPH SEPARATION',color='#7dd3c7',size=11,weight='bold')
    fig.text(.044,.61,'Same statistics.\nDifferent search costs.',color='white',size=31,weight='bold',linespacing=1.22)
    fig.text(.046,.43,'Exact counterexamples to information-gain greedy',color='#b7c6dc',size=12)
    fig.text(.046,.355,'Pairwise statistics stay fixed. Adaptive costs separate.',color='#879bb8',size=11)
    cmap=LinearSegmentedColormap.from_list('hero',['#162641','#72d6ca'])
    for k,a in enumerate(arrays):
        ax=fig.add_axes([.70+k*.13,.35,.11,.44]);ax.imshow(a,cmap=cmap,aspect='auto',interpolation='nearest');ax.set_axis_off()
        ax.set_title('A' if k==0 else 'B',color='#b7c6dc',size=11,pad=7)
    fig.text(.745,.285,'IDENTICAL GRAM',color='#7dd3c7',size=10,weight='bold')
    fig.text(.045,.16,'38 × 18',color='white',size=22,weight='bold')
    fig.text(.045,.09,'EXACT CONNECTED WITNESS',color='#879bb8',size=9)
    fig.text(.31,.16,'N / 578 + O(1)',color='white',size=22,weight='bold')
    fig.text(.31,.09,'PROVED CONTRAST · UNIFORM TIES',color='#879bb8',size=9)
    fig.text(.68,.16,'1,223',color='white',size=22,weight='bold')
    fig.text(.68,.09,'PRESERVED CONTROLLED PAIRS',color='#879bb8',size=9)
    save(fig,'hero')


def graph_pair():
    pair=read('runs/hubfree_search_v1/best.json')
    rows=[pair[w]['graph']['rows'] for w in ['bad','good']]
    common=set(map(tuple,rows[0]))&set(map(tuple,rows[1]))
    fig,axs=plt.subplots(1,3,figsize=(17,6),gridspec_kw={'width_ratios':[1,1,1.08]},layout='constrained')
    for ax,rr,name,color in zip(axs[:2],rows,['A · greedy loss','B · zero greedy loss'],[BLUE,TEAL]):
        qp={q:(0 if q<9 else 5,8-2*(q%9)) for q in range(18)}
        op={i:(1.55 if i<18 else 3.45,8.5-17*(i%18)/17) for i in range(36)}
        op.update({36:(2.5,9.6),37:(2.5,-9.6)})
        for i,r in enumerate(rr):
            changed=tuple(r) not in common
            for q in r:
                ax.plot([qp[q][0],op[i][0]],[qp[q][1],op[i][1]],color=color if changed else '#b7c4d4',
                        alpha=.80 if changed else .42,lw=1.5 if changed else .75,zorder=1)
        for q,(x,y) in qp.items():
            root=q in [3,12]
            ax.scatter(x,y,s=120,c=color if root else 'white',edgecolor=color if root else '#94a3b8',lw=1.1,zorder=3)
            ax.text(x+(-.17 if q<9 else .17),y,f'q{q}',ha='right' if q<9 else 'left',va='center',fontsize=8.5,color=INK)
        for i,(x,y) in op.items():
            ax.scatter(x,y,s=28,c=color if tuple(rr[i]) not in common else '#f1f5f9',edgecolor=color if tuple(rr[i]) not in common else '#94a3b8',lw=.7,zorder=3)
        ax.set(xlim=(-.85,5.85),ylim=(-10.5,10.8));ax.set_axis_off();ax.set_title(name,color=color,size=15,pad=10)
        regret=pair['bad' if color==BLUE else 'good']['graph']['greedy']['gap_exact']
        ax.text(.5,-.02,f'38 objects · 18 questions · regret {regret}',transform=ax.transAxes,ha='center',size=10,color=MUTED)
    a,b=[table(r,18) for r in rows];assert np.array_equal(a.T@a,b.T@b)
    ax=axs[2];im=ax.imshow(a.T@a,cmap=LinearSegmentedColormap.from_list('gram',['#f4f8fb','#bfdedc','#187c78']),vmin=0,vmax=10)
    ax.set_title('One shared question Gram matrix',size=13,pad=16)
    ax.set(xticks=[0,3,8,12,17],yticks=[0,3,8,12,17],xlabel='Question index',ylabel='Question index')
    for v in [8.5]:ax.axhline(v,color='white',lw=1.4);ax.axvline(v,color='white',lw=1.4)
    fig.colorbar(im,ax=ax,shrink=.56,label='Joint yes count')
    ax.text(.5,-.18,'Distinct degree-3 rows · max question degree 10\nBoth incidence graphs have no articulation vertex',transform=ax.transAxes,ha='center',size=10,color=MUTED,linespacing=1.5)
    save(fig,'counterexample-38')


def results():
    pair=read('runs/hubfree_search_v1/best.json')
    p=ROOT/'research/runs/main/report/paired_comparisons.csv';SOURCES[p.relative_to(ROOT/'research').as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    with p.open(encoding='utf-8-sig',newline='') as f:comparisons=list(csv.DictReader(f))
    fig,axs=plt.subplots(1,3,figsize=(17,5.4),layout='constrained')
    ax=axs[0];x=np.arange(2)
    optimum=[pair[w]['graph']['exact']['optimal_total']/38 for w in ['bad','good']]
    greedy=[float(Fraction(pair[w]['graph']['greedy']['total_uniform_exact']))/38 for w in ['bad','good']]
    ax.bar(x-.17,optimum,.33,color=TEAL,label='Exact optimal')
    ax.bar(x+.17,greedy,.33,color=ORANGE,label='Exact greedy')
    ax.set(xticks=x,xticklabels=['World A','World B'],ylim=(0,6.6),ylabel='Mean questions to identification')
    ax.set_title('Finite witness · exact DP',size=13,loc='left',pad=18)
    ax.legend(loc='upper left',frameon=False,fontsize=9,ncol=2)
    ax.text(.5,-.20,'Regret contrast = 13/76\nUniform greedy ties; every root is optimal',transform=ax.transAxes,ha='center',size=10,color=MUTED)
    ax=axs[1];t=np.linspace(76,256,181);n=17*t
    lower=(t-69)/34-235/(17*t);upper=(t+63)/34+235/(17*t)
    ax.fill_between(n,lower,upper,color='#d9e9eb',label='Proved finite interval')
    ax.plot(n,n/578,color=TEAL,lw=2,label='Leading contrast N/578')
    ax.set(xlabel='Objects N = 17T',ylabel='Regret(B) − regret(A)');ax.grid(axis='y',alpha=.15)
    ax.set_title('Expanding family · theorem',size=13,loc='left',pad=18);ax.legend(frameon=False,fontsize=9,loc='upper left')
    ax.text(.5,-.20,'Proof bounds, not large-instance DP measurements\nUniform ties · degree ≤ 10 · no global hub',transform=ax.transAxes,ha='center',size=10,color=MUTED)
    ax=axs[2];selected=[next(r for r in comparisons if r['split']=='test' and r['seed']=='41' and r['baseline']==m) for m in ['information_gain','lookahead2','lookahead3']]
    for i,r in enumerate(selected):
        mean,lo,hi=[float(r[k]) for k in ['mean_difference','ci_low','ci_high']]
        ax.errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt='o',color=BLUE if i==2 else '#93a5b9',capsize=4,lw=2,ms=7)
    ax.axvline(0,color='#aab6c4',ls='--',lw=1)
    ax.set(yticks=[0,1,2],yticklabels=['vs. IG','vs. depth 2','vs. depth 3'],xlabel='First-question regret difference (ML − baseline)',ylim=(2.6,-.6))
    ax.set_title('ML · paired uncertainty',size=13,loc='left',pad=18);ax.grid(axis='x',alpha=.15)
    ax.ticklabel_format(axis='x',style='sci',scilimits=(-3,-3))
    ax.text(.5,-.20,'179 held-out parents · 95% paired bootstrap CI\nDepth-3 interval contains zero',transform=ax.transAxes,ha='center',size=10,color=MUTED)
    save(fig,'results')


def lift():
    fig,ax=plt.subplots(figsize=(13.5,3.6),layout='constrained')
    ax.set(xlim=(-.7,10.7),ylim=(-1.6,1.95));ax.set_axis_off()
    for x,name in [(0,'BLOCK v'),(10,'BLOCK w')]:
        ax.add_patch(FancyBboxPatch((x-.45,-1.32),.9,2.65,boxstyle='round,pad=.18',fc='#f3f6fc',ec='#dae2ef'))
        ax.text(x,1.65,name,ha='center',size=12,weight='bold',color=MUTED)
        for y,q in [(1,'0'),(0,'5'),(-1,'6')]:
            ax.add_patch(Circle((x,y),.22,fc='white',ec=BLUE,lw=1.2,zorder=3));ax.text(x,y,f'q{q}',ha='center',va='center',size=11,zorder=4)
    for x,y,text,color in [(4.1,.65,'c(v → w)',TEAL),(5.9,-.65,'c(w → v)',ORANGE)]:
        ax.add_patch(FancyBboxPatch((x-.6,y-.25),1.2,.5,boxstyle='round,pad=.1',fc='white',ec=color,lw=1.8,zorder=3))
        ax.text(x,y,text,ha='center',va='center',color=color,size=12,zorder=4)
    for xs,ys,col in [([0,4.1],[1,.65],TEAL),([0,4.1],[0,.65],TEAL),([10,4.1],[-1,.65],TEAL),
                      ([10,5.9],[1,-.65],ORANGE),([10,5.9],[0,-.65],ORANGE),([0,5.9],[-1,-.65],ORANGE)]:
        ax.plot(xs,ys,color=col,lw=1.8,alpha=.8,zorder=1)
    ax.text(5,1.53,'Identical connector rows in both worlds',ha='center',weight='bold',size=14)
    ax.text(5,-1.42,'One base pair per skeleton vertex · two rows per undirected edge · no shared global question',ha='center',color=MUTED,size=11)
    save(fig,'bounded-degree-lift')


def main():
    OUT.mkdir(exist_ok=True)
    hero();graph_pair();results();lift()
    (OUT/'provenance.json').write_text(json.dumps(dict(generator='scripts/make_assets.py',
        source_sha256=SOURCES,scope='Presentation regenerated from saved results; no new scientific measurements'),indent=2)+'\n',encoding='utf-8')
    print('Rendered four figure pairs (PNG + SVG) from preserved research.')


if __name__=='__main__':main()
