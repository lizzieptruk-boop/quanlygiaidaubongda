import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Football Admin Ultimate", layout="wide")

if 'session_id' not in st.session_state:
    st.session_state.session_id = 0

# 2. KHỞI TẠO DỮ LIỆU
if 'df_doi' not in st.session_state:
    st.session_state.df_doi = pd.read_csv("Tin - Đội bóng.csv").dropna(subset=['Đội tuyển'])
if 'df_tran' not in st.session_state:
    df_t = pd.read_csv("Tin - Trận đấu.csv")
    df_t['Vòng'] = df_t['Vòng'].ffill()
    df_t = df_t.dropna(subset=[df_t.columns[4], df_t.columns[7]])
    df_t.iloc[:, 5] = pd.to_numeric(df_t.iloc[:, 5], errors='coerce').fillna(0).astype(int)
    df_t.iloc[:, 6] = pd.to_numeric(df_t.iloc[:, 6], errors='coerce').fillna(0).astype(int)
    st.session_state.df_tran = df_t
if 'history' not in st.session_state:
    st.session_state.history = []

# --- HÀM LƯU LỊCH SỬ ---
def record_history(msg):
    snapshot = {
        'msg': msg,
        'time': datetime.now().strftime("%H:%M:%S"),
        'df_doi_snap': st.session_state.df_doi.copy(),
        'df_tran_snap': st.session_state.df_tran.copy()
    }
    st.session_state.history.insert(0, snapshot)
    if len(st.session_state.history) > 20: st.session_state.history.pop()

# 3. BỘ NÃO TÍNH TOÁN
def calculate_bxh():
    teams = st.session_state.df_doi['Đội tuyển'].unique()
    bxh = pd.DataFrame(teams, columns=['Đội tuyển'])
    for col in ['Trận', 'Thắng', 'Hòa', 'Thua', 'BT', 'BB', 'HS', 'Điểm']: bxh[col] = 0
    for _, r in st.session_state.df_tran.iterrows():
        t1, s1, s2, t2 = r.iloc[4], r.iloc[5], r.iloc[6], r.iloc[7]
        if t1 in teams and t2 in teams:
            for t, sm, so in [(t1, s1, s2), (t2, s2, s1)]:
                idx_list = bxh[bxh['Đội tuyển'] == t].index
                if len(idx_list) > 0:
                    idx = idx_list[0]
                    bxh.at[idx, 'Trận'] += 1
                    bxh.at[idx, 'BT'] += sm
                    bxh.at[idx, 'BB'] += so
                    if sm > so: 
                        bxh.at[idx, 'Thắng'] += 1
                        bxh.at[idx, 'Điểm'] += 3
                    elif sm == so: 
                        bxh.at[idx, 'Hòa'] += 1
                        bxh.at[idx, 'Điểm'] += 1
                    else: 
                        bxh.at[idx, 'Thua'] += 1
    return bxh.sort_values(by=['Điểm', 'HS', 'BT'], ascending=False).reset_index(drop=True)

# 4. GIAO DIỆN
st.title("⚽ QUẢN LÝ GIẢI ĐẤU BÓNG ĐÁ")
search = st.text_input("🔍 Tra cứu đội bóng:", placeholder="Nhập tên đội...")

tab1, tab2, tab3, tab4 = st.tabs(["📊 BXH", "📅 TRẬN ĐẤU", "🛠 QUẢN LÝ", "📜 LỊCH SỬ"])

with tab1:
    df_bxh = calculate_bxh()
    if search:
        df_bxh = df_bxh[df_bxh['Đội tuyển'].str.contains(search, case=False, na=False)]
    st.dataframe(df_bxh, use_container_width=True)

with tab2:
    df_matches = st.session_state.df_tran
    if search:
        df_matches = df_matches[(df_matches.iloc[:,4].str.contains(search, case=False, na=False)) | (df_matches.iloc[:,7].str.contains(search, case=False, na=False))]
    
    for v in sorted(df_matches['Vòng'].unique()):
        with st.expander(f"Vòng {int(v)}", expanded=True):
            v_matches = df_matches[df_matches['Vòng'] == v]
            for idx, r in v_matches.iterrows():
                c1, sc1, vs, sc2, c2 = st.columns([3,1,0.5,1,3])
                with c1: st.write(f"**{r.iloc[4]}**")
                with sc1: 
                    n1 = st.number_input("", value=int(r.iloc[5]), key=f"s1_{idx}_{st.session_state.session_id}", step=1, label_visibility="collapsed")
                with vs: st.write("-")
                with sc2: 
                    n2 = st.number_input("", value=int(r.iloc[6]), key=f"s2_{idx}_{st.session_state.session_id}", step=1, label_visibility="collapsed")
                with c2: st.write(f"**{r.iloc[7]}**")
                
                if n1 != r.iloc[5] or n2 != r.iloc[6]:
                    msg = f"Sửa Vòng {int(v)}: {r.iloc[4]} vs {r.iloc[7]} ({r.iloc[5]}-{r.iloc[6]} thành {n1}-{n2})"
                    record_history(msg)
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[5]] = n1
                    st.session_state.df_tran.at[idx, st.session_state.df_tran.columns[6]] = n2
                    st.rerun()

with tab3:
    c_add, c_del = st.columns(2)
    with c_add:
        st.subheader("➕ Thêm Đội & Xếp Vòng")
        new_name = st.text_input("Tên đội mới:", key=f"in_add_{st.session_state.session_id}")
        if st.button("Bước 1: Tạo đội"):
            if new_name and new_name not in st.session_state.df_doi['Đội tuyển'].values:
                st.session_state.temp_team = new_name
                st.rerun()

        if 'temp_team' in st.session_state:
            st.markdown(f"### 🚩 Xếp lịch: **{st.session_state.temp_team}**")
            others = st.session_state.df_doi['Đội tuyển'].unique()
            v_max_hint = int(st.session_state.df_tran['Vòng'].max()) if not st.session_state.df_tran.empty else 1
            
            new_data = []
            for i, opp in enumerate(others):
                st.write(f"**Trận đấu với {opp}:**")
                v_col, s1_col, vs_col, s2_col = st.columns([2.5, 1, 0.5, 1])
                v_val = v_col.number_input(f"Vòng thứ mấy?", 1, 100, value=v_max_hint, key=f"v_set_{i}")
                s1_val = s1_col.number_input(f"Bàn {st.session_state.temp_team}", 0, key=f"s1_set_{i}")
                vs_col.markdown("<br>vs", unsafe_allow_html=True)
                s2_val = s2_col.number_input(f"Bàn {opp}", 0, key=f"s2_set_{i}")
                new_data.append([v_val, None, None, None, st.session_state.temp_team, s1_val, s2_val, opp])
                st.divider()

            if st.button("BƯỚC 2: XÁC NHẬN LƯU LỊCH THI ĐẤU"):
                record_history(f"Thêm đội {st.session_state.temp_team} và xếp lịch")
                st.session_state.df_doi = pd.concat([st.session_state.df_doi, pd.DataFrame([{"Đội tuyển": st.session_state.temp_team}])], ignore_index=True)
                new_df = pd.DataFrame(new_data, columns=st.session_state.df_tran.columns)
                st.session_state.df_tran = pd.concat([st.session_state.df_tran, new_df], ignore_index=True)
                del st.session_state.temp_team
                st.session_state.session_id += 1
                st.rerun()

    with c_del:
        st.subheader("🗑️ Xóa Đội")
        target = st.selectbox("Chọn đội:", st.session_state.df_doi['Đội tuyển'].tolist(), key=f"del_sel_{st.session_state.session_id}")
        if st.button("Xác nhận Xóa"):
            record_history(f"Xóa đội: {target}")
            st.session_state.df_doi = st.session_state.df_doi[st.session_state.df_doi['Đội tuyển'] != target]
            st.session_state.df_tran = st.session_state.df_tran[(st.session_state.df_tran.iloc[:,4] != target) & (st.session_state.df_tran.iloc[:,7] != target)]
            st.rerun()

with tab4:
    st.subheader("📜 Nhật ký & Recover")
    if not st.session_state.history: st.write("Trống.")
    for i, item in enumerate(st.session_state.history):
        c_txt, c_btn = st.columns([7, 3])
        c_txt.warning(f"🕒 {item['time']} - {item['msg']}")
        if c_btn.button("♻️ PHỤC HỒI", key=f"rec_{i}"):
            st.session_state.df_doi = item['df_doi_snap'].copy()
            st.session_state.df_tran = item['df_tran_snap'].copy()
            st.session_state.history = st.session_state.history[i+1:]
            st.session_state.session_id += 1 
            st.rerun()