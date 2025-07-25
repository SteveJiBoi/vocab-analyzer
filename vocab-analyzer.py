import streamlit as st
import re
from collections import defaultdict
from streamlit.components.v1 import html
import time

# [Previous functions (analyze_data, display_question_cards, display_test_table, display_results, export_options) remain the same]
# ... (keep all those functions exactly as they were)

def main():
    st.set_page_config(
        layout="wide", 
        page_title="词测&练习分析工具", 
        page_icon="📚",
        initial_sidebar_state="expanded"
    )
    
    # [Keep all the CSS styling exactly as before]
    st.markdown("""
    <style>
    /* All your existing CSS styles here */
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="header">
        <h1 style="margin:0; display:flex; align-items:center;">
            <span class="floating" style="margin-right:15px;">📚</span>
            <span>词测&练习分析工具</span>
        </h1>
        <p style="margin:0; opacity:0.8;">可视化分析学生词汇测试和练习数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📥 粘贴Study系统上班级学习动态", expanded=True):
        input_data = st.text_area(
            "请粘贴如下格式的数据:",
            height=200,
            placeholder="xxx同学 : 【词测 托福核心-英义-所有义-看测-2601~2700-100】: 已完成 词数：100，正确率：95%，平均反应时间：3.67 s，错误个数：5",
            key="input_area"
        )
    
    st.markdown("### 🎛️ 分析设置")
    cols = st.columns(4)  # Changed to 4 columns to accommodate new checkboxes
    with cols[0]:
        with st.container(border=True):
            min_accuracy = st.slider("词测通过分数线 (%)", 85, 100, 94)
    with cols[1]:
        with st.container(border=True):
            show_failed = st.checkbox("显示词测未通过记录", value=False)
    with cols[2]:  # New checkbox for showing vocabulary tests
        with st.container(border=True):
            show_vocab = st.checkbox("显示词测结果", value=True)
    with cols[3]:  # New checkbox for showing question cards
        with st.container(border=True):
            show_cards = st.checkbox("显示题卡结果", value=True)
    
    if st.button("🔍 开始分析", type="primary", use_container_width=True):
        if not input_data.strip():
            st.warning("请先粘贴数据!")
            st.stop()
        
        with st.spinner("分析中..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
                if i % 10 == 0:
                    status_text.text(f"分析进度: {i+1}%")
            
            results = analyze_data(input_data, min_accuracy, show_failed)
            
            # Show completion message
            progress_bar.progress(100)
            status_text.success("✅ 已完成分析")
            time.sleep(0.5)
            status_text.empty()
        
        if not results:
            st.warning("没有找到符合条件的数据")
        else:
            # Add confetti animation
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
            
            # Create a container for results and auto-scroll to it
            results_container = st.container()
            with results_container:
                for student in results:
                    if (student['passed'] or (show_failed and student['failed']) and show_vocab):
                        with st.container():
                            st.subheader(f"👤 {student['name']")
                            
                            if student['passed'] or (show_failed and student['failed']):
                                st.markdown("📝 **词测结果**")
                                if student['passed']:
                                    st.markdown("✅ **通过测试**")
                                    display_test_table(student['passed'])
                                if show_failed and student['failed']:
                                    st.markdown("❌ **未通过测试**")
                                    display_test_table(student['failed'])
                    
                    if (student['question_cards']['SAT'] or student['question_cards']['TOEFL']) and show_cards:
                        with st.container():
                            if not ((student['passed'] or (show_failed and student['failed'])) or not show_vocab:
                                st.subheader(f"👤 {student['name']")
                            
                            if student['question_cards']['SAT'] and show_cards:
                                display_question_cards(student['question_cards']['SAT'], "SAT")
                            if student['question_cards']['TOEFL'] and show_cards:
                                display_question_cards(student['question_cards']['TOEFL'], "TOEFL")
                            
                            st.markdown("---")
            
            # Auto-scroll to results
            html(f"""
            <script>
                window.scrollTo(0, document.querySelector('[data-testid="stContainer"]').scrollHeight);
            </script>
            """)
            
            st.markdown("---")
            with st.expander("📤 导出结果", expanded=False):
                export_options(results)

if __name__ == "__main__":
    main()