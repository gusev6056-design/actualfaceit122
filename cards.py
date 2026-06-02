from PIL import Image, ImageDraw, ImageFont
import io, math, random

FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG      = (10,  14,  24)
CARD    = (18,  24,  38)
CARD2   = (24,  31,  48)
BORDER  = (38,  50,  72)
ORANGE  = (255, 165,  0)
ORANGE2 = (255, 140,  0)
PINK    = (210,  50, 190)
PURPLE  = (148,  68, 210)
GREEN   = ( 45, 200,  95)
RED     = (210,  55,  68)
BLUE    = ( 75, 148, 235)
WHITE   = (215, 222, 235)
DIM     = ( 88, 105, 130)
GOLD_R  = ( 40,  30,   8)
GOLD_B  = ( 80,  60,  15)
CYAN    = (  0, 200, 220)

ANIME_COLORS = [(255,60,140),(140,60,255),(60,140,255),(255,200,60),(60,220,200)]

BADGE_COLORS  = {"admin":((80,40,150),WHITE),"lowtab":((30,140,60),WHITE),
                 "wheelchair":((80,80,80),WHITE),"premium":((160,110,0),WHITE)}
BADGE_LABELS  = {"admin":"⚙ Администратор","lowtab":"✓ Лоутаб",
                 "wheelchair":"♿ Инвалид","premium":"★ PREMIUM"}

MAP_COLORS = {"Breeze":BLUE,"Rust":ORANGE,"Province":PURPLE,"Sakura":PINK,"Sandstone":ORANGE2}

LEVEL_COLORS = [(148,68,210),(45,200,95),(45,200,95),(75,148,235),(75,148,235),
                (255,140,0),(255,140,0),(255,60,60),(255,60,60),(255,60,140)]

def F(size, bold=False):
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)
    except Exception:
        return ImageFont.load_default(size=size)

def rr(draw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def textw(draw, t, f):
    b = draw.textbbox((0,0), t, font=f); return b[2]-b[0], b[3]-b[1]

def tcx(draw, t, f, fill, cx, y):
    w, _ = textw(draw, t, f); draw.text((cx-w//2, y), t, fill=fill, font=f)

def logo(draw, W, y=18):
    f1=F(18,True); f2=F(13,True); f3=F(10)
    bx=W-125
    rr(draw, [(bx,y),(bx+34,y+34)], 7, fill=PINK)
    tcx(draw,"F",f1,WHITE,bx+17,y+6)
    draw.text((bx+42,y+2),"FLITE",fill=WHITE,font=f2)
    draw.text((bx+42,y+18),"FACEIT",fill=DIM,font=f3)

def pill(draw, x, y, text, bg, fg, size=13, bold=False, px=13, py=5):
    f=F(size,bold); tw,th=textw(draw,text,f); w,h=tw+px*2,th+py*2
    rr(draw,[(x,y),(x+w,y+h)],h//2,fill=bg); draw.text((x+px,y+py),text,fill=fg,font=f)
    return w+6

def pill_out(draw, x, y, text, oc, fg, size=12, bold=False, px=10, py=4):
    f=F(size,bold); tw,th=textw(draw,text,f); w,h=tw+px*2,th+py*2
    rr(draw,[(x,y),(x+w,y+h)],h//2,fill=CARD2,outline=oc,width=1)
    draw.text((x+px,y+py),text,fill=fg,font=f); return w+6

def bar(draw, x, y, w, h, pct, color):
    rr(draw,[(x,y),(x+w,y+h)],h//2,fill=(35,45,65))
    fw=int(w*min(max(pct,0),1))
    if fw>4: rr(draw,[(x,y),(x+fw,y+h)],h//2,fill=color)

def donut(draw, cx, cy, r, pct, color):
    draw.arc([(cx-r,cy-r),(cx+r,cy+r)],0,360,fill=(40,52,72),width=10)
    ang=int(360*min(pct,1.0))
    if ang>0: draw.arc([(cx-r,cy-r),(cx+r,cy+r)],-90,-90+ang,fill=color,width=10)

def level_color(lv):
    return LEVEL_COLORS[max(0,min(int(lv)-1,9))]

# ── Anime helpers ───────────────────────────────────────────

def draw_anime_banner(img, draw, W, y_start, banner_h):
    colors=[(255,40,120),(180,40,255),(60,120,255),(0,200,220)]
    seg=W//len(colors)
    for i,col in enumerate(colors):
        x0=i*seg; x1=x0+seg+2
        for row in range(banner_h):
            a=int(180*(1-row/banner_h))
            bl=tuple(int(BG[j]+(col[j]-BG[j])*a/255) for j in range(3))
            draw.line([(x0,y_start+row),(x1,y_start+row)],fill=bl)
    for i in range(0,W,28):
        oc=ANIME_COLORS[i%len(ANIME_COLORS)]; sz=3+(i%5)
        cx=i+14; cy=y_start+banner_h//2
        draw.ellipse([(cx-sz,cy-sz),(cx+sz,cy+sz)],fill=oc)
    draw.line([(0,y_start),(W,y_start)],fill=(255,60,200),width=2)
    draw.line([(0,y_start+banner_h-1),(W,y_start+banner_h-1)],fill=(100,60,255),width=1)
    for i in range(0,W,60):
        pts=[(i,y_start+banner_h),(i+20,y_start),(i+40,y_start+banner_h)]
        oc2=ANIME_COLORS[(i//60)%len(ANIME_COLORS)]; draw.polygon(pts,fill=oc2)

def draw_anime_side_banners(draw, W, y_top, h, left=True, right=True):
    sw=4
    if left:
        for i,col in enumerate([(255,40,120),(180,40,255)]):
            draw.rectangle([(i*sw,y_top),((i+1)*sw,y_top+h)],fill=col)
    if right:
        for i,col in enumerate([(0,200,220),(60,255,160)]):
            draw.rectangle([(W-(i+1)*sw,y_top),(W-i*sw,y_top+h)],fill=col)

def draw_anime_eye_banner(img, draw, W, H_banner):
    """Full-width anime eye/energy banner for profile top."""
    # Gradient background - deep blue/purple
    for y in range(H_banner):
        t = y / H_banner
        r = int(5 + 20*t)
        g = int(8 + 30*t)
        b = int(20 + 60*t)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Large eye circle (right side)
    ecx, ecy = int(W*0.75), H_banner//2
    for radius in range(90, 10, -12):
        alpha = int(255*(1-radius/90))
        col = (0, int(120+alpha//3), int(220+alpha//5))
        draw.ellipse([(ecx-radius,ecy-radius),(ecx+radius,ecy+radius)],
                     outline=col, width=2)

    # Iris detail
    draw.ellipse([(ecx-35,ecy-50),(ecx+35,ecy+50)], fill=(0,60,140), outline=(0,160,255), width=2)
    draw.ellipse([(ecx-15,ecy-22),(ecx+15,ecy+22)], fill=(0,20,80))
    # Highlight
    draw.ellipse([(ecx+8,ecy-30),(ecx+22,ecy-16)], fill=(180,220,255))

    # Energy lines from left to eye
    random.seed(42)
    for _ in range(18):
        x0 = random.randint(0, W//2)
        y0 = random.randint(0, H_banner)
        col_i = ANIME_COLORS[_%len(ANIME_COLORS)]
        draw.line([(x0,y0),(ecx,ecy)], fill=(*col_i[:3],), width=1)

    # Crystal shards (top-left decorations)
    for i,col in enumerate([(0,180,255),(120,60,220),(255,60,140)]):
        pts = [(40+i*25, 8), (50+i*25, 30), (35+i*25, 30)]
        draw.polygon(pts, fill=col, outline=WHITE)

    # Bottom glow line
    for x in range(W):
        t = abs(x - W//2)/(W//2)
        g = int(200*(1-t))
        draw.point((x, H_banner-2), fill=(0, g, 255))
    draw.line([(0,H_banner-1),(W,H_banner-1)], fill=(0,100,255), width=2)

def draw_crystal_frame(draw, x, y, size):
    """Crystal/gem avatar frame."""
    col_outer = (0, 160, 255)
    col_inner = (0, 80, 180)
    # Glow rings
    for off in range(5,0,-1):
        gc = tuple(max(0,c-off*20) for c in col_outer)
        rr(draw,[(x-off,y-off),(x+size+off,y+size+off)],14,outline=gc,width=1)
    rr(draw,[(x,y),(x+size,y+size)],12,fill=(8,16,36),outline=col_outer,width=3)
    # Corner gems
    gem_positions = [(x,y),(x+size-12,y),(x,y+size-12),(x+size-12,y+size-12)]
    gem_colors = [(0,200,255),(100,60,255),(255,60,120),(0,255,180)]
    for (gx,gy),gc in zip(gem_positions, gem_colors):
        draw.polygon([(gx+6,gy),(gx+12,gy+6),(gx+6,gy+12),(gx,gy+6)], fill=gc)
    # Top decoration line
    draw.line([(x+14,y-4),(x+size-14,y-4)], fill=col_outer, width=2)
    draw.ellipse([(x+size//2-4,y-8),(x+size//2+4,y)], fill=col_outer)

def draw_anime_bottom_banner(draw, W, y, h=24):
    colors=[(60,120,255),(180,40,255),(255,40,120)]
    seg=W//len(colors)
    for i in range(W):
        seg_i=min(i//seg,len(colors)-2); t=(i-seg_i*seg)/seg
        c1,c2=colors[seg_i],colors[seg_i+1]
        col=tuple(int(c1[j]+(c2[j]-c1[j])*t) for j in range(3))
        draw.line([(i,y),(i,y+2)],fill=col)
    for i in range(0,W,40):
        draw.ellipse([(i-2,y+6),(i+2,y+10)],fill=ANIME_COLORS[i%len(ANIME_COLORS)])

def _out(img):
    out=io.BytesIO(); img.save(out,format='PNG'); out.seek(0); return out


# ══════════════════════════════════════════════════════════════
#  PROFILE CARD
# ══════════════════════════════════════════════════════════════

def create_profile_card(player, stats, badges=None, league_label="Общая"):
    if badges is None: badges=[]
    W, H = 780, 1340
    img  = Image.new('RGB',(W,H),BG)
    d    = ImageDraw.Draw(img)

    # ── Anime eye banner ──
    BANNER_H = 110
    draw_anime_eye_banner(img, d, W, BANNER_H)

    # Logo
    d.text((16,10),"⚡ FLITE FACEIT",fill=WHITE,font=F(18,True))
    d.text((16,34),"PLAYER PROFILE",fill=(180,60,220),font=F(12,True))
    logo(d, W, 14)

    draw_anime_side_banners(d, W, BANNER_H, H-BANNER_H)

    y = BANNER_H+8

    # ── Avatar + crystal frame ──
    AVS = 84
    draw_crystal_frame(d, 14, y, AVS)
    tcx(d,"★",F(28,True),ORANGE,14+AVS//2,y+22)

    nx = 14+AVS+18
    username = str(player[1]) if player[1] else "Player"
    d.text((nx,y+2),username[:20],fill=WHITE,font=F(22,True))

    # Calibration badge or ELO
    from database import is_calibrated, calib_count, CALIB_THRESHOLD
    calibrated = is_calibrated(player)
    calib      = calib_count(player)
    elo_val    = stats.get('elo',1000)
    lvl_val    = stats.get('level',1)
    lc         = level_color(lvl_val)

    rr(d,[(nx,y+30),(nx+50,y+46)],6,fill=lc)
    tcx(d,f"LV{lvl_val}",F(11,True),WHITE,nx+25,y+32)

    ex=nx+58
    if calibrated:
        rr(d,[(ex,y+30),(ex+85,y+46)],6,fill=(40,34,8))
        d.text((ex+6,y+32),f"{elo_val} ELO",fill=ORANGE,font=F(11,True))
    else:
        rr(d,[(ex,y+30),(ex+120,y+46)],6,fill=(30,20,50))
        d.text((ex+6,y+32),f"КАЛИБРОВКА {calib}/{CALIB_THRESHOLD}",fill=PURPLE,font=F(11,True))

    # Badges
    bx=nx; by=y+52
    for bid in badges:
        if bid in BADGE_LABELS:
            label=BADGE_LABELS[bid]; bg_c,fg_c=BADGE_COLORS.get(bid,(CARD2,WHITE))
            bx+=pill(d,bx,by,label,bg_c,fg_c,11,True,8,4)
    bx=nx; by+=20 if badges else 0

    device=str(player[3]) if player[3] else "MOBILE"
    pill_out(d,bx,by,device,DIM,DIM,11)

    qual=player[19] if len(player)>19 and player[19] else None
    if qual: pill(d,W-140,y+10,qual,PURPLE,WHITE,11,True)

    game_id=str(player[2]) if player[2] else "0"
    d.text((nx,y+AVS-18),f"ID: #{game_id}",fill=DIM,font=F(11))

    y+=AVS+20
    # League tab row
    draw_anime_bottom_banner(d,W,y); y+=30

    rr(d,[(10,y),(W-10,y+52)],10,fill=CARD)
    d.text((20,y+8),f"💰 {stats.get('coins',0)} монет",fill=ORANGE,font=F(13))
    d.text((200,y+8),f"Матчей: {stats.get('games',0)}",fill=WHITE,font=F(13))
    d.text((20,y+28),f"Устройство: {device}",fill=DIM,font=F(12))
    d.text((200,y+28),f"Лига: {qual or 'Default'}",fill=WHITE,font=F(12))
    league_color=(PURPLE if league_label!="Общая" else DIM)
    pill(d,W-170,y+14,f"★ {league_label}",CARD2,league_color,11,True)
    y+=62

    # ── Stats ──
    d.text((14,y),"СТАТИСТИКА",fill=WHITE,font=F(15,True))
    draw_anime_bottom_banner(d,W,y+22,3); y+=30

    kills=stats.get('kills',0); deaths=stats.get('deaths',0)
    assists=stats.get('assists',0); kd=stats.get('kd',0.0)
    winrate=stats.get('winrate',0.0); games=stats.get('games',0)
    mvp=stats.get('mvp',0); headshots=stats.get('headshots',0.0)
    wins=stats.get('wins',0); losses=stats.get('losses',0)

    stat_boxes=[("УБИЙСТВ",str(kills),GREEN),("СМЕРТЕЙ",str(deaths),RED),
                ("ASSISTS",str(assists),WHITE),("K/D",f"{kd:.2f}",ORANGE),
                ("WINRATE",f"{winrate:.1f}%",GREEN if winrate>=50 else RED),
                ("МАТЧЕЙ",str(games),WHITE),("MVP",str(mvp),WHITE),
                ("HEADSHOTS",f"{headshots:.1f}%",ORANGE)]
    box_w=(W-28-18)//4
    for i,(label,val,col) in enumerate(stat_boxes):
        ci=i%4; ri=i//4
        bx3=14+ci*(box_w+6); by3=y+ri*74
        ac=ANIME_COLORS[i%len(ANIME_COLORS)]
        rr(d,[(bx3,by3),(bx3+box_w,by3+68)],10,fill=CARD,outline=ac,width=1)
        d.rectangle([(bx3,by3),(bx3+box_w,by3+3)],fill=col)
        d.text((bx3+8,by3+8),label,fill=DIM,font=F(11))
        d.text((bx3+8,by3+26),val,fill=col,font=F(20,True))
    y+=160

    # ── Detailed stats ──
    d.text((14,y),"ДЕТАЛЬНАЯ СТАТИСТИКА",fill=WHITE,font=F(15,True))
    draw_anime_bottom_banner(d,W,y+22,3); y+=30

    rr(d,[(14,y),(155,y+130)],12,fill=CARD,outline=PINK,width=1)
    donut(d,84,y+65,42,min(kd/5,1.0),ORANGE)
    tcx(d,f"{kd:.2f}",F(18,True),WHITE,84,y+46)
    tcx(d,f"K={kills} D={deaths}",F(10),DIM,84,y+76)

    avg_pm=round(kills/max(games*13,1)*10,2)
    det=[("Rating",f"{kd:.2f}","Strong" if kd>=1 else "Weak",ORANGE if kd>=1 else RED,min(kd/3,1.0)),
         ("AVG",f"{avg_pm}","Strong",GREEN,min(avg_pm/30,1.0)),
         ("Impact",f"{kd*0.9:.2f}","Strong" if kd>=1 else "Weak",GREEN if kd>=1 else RED,min(kd*0.9/3,1.0)),
         ("KPR",f"{kills/max(games*13,1):.2f}","Normal",BLUE,min(kills/max(games*13,1),1.0)),
         ("Assists",str(assists),"Normal",BLUE,min(assists/max(games*5,1),1.0)),
         ("SVR","0.00","Low",RED,0.0)]
    sw=(W-28-162)//3
    for i,(lbl,val,grade,gcol,pct) in enumerate(det):
        ci=i%3; ri=i//3
        bx3=170+ci*(sw+6); by3=y+ri*64
        rr(d,[(bx3,by3),(bx3+sw,by3+58)],10,fill=CARD)
        d.text((bx3+8,by3+6),lbl,fill=DIM,font=F(11))
        d.text((bx3+8,by3+20),val,fill=WHITE,font=F(16,True))
        bar(d,bx3+8,by3+40,sw-16,6,pct,gcol)
        d.text((bx3+8,by3+44),grade,fill=gcol,font=F(10))
    y+=142

    # ── Map stats ──
    d.text((14,y),"MAP STATISTIC",fill=WHITE,font=F(15,True))
    draw_anime_bottom_banner(d,W,y+22,3); y+=30
    maps_data=[("Breeze",BLUE),("Rust",ORANGE),("Province",PURPLE),("Sakura",PINK),("Sandstone",ORANGE2)]
    mw=(W-28-16)//5
    for i,(mname,mcol) in enumerate(maps_data):
        mx=14+i*(mw+4)
        rr(d,[(mx,y),(mx+mw,y+90)],10,fill=CARD,outline=mcol,width=1)
        d.rectangle([(mx,y),(mx+mw,y+4)],fill=mcol)
        d.text((mx+6,y+10),mname,fill=WHITE,font=F(10,True))
        d.text((mx+6,y+28),"Матчей",fill=DIM,font=F(9))
        d.text((mx+6,y+42),"—",fill=WHITE,font=F(13,True))
    y+=106

    # ── League ──
    rr(d,[(14,y),(W-14,y+80)],12,fill=CARD,outline=PURPLE,width=1)
    d.rectangle([(14,y),(W-14,y+4)],fill=PURPLE)
    d.text((26,y+10),"Лига",fill=DIM,font=F(11))
    d.text((26,y+26),qual if qual else "Default",fill=WHITE,font=F(20,True))
    d.text((26,y+52),"ⓘ Позиция появится после калибровки",fill=DIM,font=F(11))
    y+=96

    # ── Footer ──
    draw_anime_banner(img,d,W,H-36,36)
    d.text((14,H-24),"⚡ FLITE FACEIT · Season 4",fill=WHITE,font=F(11,True))
    d.text((W-145,H-24),"Made with Replit",fill=DIM,font=F(10))

    return _out(img)


# ══════════════════════════════════════════════════════════════
#  MAP VETO CARD
# ══════════════════════════════════════════════════════════════

def create_map_card(lobby, map_stats_data=None):
    if map_stats_data is None: map_stats_data={}
    map_pool=lobby.get("map_pool",[])
    bans=lobby.get("bans",[])
    all_maps=lobby.get("all_maps",map_pool+[b["map"] for b in bans])

    from database import get_player
    ct_p=get_player(lobby.get("captain_ct")) if lobby.get("captain_ct") else None
    t_p =get_player(lobby.get("captain_t"))  if lobby.get("captain_t")  else None
    ct_name=ct_p[1] if ct_p else "CT Капитан"
    t_name =t_p[1]  if t_p  else "T Капитан"
    ct_elo=ct_p[5] if ct_p else 1000; ct_lv=ct_p[4] if ct_p else 1
    t_elo =t_p[5]  if t_p  else 1000; t_lv =t_p[4]  if t_p  else 1

    map_h=80; W=680
    H=70+130+len(all_maps)*(map_h+8)+50
    img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)

    draw_anime_banner(img,d,W,0,60)
    d.text((16,10),"⚡ FLITE FACEIT",fill=WHITE,font=F(16,True))
    d.text((16,32),"MAP VETO",fill=PINK,font=F(22,True))
    logo(d,W,10); draw_anime_side_banners(d,W,60,H-60); y=68

    rr(d,[(12,y),(W-12,y+122)],12,fill=CARD,outline=BORDER,width=1)
    d.text((24,y+8),"КАПИТАНЫ",fill=DIM,font=F(12,True))
    half=(W-36)//2
    for side,(name,elo,lv,label,scol) in enumerate([
        (ct_name,ct_elo,ct_lv,"CT",(0,60,180)),
        (t_name, t_elo, t_lv, "T", (180,30,0))
    ]):
        lc=level_color(lv)
        tx=24+side*(half+8)
        rr(d,[(tx,y+28),(tx+half,y+114)],10,fill=CARD2,outline=lc,width=2)
        d.rectangle([(tx,y+28),(tx+half,y+32)],fill=lc)
        pill(d,tx+6,y+36,label,scol,WHITE,11,True)
        d.text((tx+46,y+36),name[:16],fill=WHITE,font=F(15,True))
        rr(d,[(tx+6,y+58),(tx+48,y+74)],6,fill=lc)
        tcx(d,f"LV{lv}",F(11,True),WHITE,tx+27,y+60)
        d.text((tx+58,y+60),f"{elo} ELO",fill=ORANGE,font=F(12))
    y+=130

    banned_maps={b["map"] for b in bans}
    for mname in all_maps:
        mcol=MAP_COLORS.get(mname,BLUE)
        is_banned=mname in banned_maps
        is_final=(len(map_pool)==1 and mname==map_pool[0])
        mstats=map_stats_data.get(mname,{})
        pick_pct=mstats.get("pick_pct",0.0)
        ct_wr=mstats.get("ct_wr",50.0); t_wr=mstats.get("t_wr",50.0)
        played=mstats.get("times_played",0)

        fill_col=(25,28,42) if is_banned else CARD
        border_c=RED if is_banned else (ORANGE if is_final else mcol)
        bw=3 if is_final else (2 if is_banned else 1)
        rr(d,[(12,y),(W-12,y+map_h)],12,fill=fill_col,outline=border_c,width=bw)
        if not is_banned: d.rectangle([(12,y),(17,y+map_h)],fill=mcol)

        icon_x=26
        rr(d,[(icon_x,y+14),(icon_x+42,y+54)],8,
           fill=mcol if not is_banned else (60,30,30))
        tcx(d,mname[:2].upper(),F(14,True),(120,60,60) if is_banned else WHITE,icon_x+21,y+24)

        name_x=icon_x+52
        d.text((name_x,y+10),mname,fill=(80,50,50) if is_banned else WHITE,font=F(16,True))
        if is_final:
            pill(d,name_x,y+34,"✓ ФИНАЛЬНАЯ",(30,100,30),GREEN,11,True)
        elif is_banned:
            who=next((b for b in bans if b["map"]==mname),{})
            side="CT" if who.get("by")=="ct" else "T"
            pill(d,name_x,y+34,f"БАН ({side})",(80,20,20),RED,11,True)
        else:
            d.text((name_x,y+34),"В пуле",fill=DIM,font=F(11))

        sx=W-260
        d.text((sx,y+8),"Пик",fill=DIM,font=F(10))
        d.text((sx,y+22),f"{pick_pct:.0f}%",fill=CYAN,font=F(14,True))
        bar(d,sx,y+42,60,6,pick_pct/100,CYAN)
        d.text((sx,y+54),f"{played} матч.",fill=DIM,font=F(9))
        d.text((sx+90,y+8),"CT WR",fill=BLUE,font=F(10))
        d.text((sx+90,y+22),f"{ct_wr:.0f}%",fill=BLUE,font=F(14,True))
        bar(d,sx+90,y+42,60,6,ct_wr/100,BLUE)
        d.text((sx+180,y+8),"T WR",fill=RED,font=F(10))
        d.text((sx+180,y+22),f"{t_wr:.0f}%",fill=RED,font=F(14,True))
        bar(d,sx+180,y+42,60,6,t_wr/100,RED)
        y+=map_h+8

    draw_anime_banner(img,d,W,H-32,32)
    d.text((14,H-22),"⚡ FLITE FACEIT · MAP VETO",fill=WHITE,font=F(10,True))
    return _out(img)


# ══════════════════════════════════════════════════════════════
#  LOBBY BROWSER CARD
# ══════════════════════════════════════════════════════════════

def create_lobby_card(league, lobbies_data):
    """lobbies_data: list of dicts {key, device, slot, count, status}"""
    W=860; H=520
    img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)

    draw_anime_banner(img,d,W,0,55)
    logo(d,W,10)
    d.text((16,10),"🎮 ПОИСК МАТЧА",fill=WHITE,font=F(20,True))
    d.text((16,36),f"Лига: {'⭐ QUALS' if league!='default' else '🎯 DEFAULT'}",fill=DIM,font=F(13))
    draw_anime_side_banners(d,W,55,H-55)

    y=68
    for device,icon in [("MOBILE","📱"),("PC","💻")]:
        d.text((20,y),f"{icon} {device}",fill=WHITE,font=F(15,True))
        y+=28
        slot_w=160; slot_h=90; gap=8; cols=5
        for slot in range(1,cols+1):
            key=f"{league}_{device}_{slot}"
            lobby=next((l for l in lobbies_data if l["key"]==key),None)
            count=lobby["count"] if lobby else 0
            status=lobby["status"] if lobby else "empty"
            sx=20+(slot-1)*(slot_w+gap)

            if status=="empty":
                fill_c=(16,20,32); border_c=BORDER; label="Пусто"
                count_col=DIM
            elif status=="waiting":
                fill_c=CARD; border_c=(45,200,95) if count>0 else BORDER
                label=f"{count}/10 игроков"; count_col=GREEN if count>0 else DIM
            else:
                fill_c=(30,15,15); border_c=RED; label="🔒 Идёт матч"; count_col=RED

            rr(d,[(sx,y),(sx+slot_w,y+slot_h)],12,fill=fill_c,outline=border_c,width=2)
            # Slot number badge
            rr(d,[(sx+8,y+8),(sx+36,y+30)],8,fill=border_c)
            tcx(d,str(slot),F(14,True),WHITE,sx+22,y+10)

            # Player count dots
            dot_y=y+38; dot_x=sx+10
            for i in range(10):
                col=(45,200,95) if i<count else (40,50,72)
                dx=dot_x+i*(13)
                if dx+10 > sx+slot_w-4: break
                d.ellipse([(dx,dot_y),(dx+10,dot_y+10)],fill=col)

            d.text((sx+8,y+56),label,fill=count_col,font=F(10))
        y+=slot_h+16

    draw_anime_bottom_banner(d,W,H-30)
    d.text((20,H-20),"⚡ FLITE FACEIT · Выбери лобби",fill=WHITE,font=F(11,True))
    return _out(img)


# ══════════════════════════════════════════════════════════════
#  MATCH START CARD  (FACEIT style)
# ══════════════════════════════════════════════════════════════

def create_match_start_card(match_id, map_name, league, team_ct, team_t,
                             ct_players, t_players):
    """
    ct_players / t_players: list of player rows (from DB).
    """
    W=1200; H=580
    img=Image.new('RGB',(W,H),(12,15,25)); d=ImageDraw.Draw(img)

    # Subtle grid background
    for gx in range(0,W,40):
        d.line([(gx,0),(gx,H)],fill=(20,26,40),width=1)
    for gy in range(0,H,40):
        d.line([(0,gy),(W,gy)],fill=(20,26,40),width=1)

    # ── Header bar ──
    rr(d,[(0,0),(W,50)],0,fill=(16,20,32))
    d.text((20,12),f"DEFAULT #{match_id}",fill=WHITE,font=F(22,True))
    pill(d,300,10,f"🗺 {map_name}",CARD2,DIM,14)
    pill(d,460,10,league.upper(),CARD2,PURPLE,14)
    logo(d,W,10)

    # ── CT panel (left) ──
    rr(d,[(0,50),(360,H)],0,fill=(14,20,36))
    d.rectangle([(0,50),(360,54)],fill=(40,80,180))
    d.text((20,60),"COUNTER TERRORISTS",fill=WHITE,font=F(14,True))
    # Team winrate & ELO
    ct_elos=[p[5] for p in ct_players if p]
    avg_ct_elo=sum(ct_elos)//max(len(ct_elos),1)
    ct_wins_list=[p[7] for p in ct_players if p]
    ct_losses_list=[p[8] for p in ct_players if p]
    ct_total_w=sum(ct_wins_list); ct_total_l=sum(ct_losses_list)
    ct_wr=round(ct_total_w/max(ct_total_w+ct_total_l,1)*100)
    d.text((20,82),f"Avg ELO: {avg_ct_elo}",fill=ORANGE,font=F(12))
    d.text((180,82),f"Win%: {ct_wr}%",fill=GREEN if ct_wr>=50 else RED,font=F(12))

    py=105
    for p in ct_players[:5]:
        if not p: continue
        name=str(p[1])[:14]; kills=p[9]; deaths=p[10]
        kd=round(kills/deaths,2) if deaths>0 else float(kills)
        games=p[7]+p[8]; avg=round(kills/max(games*13,1)*10,1)
        rr(d,[(12,py),(348,py+66)],10,fill=CARD)
        rr(d,[(12,py),(16,py+66)],2,fill=(40,80,200))
        rr(d,[(20,py+10),(54,py+56)],8,fill=CARD2,outline=(40,80,180),width=1)
        tcx(d,str(p[4]),F(18,True),level_color(p[4]),37,py+18)
        d.text((62,py+8),name,fill=WHITE,font=F(13,True))
        d.text((62,py+26),f"Матчей: {games}",fill=DIM,font=F(10))
        d.text((62,py+40),f"K/D: {kd}",fill=ORANGE if kd>=1 else RED,font=F(10))
        d.text((200,py+26),f"AVG: {avg}",fill=BLUE,font=F(10))
        py+=72

    # ── T panel (right) ──
    rr(d,[(840,50),(W,H)],0,fill=(28,14,14))
    d.rectangle([(840,50),(W,54)],fill=(180,40,0))
    d.text((860,60),"TERRORISTS",fill=WHITE,font=F(14,True))
    t_elos=[p[5] for p in t_players if p]
    avg_t_elo=sum(t_elos)//max(len(t_elos),1)
    t_wins_list=[p[7] for p in t_players if p]
    t_losses_list=[p[8] for p in t_players if p]
    t_total_w=sum(t_wins_list); t_total_l=sum(t_losses_list)
    t_wr=round(t_total_w/max(t_total_w+t_total_l,1)*100)
    d.text((860,82),f"Avg ELO: {avg_t_elo}",fill=ORANGE,font=F(12))
    d.text((1020,82),f"Win%: {t_wr}%",fill=GREEN if t_wr>=50 else RED,font=F(12))

    py=105
    for p in t_players[:5]:
        if not p: continue
        name=str(p[1])[:14]; kills=p[9]; deaths=p[10]
        kd=round(kills/deaths,2) if deaths>0 else float(kills)
        games=p[7]+p[8]; avg=round(kills/max(games*13,1)*10,1)
        rr(d,[(852,py),(W-12,py+66)],10,fill=CARD)
        rr(d,[(W-16,py),(W-12,py+66)],2,fill=(200,40,0))
        rr(d,[(858,py+10),(892,py+56)],8,fill=CARD2,outline=(180,40,0),width=1)
        tcx(d,str(p[4]),F(18,True),level_color(p[4]),875,py+18)
        d.text((900,py+8),name,fill=WHITE,font=F(13,True))
        d.text((900,py+26),f"Матчей: {games}",fill=DIM,font=F(10))
        d.text((900,py+40),f"K/D: {kd}",fill=ORANGE if kd>=1 else RED,font=F(10))
        d.text((1040,py+26),f"AVG: {avg}",fill=BLUE,font=F(10))
        py+=72

    # ── Center panel ──
    rr(d,[(360,50),(840,H)],0,fill=(14,18,30))
    d.rectangle([(360,50),(840,54)],fill=BORDER)

    cx=600
    d.text((cx-60,70),"🇷🇺 Moscow",fill=DIM,font=F(12))
    rr(d,[(440,95),(760,135)],8,fill=CARD)
    tcx(d,f"🗺 {map_name}",F(15,True),WHITE,cx,105)
    d.text((440,145),league.upper(),fill=PURPLE,font=F(13,True))
    d.text((550,145),"Best of 1",fill=DIM,font=F(12))
    d.text((660,145),"5vs5",fill=DIM,font=F(12))

    rr(d,[(440,175),(760,230)],10,fill=CARD)
    d.text((455,182),"ID Матча",fill=DIM,font=F(11))
    d.text((455,198),f"#{match_id}",fill=WHITE,font=F(16,True))

    # ELO bar
    elo_y=260
    d.text((cx-60,elo_y-16),"ELO",fill=DIM,font=F(12,True))
    bar_w=300; bar_h=14
    bx=cx-bar_w//2
    rr(d,[(bx,elo_y),(bx+bar_w,elo_y+bar_h)],bar_h//2,fill=(30,35,55))
    ct_fill=int(bar_w*avg_ct_elo/max(avg_ct_elo+avg_t_elo,1))
    rr(d,[(bx,elo_y),(bx+ct_fill,elo_y+bar_h)],bar_h//2,fill=(40,80,200))
    d.text((bx-40,elo_y),str(avg_ct_elo),fill=BLUE,font=F(13,True))
    d.text((bx+bar_w+6,elo_y),str(avg_t_elo),fill=RED,font=F(13,True))

    # Map info box at bottom center
    rr(d,[(400,310),(800,480)],12,fill=CARD,outline=BORDER,width=1)
    d.text((420,320),"PICKED MAP",fill=DIM,font=F(11))
    rr(d,[(420,340),(490,410)],8,fill=MAP_COLORS.get(map_name,BLUE))
    tcx(d,map_name[:2].upper(),F(20,True),WHITE,455,356)
    d.text((500,340),map_name,fill=WHITE,font=F(24,True))
    d.text((500,372),"5vs5 · Best of 1",fill=DIM,font=F(12))
    d.text((420,425),"Играется строго эта карта",fill=DIM,font=F(11))

    # Footer
    rr(d,[(0,H-36),(W,H)],0,fill=(10,13,22))
    d.text((20,H-24),"⚡ FLITE FACEIT · Матч начался!",fill=WHITE,font=F(12,True))
    d.text((W-200,H-24),"Удачи обеим командам!",fill=DIM,font=F(11))
    return _out(img)


# ══════════════════════════════════════════════════════════════
#  MATCH RESULT CARD  (FACEIT scoreboard style)
# ══════════════════════════════════════════════════════════════

def create_match_result_card(match_id, map_name, league, score_ct, score_t,
                              winner, ct_stats, t_stats):
    """
    ct_stats / t_stats: list of (player_row, kills, deaths, assists) tuples.
    """
    row_h=52; rows=max(len(ct_stats),len(t_stats))
    W=1400; H=130+80+rows*row_h+100
    img=Image.new('RGB',(W,H),(12,15,25)); d=ImageDraw.Draw(img)

    for gx in range(0,W,40): d.line([(gx,0),(gx,H)],fill=(18,22,36),width=1)
    for gy in range(0,H,40): d.line([(0,gy),(W,gy)],fill=(18,22,36),width=1)

    # ── Header ──
    rr(d,[(0,0),(W,55)],0,fill=(16,20,32))
    d.text((20,12),f"DEFAULT #{match_id}",fill=WHITE,font=F(22,True))
    pill(d,280,12,"🇷🇺 Moscow",CARD2,DIM,13)
    pill(d,420,12,f"🗺 {map_name}",CARD2,MAP_COLORS.get(map_name,BLUE),13)
    pill(d,560,12,league.upper(),CARD2,PURPLE,13)
    pill(d,700,12,"✓ Завершён",(20,80,20),GREEN,13)
    logo(d,W,12)

    # ── Score block ──
    ct_won=(winner=="ct"); t_won=(winner=="t")
    d.text((20,68),"COUNTER TERRORISTS",fill=(180,200,255),font=F(14,True))
    d.text((W-280,68),"TERRORISTS",fill=(255,160,120),font=F(14,True))

    score_str=f"{score_ct}:{score_t}"
    d.text((W//2-40,58),score_str,fill=ORANGE if ct_won else WHITE,font=F(42,True))
    if ct_won:
        pill(d,W//2-60,108,"CT ПОБЕДА",(20,80,20),GREEN,12,True)
    else:
        pill(d,W//2-50,108,"T ПОБЕДА",(100,30,0),ORANGE,12,True)

    # ── Column headers ──
    y=130
    def header_row(x_start, reverse=False):
        cols=[("PLAYER",120),("K",45),("D",45),("K/D",55),("IMP",55),("RATING",65)]
        if reverse: cols=list(reversed(cols))
        cx2=x_start
        for lbl,cw in cols:
            d.text((cx2,y+8),lbl,fill=DIM,font=F(12,True)); cx2+=cw

    rr(d,[(0,y),(W,y+28)],0,fill=(18,23,38))
    header_row(20); header_row(W//2+20)
    y+=32

    def player_row(p_row, kills, deaths, assists, rx, side_col, reverse=False):
        name  = str(p_row[1])[:16] if p_row else "—"
        kd    = round(kills/deaths,2) if deaths>0 else float(kills)
        games = p_row[7]+p_row[8] if p_row else 0
        avg   = round(kills/max(games*13,1)*10,1)
        impact= round(kd*0.9,2)
        rating= round(kd*0.85+assists*0.02,2)
        lv    = p_row[4] if p_row else 1

        vals=[name,str(kills),str(deaths),f"{kd:.2f}",f"{impact:.2f}",f"{rating:.2f}"]
        widths=[120,45,45,55,55,65]
        if reverse:
            vals=list(reversed(vals)); widths=list(reversed(widths))

        cx2=rx
        for i,(val,cw) in enumerate(zip(vals,widths)):
            is_name=(i==0 and not reverse) or (i==len(vals)-1 and reverse)
            is_k   =(i==1 and not reverse) or (i==len(vals)-2 and reverse)
            is_d   =(i==2 and not reverse) or (i==len(vals)-3 and reverse)
            col_v  = WHITE
            if is_name:
                # level badge
                if not reverse:
                    rr(d,[(cx2,y+10),(cx2+22,y+32)],5,fill=level_color(lv))
                    tcx(d,str(lv),F(11,True),WHITE,cx2+11,y+12)
                    d.text((cx2+26,y+13),val,fill=WHITE,font=F(12,True))
                else:
                    d.text((cx2,y+13),val,fill=WHITE,font=F(12,True))
                    rr(d,[(cx2+cw-24,y+10),(cx2+cw-2,y+32)],5,fill=level_color(lv))
                    tcx(d,str(lv),F(11,True),WHITE,cx2+cw-13,y+12)
            else:
                if is_k: col_v=GREEN
                elif is_d: col_v=RED
                d.text((cx2,y+13),val,fill=col_v,font=F(12,True))
            cx2+=cw

    # CT rows (left half)
    max_rating_ct=0; mvp_player=None
    for i,(p,k,dth,a) in enumerate(ct_stats[:5]):
        bg=GOLD_R if i==0 else (CARD if i%2==0 else CARD2)
        rr(d,[(0,y),(W//2-4,y+row_h-2)],0,fill=bg)
        d.rectangle([(0,y),(4,y+row_h-2)],fill=(40,80,200))
        if p:
            kd=round(k/dth,2) if dth>0 else float(k)
            rating=round(kd*0.85+a*0.02,2)
            if rating>max_rating_ct: max_rating_ct=rating; mvp_player=(p,k,dth,a)
        player_row(p,k,dth,a,20,"ct",reverse=False)
        y+=row_h

    # T rows (right half) — reset y
    y_t=y-(len(ct_stats))*row_h
    max_rating_t=0; mvp_t=None
    for i,(p,k,dth,a) in enumerate(t_stats[:5]):
        bg=(25,15,10) if i%2==0 else (20,12,8)
        rr(d,[(W//2+4,y_t),(W,y_t+row_h-2)],0,fill=bg)
        d.rectangle([(W-4,y_t),(W,y_t+row_h-2)],fill=(200,40,0))
        if p:
            kd=round(k/dth,2) if dth>0 else float(k)
            rating=round(kd*0.85+a*0.02,2)
            if rating>max_rating_t: max_rating_t=rating; mvp_t=(p,k,dth,a)
        player_row(p,k,dth,a,W//2+20,"t",reverse=False)
        y_t+=row_h

    y=max(y,y_t)+8

    # Center divider
    d.line([(W//2,130),(W//2,y)],fill=BORDER,width=2)

    # ── Footer: Map info + MVP ──
    rr(d,[(0,y),(W,H)],0,fill=(10,13,22))
    d.text((20,y+12),"MAP INFO",fill=DIM,font=F(11,True))
    rr(d,[(20,y+30),(120,y+80)],8,fill=MAP_COLORS.get(map_name,BLUE))
    tcx(d,map_name[:2].upper(),F(22,True),WHITE,70,y+38)
    d.text((130,y+30),"PICKED MAP",fill=DIM,font=F(11))
    d.text((130,y+46),map_name,fill=WHITE,font=F(18,True))

    # MVP block
    overall_mvp=mvp_player if max_rating_ct>=max_rating_t else mvp_t
    if overall_mvp:
        mp,mk,md,ma=overall_mvp
        mkd=round(mk/md,2) if md>0 else float(mk)
        rating_v=round(mkd*0.85+ma*0.02,2)
        impact_v=round(mkd*0.9,2)
        rr(d,[(W//2-200,y+12),(W//2+200,y+82)],10,fill=CARD,outline=ORANGE,width=2)
        d.text((W//2-185,y+18),"🏅 GAME MVP",fill=DIM,font=F(11,True))
        rr(d,[(W//2-185,y+34),(W//2-155,y+70)],8,fill=level_color(mp[4]))
        tcx(d,str(mp[4]),F(16,True),WHITE,W//2-170,y+40)
        d.text((W//2-145,y+34),str(mp[1])[:14],fill=WHITE,font=F(16,True))
        d.text((W//2+30,y+18),"RATING",fill=DIM,font=F(10))
        d.text((W//2+30,y+32),f"{rating_v:.2f}",fill=WHITE,font=F(20,True))
        d.text((W//2+100,y+18),"K/D",fill=DIM,font=F(10))
        d.text((W//2+100,y+32),f"{mkd:.2f}",fill=ORANGE,font=F(20,True))
        d.text((W//2+170,y+18),"IMP",fill=DIM,font=F(10))
        d.text((W//2+170,y+32),f"{impact_v:.2f}",fill=BLUE,font=F(20,True))

    d.text((20,H-18),"⚡ FLITE FACEIT · Результат матча",fill=WHITE,font=F(11,True))
    d.text((W-240,H-18),"flite-faceit.gg",fill=DIM,font=F(10))
    return _out(img)


# ══════════════════════════════════════════════════════════════
#  TOP PLAYERS CARD
# ══════════════════════════════════════════════════════════════

def create_top_card(players):
    W=920; row_h=82
    H=220+max(len(players),1)*row_h+50
    img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)

    draw_anime_banner(img,d,W,0,50); logo(d,W,10)
    d.text((40,58),"ЛУЧШИЕ",fill=ORANGE,font=F(52,True))
    d.text((40,112),"ИГРОКИ",fill=ORANGE2,font=F(52,True))
    draw_anime_side_banners(d,W,50,H-50)
    pill_out(d,40,172,"× Default",DIM,DIM,13)
    d.text((140,177),"Season 4",fill=DIM,font=F(13))

    y=212
    rr(d,[(40,y),(W-40,y+34)],6,fill=CARD)
    for lbl,cx4 in [("PLACE",60),("PLAYER",180),("GAMES",370),("WINRATE",480),("ELO",580),("K/D",680),("AVG",780)]:
        d.text((cx4,y+9),lbl,fill=DIM,font=F(12,True))
    y+=40

    medals_bg=[GOLD_R]+[CARD,CARD2]*5
    medal_bdr=[GOLD_B]+[BORDER]*9
    for i,p in enumerate(players[:10]):
        name=str(p[0]) if p[0] else "Player"
        elo=p[2] or 1000; wins=p[3] or 0; losses=p[4] or 0
        kills=p[5] or 0; deaths=p[6] or 0
        total=wins+losses; wr=(wins/total*100) if total>0 else 0.0
        kd_v=(kills/deaths) if deaths>0 else float(kills)
        avg_v=round(kills/max(total*13,1)*10,1)

        rr(d,[(40,y),(W-40,y+row_h-4)],10,fill=medals_bg[i%len(medals_bg)],
           outline=medal_bdr[i%len(medal_bdr)],width=1)
        num_col=ORANGE if i==0 else DIM
        rr(d,[(55,y+16),(88,y+50)],6,fill=(50,38,5) if i==0 else CARD2)
        tcx(d,str(i+1),F(18,True),num_col,71,y+21)
        if i==0:
            rr(d,[(100,y+12),(136,y+56)],8,fill=(50,38,5),outline=GOLD_B,width=1)
            tcx(d,"♛",F(20,True),ORANGE,118,y+20)
        av_x=145 if i==0 else 100
        rr(d,[(av_x,y+12),(av_x+42,y+56)],6,fill=CARD2,outline=BORDER,width=1)
        d.text((av_x+52,y+10),name[:18],fill=WHITE,font=F(16,True))
        d.text((av_x+52,y+48),f"#{str(p[1])[:8]}",fill=DIM,font=F(11))
        d.text((370,y+8),f"Win {wins}",fill=GREEN,font=F(12))
        d.text((430,y+8),f"Lose {losses}",fill=RED,font=F(12))
        d.text((370,y+28),str(total),fill=WHITE,font=F(20,True))
        stars="★★★" if wr>=80 else ("★★" if wr>=50 else "★")
        d.text((480,y+20),stars,fill=ORANGE,font=F(18))
        d.text((480,y+44),f"{wr:.0f}%",fill=WHITE,font=F(13,True))
        rr(d,[(578,y+8),(618,y+30)],8,fill=PURPLE)
        tcx(d,"ELO",F(10,True),WHITE,598,y+11)
        d.text((578,y+36),str(elo),fill=WHITE,font=F(16,True))
        pct=min(kd_v/5,1.0)
        donut(d,693,y+38,20,pct,GREEN if kd_v>=1 else RED)
        tcx(d,f"{kd_v:.1f}",F(13,True),WHITE,693,y+50)
        rr(d,[(780,y+12),(800,y+60)],4,fill=ORANGE)
        d.text((808,y+34),str(avg_v),fill=WHITE,font=F(14,True))
        y+=row_h

    draw_anime_banner(img,d,W,H-30,30)
    d.text((40,H-20),"⚡ FLITE FACEIT · Лучшие игроки · Season 4",fill=WHITE,font=F(11,True))
    return _out(img)


# ══════════════════════════════════════════════════════════════
#  SHOP CARD
# ══════════════════════════════════════════════════════════════

TAB_LABELS={"skins":("🎨 СКИНЫ",BLUE),"decor":("🎭 ДЕКОР",PINK),"goods":("🛍 ТОВАРЫ",PURPLE)}

def create_shop_card(category, items, coins=0):
    W,PAD=980,40; cols=3
    card_w=(W-PAD*2-(cols-1)*14)//cols; card_h=150
    rows=math.ceil(max(len(items),1)/cols)
    top=200; H=top+rows*(card_h+14)+80
    img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)

    draw_anime_banner(img,d,W,0,50); logo(d,W,10)
    draw_anime_side_banners(d,W,50,H-50)
    title,accent=TAB_LABELS.get(category,("МАГАЗИН",ORANGE))
    d.rectangle([(PAD,60),(PAD+5,100)],fill=accent)
    d.text((PAD+18,58),title,fill=WHITE,font=F(36,True))
    pill(d,W-200,62,f"💰 {coins} монет",(40,34,8),ORANGE,15,True)

    tab_y=112; tx=PAD
    for lbl,tab in [("🎨 Скины","skins"),("🎭 Декор","decor"),("🛍 Товары","goods")]:
        if tab==category: tw=pill(d,tx,tab_y,lbl,accent,WHITE,15,True,20,9)
        else: tw=pill_out(d,tx,tab_y,lbl,BORDER,DIM,14,False,18,8)
        tx+=tw+16
    d.line([(PAD,148),(W-PAD,148)],fill=BORDER,width=1)

    for idx,item in enumerate(items):
        ci=idx%cols; ri=idx//cols
        cx5=PAD+ci*(card_w+14); cy=top+ri*(card_h+14)
        glow=item.get("glow",False); icon=item.get("icon","?")
        icol=accent if glow else BORDER
        rr(d,[(cx5,cy),(cx5+card_w,cy+card_h)],14,fill=CARD,outline=icol,width=2 if glow else 1)
        if glow: rr(d,[(cx5,cy),(cx5+card_w,cy+4)],2,fill=accent)
        d.text((cx5+12,cy+10),item.get("name","")[:24],fill=DIM,font=F(12))
        pill(d,cx5+card_w-80,cy+10,f"💰{item.get('price',0)}",(40,34,8),ORANGE,11,True,8,4)
        mid_x=cx5+card_w//2; mid_y=cy+80
        if icon=="F":
            rr(d,[(mid_x-28,mid_y-24),(mid_x+28,mid_y+24)],24,fill=PINK)
            tcx(d,"F",F(22,True),WHITE,mid_x,mid_y-16)
        elif icon=="⭐": tcx(d,"★",F(44,True),ORANGE,mid_x,mid_y-28)
        elif icon=="?":
            rr(d,[(mid_x-24,mid_y-24),(mid_x+24,mid_y+24)],24,fill=(50,52,58))
            tcx(d,"?",F(28,True),(120,125,135),mid_x,mid_y-16)
        btn_y=cy+card_h-28
        rr(d,[(cx5+12,btn_y),(cx5+card_w-12,btn_y+20)],10,fill=accent if glow else CARD2)
        tcx(d,"КУПИТЬ",F(11,True),WHITE,mid_x,btn_y+4)

    draw_anime_banner(img,d,W,H-30,30)
    d.text((PAD,H-20),"⚡ FLITE FACEIT · Магазин",fill=WHITE,font=F(11,True))
    return _out(img)


# ══════════════════════════════════════════════════════════════
#  INVENTORY CARD
# ══════════════════════════════════════════════════════════════

def create_inventory_card(player, items):
    W,PAD=700,40; item_h=56
    H=280+max(len(items),1)*item_h+80
    img=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(img)

    draw_anime_banner(img,d,W,0,50); logo(d,W,10)
    draw_anime_side_banners(d,W,50,H-50)
    d.rectangle([(PAD,60),(PAD+5,100)],fill=PINK)
    d.text((PAD+18,58),"ИНВЕНТАРЬ",fill=WHITE,font=F(32,True))
    d.text((PAD,106),"Здесь хранятся все твои предметы!",fill=DIM,font=F(13))

    y=140
    username=str(player[1]) if player[1] else "Player"
    game_id=str(player[2]) if player[2] else "0"
    coins=player[6] if player[6] else 0
    d.text((PAD,y),f"#{game_id}",fill=DIM,font=F(14))
    d.text((PAD,y+22),username+" ★",fill=ORANGE,font=F(22,True))
    pill(d,PAD,y+52,f"💰 {coins} монет",(40,34,8),ORANGE,13,True)
    y+=98

    if not items:
        rr(d,[(PAD,y),(W-PAD,y+50)],10,fill=CARD)
        d.text((PAD+60,y+15),"Инвентарь пуст",fill=DIM,font=F(15))
        y+=60
    else:
        for i,row in enumerate(items):
            inv_id,item_name,item_type,item_id,activated,expires=row
            ac=ANIME_COLORS[i%len(ANIME_COLORS)]
            rr(d,[(PAD,y),(W-PAD,y+item_h-4)],10,fill=CARD,outline=ac,width=1)
            dot_col={"qual":PURPLE,"premium":ORANGE,"x2coins":PINK,
                     "skin":BLUE,"decor":GREEN,"unwarn":RED,"nick_change":CYAN}.get(item_type,DIM)
            rr(d,[(PAD+12,y+item_h//2-6),(PAD+24,y+item_h//2+6)],6,fill=dot_col)
            d.text((PAD+34,y+10),f'"{item_name}"',fill=WHITE,font=F(15,True))
            if activated:
                stxt="✅ Активировано"+(f" · до {expires[:10]}" if expires else "")
                scol=GREEN
            else:
                stxt="⚡ Нажми Активировать"
                scol=ORANGE
            d.text((PAD+34,y+30),stxt,fill=scol,font=F(12))
            y+=item_h

    y+=20
    d.text((PAD,y),"Страница 1 из 1",fill=DIM,font=F(12))
    draw_anime_banner(img,d,W,H-28,28)
    d.text((PAD,H-18),"⚡ FLITE FACEIT",fill=WHITE,font=F(12,True))
    return _out(img)
