STYLE_CSS = """
<style>
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1.5rem;
        color: #ffffff;
        font-weight: 500;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem;
    }
    
    [data-testid="stSidebar"] {
        background-color: #F8F9FA;
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] h1 {
        font-size: 1.5rem;
        color: #2C3E50;
        margin-bottom: 1rem;
    }
    
    .stTextInput input {
        border-radius: 8px;
        border: 2px solid #E8E8E8;
        padding: 0.5rem;
    }
    
    .stTextInput input:focus {
        border-color: #3498DB;
        box-shadow: 0 0 0 0.2rem rgba(52, 152, 219, 0.25);
    }
    
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    .stAlert {
        border-radius: 8px;
        padding: 1rem;
    }
    
    div[data-testid="column"] {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
    }
    
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 2px solid #E8E8E8;
    }
    
    .js-plotly-plot {
        border-radius: 10px;
    }
    
    .stCheckbox {
        padding: 0.5rem 0;
    }
    
    .block-container {
        padding-top: 3rem;
        padding-bottom: 2rem;
    }
    
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1.5rem;
        }
    }
</style>
"""