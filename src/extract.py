from flashrag.prompt import PromptTemplate
import re
def extract_question_with_llm(text, generator, config):
    """提取核心问题"""
    if len(text) < 20:
        return text
    
    extract_prompt = PromptTemplate(
        config,
        system_prompt="""Extract the core question, removing all background information.

Examples:
Input: A Japanese musician who joined a famous Japanese band at age 26. The band's name contains a well-known Japanese city. Who is the musician?
Output: Who is the musician

Input: What title was this Peking Opera performer awarded by the Ministry of Culture between 2015-2020?
Output: What title was awarded""",
        user_prompt="{text}"
    )
    
    prompt = extract_prompt.get_string(text=text)
    
    try:
        result = generator.generate([prompt])
        if result:
            core_q = result[0].strip()
            # 清理前缀
            for prefix in ['Output:', 'Answer:', 'Question:', 'Core question:']:
                if core_q.startswith(prefix):
                    core_q = core_q[len(prefix):].strip()
            core_q = core_q.rstrip('?.').strip()
            if len(core_q) < 3:
                raise ValueError("太短")
            return core_q
    except:
        pass
    
    # 降级：提取最后一句（英文标点）
    sentences = re.split(r'[.?!]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences[-1] if sentences else text


def extract_core_entities(text, generator, config):
    """提取全面的搜索关键词（保留语义）"""
    # 如果文本太短，直接返回包裹在列表中的原文本
    if len(text) < 10:
        return [text]
    
    entity_prompt = PromptTemplate(
        config,
        system_prompt="""Extract search keywords from the text, preserving complete semantics.

**Extraction Rules:**
1. Extract core entities: names, places, organizations, proper nouns
2. Extract key numbers: ages, years, time periods
3. Extract important features: professions, awards, works, location characteristics
4. Keep important qualifiers: famous, first, etc.
5. Separate each keyword with space, extract 5-10 keywords
6. Output directly, no explanations

**Example 1:**
Input: A Japanese musician who joined a famous Japanese band at age 26. The band's name contains a well-known Japanese city
Output: Japanese musician 26 years old famous band city name

**Example 2:**
Input: He is both a singer and actor who studied medicine early on. He debuted in the 1980s and won multiple Gold Record Awards
Output: singer actor medicine 1980s Gold Record Award

**Example 3:**
Input: What title was this Peking Opera performer awarded by the Ministry of Culture between 2015-2020
Output: Peking Opera performer 2015-2020 Ministry of Culture title

**Example 4:**
Input: This city is in a landlocked Chinese province, ancestral home of a Chinese leader, dates back to Yuan Dynasty
Output: landlocked province city leader ancestral home Yuan Dynasty""",
        user_prompt="{text}"
    )
    
    prompt = entity_prompt.get_string(text=text)
    
    try:
        result = generator.generate([prompt])
        if result:
            entities_str = result[0].strip()
            # 清理前缀
            for prefix in ['Output:', 'Keywords:', 'Entities:']:
                if entities_str.startswith(prefix):
                    entities_str = entities_str[len(prefix):].strip()
            entities = re.split(r'[,\s]+', entities_str)
            entities = [e.strip() for e in entities if e.strip() and len(e) > 1]
            # 返回5-10个关键词
            return entities[:10]
    except Exception as e:
        print(f"   ⚠️ 关键词提取失败: {e}")
    
    # 降级方案
    keywords = []
    words = re.findall(r'\b[A-Za-z]{2,15}\b', text)
    numbers = re.findall(r'\d+', text)
    keywords.extend(words[:6])
    keywords.extend(numbers[:3])
    return keywords[:10] if keywords else [text[:30]]



def extract_core_querys(text, generator, config):
    """提取全面的搜索查询（保留语义），并拆分为列表"""
    
    if len(text) < 10:
        return [text]
    
    entity_prompt = PromptTemplate(
        config,
        system_prompt="""# Role
Search Query Architect for Complex Riddles.

# Task
Break down the complex nested question into **3-5 independent, factual search queries**. 
You MUST separate the constraints based on the **Subject/Entity** they describe.

# Critical Rules
1. **Remove Interrogatives**: Delete "What is", "Who is", "Name of the..." etc. Convert them into declarative phrases.
2. **De-nest Clauses**: If a sentence says "A university that is X, Y, and Z", create a query specifically for "University X Y Z".
3. **Keep Original Language**: If the input is English, output English queries. Specific terms like "Land-grant", "Academy Award", "Fortune 500" work best in English.
4. **No Summarization**: Do not shorten "second half of the 1800s" to "1800s". Keep the specific detail.

# Decomposition Strategy (Example)
Input: "What is the band that released an album in 1990, after playing at a university where a Nobel winner graduated?"
*Analysis*: 
- Entity 1: Band (Action: Album 1990)
- Entity 2: University (Constraint: Nobel winner graduated)
*Output*: 
- band released album 1990
- university Nobel prize winner graduated
- band played concert at university with Nobel alumni

# Your Turn

# Output format
Output only the queries separated by commas.
""",
        user_prompt="{text}"
    )
    
    prompt = entity_prompt.get_string(text=text)
    
    try:
        # 1. 获取模型生成的原始字符串
        result = generator.generate([prompt])
        raw_output = result[0].strip()
        
        # 2. 预处理：防止模型混用中文逗号，统一替换为英文逗号
        raw_output = raw_output.replace('，', ',')
        
        # 3. 拆分与清洗：
        # - split(','): 按逗号分割
        # - x.strip(): 去除每个短语前后的空格
        # - if x.strip(): 过滤掉空字符串（防止连续逗号导致的空项）
        keyword_list = [x.strip() for x in raw_output.split(',') if x.strip()]
        
        return keyword_list
        
    except Exception as e:
        print(f"   ⚠️ 关键词提取失败: {e}")
        # 出错时返回原文本（作为列表的一个元素），保证返回类型一致
        return [text]




def extract_relevant_sentences(documents, question, max_sentences=3):
    """从搜索结果中提取最相关的句子"""
    if not documents:
        return ""
    
    all_sentences = []
    for doc in documents:
        sentences = re.split(r'[。！？\n]+', doc)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        all_sentences.extend(sentences)
    
    if not all_sentences:
        return documents[0][:200] if documents else ""
    
    question_keywords = set(re.findall(r'\b[A-Za-z]{2,}\b', question.lower()))
    
    sentence_scores = []
    for sent in all_sentences[:50]:
        sent_words = set(re.findall(r'\b[A-Za-z]{2,}\b', sent.lower()))
        score = len(question_keywords & sent_words)
        sentence_scores.append((score, sent))
    
    sentence_scores.sort(key=lambda x: x[0], reverse=True)
    top_sentences = [sent for score, sent in sentence_scores[:max_sentences] if score > 0]
    
    if not top_sentences:
        return '\n'.join(all_sentences[:2])
    
    return '\n'.join(top_sentences)