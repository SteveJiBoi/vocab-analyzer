import streamlit as st
import re
from collections import defaultdict
from streamlit.components.v1 import html
import time

def main():
    # Configure page with colorful theme
    st.set_page_config(
        layout="wide", 
        page_title="词测&练习分析工具", 
        page_icon="📚",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS with animations and decorations
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    * {
        font-family: 'Noto Sans SC', sans-serif;
    }
    
    .main {
        background-color: #f8f9fa;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
    }
    
    .header {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
        animation: fadeIn 1s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .stButton>button {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    
    .stDataFrame {
        font-size: 14px !important;
        border-radius: 10px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    
    .question-card {
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .question-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    .sat-card { 
        border-left: 5px solid #4b8bbe;
        background: linear-gradient(90deg, rgba(75,139,190,0.1) 0%, rgba(255,255,255,1) 100%);
    }
    
    .toefl-card { 
        border-left: 5px solid #e74c3c;
        background: linear-gradient(90deg, rgba(231,76,60,0.1) 0%, rgba(255,255,255,1) 100%);
    }
    
    .student-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .student-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    .progress-container {
        height: 10px;
        background-color: #e9ecef;
        border-radius: 5px;
        margin-top: 5px;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 5px;
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
        transition: width 1s ease-in-out;
    }
    
    .floating { 
        animation-name: floating;
        animation-duration: 3s;
        animation-iteration-count: infinite;
        animation-timing-function: ease-in-out;
    }
    
    @keyframes floating {
        0% { transform: translate(0,  0px); }
        50%  { transform: translate(0, 10px); }
        100%   { transform: translate(0, -0px); }   
    }
    
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        background-color: #f00;
        border-radius: 50%;
        animation: fall 5s linear infinite;
    }
    
    @keyframes fall {
        to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Animated header with floating icon
    st.markdown("""
    <div class="header">
        <h1 style="margin:0; display:flex; align-items:center;">
            <span class="floating" style="margin-right:15px;">📚</span>
            <span>词测&练习分析工具</span>
        </h1>
        <p style="margin:0; opacity:0.8;">可视化分析学生词汇测试和练习数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input section with animated border
    with st.expander("📥 粘贴Study系统上班级学习动态", expanded=True):
        input_data = st.text_area(
            "请粘贴如下格式的数据:",
            height=200,
            placeholder="xxx同学 : 【词测 托福核心-英义-所有义-看测-2601~2700-100】: 已完成 词数：100，正确率：95%，平均反应时间：3.67 s，错误个数：5",
            key="input_area"
        )
    
    # Processing controls in cards
    st.markdown("### 🎛️ 分析设置")
    cols = st.columns(3)
    with cols[0]:
        with st.container(border=True):
            min_accuracy = st.slider("词测通过分数线 (%)", 85, 100, 94)
    with cols[1]:
        with st.container(border=True):
            show_failed = st.checkbox("显示词测未通过记录", value=False)
    with cols[2]:
        with st.container(border=True):
            show_details = st.checkbox("显示详细分析", value=True)
    
    # Animated analyze button
    if st.button("🔍 开始分析", type="primary", use_container_width=True):
        if not input_data.strip():
            st.warning("请先粘贴数据!")
            st.stop()
        
        with st.spinner("分析中..."):
            # Add a simple progress bar animation
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            results = analyze_data(input_data, min_accuracy, show_failed)
        
        # Display results with animation
        if not results:
            st.warning("没有找到符合条件的数据")
        else:
            # Add confetti animation for successful analysis
            html("""
            <script>
            function createConfetti() {
                const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff'];
                for (let i = 0; i < 50; i++) {
                    const confetti = document.createElement('div');
                    confetti.className = 'confetti';
                    confetti.style.left = Math.random() * 100 + 'vw';
                    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                    confetti.style.width = (Math.random() * 10 + 5) + 'px';
                    confetti.style.height = confetti.style.width;
                    confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
                    document.body.appendChild(confetti);
                    setTimeout(() => confetti.remove(), 5000);
                }
            }
            createConfetti();
            </script>
            """)
            
            display_results(results, show_failed)
            
            # Export options
            st.markdown("---")
            with st.expander("📤 导出结果", expanded=False):
                export_options(results)

# [Rest of your functions (analyze_data, display_question_cards, display_test_table, display_results, export_options) remain the same]
# ...

if __name__ == "__main__":
    main()