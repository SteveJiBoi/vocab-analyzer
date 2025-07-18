import streamlit as st
import re
from collections import defaultdict

def main():
    # Configure page
    st.set_page_config(layout="wide", page_title="词测分析工具", page_icon="📚")
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .stDataFrame { font-size: 14px !important; }
    .st-emotion-cache-1qg05tj { font-size: 16px !important; }
    div[data-testid="stExpander"] details summary p { font-size: 18px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("📚 词测分析工具 (Web版)")
    st.markdown("---")
    
    # Input section
    with st.expander("📥 粘贴WPS云文档词测数据", expanded=True):
        input_data = st.text_area(
            "请粘贴如下格式的数据:",
            height=200,
            placeholder="xxx同学 : 【词测 托福核心-英义-所有义-看测-2601~2700-100】: 已完成 词数：100，正确率：95%，平均反应时间：3.67 s，错误个数：5"
        )
    
    # Processing controls
    col1, col2 = st.columns(2)
    with col1:
        min_accuracy = st.slider("通过分数线 (%)", 85, 100, 94)
    with col2:
        show_failed = st.checkbox("显示未通过记录", value=False)
    
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
            display_results(results)
            
            # Export options
            st.markdown("---")
            with st.expander("📤 导出结果"):
                export_options(results)

def analyze_data(text, min_accuracy=94, show_failed=False):
    """核心分析函数 (保留所有原Tkinter功能)"""
    def extract_test_info(test_str):
        test_type = "听测" if "听测" in test_str else "看测"
        range_match = re.search(r'(\d+~\d+)|(?<!\d)(\d+)(?!\d)', test_str)
        test_range = range_match.group() if range_match else "未知范围"
        return test_type, test_range
    
    # 第一次遍历：统计未通过次数
    failed_counts = defaultdict(lambda: defaultdict(int))
    student_entries = re.split(r'\n\s*\n', text.strip())
    
    for entry in student_entries:
        if not entry:
            continue
            
        name_match = re.match(r'^(.+?)\s*:', entry)
        if not name_match:
            continue
            
        full_name = name_match.group(1).strip()
        tests = re.findall(r'【词测 (.+?)】:\s*(.+?)(?:,\s*|$)', entry)
        
        for test_info, test_result in tests:
            if "正在进行" in test_result:
                continue
                
            accuracy_match = re.search(r'正确率：(\d+)%', test_result)
            if not accuracy_match:
                continue
            accuracy = int(accuracy_match.group(1))
            
            if accuracy < min_accuracy:
                test_type, test_range = extract_test_info(test_info)
                key = f"{test_type}-{test_range}"
                failed_counts[full_name][key] += 1
    
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
            "failed": []
        }
        
        tests = re.findall(r'【词测 (.+?)】:\s*(.+?)(?:,\s*|$)', entry)
        for test_info, test in tests:
            if "正在进行" in test:
                continue
                
            test_type, test_range = extract_test_info(test_info)
            
            # 提取各项数据
            word_count = re.search(r'词数：(\d+)', test)
            accuracy = re.search(r'正确率：(\d+)%', test)
            time = re.search(r'平均反应时间：([\d.]+)\s*s', test)
            errors = re.search(r'错误个数：(\d+)', test)
            
            if all([word_count, accuracy, time, errors]):
                word_count = int(word_count.group(1))
                accuracy_val = int(accuracy.group(1))
                reaction_time = float(time.group(1))
                errors = int(errors.group(1))
                
                test_data = {
                    "type": test_type,
                    "range": test_range,
                    "count": word_count,
                    "accuracy": accuracy_val,
                    "time": reaction_time,
                    "errors": errors,
                    "accuracy_str": f"{accuracy_val}%"
                }
                
                # 添加星号标记未通过的相同范围测试
                key = f"{test_type}-{test_range}"
                failed_count = failed_counts[full_name].get(key, 0)
                if failed_count > 0:
                    test_data["accuracy_str"] += "*" * failed_count
                
                if accuracy_val >= min_accuracy:
                    student_data["passed"].append(test_data)
                else:
                    student_data["failed"].append(test_data)
        
        if student_data["passed"] or (show_failed and student_data["failed"]):
            results.append(student_data)
    
    return results

def display_results(results):
    """显示分析结果"""
    for student in results:
        with st.container():
            st.subheader(f"👤 {student['name']}")
            
            # 通过测试
            if student['passed']:
                st.markdown("✅ **通过测试**")
                display_test_table(student['passed'])
            
            # 未通过测试 (如果启用显示)
            if student['failed']:
                st.markdown("❌ **未通过测试**")
                display_test_table(student['failed'])
            
            st.markdown("---")

def display_test_table(tests):
    """显示测试数据表格"""
    # 准备表格数据
    table_data = []
    for test in tests:
        table_data.append({
            "类型": test["type"],
            "测试范围": test["range"],
            "词数": test["count"],
            "正确率": test["accuracy_str"],
            "反应时间": f"{test['time']:.2f}s",
            "错误数": test["errors"]
        })
    
    # 显示表格
    st.dataframe(
        table_data,
        column_config={
            "类型": st.column_config.TextColumn(width="small"),
            "测试范围": st.column_config.TextColumn(width="medium"),
            "正确率": st.column_config.ProgressColumn(
                min_value=0,
                max_value=100,
                format="%d%%",
                width="medium"
            )
        },
        hide_index=True,
        use_container_width=True
    )

def export_options(results):
    """导出功能"""
    # CSV导出
    import pandas as pd
    import io
    
    # 准备所有数据
    all_data = []
    for student in results:
        for test in student['passed'] + student['failed']:
            all_data.append({
                "姓名": student['name'],
                "类型": test["type"],
                "测试范围": test["range"],
                "词数": test["count"],
                "正确率": test["accuracy"],
                "反应时间": test["time"],
                "错误数": test["errors"]
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