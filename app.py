# 导入 Flask 所需模块：网页渲染、请求处理、JSON 返回
from flask import Flask, render_template, request, jsonify
# 发送 HTTP 请求调用智谱 AI
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# 初始化 Flask 应用
app = Flask(__name__)

# 智谱 AI 密钥（身份验证）
API_KEY = os.getenv("ZHIPU_API_KEY", "")
# 智谱 AI 接口地址
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

# ------------------------------
# 读取风格文件 my_style.txt
# 如果文件不存在，使用默认风格
# ------------------------------
def load_style():
    try:
        # 尝试读取本地风格配置文件
        with open("my_style.txt", "r", encoding="utf-8") as f:
            return f.read()
    except:
        # 文件不存在时返回默认风格
        return "小红书爆款风格，吸引人，有情绪，有悬念，有用"

# ------------------------------
# 主页路由（访问网站首页）
# 返回工具按钮、风格标签并渲染页面
# ------------------------------
@app.route("/")
def index():
    # 工具按钮列表
    tools = ["PPT课件", "观察记录", "成长画册", "寄语卡片", "主题月课程", "环创设计", "教案生成", "课程故事"]
    # 风格标签列表
    style_tags = ["多加点emoji", "更有网感一点", "更短更抓眼", "更戳痛点", "更夸张吸睛", "加减负感"]
    # 渲染前端页面
    return render_template("index.html", tools=tools, style_tags=style_tags)

# ------------------------------
# AI 生成接口（前端发送消息，后端返回标题）
# ------------------------------
@app.route("/generate", methods=["POST"])
def generate():
    # 获取前端传来的 JSON 数据
    data = request.get_json()
    # 用户输入的内容
    user_input = data.get("message", "")
    # 用户身份：幼师或教师
    identity = data.get("identity", "幼师")
    # 聊天历史记录
    history = data.get("history", [])

    # 空内容判断
    if not user_input or user_input.strip() == "":
        return jsonify({"reply": "请输入内容~"})
    
    # 轻微延迟，让前端“思考中”状态更自然
    import time
    time.sleep(0.3)
    
    # 读取风格配置
    style = load_style()
    # 系统提示词（定义 AI 角色）
    system_prompt = f"""
你是小红书标题生成助手，聊天友好、带emoji，像朋友一样。
当前用户身份：{identity}。

如果身份是教师：
- 生成教师相关标题
- 不要出现“幼师”“园长”“托育”“幼儿园”
- 可以使用“校长”“教研员”“老师”“课堂”“课程”等描述
- 可以使用“校长”“教研员”“老师”等角色做夸张修辞、吸睛表达
- 但不要把这些角色写成当前用户身份
- 标题主体仍要围绕教师内容，不要写成“幼师”或“园长”作为主体身份
- 工具名称要匹配教师场景

如果身份是幼师：
- 保持幼教场景风格
- 可以继续使用幼师相关表达
- 可以用“园长”这种夸张修辞来强化吸引力

根据用户需求，**只生成用户当前指定的工具的标题**，严格遵守：
1.  只生成当前对话中用户明确提到的工具，绝对不生成其他无关工具（如用户要PPT课件，就只写PPT课件相关标题，禁止混入环创设计、观察记录、教案生成等其他内容）
2.  禁止将不同工具的内容、关键词、场景混在一起输出
3.  工具名称必须和用户输入的完全一致，禁止替换、修改或扩展
4.  后续用户调整风格（如加emoji、更网感）时，**只修改语气/格式，不改变工具类型和核心主题**

生成5条爆款小红书标题。
我的风格要求：
{style}

必须保持上下文记忆，用户要求修改时，只修改内容，不要重新生成无关内容。

### 强制固定结构（严格遵守）
1. 开头：**一句简短友好的引导语**（例如：为你准备了5条爆款标题✨ / 来啦！给你生成了5条超吸睛标题）
2. 中间：列出5条小红书标题
3. 结尾：**一句简短友好的结束语（每次不一样）**
   例子：
   - 有什么想要改动的地方可以告诉我哟😉~
   - 喜欢吗？想调整风格随时跟我说哈！
   - 还需要修改或补充都可以告诉我✨
   - 看看这些怎么样？不满意我再改！

### 格式要求
- 引导语1句 + 5条标题 + 结束语1句
- 引导语和结束语每次可以变化，但必须有
- 不要多余废话，结构干净清晰
"""

    # 构造完整对话上下文记忆
    messages = [{"role": "system", "content": system_prompt}]

    # 把前端传来的历史（user/bot）正确转换成 AI 接口需要的格式
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "bot":
            messages.append({"role": "assistant", "content": msg["content"]})

    # 请求头：身份验证 + 数据格式
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # 请求体：模型、上下文、温度参数
    payload = {
        "model": "glm-4.5-air",
        "messages": messages,
        "temperature": 0.7
    }

    try:
        # 发送请求到智谱 AI
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        # 解析返回结果
        result = resp.json()
        # 提取 AI 回复内容
        reply = result["choices"][0]["message"]["content"]
        # 返回给前端
        return jsonify({"reply": reply})
    except Exception as e:
        # 异常处理：返回错误信息
        print("接口错误：", e)
        return jsonify({"reply": "网络或接口出错啦，请重试~"})

# ------------------------------
# 启动 Flask 服务
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)