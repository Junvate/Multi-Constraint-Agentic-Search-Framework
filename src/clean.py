def clean_answer_aggressive(answer):
    """超激进的答案清理"""
    if not answer:
        return ""
    
    original = answer
    
    # 1. 清理前缀（英文）
    bad_starts = [
        "According to the provided information", "According to the reference", "According to", "Based on the information",
        "Based on the reference", "Based on", "From the information", "From the reference",
        "The provided information", "The reference shows", "The information shows", "The search results show",
        "Here is", "Here are", "This is", "This", "That", "The",
        "The answer is", "Answer is", "Answer:", "Answer:",
        "It is:", "It is", "It:", "Is:", "Is",
        "Should be", "Could be", "Might be"
    ]
    
    for bad in bad_starts:
        if answer.startswith(bad):
            answer = answer[len(bad):].strip()
            break
    
    # 2. 处理冒号
    if ':' in answer and answer.index(':') < 15:
        answer = answer.split(':', 1)[-1].strip()
    
    # 3. 去除引号
    answer = answer.strip('"\'')
    
    # 4. 只取第一句（英文分隔符）
    for delimiter in [',', '.', '\n', ';']:
        if delimiter in answer:
            first = answer.split(delimiter)[0].strip()
            if len(first) > 2:
                answer = first
                break
    
    # 5. 清理标点
    answer = answer.rstrip('.,;!?')
    
    # 6. 长度限制
    if len(answer) > 30:
        answer = answer[:30]
    
    answer = answer.strip()
    return answer if answer else original[:20]
