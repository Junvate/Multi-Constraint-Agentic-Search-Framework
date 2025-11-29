# config.py
import os
import dotenv

# 加载 .env 环境变量
dotenv.load_dotenv('.env')
TARGET_MODEL= os.getenv('TARGET_MODEL')


# === 文件路径配置 ===
BASE_DIR=r"D:/aaaaYINGBOWEN/Multi-Constraint-Agentic-Search-Framework"
INPUT_FILE = os.path.join(BASE_DIR, 'data/data_b.json')
OUTPUT_DIR = os.path.join(BASE_DIR, 'result')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'data_b.jsonl')

# === 模型参数配置 ===

FLASH_RAG_CONFIG = {
    "generator_type": "openai",
    "framework": "openai",
    "model2path": {
        "Qwen/Qwen2.5-32B-Instruct": TARGET_MODEL
    },
    "generator_model": TARGET_MODEL,
    "generation_params": {
        "max_tokens": 50,
        "temperature": 0.1,
        "top_p": 0.9,
    },
    "device": "cpu",
}