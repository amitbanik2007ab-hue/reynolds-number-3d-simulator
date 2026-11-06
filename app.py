import time
import math
import numpy as np
import streamlit as st
import plotly.graph_objects as go
from streamlit_mic_recorder import speech_to_text

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(
    page_title="Reynolds Number 3D Simulator - JU",
    page_icon="🌊",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.1rem; padding-bottom: 1.5rem; }
      h1 { line-height: 1.15; }
      div[data-testid="stSlider"] { padding-top: 0.35rem; padding-bottom: 0.65rem; }
      div.stButton > button { min-height: 2.8rem; width: 100%; font-weight: 600; }
      .ju-footer { text-align: center; margin-top: 2.2rem; color: #777; font-size: 0.9rem; }
      .ju-footer strong { font-family: "Times New Roman", Times, serif; font-size: 1.05rem; color: inherit; }
      .small-note { color: #777; font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Reynolds Number 3D Simulator - JU - Free For All")
st.caption("Move slider OR speak: “increase diameter”")

# ------------------------------------------------------------
# Fluid data at approximately 25 °C
# ------------------------------------------------------------
FLUIDS = {
    "Water": {"density": 997.0, "viscosity": 0.00089},
    "Oil": {"density": 870.0, "viscosity": 0.08},
    "Honey": {"density": 1420.0, "viscosity": 10.0},
    "Air": {"density": 1.2, "viscosity": 0.000018},
}

PRESETS = {
    "JU Class Example": {"fluid": "Water", "velocity": 0.5, "diameter": 0.05},
    "JU Hostel Example": {"fluid": "Water", "velocity": 0.1, "diameter": 0.01},
    "Kolkata Water Supply (illustrative)": {
        "fluid": "Water", "velocity": 1.5, "diameter": 0.15
    },
}

# ------------------------------------------------------------
# Session state defaults
# ------------------------------------------------------------
defaults = {
    "fluid": "Water",
    "velocity": 0.5,
    "diameter": 0.05,
    "voice_message": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def apply_preset(preset_name):
    preset = PRESETS[preset_name]
    st.session_state.fluid = preset["fluid"]
    st.session_state.velocity = preset["velocity"]
    st.session_state.diameter = preset["diameter"]


# ------------------------------------------------------------
# Presets and reset
# ------------------------------------------------------------
st.subheader("Quick examples")
preset_cols = st.columns(3)
for col, preset_name in zip(preset_cols, PRESETS):
    with col:
        if st.button(preset_name, key=f"preset_{preset_name}"):
            apply_preset(preset_name)
            st.rerun()

if st.button("↺ Reset to JU Class Example", type="primary"):
    apply_preset("JU Class Example")
    st.rerun()

# ------------------------------------------------------------
# Voice control
# ------------------------------------------------------------
st.subheader("Voice control")
st.caption(
    "Tap the microphone, speak a command in English, then stop recording. "
    "Examples: “increase diameter”, “velocity barao”, “honey koro”."
)

try:
    spoken_text = speech_to_text(
        language="en",
        start_prompt="🎤 Speak Command",
        stop_prompt="⏹️ Stop Recording",
        just_once=True,
        key="ju_voice_control",
    )
except Exception as exc:
    spoken_text = None
    st.warning(
        "Microphone control could not start in this browser/session. "
        "Use the sliders instead. Check microphone permission and HTTPS. "
        f"Technical detail: {exc}"
    )

if spoken_text:
    command = spoken_text.lower().strip()
    st.session_state.voice_message = spoken_text

    if any(term in command for term in ["increase diameter", "diameter barao", "diameter barhao"]):
        st.session_state.diameter = min(0.2, round(st.session_state.diameter + 0.01, 3))
        st.success(f"Diameter increased. Recognized: “{spoken_text}”")
    elif any(term in command for term in ["decrease diameter", "diameter komao", "diameter kam karo"]):
        st.session_state.diameter = max(0.01, round(st.session_state.diameter - 0.01, 3))
        st.success(f"Diameter decreased. Recognized: “{spoken_text}”")
    elif any(term in command for term in ["increase velocity", "velocity barao", "velocity barhao"]):
        st.session_state.velocity = min(5.0, round(st.session_state.velocity + 0.1, 2))
        st.success(f"Velocity increased. Recognized: “{spoken_text}”")
    elif any(term in command for term in ["decrease velocity", "velocity komao", "velocity kam karo"]):
        st.session_state.velocity = max(0.1, round(st.session_state.velocity - 0.1, 2))
        st.success(f"Velocity decreased. Recognized: “{spoken_text}”")
    elif "make it laminar" in command:
        # Reduce velocity to a value that targets Re < 2300 for the current fluid/diameter.
        props = FLUIDS[st.session_state.fluid]
        target_v = 0.8 * 2300 * props["viscosity"] / (
            props["density"] * st.session_state.diameter
        )
        st.session_state.velocity = min(5.0, max(0.1, round(target_v, 2)))
        st.info("Adjusted velocity toward the laminar range; check the live Reynolds number.")
    elif any(term in command for term in ["honey", "honey koro"]):
        st.session_state.fluid = "Honey"
        st.success("Fluid changed to Honey.")
    elif "water" in command:
        st.session_state.fluid = "Water"
        st.success("Fluid changed to Water.")
    elif "oil" in command:
        st.session_state.fluid = "Oil"
        st.success("Fluid changed to Oil.")
    elif "air" in command:
        st.session_state.fluid = "Air"
        st.success("Fluid changed to Air.")
    else:
        st.info(
            f"Recognized “{spoken_text}”, but no matching command was found. "
            "Try “increase diameter” or “change fluid to honey”."
        )

# ------------------------------------------------------------
# User controls
# ------------------------------------------------------------
st.subheader("Simulator controls")
control_left, control_right = st.columns([1, 1], gap="large")

with control_left:
    st.selectbox("Choose fluid", list(FLUIDS.keys()), key="fluid")
    st.slider(
        "Flow velocity (m/s)",
        min_value=0.1,
        max_value=5.0,
        step=0.1,
        key="velocity",
    )

with control_right:
    st.slider(
        "Pipe diameter (m)",
        min_value=0.01,
        max_value=0.20,
        step=0.005,
        key="diameter",
    )

fluid = st.session_state.fluid
velocity = float(st.session_state.velocity)
diameter = float(st.session_state.diameter)
density = FLUIDS[fluid]["density"]
viscosity = FLUIDS[fluid]["viscosity"]

# Reynolds number: Re = rho * V * D / mu
reynolds = density * velocity * diameter / viscosity

if reynolds < 2300:
    regime = "Laminar"
    flow_color = "#35A7FF"
    regime_description = "Fluid moves in smooth, orderly layers with little mixing."
elif reynolds <= 4000:
    regime = "Transitional"
    flow_color = "#F4B942"
    regime_description = "Flow is in the transition zone; disturbances may grow."
else:
    regime = "Turbulent"
    flow_color = "#F06445"
    regime_description = "Flow is irregular, with strong mixing and fluctuating motion."

# ------------------------------------------------------------
# Live result and speedometer
# ------------------------------------------------------------
st.subheader("Live result")
metric_cols = st.columns(3)
metric_cols[0].metric("Reynolds number", f"{reynolds:,.1f}")
metric_cols[1].metric("Flow regime", regime)
metric_cols[2].metric("Fluid", fluid)

gauge = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=reynolds,
        number={"valueformat": ",.0f"},
        title={"text": "Reynolds Number"},
        gauge={
            "axis": {"range": [0, max(5000, min(20000, reynolds * 1.15))]},
            "bar": {"color": flow_color},
            "steps": [
                {"range": [0, 2300], "color": "#DDF3E4"},
                {"range": [2300, 4000], "color": "#FFF0C2"},
                {"range": [4000, max(5000, min(20000, reynolds * 1.15))], "color": "#F9D8D2"},
            ],
            "threshold": {
                "line": {"color": "#333", "width": 3},
                "thickness": 0.8,
                "value": reynolds,
            },
        },
    )
)
gauge.update_layout(height=260, margin=dict(l=20, r=20, t=45, b=10))
st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})

st.markdown(f"**Flow explanation:** {regime_description}")
st.latex(r"\mathrm{Re} = \frac{\rho V D}{\mu}")

# ------------------------------------------------------------
# 3D pipe and animated particles
st.subheader("3D pipe view")

animate_particles = st.checkbox("▶️ Animate Particles", value=True)

animation_speed = st.slider(
    "Animation Speed",
    min_value=0.5,
    max_value=2.0,
    value=1.0,
    step=0.1,
)

pipe_length = 1.8
particle_count = 30

if "particle_animation_start" not in st.session_state:
    st.session_state.particle_animation_start = time.monotonic()

@st.fragment(run_every=0.05 if animate_particles else None)
def render_animated_pipe():

    # Read live slider values on every refresh
    v = float(st.session_state.velocity)
    d = float(st.session_state.diameter)
    fluid_now = st.session_state.fluid

    rho = FLUIDS[fluid_now]["density"]
    mu = FLUIDS[fluid_now]["viscosity"]
    re = rho * v * d / mu

    if re < 2300:
        regime_now = "Laminar"
        particle_color = "#35A7FF"
    elif re <= 4000:
        regime_now = "Transitional"
        particle_color = "#F4B942"
    else:
        regime_now = "Turbulent"
        particle_color = "#F06445"

    # Time elapsed since animation began
    elapsed = time.monotonic() - st.session_state.particle_animation_start

    # Starting positions of 30 particles
    particle_id = np.arange(particle_count)
    base_x = np.linspace(0, pipe_length, particle_count, endpoint=False)

    rng = np.random.default_rng(7)

    if regime_now == "Laminar":
        # Three orderly layers; no sideways mixing
        base_y = np.repeat([-0.10, 0.0, 0.10], 10)
        base_z = np.repeat([0.05, 0.0, -0.05], 10)
        wobble = 0.0

    else:
        # Spread particles across the pipe
        angle = rng.uniform(0, 2 * np.pi, particle_count)
        r = np.sqrt(rng.uniform(0, 1, particle_count)) * 0.13
        base_y = r * np.cos(angle)
        base_z = r * np.sin(angle)

        wobble = 0.008 if regime_now == "Transitional" else 0.02

    # Main movement: faster velocity = faster particle movement
    if animate_particles:
        particle_x = (
            base_x + v * elapsed * animation_speed
        ) % pipe_length
    else:
        particle_x = base_x

    # Wobble for transitional and turbulent flow
    phase = elapsed * 5 + particle_id

    particle_y = base_y + np.sin(phase) * wobble
    particle_z = base_z + np.cos(phase) * wobble

    # Draw the pipe
    theta = np.linspace(0, 2 * np.pi, 48)
    x_axis = np.linspace(0, pipe_length, 32)
    theta_grid, x_grid = np.meshgrid(theta, x_axis)

    radius = 0.28
    y_pipe = radius * np.cos(theta_grid)
    z_pipe = radius * np.sin(theta_grid)

    pipe = go.Surface(
        x=x_grid,
        y=y_pipe,
        z=z_pipe,
        opacity=0.18,
        showscale=False,
        colorscale=[[0, "#9BCBEA"], [1, "#9BCBEA"]],
        hoverinfo="skip",
    )

    particles = go.Scatter3d(
        x=particle_x,
        y=particle_y,
        z=particle_z,
        mode="markers",
        marker=dict(
            size=5,
            color=particle_color,
            opacity=0.95,
        ),
        name="Moving particles",
    )

    fig = go.Figure(data=[pipe, particles])

    fig.update_layout(
        height=560,
        margin=dict(l=0, r=0, t=10, b=0),
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            aspectmode="manual",
            aspectratio=dict(x=2.5, y=1, z=1),
            camera=dict(eye=dict(x=1.7, y=1.6, z=1.2)),
        ),
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "responsive": True,
        },
    )

render_animated_pipe()

st.caption(
    "Conceptual 3D flow animation, not a computational-fluid-dynamics simulation."
)

# Use a repeatable set of particle positions; color indicates flow regime.
rng = np.random.default_rng(7)
particle_x = np.linspace(0.08, 1.72, 30)
particle_angle = rng.uniform(0, 2 * np.pi, 30)
particle_r = np.sqrt(rng.uniform(0.0, 0.72, 30)) * radius * 0.78
particle_y = particle_r * np.cos(particle_angle)
particle_z = particle_r * np.sin(particle_angle)

# Show orderly layers for laminar flow, and a more spread-out arrangement for
# transitional/turbulent flow. This is a conceptual illustration, not CFD.
if regime == "Laminar":
    particle_y = np.linspace(-0.12, 0.12, 30)
    particle_z = np.zeros(30)
elif regime == "Transitional":
    particle_y = particle_y * 1.15
    particle_z = particle_z * 1.15

particles = go.Scatter3d(
    x=particle_x,
    y=particle_y,
    z=particle_z,
    mode="markers",
    marker={
        "size": 5,
        "color": flow_color,
        "opacity": 0.95,
        "line": {"width": 0.5, "color": "white"},
    },
    name="Flow particles",
    hovertemplate="Representative particle<extra></extra>",
)

fig = go.Figure(data=[pipe, particles])
fig.update_layout(
    height=560,
    margin=dict(l=0, r=0, t=10, b=0),
    scene={
        "xaxis": {"visible": False},
        "yaxis": {"visible": False},
        "zaxis": {"visible": False},
        "aspectmode": "manual",
        "aspectratio": {"x": 2.5, "y": 1, "z": 1},
        "camera": {"eye": {"x": 1.7, "y": 1.6, "z": 1.2}},
    },
    showlegend=False,
)
st.plotly_chart(
    fig,
    use_container_width=True,
    config={"scrollZoom": True, "displayModeBar": True, "responsive": True},
)
st.caption(
    "Conceptual 3D illustration of the flow regime; it is not a computational-fluid-dynamics (CFD) simulation."
)

# ------------------------------------------------------------
# Live values table
# ------------------------------------------------------------
st.subheader("Live data table")
st.table(
    {
        "Parameter": [
            "Density (kg/m³)",
            "Dynamic viscosity (Pa·s)",
            "Velocity (m/s)",
            "Diameter (m)",
            "Reynolds number",
        ],
        "Live value": [
            f"{density:,.6g}",
            f"{viscosity:,.6g}",
            f"{velocity:.3f}",
            f"{diameter:.3f}",
            f"{reynolds:,.2f}",
        ],
    }
)

# ------------------------------------------------------------
# Story mode and rule-based explanation
# ------------------------------------------------------------
st.subheader("Story Mode – JU Hostel Water Problem")
st.write(
    "Imagine water is not reaching the 4th floor of a JU hostel. "
    "In this simplified learning example, explore how pipe diameter changes "
    "the Reynolds number when average velocity is held fixed."
)
if reynolds < 2300:
    st.success("Laminar range reached (Re < 2300) in this simplified example.")
elif reynolds > 4000:
    st.warning(
        "Re is above 4000. Try changing the pipe diameter or fluid and observe "
        "how the Reynolds number responds."
    )
else:
    st.info("You are in the transitional range (2300–4000).")

with st.expander("AI Explain (rule-based learning explanation)"):
    st.write(
        f"For {fluid}, density is {density:g} kg/m³ and dynamic viscosity is "
        f"{viscosity:g} Pa·s. With velocity {velocity:.3f} m/s and diameter "
        f"{diameter:.3f} m, Re = ρVD/μ = {reynolds:,.2f}. "
        f"This is classified as {regime.lower()} flow. "
        "This explanation is generated from built-in rules, not a connected generative-AI service."
    )

# ------------------------------------------------------------
# How to use and footer
# ------------------------------------------------------------
st.subheader("How to Use")
st.markdown(
    """
    1. **Choose Fluid** from Water, Oil, Honey, or Air.
    2. **Move a slider or speak** a supported command.
    3. **Watch the 3D pipe** and the live Reynolds number / flow regime update.
    """
)

st.markdown(
    """
    <div class="ju-footer">
      Made by <strong>Amit Banik</strong>, Chemical Engineering, Jadavpur University.
      For 1st Year Students.
    </div>
    """,
    unsafe_allow_html=True,
)
