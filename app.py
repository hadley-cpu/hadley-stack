import math
import re
import itertools
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ==========================================
# 0. 다국어 딕셔너리
# ==========================================
TRANSLATIONS = {
    "Korean": {
        "sidebar_title": "입력 설정",
        "sec1_title": "1. 제품 & 무게 정보",
        "dim_label": "제품 치수 (예: 180*120*50)",
        "dim_help": "가로, 세로, 높이를 구분자(*, x, 공백, 콤마)로 입력하세요.",
        "rot_label": "제품 회전 허용 (L,W,H 변경)",
        "weight_label": "제품무게(g)",
        "max_box_label": "박스최대(g)",
        "sec2_title": "2. 박스 규격 & 수량",
        "box_type_label": "골판지 종류",
        "min_qty": "최소입수",
        "max_qty": "최대입수",
        "sec3_title": "3. 파레트 규격",
        "pl_l": "가로(L)",
        "pl_w": "세로(W)",
        "pl_h": "적재높이",
        "pl_h_help": "파레트 바닥 높이를 제외한 순수 화물 적재 높이",
        "btn_calc": "분석 시작",
        "err_dim_fmt": "❌ 제품 치수 형식이 올바르지 않습니다.",
        "success_msg": "✅ 분석 완료! Top {n} 옵션 도출",
        "err_no_result": "❌ 조건에 맞는 박스 구성을 찾지 못했습니다.",
        "res_title": "4. 추천 적재 옵션",
        "opt_label": "옵션 선택:",
        "rank": "순위",
        "warn": "[위험]",
        "qty_unit": "입",
        "total_unit": "개",
        "eff": "효율",
        "detail_title": "📊 상세 리포트",
        "unsafe_msg": "🚫 **[비추천]** 강도 부족 (안전계수: {sf:.1f})",
        "safe_msg": "✅ **[안전]** 강도 충분 (안전계수: {sf:.1f})",
        "t_cat": "구분",
        "t_dim": "치수 (mm)",
        "t_cont": "내용",
        "l_prod_in": "제품(입력)",
        "l_prod_act": "제품(적재)",
        "l_desc_act": "실제 적재 방향",
        "l_box": "박스",
        "l_load": "적재",
        "eff_label": "적재 효율",
        "load_bottom": "최하단 하중",
        "bct": "압축강도(BCT)",
        "g_title": "하중 vs 강도",
        "viewer_pallet_2d": "🏗️ 파레트: 1단 도면",
        "viewer_pallet_3d": "🏗️ 파레트: 3D 뷰",
        "viewer_box_2d": "📦 박스 내부: 1단 도면",
        "viewer_box_3d": "📦 박스 내부: 3D 뷰",
        "box_types": ["A골 (5mm)", "B골 (3mm)", "AB골 (8mm)"],
        "pat_no_int": "No Interlock",
        "pat_pat_rot": "Pattern Rotation",
        "pat_box_rot": "Box Rotation",
        "pat_pinwheel": "Pinwheel",
        "pat_expanded": "Expanded Pinwheel"
    },
    "English": {
        "sidebar_title": "Settings",
        "sec1_title": "1. Product & Weight",
        "dim_label": "Dimensions (e.g. 180*120*50)",
        "dim_help": "Enter L, W, H separated by *, x, space, or comma.",
        "rot_label": "Allow Rotation (Swap L,W,H)",
        "weight_label": "Unit Wgt(g)",
        "max_box_label": "Box Max(g)",
        "sec2_title": "2. Box Spec & Qty",
        "box_type_label": "Cardboard Type",
        "min_qty": "Min Qty",
        "max_qty": "Max Qty",
        "sec3_title": "3. Pallet Spec",
        "pl_l": "Length(L)",
        "pl_w": "Width(W)",
        "pl_h": "Load Height",
        "pl_h_help": "Max load height excluding pallet base height",
        "btn_calc": "Start Analysis",
        "err_dim_fmt": "❌ Invalid dimension format.",
        "success_msg": "✅ Done! Top {n} options found",
        "err_no_result": "❌ No valid configuration found.",
        "res_title": "4. Recommended Options",
        "opt_label": "Select Option:",
        "rank": "Rank",
        "warn": "[Unsafe]",
        "qty_unit": "ea/box",
        "total_unit": "total",
        "eff": "Eff",
        "detail_title": "📊 Detailed Report",
        "unsafe_msg": "🚫 **[Unsafe]** Insufficient Strength (SF: {sf:.1f})",
        "safe_msg": "✅ **[Safe]** Sufficient Strength (SF: {sf:.1f})",
        "t_cat": "Category",
        "t_dim": "Dim (mm)",
        "t_cont": "Content",
        "l_prod_in": "Prod(Input)",
        "l_prod_act": "Prod(Actual)",
        "l_desc_act": "Actual Orientation",
        "l_box": "Box (Outer)",
        "l_load": "Pallet Load",
        "eff_label": "Efficiency",
        "load_bottom": "Bottom Load",
        "bct": "Box Strength(BCT)",
        "g_title": "Load vs Strength",
        "viewer_pallet_2d": "🏗️ Pallet: Layer View (2D)",
        "viewer_pallet_3d": "🏗️ Pallet: 3D View",
        "viewer_box_2d": "📦 Inside Box: Layer View (2D)",
        "viewer_box_3d": "📦 Inside Box: 3D View",
        "box_types": ["A-Flute (5mm)", "B-Flute (3mm)", "AB-Flute (8mm)"],
        "pat_no_int": "No Interlock",
        "pat_pat_rot": "Pattern Rotation",
        "pat_box_rot": "Box Rotation",
        "pat_pinwheel": "Pinwheel",
        "pat_expanded": "Expanded Pinwheel"
    }
}

# ==========================================
# 1. 유틸리티 함수
# ==========================================
def parse_dimensions(dim_str):
    try:
        cleaned = re.sub(r'[^\d.]+', ',', dim_str)
        parts = [float(x) for x in cleaned.split(',') if x.strip()]
        if len(parts) == 3:
            return [int(p) for p in parts]
        return None
    except:
        return None

# ==========================================
# 2. 계산 로직 (Core Logic)
# ==========================================
class PalletLogic:
    def __init__(self):
        self.MATERIAL_PROPS = {
            0: {"ect": 5.0, "thick": 5.0}, 
            1: {"ect": 4.0, "thick": 3.0}, 
            2: {"ect": 7.0, "thick": 8.0}  
        }

    def check_pinwheel_layers(self, box_l, box_w, pallet_l):
        remaining_space = pallet_l - box_l
        if remaining_space < box_w:
            return 0
        return int(remaining_space // box_w)

    def calculate_bct(self, length, width, fl_idx):
        props = self.MATERIAL_PROPS.get(fl_idx)
        if not props: return 0
        ect = props['ect'] 
        caliper = props['thick'] 
        perimeter = (length + width) * 2 
        bct_newton = 5.87 * ect * math.sqrt(caliper * perimeter)
        bct_kgf = bct_newton / 9.80665 * 1000 
        return bct_kgf 

    def find_candidates(self, p_dims_input, p_weight_g, max_box_w_g, box_type_idx, box_margin, min_qty, max_qty, pallet_dims, allow_rotation):
        pl_L, pl_W, pl_H = pallet_dims
        
        if max_box_w_g <= 0: max_box_w_g = 999999
        if p_weight_g <= 0: p_weight_g = 1
        
        limit_qty_by_weight = int(max_box_w_g / p_weight_g)
        
        candidates = []
        seen_configs = set()

        raw_d1, raw_d2, raw_d3 = p_dims_input
        prod_orientations = [(raw_d1, raw_d2, raw_d3)]
        
        if allow_rotation:
            perms = set(itertools.permutations([raw_d1, raw_d2, raw_d3]))
            prod_orientations = list(perms)

        for (p_L, p_W, p_H) in prod_orientations:
            for div_x in range(2, 7):
                for div_y in range(2, 7):
                    grid_l = int(pl_L / div_x)
                    grid_w = int(pl_W / div_y)
                    limit_in_l = grid_l - box_margin
                    limit_in_w = grid_w - box_margin

                    if limit_in_l < min(p_L, p_W) or limit_in_w < min(p_L, p_W): continue

                    orientations_inside = [(p_L, p_W), (p_W, p_L)]
                    for d1, d2 in orientations_inside:
                        max_c = limit_in_l // d1
                        max_r = limit_in_w // d2
                        if max_c * max_r == 0: continue
                        
                        search_range_c = range(max_c, max(0, max_c - 3), -1)
                        search_range_r = range(max_r, max(0, max_r - 3), -1)
                        
                        for c in search_range_c:
                            for r in search_range_r:
                                if c * r == 0: continue
                                req_in_l = c * d1
                                req_in_w = r * d2
                                out_l = req_in_l + box_margin
                                out_w = req_in_w + box_margin
                                
                                long_side = max(out_l, out_w)
                                short_side = min(out_l, out_w)
                                if short_side > 0 and (long_side / short_side) > 3.0: continue
                                
                                max_stable_height = long_side * 0.6
                                avail_prod_h = max_stable_height - box_margin
                                geo_max_layers = int(avail_prod_h // p_H)
                                if geo_max_layers < 1:
                                    if (p_H + box_margin) <= long_side: geo_max_layers = 1
                                    else: continue
                                
                                weight_max_layers = limit_qty_by_weight // (c * r)
                                user_max_layers = max_qty // (c * r)
                                safe_layers = min(weight_max_layers, geo_max_layers, user_max_layers)
                                if safe_layers == 0: continue
                                
                                qty = (c * r) * safe_layers
                                if qty < min_qty: continue

                                req_in_h = safe_layers * p_H
                                out_h = req_in_h + box_margin 

                                if out_h > grid_l + 5 and out_h > grid_w + 5: continue
                                p_layers = int(pl_H // out_h)
                                if p_layers < 1: continue

                                box_weight_kg = (qty * p_weight_g) / 1000.0
                                bct_val = self.calculate_bct(out_l, out_w, box_type_idx)
                                stack_load = box_weight_kg * (p_layers - 1)
                                if stack_load <= 0: stack_load = 0.1
                                sf = bct_val / stack_load
                                is_unsafe = sf < 3.0
                                
                                grid_yield = div_x * div_y
                                layer_total_l = div_x * out_l
                                layer_total_w = div_y * out_w
                                is_perfect_square = abs(layer_total_l - layer_total_w) <= 20
                                
                                desc_key = 'pat_no_int'
                                if is_perfect_square:
                                    if div_x != div_y: desc_key = 'pat_pat_rot'
                                    elif abs(out_l - out_w) <= 5: desc_key = 'pat_box_rot'
                                
                                if 'rot' in desc_key:
                                    load_l = max(layer_total_l, layer_total_w)
                                    load_w = load_l
                                else:
                                    load_l = layer_total_l
                                    load_w = layer_total_w

                                total = grid_yield * p_layers * qty
                                eff = (out_l * out_w * grid_yield) / (pl_L * pl_W) * 100
                                
                                score = total
                                if 'rot' in desc_key: score += 15
                                if is_unsafe: score -= 500
                                
                                config_key = (out_l, out_w, out_h, desc_key, qty, grid_yield, p_L, p_W, p_H)
                                if config_key not in seen_configs:
                                    candidates.append({
                                        'qty': qty, 
                                        'pattern_type': 'grid',
                                        'pattern_dims': (div_x, div_y),
                                        'box_outer': (out_l, out_w, out_h),
                                        'box_inner': (req_in_l, req_in_w, req_in_h),
                                        'prod_detail': (d1, d2, p_H, c, r, safe_layers),
                                        'prod_dims_used': (p_L, p_W, p_H),
                                        'yield_per_layer': grid_yield,
                                        'total': total, 
                                        'interlock_desc_key': desc_key,
                                        'weight': box_weight_kg,
                                        'score': score,
                                        'p_layers': p_layers,
                                        'efficiency': eff,
                                        'pinwheel_k': 0,
                                        'load_dims': (load_l, load_w, p_layers * out_h),
                                        'pallet_dims': pallet_dims,
                                        'strength': {'bct': bct_val, 'load': stack_load, 'sf': sf, 'unsafe': is_unsafe}
                                    })
                                    seen_configs.add(config_key)

                                if c == max_c and r == max_r:
                                    pw_k = self.check_pinwheel_layers(out_l, out_w, pl_L)
                                    if pw_k > 0:
                                        pat_type_pw = 'pinwheel'
                                        pinwheel_yield = 4 * pw_k
                                        desc_key_pw = 'pat_pinwheel'
                                        if pw_k > 1: desc_key_pw = 'pat_expanded'
                                        
                                        total_pw = pinwheel_yield * p_layers * qty
                                        eff_pw = (out_l * out_w * pinwheel_yield) / (pl_L * pl_W) * 100
                                        score_pw = total_pw + 20
                                        if is_unsafe: score_pw -= 500
                                        pw_size = out_l + (pw_k * out_w)
                                        
                                        config_key_pw = (out_l, out_w, out_h, desc_key_pw, qty, pinwheel_yield, p_L, p_W, p_H)
                                        if config_key_pw not in seen_configs:
                                            candidates.append({
                                                'qty': qty,
                                                'pattern_type': pat_type_pw,
                                                'pattern_dims': (div_x, div_y),
                                                'box_outer': (out_l, out_w, out_h),
                                                'box_inner': (req_in_l, req_in_w, req_in_h),
                                                'prod_detail': (d1, d2, p_H, c, r, safe_layers),
                                                'prod_dims_used': (p_L, p_W, p_H),
                                                'yield_per_layer': pinwheel_yield,
                                                'total': total_pw,
                                                'interlock_desc_key': desc_key_pw,
                                                'weight': box_weight_kg,
                                                'score': score_pw,
                                                'p_layers': p_layers,
                                                'efficiency': eff_pw,
                                                'pinwheel_k': pw_k,
                                                'load_dims': (pw_size, pw_size, p_layers * out_h),
                                                'pallet_dims': pallet_dims,
                                                'strength': {'bct': bct_val, 'load': stack_load, 'sf': sf, 'unsafe': is_unsafe}
                                            })
                                            seen_configs.add(config_key_pw)

        if not candidates: return []
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates[:12]

# ==========================================
# 3. 2D & 3D 시각화 함수
# ==========================================
def create_cube_mesh(x, y, z, dx, dy, dz, color, opacity=1.0):
    x_pts = [x, x+dx, x+dx, x, x, x+dx, x+dx, x]
    y_pts = [y, y, y+dy, y+dy, y, y, y+dy, y+dy]
    z_pts = [z, z, z, z, z+dz, z+dz, z+dz, z+dz]
    i = [7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2]
    j = [3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3]
    k = [0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6]
    return go.Mesh3d(x=x_pts, y=y_pts, z=z_pts, i=i, j=j, k=k, color=color, opacity=opacity, flatshading=True, lighting=dict(ambient=0.5, diffuse=0.8), hoverinfo='skip')

def draw_wireframe(x, y, z, dx, dy, dz):
    xe = [x, x+dx, x+dx, x, x, None, x, x+dx, x+dx, x, x, None, x+dx, x+dx, None, x+dx, x+dx, None, x, x]
    ye = [y, y, y+dy, y+dy, y, None, y, y, y+dy, y+dy, y, None, y, y, None, y+dy, y+dy, None, y+dy, y+dy]
    ze = [z, z, z, z, z, None, z+dz, z+dz, z+dz, z+dz, z+dz, None, z, z+dz, None, z, z+dz, None, z, z+dz]
    return go.Scatter3d(x=xe, y=ye, z=ze, mode='lines', line=dict(color='black', width=2), showlegend=False, hoverinfo='skip')

# --- Pallet 2D ---
def get_pallet_2d_fig(res, pl_L, pl_W):
    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=0, x1=pl_L, y1=pl_W, line=dict(color="black", width=3))
    
    L, W, H = res['box_outer']
    rects = []
    
    if res['pattern_type'] == 'pinwheel':
        k = res['pinwheel_k']
        total_span = L + (k * W)
        off_x = (pl_L - total_span) / 2
        off_y = (pl_W - total_span) / 2
        for i in range(k):
            # 2D 뷰는 짝수층(Standard Layer) 기준으로 보여줌
            rects.append((off_x, off_y + (i * W), L, W))
            rects.append((off_x + L + (i * W), off_y, W, L))
            rects.append((off_x + (k * W), off_y + L + (i * W), L, W))
            rects.append((off_x + (i * W), off_y + (k * W), W, L))
    else:
        dx, dy = res['pattern_dims']
        total_w = dx * L
        total_h = dy * W
        start_x = (pl_L - total_w) / 2
        start_y = (pl_W - total_h) / 2
        for r in range(dy):
            for c in range(dx):
                bx = start_x + c * L
                by = start_y + r * W
                rects.append((bx, by, L, W))
    
    for i, (rx, ry, rdx, rdy) in enumerate(rects):
        fig.add_trace(go.Scatter(
            x=[rx, rx+rdx, rx+rdx, rx, rx], y=[ry, ry, ry+rdy, ry+rdy, ry],
            fill="toself", fillcolor="#85C1E9", line=dict(color="blue", width=1),
            mode='lines+text', text=str(i+1), textposition="middle center",
            showlegend=False, hoverinfo='text', hovertext=f"Box {i+1}"
        ))

    fig.update_layout(
        xaxis=dict(range=[-50, pl_L+50], showgrid=False, zeroline=False, visible=True),
        yaxis=dict(range=[-50, pl_W+50], showgrid=False, zeroline=False, visible=True, scaleanchor="x", scaleratio=1),
        margin=dict(l=20, r=20, b=20, t=20), height=350, plot_bgcolor="white"
    )
    return fig

# --- Pallet 3D ---
def get_pallet_3d_fig(res, pl_L, pl_W):
    fig = go.Figure()
    L, W, H = res['box_outer']
    layers = res['p_layers']
    fig.add_trace(draw_wireframe(0, 0, 0, pl_L, pl_W, 0))
    c_blue, c_red = '#355C7D', '#C06C84'
    gap = 2

    for z in range(layers):
        cur_z = z * H
        is_odd = (z % 2 != 0)
        color = c_red if is_odd else c_blue
        boxes = []
        
        if res['pattern_type'] == 'pinwheel':
            k = res['pinwheel_k']
            total_span = L + (k * W)
            off_x = (pl_L - total_span) / 2
            off_y = (pl_W - total_span) / 2
            
            # [FIXED] 핀휠 좌표 계산 로직 완전 수정 (대각선 대칭)
            # 기준(짝수층) 좌표 리스트 생성
            even_layer_boxes = [] # (local_x, local_y, dx, dy)
            for i in range(k):
                # 1. Bottom (L x W)
                even_layer_boxes.append((0, i*W, L, W))
                # 2. Right (W x L)
                even_layer_boxes.append((L + i*W, 0, W, L))
                # 3. Top (L x W)
                even_layer_boxes.append((k*W, L + i*W, L, W))
                # 4. Left (W x L)
                even_layer_boxes.append((i*W, k*W, W, L))
            
            # 층에 따라 좌표 적용
            for (lx, ly, dx, dy) in even_layer_boxes:
                if not is_odd:
                    # 짝수층: 그대로 적용
                    boxes.append((off_x + lx, off_y + ly, cur_z, dx - gap, dy - gap, H - gap))
                else:
                    # 홀수층: x, y를 Swap (대각선 대칭)하여 완벽한 Interlock 구현
                    # dx, dy도 Swap
                    boxes.append((off_x + ly, off_y + lx, cur_z, dy - gap, dx - gap, H - gap))
                    
        else:
            dx, dy = res['pattern_dims']
            is_perfect = 'rot' in res['interlock_desc_key']
            do_rotate = (is_perfect and is_odd)
            
            cols, rows = (dy, dx) if do_rotate else (dx, dy)
            box_l, box_w = (W, L) if do_rotate else (L, W)
            
            total_w = cols * box_l
            total_h = rows * box_w
            start_x = (pl_L - total_w) / 2
            start_y = (pl_W - total_h) / 2
            
            for r in range(rows):
                for c in range(cols):
                    bx = start_x + c * box_l
                    by = start_y + r * box_w
                    boxes.append((bx, by, cur_z, box_l-gap, box_w-gap, H-gap))

        for (bx, by, bz, bdx, bdy, bdz) in boxes:
            fig.add_trace(create_cube_mesh(bx, by, bz, bdx, bdy, bdz, color))
            fig.add_trace(draw_wireframe(bx, by, bz, bdx, bdy, bdz))

    camera = dict(eye=dict(x=1.5, y=1.5, z=1.5))
    fig.update_layout(height=350, showlegend=False, scene=dict(aspectmode='data', camera=camera), margin=dict(l=0, r=0, b=0, t=0))
    return fig

# --- Product 2D (Inside Box) ---
def get_prod_layer_2d_fig(res):
    fig = go.Figure()
    p_d1, p_d2, p_d3, n_c, n_r, n_l = res['prod_detail']
    in_L, in_W, in_H = res['box_inner']
    
    # 박스 내부 테두리
    fig.add_shape(type="rect", x0=0, y0=0, x1=in_L, y1=in_W, line=dict(color="black", width=3))
    
    count = 0
    for r in range(n_r):
        for c in range(n_c):
            count += 1
            bx = c * p_d1
            by = r * p_d2
            fig.add_trace(go.Scatter(
                x=[bx, bx+p_d1, bx+p_d1, bx, bx],
                y=[by, by, by+p_d2, by+p_d2, by],
                fill="toself", fillcolor="#F9E79F", line=dict(color="orange", width=1),
                mode='lines+text', text=str(count), textposition="middle center",
                showlegend=False, hoverinfo='text', hovertext=f"Prod {count}"
            ))
            
    fig.update_layout(
        xaxis=dict(range=[-10, in_L+10], showgrid=False, zeroline=False, visible=True),
        yaxis=dict(range=[-10, in_W+10], showgrid=False, zeroline=False, visible=True, scaleanchor="x", scaleratio=1),
        margin=dict(l=20, r=20, b=20, t=20), height=350, plot_bgcolor="white"
    )
    return fig

# --- Product 3D (Inside Box) ---
def get_prod_3d_fig(res):
    fig = go.Figure()
    p_d1, p_d2, p_d3, n_c, n_r, n_l = res['prod_detail']
    in_L, in_W, in_H = res['box_inner']
    
    # 박스 와이어프레임
    fig.add_trace(draw_wireframe(0, 0, 0, in_L, in_W, in_H))
    
    for k in range(n_l):
        color = '#F5B7B1' if k % 2 == 0 else '#D2B4DE'
        for j in range(n_r):
            for i in range(n_c):
                px = i * p_d1
                py = j * p_d2
                pz = k * p_d3
                fig.add_trace(create_cube_mesh(px+0.5, py+0.5, pz+0.5, p_d1-1, p_d2-1, p_d3-1, color))
                fig.add_trace(draw_wireframe(px+0.5, py+0.5, pz+0.5, p_d1-1, p_d2-1, p_d3-1))

    camera = dict(eye=dict(x=1.5, y=1.5, z=1.5))
    fig.update_layout(height=350, showlegend=False, scene=dict(aspectmode='data', camera=camera), margin=dict(l=0, r=0, b=0, t=0))
    return fig

# ==========================================
# 4. Streamlit UI
# ==========================================
def main():
    st.set_page_config(page_title="Pallet Simulator", layout="wide")
    
    with st.sidebar:
        lang_code = st.selectbox("🌐 Language", ["Korean", "English"], index=0)
        t = TRANSLATIONS[lang_code]

    st.title(f"📦 Pallet Simulator - {lang_code}")
    st.markdown("---")

    with st.sidebar:
        st.subheader(t['sec1_title'])
        dims_str = st.text_input(t['dim_label'], value="180,120,50", help=t['dim_help'])
        allow_rotation = st.checkbox(t['rot_label'], value=True)
        
        c1, c2 = st.columns(2)
        weight_val = c1.number_input(t['weight_label'], value=5.0)
        max_box_w_g = c2.number_input(t['max_box_label'], value=10000.0)

        st.subheader(t['sec2_title'])
        box_type_label = st.selectbox(t['box_type_label'], t['box_types'])
        box_type_idx = t['box_types'].index(box_type_label)
        box_margins = [10, 14, 24]
        margin_val = box_margins[box_type_idx]
        
        c3, c4 = st.columns(2)
        min_qty_val = c3.number_input(t['min_qty'], value=10, step=5)
        max_qty_val = c4.number_input(t['max_qty'], value=100, step=5)

        st.subheader(t['sec3_title'])
        c5, c6, c7 = st.columns(3)
        pallet_l = c5.number_input(t['pl_l'], value=1100)
        pallet_w = c6.number_input(t['pl_w'], value=1100)
        pallet_h = c7.number_input(t['pl_h'], value=1650, help=t['pl_h_help'])

        st.markdown("---")
        btn_calc = st.button(t['btn_calc'], type="primary", use_container_width=True)

    if 'sim_results' not in st.session_state:
        st.session_state.sim_results = None

    sim = PalletLogic()

    if btn_calc:
        p_dims = parse_dimensions(dims_str)
        if not p_dims:
            st.error(t['err_dim_fmt'])
        else:
            try:
                pallet_dims = (pallet_l, pallet_w, pallet_h)
                candidates = sim.find_candidates(
                    p_dims, weight_val, max_box_w_g, box_type_idx, margin_val, 
                    min_qty_val, max_qty_val, pallet_dims, allow_rotation
                )
                if candidates:
                    st.session_state.sim_results = candidates
                    st.success(t['success_msg'].format(n=len(candidates)))
                else:
                    st.session_state.sim_results = None
                    st.error(t['err_no_result'])
            except Exception as e:
                st.error(f"Error: {e}")

    if st.session_state.sim_results:
        st.header(t['res_title'])
        results = st.session_state.sim_results
        
        options = {}
        for idx, res in enumerate(results):
            pat_name = t[res['interlock_desc_key']]
            if res.get('pinwheel_k', 0) > 1:
                pat_name += f" ({res['pinwheel_k']}-Layer)"
            warn = f" ⚠️{t['warn']}" if res['strength']['unsafe'] else ""
            label = (f"{t['rank']} {idx+1}{warn}: {pat_name} "
                     f"| {res['qty']}{t['qty_unit']} ({t['total_unit']} {res['total']}) "
                     f"| {t['eff']} {res['efficiency']:.1f}%")
            options[label] = res
        
        selected_label = st.radio(t['opt_label'], list(options.keys()), horizontal=False)
        res = options[selected_label]
        st_data = res['strength']
        
        p_dims_input = parse_dimensions(dims_str)
        used_dims = res.get('prod_dims_used', p_dims_input)
        b_l, b_w, b_h = res['box_outer']
        l_l, l_w, l_h = res['load_dims'] 
        
        st.markdown("---")
        
        st.subheader(t['detail_title'])
        if st_data['unsafe']:
            st.error(t['unsafe_msg'].format(sf=st_data['sf']))
        else:
            st.success(t['safe_msg'].format(sf=st_data['sf']))

        c_info, c_gauge = st.columns([2, 1])
        with c_info:
            st.markdown(f"""
            | {t['t_cat']} | {t['t_dim']} | {t['t_cont']} |
            | :--- | :--- | :--- |
            | **{t['l_prod_in']}** | {p_dims_input} | - |
            | **{t['l_prod_act']}** | **{used_dims}** | **{t['l_desc_act']}** |
            | **{t['l_box']}** | **{b_l} x {b_w} x {b_h}** | {res['qty']}{t['qty_unit']} / {res['weight']:.2f}kg |
            | **{t['l_load']}** | {int(l_l)} x {int(l_w)} x {int(l_h)} | {res['p_layers']}L / {t['total_unit']} {res['total']} |
            | **{t['eff_label']}** | **{res['efficiency']:.1f}%** | {t['bct']}: {st_data['bct']:.1f} kgf |
            """)
        with c_gauge:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta", value = st_data['load'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': t['g_title'], 'font': {'size': 12}},
                delta = {'reference': st_data['bct']/3, 'increasing': {'color': "red"}},
                gauge = {
                    'axis': {'range': [None, st_data['bct']], 'tickwidth': 1},
                    'bar': {'color': "#2E86C1"},
                    'steps': [{'range': [0, st_data['bct']/3], 'color': "#D4EFDF"}, {'range': [st_data['bct']/3, st_data['bct']], 'color': "#FADBD8"}],
                    'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': st_data['bct']/3}
                }
            ))
            fig_gauge.update_layout(height=180, margin=dict(l=20, r=20, t=30, b=0))
            st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("---")
        
        # 2. 파레트 뷰 (상단)
        c_p2d, c_p3d = st.columns(2)
        with c_p2d:
            st.subheader(t['viewer_pallet_2d'])
            fig_p2d = get_pallet_2d_fig(res, pallet_l, pallet_w)
            st.plotly_chart(fig_p2d, use_container_width=True)
        with c_p3d:
            st.subheader(t['viewer_pallet_3d'])
            fig_p3d = get_pallet_3d_fig(res, pallet_l, pallet_w)
            st.plotly_chart(fig_p3d, use_container_width=True)

        st.markdown("---")

        # 3. 박스 내부 뷰 (하단)
        c_b2d, c_b3d = st.columns(2)
        with c_b2d:
            st.subheader(t['viewer_box_2d'])
            fig_b2d = get_prod_layer_2d_fig(res)
            st.plotly_chart(fig_b2d, use_container_width=True)
        with c_b3d:
            st.subheader(t['viewer_box_3d'])
            fig_b3d = get_prod_3d_fig(res)
            st.plotly_chart(fig_b3d, use_container_width=True)

if __name__ == "__main__":
    main()