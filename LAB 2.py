import streamlit as st
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point, LineString
import folium
from streamlit_folium import folium_static
import json

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="PUO Survey Lot System", layout="wide")

# --- DATA PENGGUNA (ID & NAMA) ---
users_db = {
    "1": "AIN NURLYDIA",
    "2": "DHIA ARWIENA",
    "3": "QURRATU AIN",
    "admin": "PENTADBIR SYSTEMS"
}

# --- FUNGSI LOG MASUK ---
def login_page():
    _, col_mid, _ = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://www.puo.edu.my/webportal/wp-content/uploads/2023/12/Poli_Logo1-1024x599.png", width=350)
        st.markdown("### 🔑 Log Masuk Sistem")
        
        user_input = st.text_input("Username (1, 2, 3 atau admin)")
        pass_input = st.text_input("Password", type="password")
        
        if st.button("Masuk"):
            if user_input in users_db and pass_input == "puo123":
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user_input
                st.session_state["user_name"] = users_db[user_input]
                st.rerun()
            else:
                st.error("Username atau Password salah!")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- KAWALAN PAPARAN BERDASARKAN STATUS LOGIN ---
if not st.session_state["logged_in"]:
    login_page()
else:
    # --- SIDEBAR: PROFIL & KAWALAN ---
    with st.sidebar:
        st.markdown(f"""
            <div style="background-color: #FFC0CB; padding: 20px; border-radius: 15px; text-align: center; color: white;">
                <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                    <div style="width: 120px; height: 120px; border-radius: 50%; border: 4px solid white; overflow: hidden; background-color: white;">
                        <img src="https://raw.githubusercontent.com/Aris-T2/Static-Assets/main/anime_girl_profile.jpg" 
                             style="width: 100%; height: 100%; object-fit: cover;">
                    </div>
                </div>
                <h3 style="margin-top: 5px; margin-bottom: 0px; color: #D81B60; font-family: sans-serif;">Hai, {st.session_state['user_name']}!</h3>
                <p style="font-weight: bold; letter-spacing: 2px; margin-top: 5px; color: #D81B60;">{st.session_state['user_name']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**ID:** {st.session_state['user_id']}")
        
        if st.button("Log Keluar"):
            st.session_state["logged_in"] = False
            st.rerun()
        
        st.markdown("---")
        st.header("⚙️ Kawalan Paparan")
        sz_marker = st.slider("Saiz Marker Stesen", 5, 40, 22)
        sz_font = st.slider("Saiz Bearing/Jarak", 8, 25, 12)
        zoom_lvl = st.slider("Tahap Zoom Awal", 10, 25, 19)
        poly_color = st.color_picker("Warna Poligon", "#FFFF00")

    # --- CUSTOM CSS ---
    st.markdown("""
        <style>
        .header-box {
            background-color: white; padding: 25px; border-radius: 10px;
            border-left: 10px solid #D81B60; color: black;
            box-shadow: 2px 2px 15px rgba(0,0,0,0.3); margin-bottom: 20px;
        }
        .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; color: white; }
        </style>
        """, unsafe_allow_html=True)

    # --- HEADER UTAMA ---
    col_logo, col_title = st.columns([1, 3])
    with col_logo:
        st.image("https://www.puo.edu.my/webportal/wp-content/uploads/2023/12/Poli_Logo1-1024x599.png", width=220)
    with col_title:
        st.markdown(f"""<div class="header-box">
            <h1 style='margin:0;'>SISTEM SURVEY LOT</h1>
            <p style='margin:0;'>Politeknik Ungku Omar | Pengguna: {st.session_state['user_name']}</p>
        </div>""", unsafe_allow_html=True)

    # --- INPUT FAIL ---
    with st.sidebar:
        st.markdown("---")
        st.header("📂 Kawalan Fail")
        uploaded_file = st.file_uploader("Upload fail CSV (STN, E, N)", type=["csv"])
        base_map = st.radio("Pilihan Peta:", ["Google Hybrid (Satelit)", "Peta Jalan (OSM)"], index=0)

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if 'E' in df.columns and 'N' in df.columns:
            try:
                # --- PROSES GEOMETRI ---
                gdf_rso = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.E, df.N), crs="EPSG:4390")
                gdf_wgs = gdf_rso.to_crs("EPSG:4326")
                df['lat'], df['lon'] = gdf_wgs.geometry.y, gdf_wgs.geometry.x
                coords_meter = df[['E', 'N']].values.tolist()
                poly_obj = Polygon(coords_meter)
                area_val = poly_obj.area
                area_ha = area_val / 10000
                perimeter_val = poly_obj.length

                # --- BINA PETA ---
                m = folium.Map(location=[df['lat'].mean(), df['lon'].mean()], zoom_start=zoom_lvl, max_zoom=25)
                if "Google Hybrid" in base_map:
                    folium.TileLayer(
                        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                        attr='Google', name='Google Hybrid', max_zoom=25, overlay=False
                    ).add_to(m)

                # --- POPUP MAKLUMAT LOT ---
                lot_popup_html = f"""
                <div style="font-family: sans-serif; min-width: 200px; padding: 5px;">
                    <b style="color: #1A73E8; font-size: 14px;">MAKLUMAT LOT</b><br><br>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td><b>Surveyor:</b></td><td>{st.session_state['user_name']}</td></tr>
                        <tr><td><b>Luas:</b></td><td>{area_val:.3f} m²</td></tr>
                        <tr><td><b>Perimeter:</b></td><td>{perimeter_val:.3f} m</td></tr>
                    </table>
                </div>
                """

                folium.Polygon(
                    locations=list(zip(df.lat, df.lon)),
                    color=poly_color, weight=3, fill=True, fill_opacity=0.3,
                    popup=folium.Popup(lot_popup_html, max_width=300)
                ).add_to(m)

                # 2. Marker Stesen
                for i, row in df.iterrows():
                    stn_popup_html = f"""
                    <div style="font-family: Arial; width: 130px;">
                        <b style="color:red;">STESEN {int(row['STN'])}</b><br>
                        <hr style="margin:5px 0;">
                        <b>E:</b> {row['E']:.3f}<br>
                        <b>N:</b> {row['N']:.3f}
                    </div>
                    """
                    folium.CircleMarker(
                        [row['lat'], row['lon']], 
                        radius=sz_marker/2.5, color='white', fill=True, fill_color='red', fill_opacity=1
                    ).add_to(m)
                    
                    folium.Marker(
                        [row['lat'], row['lon']], 
                        popup=folium.Popup(stn_popup_html, max_width=200),
                        icon=folium.DivIcon(html=f'<b style="color:white; font-size:{sz_font}pt; transform: translate(-50%, -50%); display:block; text-align:center; width:30px; text-shadow: 1px 1px 2px black;">{int(row["STN"])}</b>')
                    ).add_to(m)

                # 3. Label Bearing & Jarak (Simpan info untuk Eksport)
                list_labels = []
                coords_wgs84 = list(zip(df.lat, df.lon))
                for i in range(len(coords_meter)):
                    p1, p2 = coords_meter[i], coords_meter[(i+1)%len(coords_meter)]
                    w1, w2 = coords_wgs84[i], coords_wgs84[(i+1)%len(coords_wgs84)]
                    
                    de, dn = p2[0]-p1[0], p2[1]-p1[1]
                    dist_val = np.sqrt(de**2 + dn**2)
                    brg_raw = np.degrees(np.arctan2(de, dn)) % 360
                    
                    deg, mnt = int(brg_raw), int((brg_raw - int(brg_raw)) * 60)
                    label_text = f"{deg}°{mnt:02d}' {dist_val:.2f}m"
                    list_labels.append(label_text)
                    
                    calc_angle = np.degrees(np.arctan2(p2[1]-p1[1], p2[0]-p1[0]))
                    rotation = -calc_angle 
                    
                    if rotation > 90: rotation -= 180
                    if rotation < -90: rotation += 180

                    folium.Marker(
                        location=[(w1[0]+w2[0])/2, (w1[1]+w2[1])/2], 
                        icon=folium.DivIcon(html=f"""
                            <div style="
                                transform: rotate({rotation}deg); 
                                color:#00008B; 
                                font-weight:bold; 
                                font-size:{sz_font}pt; 
                                text-align:center; 
                                width:200px; 
                                margin-left:-100px;
                                margin-top:-22px; 
                                text-shadow: 0px 0px 4px white, 0px 0px 6px white;
                                white-space: nowrap;
                                pointer-events: none;
                            ">
                                {label_text}
                            </div>""")
                    ).add_to(m)

                # Paparan Utama
                col_map, col_info = st.columns([3, 1])
                with col_map: 
                    folium_static(m, width=950, height=600)
                
                with col_info:
                    st.metric("Luas (m²)", f"{area_val:,.2f}")
                    st.metric("Luas (Hektar)", f"{area_ha:.4f}")
                    st.info(f"Surveyor: {st.session_state['user_name']}")
                    
                    st.markdown("---")
                    st.markdown("### 💾 Eksport Data")
                    
                    # --- LOGIK EKSPORT KHAS UNTUK QGIS ---
                    features = []
                    
                    # 1. TAMBAH POINT DAHULU (Supaya QGIS utamakan stesen)
                    for i, row in gdf_wgs.iterrows():
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "Layer": "Stesen",
                                "STN_ID": int(row['STN']),
                                "Label": str(int(row['STN'])),
                                "Easting": float(row['E']),
                                "Northing": float(row['N'])
                            },
                            "geometry": {"type": "Point", "coordinates": [row.geometry.x, row.geometry.y]}
                        })

                    # 2. TAMBAH LINE (Bearing & Jarak)
                    for i in range(len(coords_meter)):
                        p1, p2 = coords_meter[i], coords_meter[(i+1)%len(coords_meter)]
                        line_seg = LineString([p1, p2])
                        line_json = json.loads(gpd.GeoSeries([line_seg], crs="EPSG:4390").to_crs("EPSG:4326").to_json())
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "Layer": "Sempadan",
                                "Label": list_labels[i]
                            },
                            "geometry": line_json['features'][0]['geometry']
                        })

                    # 3. TAMBAH POLYGON (Isi Lot)
                    poly_json = json.loads(gpd.GeoSeries([poly_obj], crs="EPSG:4390").to_crs("EPSG:4326").to_json())
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "Layer": "Lot",
                            "Label": f"LUAS: {area_val:.2f}m²",
                            "Area_M2": round(area_val, 3),
                            "Surveyor": st.session_state['user_name']
                        },
                        "geometry": poly_json['features'][0]['geometry']
                    })
                    
                    final_geojson = {"type": "FeatureCollection", "features": features}
                    
                    st.download_button(
                        label="🚀 Export to QGIS (.geojson)",
                        data=json.dumps(final_geojson),
                        file_name="survey_lot_complete.geojson",
                        mime="application/json",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"Ralat: {e}")