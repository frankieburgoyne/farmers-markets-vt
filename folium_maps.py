import os
import html
import pandas as pd
import folium
from folium.plugins import MarkerCluster

os.makedirs("maps", exist_ok=True)
df = pd.read_csv("us-farmers-markets-2026.csv")
df.columns = df.columns.str.strip()

# A market counts as "accepts SNAP/EBT" if EITHER column is True
df['snap_any'] = (df['accepts_snap'] == True) | (df['accepts_ebt'] == True)
# A market is "unknown" if BOTH columns are missing
known = df['accepts_snap'].notna() | df['accepts_ebt'].notna()

df['snap_status'] = 'Unknown (no data)'
df.loc[known & ~df['snap_any'], 'snap_status'] = 'Does not accept'
df.loc[df['snap_any'], 'snap_status'] = 'Accepts SNAP/EBT'

# some coordinates are missing, zero, or far outside the US - filter them out
map_df = df.dropna(subset=['lat', 'lng'])
map_df = map_df[(map_df['lat'].between(17, 72)) & (map_df['lng'].between(-180, -60))]
print("Markets with usable coordinates:", len(map_df), "of", len(df))

def clean(value):
    if pd.isna(value):
        return ""
    return html.escape(str(value))

us_map = folium.Map(
    location=[39.5, -98.35],
    zoom_start=4,
    max_zoom=16,
    tiles=None   # we add the background map ourselves below
)

# free light-gray background map from Esri, no API key needed
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    attr='Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
    name='Light gray basemap',
    max_zoom=16,
    control=False
).add_to(us_map)

# title banner at the top of the map
title_html = """
<div style="position: fixed; top: 10px; left: 50%; transform: translateX(-50%);
            z-index: 9999; background: white; padding: 8px 18px;
            border: 2px solid #444; border-radius: 6px; text-align: center;">
    <span style="font-size: 20px; font-weight: bold; text-decoration: underline;">
    US Farmers Markets: SNAP/EBT Acceptance
    </span><br>
</div>
"""
us_map.get_root().html.add_child(folium.Element(title_html))

# ------------------------------------------------------------
# Add the markets - one clustered layer per status
# ------------------------------------------------------------
# (color, shown by default?) for each status - same colors as the other charts
layers = {
    'Accepts SNAP/EBT': ('teal', True),
    'Does not accept': ('coral', True),
    'Unknown (no data)': ('gray', False)   # off by default, turn on in the layer control
}

for status, (color, show) in layers.items():
    # one layer per status so each can be switched on and off
    group = folium.FeatureGroup(name=f"{status}", show=show)
    cluster = MarkerCluster().add_to(group)

    subset = map_df[map_df['snap_status'] == status]
    for index, row in subset.iterrows():
        # text that shows when a dot is clicked
        popup_text = (
            f"<b>{clean(row['name'])}</b><br>"
            f"{clean(row['city'])}, {clean(row['state'])}<br>"
            f"Season: {clean(row['season'])}<br>"
            f"SNAP/EBT: {status}"
        )
        folium.CircleMarker(
            location=[row['lat'], row['lng']],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=260),
            tooltip=clean(row['name'])
        ).add_to(cluster)

    group.add_to(us_map)

# switch layers on and off
folium.LayerControl(collapsed=False).add_to(us_map)

# ------------------------------------------------------------
# Legend (small box in the bottom left)
# ------------------------------------------------------------
legend_html = """
<div style="position: fixed; bottom: 30px; left: 30px; z-index: 9999;
            background: white; padding: 10px 14px; border: 2px solid #444;
            border-radius: 6px; font-size: 13px;">
    <b>SNAP/EBT status</b><br>
    <span style="color: teal; font-size: 16px;">&#9679;</span> Accepts SNAP/EBT<br>
    <span style="color: coral; font-size: 16px;">&#9679;</span> Does not accept<br>
    <span style="color: gray; font-size: 16px;">&#9679;</span> Unknown (no data)
</div>
"""
us_map.get_root().html.add_child(folium.Element(legend_html))

# ------------------------------------------------------------
# Save the map (open the HTML file in a browser)
# ------------------------------------------------------------
us_map.save("maps/03_folium_market_map.html")
print("Saved maps/03_folium_market_map.html - open it in your browser.")