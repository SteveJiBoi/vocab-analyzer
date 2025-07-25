import streamlit as st
import re
from collections import defaultdict

def main():
    # Configure page
    st.set_page_config(layout="wide", page_title="词测&练习分析工具", page_icon="📚")
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stDataFrame { font-size: 14px !important; }
    .st-emotion-cache-1qg05tj { font-size: 16px !important; }
    div[data-testid="stExpander"] details summary p { font-size: 18px; font-weight: bold; }
    .question-card { 
        padding: 10px; 
        margin: 5px 0; 
        border-radius: 5px; 
        background-color: #f0f2f6;
    }
    .sat-card { border-left: 4px solid #4b8bbe; }
    .toefl-card { border-left: 4px solid #e74c3c; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📚 词测分析工具 (Web版)")
    st.markdown("---")
    
    # Input section
    with st.expander("📥 粘贴Study系统上班级学习动态", expanded=True):
        input_data = st.text_area(
            "请粘贴如下格式的数据:",
            height=200,
            placeholder="xxx同学 : 【词测 托福核心-英义-所有义-看测-2601~2700-100】: 已完成 词数：100，正确率：95%，平均反应时间：3.67 s，错误个数：5"
        )
    
    # Processing controls
    col1, col2 = st.columns(2)
    with col1:
        min_accuracy = st.slider("词测通过分数线 (%)", 85, 100, 94)
    with col2:
        show_failed = st.checkbox("显示词测未通过记录", value=False)
    
    if st.button("🔍 开始分析", type="primary", use_container_width=True):
        if not input_data.strip():
            st.warning("请先粘贴数据!")
            st.stop()
        
        with st.spinner("分析中..."):
            results = analyze_data(input_data, min_accuracy, show_failed)
        
        # Display results
        if not results:
            st.warning("没有找到符合条件的数据")
        else:
            display_results(results, show_failed)
            
            # Export options
            st.markdown("---")
            with st.expander("📤 导出结果"):
                export_options(results)

def analyze_data(text, min_accuracy=94, show_failed=False):
    """核心分析函数 - 提取词测和题卡数据"""
    def extract_test_info(test_str):
        test_type = "听测" if "听测" in test_str else "看测"
        range_match = re.search(r'(\d+~\d+)|(?<!\d)(\d+)(?!\d)', test_str)
        test_range = range_match.group() if range_match else "未知范围"
        return test_type, test_range
    
    # 跟踪每个学生每个测试范围的历史尝试（包括通过的）
    history = defaultdict(list)
    student_entries = re.split(r'\n\s*\n', text.strip())
    
    # 第一次遍历：收集所有尝试记录
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
    
    # 第二次遍历：生成结果
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
                
                # 提取当前测试数据
                word_count = re.search(r'词数：(\d+)', test)
                accuracy = re.search(r'正确率：(\d+)%', test)
                time = re.search(r'平均反应时间：([\d.]+)\s*s', test)
                errors = re.search(r'错误个数：(\d+)', test)
                
                if all([word_count, accuracy, time, errors]):
                    word_count = int(word_count.group(1))
                    accuracy_val = int(accuracy.group(1))
                    reaction_time = float(time.group(1))
                    errors = int(errors.group(1))
                    
                    # 计算该测试范围的未通过次数
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
                # 提取题卡信息
                card_type = "SAT" if "[SAT]" in test_info else "TOEFL"
                card_name = test_info.split('] ')[-1].strip()
                
                # 提取错误信息
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
    """显示题卡信息"""
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
    """显示测试数据表格"""
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

def display_results(results, show_failed):
    """显示分析结果"""
    for student in results:
        # 只有当有数据时才显示
        if student['passed'] or (show_failed and student['failed']) or student['question_cards']['SAT'] or student['question_cards']['TOEFL']:
            with st.container():
                st.subheader(f"👤 {student['name']}")
                
                # 词测结果
                if student['passed'] or (show_failed and student['failed']):
                    st.markdown("📝 **词测结果**")
                    if student['passed']:
                        st.markdown("✅ **通过测试**")
                        display_test_table(student['passed'])
                    if show_failed and student['failed']:
                        st.markdown("❌ **未通过测试**")
                        display_test_table(student['failed'])
                
                # 题卡结果
                display_question_cards(student['question_cards']['SAT'], "SAT")
                display_question_cards(student['question_cards']['TOEFL'], "TOEFL")
                
                st.markdown("---")

def export_options(results):
    """导出功能"""
    import pandas as pd
    import io
    
    # 准备所有数据
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
    
    # CSV下载按钮
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        "📥 导出CSV",
        csv,
        "词测分析结果.csv",
        "text/csv",
        help="导出为Excel兼容格式"
    )
    
    # 显示原始数据
    if st.checkbox("显示处理后的原始数据"):
        st.json(results, expanded=False)

if __name__ == "__main__":
    main()