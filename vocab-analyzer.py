import streamlit as st
import re
from collections import defaultdict
from streamlit.components.v1 import html
import time

def analyze_data(text, min_accuracy=94, show_failed=False):
    """核心分析函数 - 提取词测和题卡数据"""
    def extract_test_info(test_str):
        test_type = "听测" if "听测" in test_str else "看测"
        range_match = re.search(r'(\d+~\d+)|(?<!\d)(\d+)(?!\d)', test_str)
        test_range = range_match.group() if range_match else "未知范围"
        return test_type, test_range
    
    history = defaultdict(list)
    student_entries = re.split(r'\n\s*\n', text.strip())
    
    for entry in student_entries:
        if not entry:
            continue
            
        name_match = re.match(r'^(.+?)\s*:', entry)
        if not name_match:
            continue
            
        full_name = name_match.group(1).strip()
        tests = re.findall(r'【(词测|题卡) (.+?)】:\s*(.+?)(?:,\s*|$)', entry)
        
        for test_type, test_info, test_result in tests:
            if test_type == "词测":
                if "正在进行" in test_result:
                    continue
                    
                accuracy_match = re.search(r'正确率：(\d+)%', test_result)
                if not accuracy_match:
                    continue
                    
                accuracy = int(accuracy_match.group(1))
                test_type, test_range = extract_test_info(test_info)
                key = (full_name, test_type, test_range)
                history[key].append(accuracy)
    
    results = []
    for entry in student_entries:
        if not entry:
            continue
            
        name_match = re.match(r'^(.+?)\s*:', entry)
        if not name_match:
            continue
            
        full_name = name_match.group(1).strip()
        student_data = {
            "name": full_name,
            "passed": [],
            "failed": [],
            "question_cards": {
                "SAT": [],
                "TOEFL": []
            }
        }
        
        tests = re.findall(r'【(词测|题卡) (.+?)】:\s*(.+?)(?:,\s*|$)', entry)
        for test_type, test_info, test in tests:
            if test_type == "词测":
                if "正在进行" in test:
                    continue
                    
                test_type, test_range = extract_test_info(test_info)
                key = (full_name, test_type, test_range)
                
                word_count = re.search(r'词数：(\d+)', test)
                accuracy = re.search(r'正确率：(\d+)%', test)
                time_taken = re.search(r'平均反应时间：([\d.]+)\s*s', test)
                errors = re.search(r'错误个数：(\d+)', test)
                
                if all([word_count, accuracy, time_taken, errors]):
                    word_count = int(word_count.group(1))
                    accuracy_val = int(accuracy.group(1))
                    reaction_time = float(time_taken.group(1))
                    errors = int(errors.group(1))
                    
                    previous_attempts = history.get(key, [])
                    failed_attempts = sum(1 for a in previous_attempts if a < min_accuracy)
                    
                    if accuracy_val < min_accuracy:
                        failed_attempts = max(0, failed_attempts - 1)
                    
                    test_data = {
                        "type": test_type,
                        "range": test_range,
                        "count": word_count,
                        "accuracy": accuracy_val,
                        "time": reaction_time,
                        "errors": errors,
                        "accuracy_str": f"{accuracy_val}%{'*' * failed_attempts}"
                    }
                    
                    if accuracy_val >= min_accuracy:
                        student_data["passed"].append(test_data)
                    else:
                        student_data["failed"].append(test_data)
            
            elif test_type == "题卡":
                card_type = "SAT" if "[SAT]" in test_info else "TOEFL"
                card_name = test_info.split('] ')[-1].strip()
                
                initial_errors = re.search(r'错误个数: (\d+)/(\d+)', test)
                corrected_errors = re.search(r'订正后错误个数: (\d+)/(\d+)', test)
                
                if initial_errors:
                    wrong = int(initial_errors.group(1))
                    total = int(initial_errors.group(2))
                    accuracy = round((total - wrong) / total * 100) if total > 0 else 0
                    
                    card_data = {
                        "name": card_name,
                        "initial_wrong": wrong,
                        "total": total,
                        "initial_accuracy": accuracy,
                        "corrected_wrong": None,
                        "corrected_accuracy": None,
                        "status": "已完成" if "已完成" in test else "正在进行"
                    }
                    
                    if corrected_errors:
                        corrected_wrong = int(corrected_errors.group(1))
                        corrected_accuracy = round((total - corrected_wrong) / total * 100) if total > 0 else 0
                        card_data.update({
                            "corrected_wrong": corrected_wrong,
                            "corrected_accuracy": corrected_accuracy
                        })
                    
                    student_data["question_cards"][card_type].append(card_data)
        
        if student_data["passed"] or (show_failed and student_data["failed"]) or student_data["question_cards"]["SAT"] or student_data["question_cards"]["TOEFL"]:
            results.append(student_data)
    
    return results

def display_question_cards(cards, card_type):
    if not cards:
        return
    
    st.markdown(f"📋 **{card_type}题卡**")
    
    for card in cards:
        card_class = "sat-card" if card_type == "SAT" else "toefl-card"
        st.markdown(f"""
        <div class="question-card {card_class}">
            <b>{card['name']}</b> - {card['status']}<br>
            初次错题: {card['initial_wrong']}/{card['total']} (正确率: {card['initial_accuracy']}%)
            {f"<br>订正后错题: {card['corrected_wrong']}/{card['total']} (正确率: {card['corrected_accuracy']}%)" if card['corrected_wrong'] is not None else ""}
        </div>
        """, unsafe_allow_html=True)

def display_test_table(tests):
    table_data = []
    for test in tests:
        table_data.append({
            "测试类型": test["type"],
            "范围": test["range"],
            "词数": test["count"],
            "正确率": test["accuracy_str"],
            "进度": test["accuracy"],
            "反应时间": f"{test['time']:.2f}s",
            "错误数": test["errors"]
        })
    
    st.dataframe(
        table_data,
        column_config={
            "进度": st.column_config.ProgressColumn(
                "正确率进度",
                min_value=0,
                max_value=100,
                format="%d%%"
            ),
            "正确率": st.column_config.TextColumn(
                "正确率(带重试)",
                help="*号表示之前未通过的次数"
            )
        },
        hide_index=True,
        use_container_width=True,
        height=(len(table_data) * 35 + 38)
    )

def export_options(results):
    import pandas as pd
    import io
    
    all_data = []
    for student in results:
        for test in student['passed'] + student['failed']:
            all_data.append({
                "姓名": student['name'],
                "类型": "词测",
                "测试类型": test["type"],
                "测试范围": test["range"],
                "词数": test["count"],
                "正确率": test["accuracy"],
                "反应时间": test["time"],
                "错误数": test["errors"]
            })
        
        for card_type in ['SAT', 'TOEFL']:
            for card in student['question_cards'][card_type]:
                all_data.append({
                    "姓名": student['name'],
                    "类型": "题卡",
                    "题卡类型": card_type,
                    "题卡名称": card['name'],
                    "状态": card['status'],
                    "总题数": card['total'],
                    "初次错误数": card['initial_wrong'],
                    "初次正确率": card['initial_accuracy'],
                    "订正后错误数": card['corrected_wrong'] if card['corrected_wrong'] is not None else "N/A",
                    "订正后正确率": card['corrected_accuracy'] if card['corrected_accuracy'] is not None else "N/A"
                })
    
    df = pd.DataFrame(all_data)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 导出CSV",
        csv,
        "词测分析结果.csv",
        "text/csv",
        help="导出为Excel兼容格式"
    )
    
    if st.checkbox("显示处理后的原始数据"):
        st.json(results, expanded=False)

def main():
    st.set_page_config(
        layout="wide", 
        page_title="词测&练习分析工具", 
        page_icon="📚",
        initial_sidebar_state="expanded"
    )
    
    # Google-style CSS with animations
    st.markdown("""
    <style>
    /* Google-inspired color scheme */
    :root {
        --primary-color: #4285F4;
        --success-color: #34A853;
        --warning-color: #FBBC05;
        --danger-color: #EA4335;
        --text-color: #202124;
        --secondary-text: #5F6368;
        --border-color: #DADCE0;
        --bg-color: #FFFFFF;
        --hover-color: #F1F3F4;
    }
    
    /* Base styles */
    body {
        font-family: 'Google Sans', Arial, sans-serif;
        color: var(--text-color);
        background-color: var(--bg-color);
    }
    
    /* Header animation */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .header {
        animation: fadeIn 0.5s ease-out;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
    }
    
    /* Input field focus animation */
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.2) !important;
        transition: all 0.2s ease;
    }
    
    /* Button animations */
    .stButton>button {
        transition: all 0.2s ease;
        border-radius: 4px !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15) !important;
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Progress bar animation */
    .stProgress>div>div>div {
        background-color: var(--primary-color) !important;
        transition: width 0.3s ease;
    }
    
    /* Card animations */
    .question-card {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border-left: 4px solid;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.1);
        transition: all 0.2s ease;
    }
    
    .question-card:hover {
        box-shadow: 0 1px 3px 0 rgba(60,64,67,0.2), 0 4px 8px 3px rgba(60,64,67,0.1);
        transform: translateY(-1px);
    }
    
    .sat-card {
        border-left-color: var(--warning-color);
        background-color: rgba(251, 188, 5, 0.05);
    }
    
    .toefl-card {
        border-left-color: var(--danger-color);
        background-color: rgba(234, 67, 53, 0.05);
    }
    
    /* Table hover effect */
    .dataframe tbody tr:hover {
        background-color: var(--hover-color) !important;
    }
    
    /* Confetti animation */
    @keyframes confetti-fall {
        0% { transform: translateY(-100px) rotate(0deg); opacity: 1; }
        100% { transform: translateY(100vh) rotate(360deg); opacity: 0; }
    }
    
    .confetti {
        position: fixed;
        width: 10px;
        height: 10px;
        opacity: 0;
        z-index: 9999;
        animation: confetti-fall 3s ease-in forwards;
    }
    
    /* Loading spinner animation */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-spinner {
        border: 4px solid rgba(0, 0, 0, 0.1);
        border-radius: 50%;
        border-top: 4px solid var(--primary-color);
        width: 40px;
        height: 40px;
        animation: spin 1s linear infinite;
        margin: 20px auto;
    }
    
    /* Simple fade-in for results */
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .result-section {
        animation: slideIn 0.4s ease-out;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .stDataFrame {
            width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Google-style header with animation
    st.markdown("""
    <div class="header">
        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 8px;">
            <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M20 0C8.96 0 0 8.96 0 20C0 31.04 8.96 40 20 40C31.04 40 40 31.04 40 20C40 8.96 31.04 0 20 0ZM29.2 20.18C29.2 24.66 25.66 28.2 21.18 28.2H12.8V11.8H21.18C25.66 11.8 29.2 15.34 29.2 19.82V20.18Z" fill="#4285F4"/>
                <path d="M12.8 11.8V28.2H21.18C25.66 28.2 29.2 24.66 29.2 20.18V19.82C29.2 15.34 25.66 11.8 21.18 11.8H12.8Z" fill="#34A853"/>
                <path d="M12.8 11.8L21.18 11.8C25.66 11.8 29.2 15.34 29.2 19.82V20.18C29.2 24.66 25.66 28.2 21.18 28.2L12.8 28.2V11.8Z" fill="#FBBC05"/>
                <path d="M12.8 11.8V28.2H7.6C3.12 28.2 -0.42 24.66 -0.42 20.18V19.82C-0.42 15.34 3.12 11.8 7.6 11.8H12.8Z" fill="#EA4335"/>
            </svg>
            <h1 style="margin:0; color: var(--text-color); font-weight: 500;">词测分析工具</h1>
        </div>
        <p style="margin:0; color: var(--secondary-text);">可视化分析学生词汇测试和练习数据</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Input section with subtle animation
    with st.expander("📥 粘贴Study系统上班级学习动态", expanded=True):
        input_data = st.text_area(
            "请粘贴如下格式的数据:",
            height=200,
            placeholder="xxx同学 : 【词测 托福核心-英义-所有义-看测-2601~2700-100】: 已完成 词数：100，正确率：95%，平均反应时间：3.67 s，错误个数：5",
            key="input_area"
        )
    
    # Settings section with cards
    st.markdown("### 🎛️ 分析设置")
    cols = st.columns(4)
    with cols[0]:
        with st.container(border=True):
            min_accuracy = st.slider("词测通过分数线 (%)", 85, 100, 94, help="设置词测通过的最低正确率")
    with cols[1]:
        with st.container(border=True):
            show_failed = st.checkbox("显示词测未通过记录", value=False, help="显示未达到分数线的测试记录")
    with cols[2]:
        with st.container(border=True):
            show_vocab = st.checkbox("显示词测结果", value=True, help="显示词汇测试的分析结果")
    with cols[3]:
        with st.container(border=True):
            show_cards = st.checkbox("显示题卡结果", value=True, help="显示题卡练习的分析结果")
    
    # Primary action button with animation
    if st.button("🔍 开始分析", type="primary", use_container_width=True):
        if not input_data.strip():
            st.warning("请先粘贴数据!")
            st.stop()
        
        # Animated loading sequence
        with st.spinner(""):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Display loading spinner
            status_text.markdown("""
            <div style="text-align: center;">
                <div class="loading-spinner"></div>
                <p style="margin-top: 10px; color: var(--secondary-text);">分析中...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Simulate progress
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
                if i % 20 == 0:
                    status_text.markdown(f"""
                    <div style="text-align: center;">
                        <div class="loading-spinner"></div>
                        <p style="margin-top: 10px; color: var(--secondary-text);">分析中... {i+1}%</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Actual analysis
            results = analyze_data(input_data, min_accuracy, show_failed)
            
            # Complete animation
            progress_bar.progress(100)
            status_text.markdown("""
            <div style="text-align: center; animation: fadeIn 0.5s ease;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM10 17L5 12L6.41 10.59L10 14.17L17.59 6.58L19 8L10 17Z" fill="#34A853"/>
                </svg>
                <p style="margin-top: 10px; color: var(--success-color); font-weight: 500;">分析完成</p>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(0.5)
            status_text.empty()
        
        # Confetti celebration
        html("""
        <script>
        function createConfetti() {
            const colors = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#8AB4F8'];
            for (let i = 0; i < 100; i++) {
                const confetti = document.createElement('div');
                confetti.className = 'confetti';
                confetti.style.left = Math.random() * 100 + 'vw';
                confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
                confetti.style.width = (Math.random() * 8 + 4) + 'px';
                confetti.style.height = confetti.style.width;
                confetti.style.borderRadius = '50%';
                confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
                confetti.style.animationDelay = (Math.random() * 0.5) + 's';
                document.body.appendChild(confetti);
                setTimeout(() => confetti.remove(), 5000);
            }
        }
        createConfetti();
        </script>
        """)
        
        # Results display with animation
        results_container = st.container()
        with results_container:
            for student in results:
                display_student = False
                
                if (student['passed'] or (show_failed and student['failed'])) and show_vocab:
                    display_student = True
                    with st.container():
                        st.markdown(f"""
                        <div class="result-section">
                            <h3 style="color: var(--text-color); margin-bottom: 0.5rem;">👤 {student['name']}</h3>
                            <p style="color: var(--secondary-text); margin-top: 0;">📝 <b>词测结果</b></p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if student['passed']:
                            st.markdown("""
                            <div style="display: flex; align-items: center; gap: 8px; color: var(--success-color); margin: 0.5rem 0;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M9 16.17L4.83 12L3.41 13.41L9 19L21 7L19.59 5.59L9 16.17Z" fill="#34A853"/>
                                </svg>
                                <span style="font-weight: 500;">通过测试</span>
                            </div>
                            """, unsafe_allow_html=True)
                            display_test_table(student['passed'])
                            
                        if show_failed and student['failed']:
                            st.markdown("""
                            <div style="display: flex; align-items: center; gap: 8px; color: var(--danger-color); margin: 0.5rem 0;">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M19 6.41L17.59 5L12 10.59L6.41 5L5 6.41L10.59 12L5 17.59L6.41 19L12 13.41L17.59 19L19 17.59L13.41 12L19 6.41Z" fill="#EA4335"/>
                                </svg>
                                <span style="font-weight: 500;">未通过测试</span>
                            </div>
                            """, unsafe_allow_html=True)
                            display_test_table(student['failed'])
                
                if (student['question_cards']['SAT'] or student['question_cards']['TOEFL']) and show_cards:
                    if not display_student:
                        st.markdown(f"""
                        <div class="result-section">
                            <h3 style="color: var(--text-color); margin-bottom: 0.5rem;">👤 {student['name']}</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        display_student = True
                    
                    if student['question_cards']['SAT']:
                        display_question_cards(student['question_cards']['SAT'], "SAT")
                    if student['question_cards']['TOEFL']:
                        display_question_cards(student['question_cards']['TOEFL'], "TOEFL")
                
                if display_student:
                    st.markdown("---")
        
        # Auto-scroll to results
        html(f"""
        <script>
            setTimeout(() => {{
                window.scrollTo({{
                    top: document.querySelector('[data-testid="stContainer"]').scrollHeight,
                    behavior: 'smooth'
                }});
            }}, 300);
        </script>
        """)
        
        # Export section
        st.markdown("---")
        with st.expander("📤 导出结果", expanded=False):
            export_options(results)

if __name__ == "__main__":
    main()