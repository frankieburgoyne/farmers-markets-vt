import os
import pandas as pd
import plotly.express as px

os.makedirs("plotly_maps", exist_ok=True)

df = pd.read_csv("us-farmers-markets-2026.csv")
df.columns = df.columns.str.strip()

# A market counts as "accepts SNAP/EBT" if EITHER column is True
df['snap_any'] = (df['accepts_snap'] == True) | (df['accepts_ebt'] == True)
# A market is "unknown" if BOTH columns are missing
known = df['accepts_snap'].notna() | df['accepts_ebt'].notna()

df['snap_status'] = 'Unknown (no data)'
df.loc[known & ~df['snap_any'], 'snap_status'] = 'Does not accept'
df.loc[df['snap_any'], 'snap_status'] = 'Accepts SNAP/EBT'

#map 1
markets_per_state = df.groupby('state')['name'].count()
snap_per_state = df.groupby('state')['snap_any'].sum()
snap_pct = (snap_per_state / markets_per_state * 100).round(1)

state_stats = pd.DataFrame({
    'markets': markets_per_state,
    'snap_markets': snap_per_state,
    'snap_pct': snap_pct
}).reset_index()   # 'state' becomes a normal column (two-letter code)

fig1 = px.choropleth(
    state_stats,
    locations='state',            # two-letter state codes
    locationmode='USA-states',
    color='snap_pct',
    scope='usa',
    color_continuous_scale='Teal',
    range_color=(0, 30),          # cap the scale so RI (60%) doesn't wash out the rest
    hover_name='state',
    hover_data={'state': False, 'markets': True, 'snap_markets': True, 'snap_pct': ':.1f'},
    labels={'snap_pct': '% accepting<br>SNAP/EBT',
            'markets': 'Markets', 'snap_markets': 'Accept SNAP/EBT'},
    title='<b><u>Share of Farmers Markets Accepting SNAP/EBT, by State</u></b><br>'
)
fig1.update_layout(
    margin=dict(l=10, r=10, t=100, b=10),
    title_x=0.5,           # 0.5 = centered
    title_font_size=26     # bigger title
)

fig1.write_html("maps/01_state_choropleth.html")
fig1.show()

#map 2
map_df = df.dropna(subset=['lat', 'lng'])
map_df = map_df[(map_df['lat'].between(17, 72)) & (map_df['lng'].between(-180, -60))]
print("Markets with usable coordinates:", len(map_df), "of", len(df))

# draw order: unknown first, SNAP/EBT last, so the teal dots sit on top
order = ['Unknown (no data)', 'Does not accept', 'Accepts SNAP/EBT']
map_df = map_df.sort_values('snap_status', key=lambda col: col.map(order.index))

fig2 = px.scatter_geo(
    map_df,
    lat='lat',
    lon='lng',
    color='snap_status',
    color_discrete_map={
        'Accepts SNAP/EBT': 'teal',
        'Does not accept': 'coral',
        'Unknown (no data)': 'lightgray'
    },
    category_orders={'snap_status': order},
    hover_name='name',
    hover_data={'city': True, 'state': True, 'season': True,
                'snap_status': False, 'lat': False, 'lng': False},
    scope='usa',
    opacity=0.7,
    title='<b><u>US Farmers Markets: SNAP/EBT Acceptance</u></b>'
)
fig2.update_traces(marker=dict(size=4))
fig2.update_layout(
    legend_title_text='SNAP/EBT status',
    legend=dict(itemsizing='constant'),
    margin=dict(l=10, r=10, t=80, b=10),
    title_x=0.5,
    title_font_size=26
)

fig2.write_html("maps/02_market_points.html")
fig2.show()