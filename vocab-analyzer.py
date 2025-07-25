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
    cols = st.columns(4)
    with cols[0]:
        with st.container(border=True):
            min_accuracy = st.slider("词测通过分数线 (%)", 85, 100, 94)
    with cols[1]:
        with st.container(border=True):
            show_failed = st.checkbox("显示词测未通过记录", value=False)
    with cols[2]:
        with st.container(border=True):
            show_vocab = st.checkbox("显示词测结果", value=True)
    with cols[3]:
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
            
            progress_bar.progress(100)
            status_text.success("✅ 已完成分析")
            time.sleep(0.5)
            status_text.empty()
        
        if not results:
            st.warning("没有找到符合条件的数据")
        else:
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
            
            results_container = st.container()
            with results_container:
                for student in results:
                    display_student = False
                    
                    if (student['passed'] or (show_failed and student['failed'])) and show_vocab:
                        display_student = True
                        with st.container():
                            st.subheader(f"👤 {student['name']}")
                            st.markdown("📝 **词测结果**")
                            if student['passed']:
                                st.markdown("✅ **通过测试**")
                                display_test_table(student['passed'])
                            if show_failed and student['failed']:
                                st.markdown("❌ **未通过测试**")
                                display_test_table(student['failed'])
                    
                    if (student['question_cards']['SAT'] or student['question_cards']['TOEFL']) and show_cards:
                        if not display_student:
                            st.subheader(f"👤 {student['name']}")
                            display_student = True
                        
                        if student['question_cards']['SAT']:
                            display_question_cards(student['question_cards']['SAT'], "SAT")
                        if student['question_cards']['TOEFL']:
                            display_question_cards(student['question_cards']['TOEFL'], "TOEFL")
                    
                    if display_student:
                        st.markdown("---")
            
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