# -*- coding: utf-8 -*-
import dotenv
import os
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 拼接出 .env 的绝对路径
env_path = os.path.join(current_dir, '.env')
print(f"DEBUG: 正在尝试读取文件: {env_path}")
dotenv.load_dotenv(env_path)
if not dotenv.load_dotenv(env_path):
    print("错误：找不到 .env 文件")
    exit()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID')
PROXY_URL = os.getenv('PROXY_URL')
BAIDU_APPBUILDER_API_KEY = os.getenv('BAIDU_APPBUILDER_API_KEY')

OPENAI_API_KEY=os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL=os.getenv('OPENAI_BASE_URL')
TARGET_MODEL=os.getenv('TARGET_MODEL')

# 设置环境变量供 FlashRAG 使用
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL

import json
import time
import sys
import re
from flashrag.config import Config
from flashrag.prompt import PromptTemplate
from flashrag.utils import get_generator

from extract import extract_question_with_llm
from extract import extract_core_entities
from extract import extract_relevant_sentences
from clean import clean_answer_aggressive

import config as cfg

from BaiduSearchClient import BaiduSearchClient
from GoogleSearchClient import GoogleSearchClient


def main():
    print("正在初始化...")
    config = Config(config_dict=cfg.FLASH_RAG_CONFIG)
    generator = get_generator(config)
    print("初始化完成")

    if not os.path.exists(cfg.INPUT_FILE):
        print(f"错误：找不到文件 {cfg.INPUT_FILE}")
        return

    with open(cfg.INPUT_FILE, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"准备处理 {len(questions)} 个问题")
    print(f"结果将保存到: {cfg.OUTPUT_FILE}\n")
    
    # 创建详细过程日志文件
    process_log_file = cfg.OUTPUT_FILE.replace('.jsonl', '_process.json')
    process_logs = []

    with open(cfg.OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for i, q in enumerate(questions):
            if not isinstance(q, dict) or "input_field" not in q:
                continue

            question_id = q.get("id", f"q_{i}")
            question_text = q["input_field"]
            correct_answer = q.get("output_field", "")

            print(f"\n=== [{i+1}/{len(questions)}] ID: {question_id} ===")
            print(f"问题: {question_text[:60]}...")
            print(f"正确答案: {correct_answer}")
            
            # 创建详细日志
            log_entry = {
                "id": question_id,
                "原始问题": question_text,
                "正确答案": correct_answer,
                "处理步骤": {}
            }
            
            # 步骤1: 提取核心问题
            core_question = extract_question_with_llm(question_text, generator, config)
            print(f"核心问题: {core_question}")
            log_entry["处理步骤"]["1_核心问题提取"] = core_question
            time.sleep(0.2)
            
            # 步骤2: 提取核心实体用于搜索
            entities = extract_core_entities(question_text, generator, config)
            search_query = " ".join(entities) if entities else core_question
            print(f"搜索查询: {search_query}")
            log_entry["处理步骤"]["2_搜索关键词"] = entities
            log_entry["处理步骤"]["3_搜索查询"] = search_query
            time.sleep(0.2)
            
            # 步骤3: 谷歌搜索
            print(f"谷歌搜索中...")
            search_client = GoogleSearchClient(
                api_key=GOOGLE_API_KEY, 
                cse_id=GOOGLE_CSE_ID,
                proxy=PROXY_URL
            )

            search_result = search_client.web_search(
                query=search_query,
                top_k=10,
            )
            
            # 步骤4: 提取文档内容（这是关键！）
            documents = []
            search_details = []
            if "references" in search_result and search_result["references"]:
                for idx, ref in enumerate(search_result["references"][:5]):
                    # 提取标题和摘要
                    title = ref.get("title", "")
                    content = ref.get("content", "")
                    url = ref.get("url", "")
                    
                    search_details.append({
                        "序号": idx + 1,
                        "标题": title,
                        "内容": content[:200] + "..." if len(content) > 200 else content,
                        "链接": url
                    })
                    
                    if title:
                        documents.append(title)
                    if content:
                        documents.append(content)
                print(f"找到 {len(search_result['references'])} 条搜索结果")
                log_entry["处理步骤"]["4_百度搜索结果"] = {
                    "结果数量": len(search_result["references"]),
                    "前5条详情": search_details
                }
            else:
                print(f"未找到搜索结果")
                log_entry["处理步骤"]["4_百度搜索结果"] = {"结果数量": 0, "详情": "未找到"}
            
            time.sleep(0.3)
            
            # 步骤5: RAG核心 - 提取最相关的句子
            # 这是真正的RAG：不是把整个文档给LLM，而是提取最相关的1-2句话
            relevant_context = extract_relevant_sentences(documents, question_text, max_sentences=2)
            print(f"相关上下文: {relevant_context[:80]}...")
            log_entry["处理步骤"]["5_提取的相关句子"] = relevant_context
            
            # 步骤6: 用极简的上下文生成答案
            print(f"生成答案...")
            
            # 超简洁的Prompt - 因为上下文已经是最相关的了
            prompt_template = PromptTemplate(
                config,
                system_prompt="""Answer the question in the most concise way.

Context:
{context}

Rules:
1. Output only the answer (name/place/number/time)
2. Maximum 10 words
3. No explanations

Examples:
Question: Who is the musician
Answer: Ringo Sheena

Question: What title was awarded
Answer: Outstanding Young Talent""",
                user_prompt="{query}"
            )
            
            prompt = prompt_template.get_string(
                context=relevant_context,
                query=core_question
            )
            
            result_item = {"id": question_id, "output_field": ""}
            
            try:
                answer_list = generator.generate([prompt])
                if answer_list:
                    answer_text = answer_list[0].strip()
                    original_answer = answer_text
                    answer_text = clean_answer_aggressive(answer_text)
                    
                    print(f"生成答案: {answer_text}")
                    log_entry["处理步骤"]["6_原始生成答案"] = original_answer
                    log_entry["处理步骤"]["7_清理后答案"] = answer_text
                    
                    # 如果答案太短或包含无效词，重试
                    if len(answer_text) < 2 or any(bad in answer_text for bad in ["according", "based on", "information", "reference"]):
                        print(f"答案质量不佳，重试...")
                        simple_prompt = f"{relevant_context}\n\nQuestion: {core_question}\nAnswer:"
                        retry = generator.generate([{"role": "user", "content": simple_prompt}])
                        if retry:
                            retry_original = retry[0]
                            answer_text = clean_answer_aggressive(retry[0])
                            log_entry["处理步骤"]["8_重试生成"] = retry_original
                            log_entry["处理步骤"]["9_重试清理后"] = answer_text
                    
                    result_item["output_field"] = answer_text
                    print(f"最终答案: {answer_text}")
                    print(f"对比: {answer_text} vs {correct_answer}")
                else:
                    result_item["output_field"] = "生成失败"
                    log_entry["处理步骤"]["6_生成结果"] = "失败"
                    
            except Exception as e:
                result_item["output_field"] = f"错误"
                print(f"出错: {e}")
                log_entry["处理步骤"]["错误"] = str(e)
            
            # 记录最终对比
            log_entry["最终答案"] = result_item["output_field"]
            log_entry["答案对比"] = {
                "生成答案": result_item["output_field"],
                "正确答案": correct_answer,
                "是否正确": result_item["output_field"] == correct_answer
            }
            
            # 添加到日志列表
            process_logs.append(log_entry)
            
            f_out.write(json.dumps(result_item, ensure_ascii=False, indent=2) + '\n')
            f_out.flush()
            
            time.sleep(0.5)
    
    # 保存详细过程日志
    with open(process_log_file, 'w', encoding='utf-8') as f_log:
        json.dump(process_logs, f_log, ensure_ascii=False, indent=2)
    
    print(f"\n处理完成！")
    print(f"结果已保存到: {cfg.OUTPUT_FILE}")
    print(f"详细过程已保存到: {process_log_file}")

if __name__ == "__main__":
    main()
