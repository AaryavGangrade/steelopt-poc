"""Educational 2D rectangular nesting + offcut decision support (NOT CNC software)."""
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass(frozen=True)
class Stock:
    id: str
    project: str
    width: int
    height: int
    grade: str
    thickness: int
    kind: str = 'plate'
    status: str = 'available'
    traceable: bool = True
    unit_cost_per_m2: float = 0.0

@dataclass(frozen=True)
class Part:
    id: str
    project: str
    width: int
    height: int
    grade: str
    thickness: int
    allow_rotation: bool = True

@dataclass(frozen=True)
class Placement:
    stock_id: str
    part_id: str
    x: int
    y: int
    width: int
    height: int
    rotated: bool


def compatible(stock: Stock, part: Part) -> bool:
    return (stock.grade == part.grade and stock.thickness == part.thickness
            and stock.status == 'available' and stock.traceable)


def validate_layout(stock: Stock, parts: list[Part], placements: list[Placement], kerf: int = 5) -> list[str]:
    """Checks bounds, exact part identity and conservative pairwise kerf clearance."""
    errors = []
    lookup = {p.id: p for p in parts}
    seen = set()
    for a in placements:
        p = lookup.get(a.part_id)
        if not p or a.part_id in seen:
            errors.append(f'{a.part_id}: unknown or duplicate part')
            continue
        seen.add(a.part_id)
        if a.stock_id != stock.id or not compatible(stock, p):
            errors.append(f'{a.part_id}: invalid stock or incompatible material')
        if (a.width, a.height) not in ([(p.width,p.height),(p.height,p.width)] if p.allow_rotation else [(p.width,p.height)]):
            errors.append(f'{a.part_id}: dimensions/rotation mismatch')
        if a.x < 0 or a.y < 0 or a.x+a.width > stock.width or a.y+a.height > stock.height:
            errors.append(f'{a.part_id}: out of bounds')
    for i, a in enumerate(placements):
        for b in placements[i+1:]:
            if not (a.x+a.width+kerf <= b.x or b.x+b.width+kerf <= a.x
                    or a.y+a.height+kerf <= b.y or b.y+b.height+kerf <= a.y):
                errors.append(f'{a.part_id}/{b.part_id}: collision or insufficient kerf')
    return errors


def pack_shelves(stock: Stock, parts: list[Part], kerf: int = 5, sort: bool = True) -> tuple[list[Placement], list[str]]:
    """Simple deterministic shelf heuristic. For demonstrative comparison only."""
    if kerf < 0: raise ValueError('kerf must be >=0')
    pending = sorted(parts, key=lambda p:(-max(p.width,p.height), -p.width*p.height, p.id)) if sort else parts
    shelves = []  # (y, used_x, shelf_height)
    placements, missing = [], []
    for part in pending:
        if not compatible(stock, part):
            missing.append(part.id)
            continue
        orientations = [(part.width,part.height,False)]
        if part.allow_rotation and part.width != part.height:
            orientations.append((part.height,part.width,True))
        candidates = []
        for si,(sy,sx,sh) in enumerate(shelves):
            for w,h,rot in orientations:
                if h <= sh and sx+w <= stock.width:
                    candidates.append((sy, sx, rot, si, w, h))
        if candidates:
            sy,sx,rot,si,w,h = min(candidates)
            placements.append(Placement(stock.id,part.id,sx,sy,w,h,rot))
            shelves[si] = (sy,sx+w+kerf,shelves[si][2])
            continue
        new_y = 0 if not shelves else shelves[-1][0]+shelves[-1][2]+kerf
        fits = [(h*w,h,w,rot) for w,h,rot in orientations if w <= stock.width and new_y+h <= stock.height]
        if not fits:
            missing.append(part.id)
            continue
        _,h,w,rot = min(fits)
        placements.append(Placement(stock.id,part.id,0,new_y,w,h,rot))
        shelves.append((new_y,w+kerf,h))
    errors = validate_layout(stock,parts,placements,kerf)
    if errors: raise AssertionError('Algorithm produced invalid layout: '+str(errors))
    return placements, missing


def layout_stats(stock: Stock, placements: list[Placement]) -> dict:
    area = stock.width*stock.height
    used = sum(p.width*p.height for p in placements)
    return {'stock_id':stock.id, 'part_count':len(placements), 'part_area_m2':round(used/1e6,4),
            'stock_area_m2':round(area/1e6,4),'utilization_pct':round(100*used/area,2),
            'unallocated_area_m2':round((area-used)/1e6,4)}


def offcut_matches(parts: list[Part], stock: list[Stock], kerf: int = 5) -> list[dict]:
    """Candidates ONLY; no reservation or accounting transfer is ever made."""
    results=[]
    for p in parts:
        for s in stock:
            if s.kind != 'offcut' or not compatible(s,p): continue
            orientations=[(p.width,p.height)]
            if p.allow_rotation: orientations.append((p.height,p.width))
            # Single part in an offcut: dimensions already describe usable surface;
            # kerf margin required along both edges as a conservative assumption.
            if not any(w+kerf <= s.width and h+kerf <= s.height for w,h in orientations): continue
            cross=s.project != p.project
            results.append({'part_id':p.id,'part_project':p.project,'offcut_id':s.id,
                            'owner_project':s.project,'cross_project':cross,
                            'geometry_material_match':True,
                            'decision':'PENDING_COST_CONTROL_APPROVAL' if cross else 'PENDING_NESTER_APPROVAL',
                            'gross_part_area_m2':round(p.width*p.height/1e6,4),
                            'illustrative_area_value':round(p.width*p.height/1e6*s.unit_cost_per_m2,2),
                            'realized_savings':None})
    return sorted(results,key=lambda r:(r['part_id'],r['cross_project'],r['offcut_id']))


def plot_layout(ax, stock: Stock, placements: list[Placement], title: str):
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((0,0),stock.width,stock.height,facecolor='#e8ecf0',edgecolor='#28313b',linewidth=2))
    colors=['#A9D2F5','#7CC8B5','#EBCB8B','#B7A9E8','#F5B4A8']
    for i,p in enumerate(placements):
        ax.add_patch(Rectangle((p.x,p.y),p.width,p.height,facecolor=colors[i%len(colors)],edgecolor='#27364a',linewidth=1.2))
        ax.text(p.x+p.width/2,p.y+p.height/2,p.part_id,ha='center',va='center',fontsize=8)
    ax.set_xlim(-60,stock.width+60);ax.set_ylim(stock.height+60,-60)
    ax.set_aspect('equal');ax.set_title(title);ax.set_xlabel('mm');ax.set_ylabel('mm')
