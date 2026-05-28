import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Pricing Elasticity Engine",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #F7F7F5;
}
.main { background-color: #F7F7F5; }
.block-container { padding: 2rem 2.5rem; }

[data-testid="stSidebar"] {
    background-color: #1a1a2e;
    border-right: none;
}
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label {
    color: #a0a0b0 !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    border: 1px solid #EBEBEB;
    height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-label {
    font-size: 11px;
    font-weight: 500;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.07em;
}
.kpi-value {
    font-size: 28px;
    font-weight: 600;
    color: #1a1a2e;
    line-height: 1;
}
.kpi-sub { font-size: 12px; color: #1D9E75; font-weight: 500; }
.kpi-sub.negative { color: #E24B4A; }

.chart-title {
    font-size: 14px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 4px;
}
.chart-subtitle {
    font-size: 12px;
    color: #888;
    margin-bottom: 16px;
}

.main-title {
    font-size: 28px;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 4px;
}
.main-subtitle {
    font-size: 14px;
    color: #888;
    margin-bottom: 24px;
}

.divider {
    height: 1px;
    background: #EBEBEB;
    margin: 24px 0;
}

.insight-box {
    background: #F0FDF9;
    border: 1px solid #6EE7C7;
    border-radius: 10px;
    padding: 14px 18px;
    margin-top: 12px;
}
.insight-title {
    font-size: 12px;
    font-weight: 600;
    color: #0F6E56;
    margin-bottom: 4px;
}
.insight-text {
    font-size: 12px;
    color: #085041;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base = Path(__file__).parent.parent
    return pd.read_csv(base / "data/elasticity_by_category.csv")

elasticity_df = load_data()

def price_optimizer(current_price, current_qty,
                    elasticity, std_error, n_sims=10000):
    e_samples   = np.random.normal(elasticity, std_error, n_sims)
    multipliers = np.linspace(0.5, 2.0, 100)
    rows = []
    for mult in multipliers:
        new_price = current_price * mult
        revenues  = new_price * current_qty * np.exp(e_samples * np.log(mult))
        rows.append({
            "price":       round(new_price, 2),
            "rev_mean":    revenues.mean(),
            "rev_p10":     np.percentile(revenues, 10),
            "rev_p90":     np.percentile(revenues, 90),
            "prob_better": (revenues > current_price * current_qty).mean()
        })
    return pd.DataFrame(rows)

with st.sidebar:
    st.markdown("### ⚙️ Controls")
    st.markdown("---")
    category = st.selectbox(
        "Product category",
        options=elasticity_df["category"].str.replace("_", " ").str.title().tolist()
    )
    st.markdown(" ")
    current_price = st.slider("Current price (R$)", 10, 500, 100, step=5)
    current_qty   = st.slider("Monthly sales (units)", 10, 2000, 200, step=10)
    st.markdown("---")
    st.markdown("##### 📖 Methodology")
    st.markdown("""
Elasticity estimated using **2SLS IV regression**.
Freight cost used as instrument to correct OLS endogeneity bias.

Monte Carlo runs **10,000 simulations** per price point.
    """)
    st.markdown("---")
    st.markdown("Built by **Satyam Patel**  \nASU · Business Analytics + Economics")

st.markdown('<div class="main-title">Pricing Elasticity Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">Brazilian e-commerce · Olist dataset · IV regression (2SLS) · Monte Carlo simulation · 108k transactions</div>', unsafe_allow_html=True)

cat_key     = category.lower().replace(" ", "_")
e_row       = elasticity_df[elasticity_df["category"] == cat_key].iloc[0]
e_mean, e_se = e_row["elasticity"], e_row["std_error"]
results     = price_optimizer(current_price, current_qty, e_mean, e_se)
best        = results.loc[results["rev_mean"].idxmax()]
current_rev = current_price * current_qty
uplift      = (best["rev_mean"] / current_rev - 1) * 100

c1, c2, c3, c4 = st.columns(4)

with c1:
    direction = "Elastic" if e_mean < 0 else "Inelastic"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Price elasticity</div>
        <div class="kpi-value">{e_mean:.2f}</div>
        <div class="kpi-sub">{direction}</div>
    </div>""", unsafe_allow_html=True)

with c2:
    diff = best['price'] - current_price
    diff_str = f"{'↑' if diff > 0 else '↓'} R${abs(diff):.0f} from current"
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Optimal price</div>
        <div class="kpi-value">R${best['price']:.0f}</div>
        <div class="kpi-sub">{diff_str}</div>
    </div>""", unsafe_allow_html=True)

with c3:
    color_class = "negative" if uplift < 0 else ""
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Revenue uplift</div>
        <div class="kpi-value">{uplift:.1f}%</div>
        <div class="kpi-sub {color_class}">vs current pricing</div>
    </div>""", unsafe_allow_html=True)

with c4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Confidence</div>
        <div class="kpi-value">{best['prob_better']*100:.0f}%</div>
        <div class="kpi-sub">probability of improvement</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='margin-top:20px'></div>", unsafe_allow_html=True)

left, right = st.columns([3, 2])

with left:
    st.markdown(f'<div class="chart-title">Revenue optimization curve</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-subtitle">{category} · Monte Carlo 10k simulations · 80% confidence band</div>', unsafe_allow_html=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=results["price"], y=results["rev_mean"],
        name="Expected revenue",
        line=dict(color="#4F46E5", width=2.5)
    ))
    fig.add_trace(go.Scatter(
        x=list(results["price"]) + list(results["price"][::-1]),
        y=list(results["rev_p90"]) + list(results["rev_p10"][::-1]),
        fill="toself", fillcolor="rgba(79,70,229,0.08)",
        line=dict(color="rgba(0,0,0,0)"),
        name="80% confidence interval"
    ))
    fig.add_vline(x=current_price, line_color="#F59E0B",
                  line_dash="dash", line_width=1.5,
                  annotation_text=f"Current R${current_price}",
                  annotation_font_size=11,
                  annotation_position="top right")
    fig.add_vline(x=best["price"], line_color="#10B981",
                  line_dash="dash", line_width=1.5,
                  annotation_text=f"Optimal R${best['price']:.0f}",
                  annotation_font_size=11,
                  annotation_position="top left")
    fig.update_layout(
        xaxis_title="Price (R$)",
        yaxis_title="Expected monthly revenue (R$)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=380,
        margin=dict(t=20, b=40, l=60, r=20),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.01, xanchor="left", x=0),
        font=dict(size=11, color="#555"),
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0", linecolor="#E0E0E0"),
        yaxis=dict(showgrid=True, gridcolor="#F0F0F0", linecolor="#E0E0E0")
    )
    st.plotly_chart(fig, use_container_width=True)

    if uplift > 50:
        st.markdown(f"""
        <div class="insight-box">
            <div class="insight-title">💡 Key insight</div>
            <div class="insight-text">
                <b>{category}</b> is highly price-sensitive (elasticity {e_mean:.2f}).
                Moving from R${current_price} to R${best['price']:.0f} could generate
                <b>{uplift:.0f}% more revenue</b> with {best['prob_better']*100:.0f}% confidence.
            </div>
        </div>""", unsafe_allow_html=True)

with right:
    st.markdown('<div class="chart-title">Elasticity by category</div>', unsafe_allow_html=True)
    st.markdown('<div class="chart-subtitle">Red = price sensitive · Blue = inelastic / Veblen effect</div>', unsafe_allow_html=True)

    plot_df = elasticity_df.sort_values("elasticity")
    colors  = ["#EF4444" if v < -2 else "#FCA5A5" if v < 0
               else "#93C5FD" if v < 3 else "#1D4ED8"
               for v in plot_df["elasticity"]]

    fig2 = go.Figure(go.Bar(
        x=plot_df["elasticity"],
        y=plot_df["category"].str.replace("_", " ").str.title(),
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        error_x=dict(type="data", array=plot_df["std_error"],
                     visible=True, color="#CCCCCC", thickness=1.5)
    ))
    fig2.add_vline(x=0, line_color="#1a1a2e", line_width=1)
    fig2.update_layout(
        xaxis_title="Elasticity coefficient",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=380,
        margin=dict(t=20, b=40, l=10, r=20),
        font=dict(size=10, color="#555"),
        xaxis=dict(showgrid=True, gridcolor="#F0F0F0", linecolor="#E0E0E0", zeroline=False),
        yaxis=dict(showgrid=False, linecolor="#E0E0E0")
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
st.markdown("""
<div style='display:flex; justify-content:space-between; align-items:center'>
    <div style='font-size:12px; color:#aaa'>
        Built by <b style='color:#555'>Satyam Patel</b> ·
        Business Analytics + Economics, ASU ·
        <a href='https://github.com/devsp18' style='color:#4F46E5'>github.com/devsp18</a>
    </div>
    <div style='font-size:11px; color:#bbb'>
        Dataset: Olist Brazilian E-Commerce · 108k transactions · 2016–2018
    </div>
</div>
""", unsafe_allow_html=True)