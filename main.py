#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
警告：此脚本会执行由 LLM 生成的任意代码，存在严重安全风险！
仅用于学习目的，请在隔离环境中使用，并人工审查生成的代码。
"""

import sys
import os
import openai
import subprocess
import tempfile


def read_input_file(file_path: str) -> str:
    """读取输入文件内容（UTF-8编码）"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"输入文件不存在: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_code_from_openai(content: str, api_base: str, api_key: str, model: str) -> str:
    """
    通过 OpenAI API 获取可执行的 Python 代码
    """
    # 配置客户端
    client = openai.OpenAI(
        base_url=api_base,
        api_key=api_key
    )

    # 构造提示词：要求只返回纯 Python 代码，不含 markdown 标记
    prompt = f"""
你是一个 Python 代码生成助手。请根据以下输入内容，编写一个完整、可独立运行的 Python 脚本。
要求：
1. 只输出纯 Python 代码，不要包含 ```python 或 ``` 等 markdown 标记。
2. 不要包含任何解释性文字。
3. 代码必须能直接通过 python 解释器执行。
4. 如果输入内容是问题，请编写解决该问题的代码；如果是数据，请编写处理该数据的代码。

输入内容：
{content}
"""

    try:
        response = client.chat.completions.create(
            model=model,  # 可根据需要修改模型名称
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs only raw Python code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )

        code = response.choices[0].message.content.strip()

        # 清理可能的 markdown 代码块标记（尽管提示词已要求避免）
        if code.startswith("```python"):
            code = code[len("```python"):]
        if code.startswith("```"):
            code = code[len("```"):]
        if code.endswith("```"):
            code = code[:-len("```")]

        return code.strip()

    except Exception as e:
        raise RuntimeError(f"调用 OpenAI API 失败: {str(e)}")


def execute_code(code: str):
    """
    执行生成的 Python 代码
    注意：此处使用 subprocess 在新进程中执行，以避免污染当前命名空间
    但仍存在安全风险！
    """
    # print("=" * 50)
    # print("⚠️  即将执行以下由 LLM 生成的代码：")
    # print("=" * 50)
    # print(code)
    # print("=" * 50)
    #
    # confirm = input("\n是否确认执行？(输入 yes 继续，其他任意键取消): ")
    # if confirm.lower() != "yes":
    #     print("❌ 执行已取消。")
    #     return

    # 将代码写入临时文件并执行
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        # 执行临时文件
        result = subprocess.run(
            [sys.executable, tmp_file_path],
            capture_output=True,
            text=True,
            timeout=30  # 设置30秒超时，防止无限循环
        )

        # print("\n--- 执行 stdout ---")
        print(result.stdout)

        if result.stderr:
            # print("\n--- 执行 stderr ---")
            print(result.stderr)

        if result.returncode != 0:
            print(f"\n❌ 代码执行失败，返回码: {result.returncode}")
        # else:
        #     print("\n✅ 代码执行成功。")

    except subprocess.TimeoutExpired:
        print("\n❌ 代码执行超时（超过30秒），可能被终止。")
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {str(e)}")
    finally:
        # 清理临时文件
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass


def main():
    if len(sys.argv) != 5:
        print("用法: python main.py <输入文件> <API Base> <API key> <model>")
        print("示例: python main.py input.txt https://api.openai.com/v1 sk-xxx")
        sys.exit(1)

    input_file = sys.argv[1]
    api_base = sys.argv[2]
    api_key = sys.argv[3]
    model = sys.argv[4]

    try:
        # 1. 读取输入文件
        # print(f"📖 正在读取文件: {input_file}")
        content = read_input_file(input_file)

        # 2. 通过 OpenAI 获取代码
        # print("🤖 正在通过 OpenAI 生成代码...")
        generated_code = get_code_from_openai(content, api_base, api_key, model)

        # 3. 执行代码
        execute_code(generated_code)

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()