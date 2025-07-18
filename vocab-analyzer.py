import streamlit as st
import re
from collections import defaultdict

def main():
    st.set_page_config(layout="wide")
    st.title("📚 词测分析工具 (Web版)")
    
    # Input section
    with st.expander("📥 输入数据", expanded=True):
        input_data = st.text_area("粘贴WPS词测数据:", height=200, 
                                placeholder="钱采辰 : 【词测 托福核心-中义-随机义-听测-2501~2600-100】: 已完成 词数：100，正确率：96%...")
    
    if st.button("🔍 分析数据", type="primary"):
        if not input_data.strip():
            st.warning("请输入数据!")
            return
        
        results = analyze_data(input_data)
        
        # Display results
        for student in results:
            st.markdown(f"### 👤 {student['name']}")
            st.dataframe(
                student['tests'],
                column_config={
                    "type": "类型",
                    "range": "测试范围",
                    "count": "词数",
                    "accuracy": "正确率",
                    "time": "反应时间",
                    "errors": "错误数"
                },
                hide_index=True,
                use_container_width=True
            )
            st.divider()

def analyze_data(text):
    """Adapted analysis function"""
    def extract_test_info(test_str):
        test_type = "听测" if "听测" in test_str else "看测"
        range_match = re.search(r'(\d+~\d+)|(?<!\d)(\d+)(?!\d)', test_str)
        test_range = range_match.group() if range_match else "未知范围"
        return test_type, test_range

    results = []
    student_entries = re.split(r'\n\s*\n', text.strip())
    
    for entry in student_entries:
        if not entry:
            continue
            
        name_match = re.match(r'^(.+?)\s*:', entry)
        if not name_match:
            continue
            
        student = {
            "name": name_match.group(1).strip(),
            "tests": []
        }
        
        tests = re.findall(r'【词测 (.+?)】:\s*(.+?)(?:,\s*|$)', entry)
        for test_info, test in tests:
            if "正在进行" in test:
                continue
                
            test_type, test_range = extract_test_info(test_info)
            
            # Extract metrics
            word_count = re.search(r'词数：(\d+)', test)
            accuracy = re.search(r'正确率：(\d+)%', test)
            time = re.search(r'平均反应时间：([\d.]+)\s*s', test)
            errors = re.search(r'错误个数：(\d+)', test)
            
            if all([word_count, accuracy, time, errors]):
                student['tests'].append({
                    "type": test_type,
                    "range": test_range,
                    "count": int(word_count.group(1)),
                    "accuracy": f"{accuracy.group(1)}%",
                    "time": f"{float(time.group(1)):.2f}s",
                    "errors": int(errors.group(1))
                })
        
        if student['tests']:
            results.append(student)
    
    return results

if __name__ == "__main__":
    main()