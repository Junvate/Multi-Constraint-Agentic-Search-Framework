# Multi-Constraint-Agentic-Search-Framework

Multi-Constraint Agentic Search Framework 是一个基于大语言模型（LLM）和多源搜索引擎的智能搜索与问答框架。它专为处理包含复杂约束条件的查询而设计，通过分解问题、提取核心实体、执行多源搜索（Google/Baidu）以及 RAG（检索增强生成）流程，生成精准的答案。


# ✨ 核心功能
多约束问题分析: 使用 LLM (Qwen, GPT 等) 自动提取查询中的核心实体、时间限制和关键特征。

多源搜索集成: 支持 Google Custom Search 和 百度 AppBuilder 接口，确保信息获取的广度与时效性。

智能清洗与重组: 内置 clean 和 extract 模块，对搜索结果进行清洗，去除无关噪声。

FlashRAG 集成: 结合检索增强生成技术，提升长文本问答的准确率。

自动化流水线: 提供从 JSON 数据输入到 JSONL 结果输出的全自动处理流程。


# 📂 项目结构
```
Multi-Constraint-Agentic-Search-Framework/
├── data/                  # 输入数据文件夹
│   └── data_b.json        # 原始查询数据
├── result/                # 输出结果文件夹 (自动生成)
│   └── data_b.jsonl       # 处理后的问答结果
├── src/                   # 源代码目录
│   ├── .env               # [重要] 配置文件 (需自行创建)
│   ├── config.py          # 配置加载模块
│   ├── clean.py           # 答案清洗与后处理
│   ├── extract.py         # 问题提取与实体识别
│   └── mian.py            # 主启动程序 (Entry Point)
├── requirements.txt       # 项目依赖
└── README.md              # 项目文档
```


# 🚀 快速开始
## 1. 环境准备
确保你的 Python 版本 >= 3.8。


# 克隆项目
```
git clone https://github.com/Junvate/Multi-Constraint-Agentic-Search-Framework.git
cd Multi-Constraint-Agentic-Search-Framework
```
# 安装依赖
```
pip install -r requirements.txt
```


## 2. 配置环境变量 (关键步骤)
本项目依赖环境变量进行 API 认证。请在 src/ 目录下创建一个名为 .env 的文件（注意文件名必须是 .env，不要有后缀）。

src/.env 文件模板

# === LLM 设置 (OpenAI 格式) ===
# 如果使用中转服务 (如 AIGCBest)，请填写中转 Key 和 URL
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_BASE_URL=https://api2.aigcbest.top/v1
TARGET_MODEL=Qwen/Qwen2.5-32B-Instruct
```
# === 谷歌搜索配置 ===
```
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxx
GOOGLE_CSE_ID=0123456789:xxxxxx
```
# === 百度搜索配置 ===
```
BAIDU_APPBUILDER_API_KEY=bce-v3/xxxxxxxxxxxx
```
# === 网络代理 (可选) ===
# 如果在中国大陆访问 Google API，可能需要配置本地代理
```
PROXY_URL=http://127.0.0.1:7890
```


## 3. 运行项目
请在项目根目录下运行以下命令：

# 注意：入口文件在 src 目录下
```
python src/mian.py
```