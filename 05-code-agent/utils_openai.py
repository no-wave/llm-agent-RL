"""
Agent RL 튜토리얼 - OpenAI API 공통 유틸리티
============================================
사용법:
    1) 터미널에서 API 키 설정: export OPENAI_API_KEY='sk-...'
    2) 노트북에서 import:     from utils_openai import *
"""

import os, json, time
from openai import OpenAI
from dataclasses import dataclass, field

# ── 클라이언트 & 모델 ──────────────────────────────────────
MODEL = "gpt-4o-mini"
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


# ── 1. 기본 호출 함수 ─────────────────────────────────────
def ask(prompt, system="", temperature=0.7, max_tokens=1024):
    """가장 간단한 LLM 호출 함수이다. 텍스트를 넣으면 텍스트가 나온다."""
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})
    resp = client.chat.completions.create(
        model=MODEL, messages=msgs,
        temperature=temperature, max_tokens=max_tokens,
    )
    return resp.choices[0].message.content


def chat(messages, temperature=0.7, max_tokens=1024, tools=None):
    """멀티턴 대화용 호출 함수이다. messages 리스트를 직접 전달한다."""
    kwargs = dict(model=MODEL, messages=messages,
                  temperature=temperature, max_tokens=max_tokens)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return client.chat.completions.create(**kwargs)


# ── 2. Function Calling 유틸리티 ──────────────────────────
def tool_schema(name, description, properties, required=None):
    """OpenAI function calling용 도구 스키마를 만든다."""
    params = {"type": "object", "properties": properties}
    if required:
        params["required"] = required
    return {"type": "function",
            "function": {"name": name, "description": description,
                         "parameters": params}}


def run_tools(response, tool_map):
    """API 응답에 포함된 도구 호출을 실행하고 결과 메시지를 반환한다."""
    results = []
    for tc in response.choices[0].message.tool_calls:
        func = tool_map[tc.function.name]
        args = json.loads(tc.function.arguments)
        out = func(**args)
        results.append({"tool_call_id": tc.id, "role": "tool",
                        "content": json.dumps(out, ensure_ascii=False)})
    return results


# ── 3. 메모리 스트림 (Generative Agent Memory) ────────────
class MemoryStream:
    """
    Perceive → Memory Stream → Retrieve → Act 구조의 핵심이다.
    검색 점수 = 관련성(0.5) + 최신성(0.2) + 중요도(0.3)
    """

    def __init__(self):
        self.memories = []

    def add(self, content, importance=0.5, mem_type="observation"):
        """메모리를 저장한다."""
        self.memories.append({
            "content": content,
            "importance": importance,
            "type": mem_type,
            "timestamp": time.time(),
            "access_count": 0,
        })

    def retrieve(self, query, top_k=3):
        """관련성 + 최신성 + 중요도 가중합으로 메모리를 검색한다."""
        q_words = set(query.lower().split())
        scored = []
        for m in self.memories:
            m_words = set(m["content"].lower().split())
            relevance = len(q_words & m_words) / max(len(q_words), 1)
            recency = 1.0 / (1.0 + time.time() - m["timestamp"])
            score = relevance * 0.5 + recency * 0.2 + m["importance"] * 0.3
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        for _, m in scored[:top_k]:
            m["access_count"] += 1
        return [m for _, m in scored[:top_k]]

    def reflect(self, query):
        """저장된 메모리를 바탕으로 상위 수준의 통찰(Reflect)을 생성한다."""
        relevant = self.retrieve(query, top_k=5)
        if not relevant:
            return "아직 반성할 메모리가 충분하지 않다."
        mem_text = "\n".join(f"- {m['content']}" for m in relevant)
        insight = ask(
            f"다음 기억들을 종합하여 핵심 인사이트를 한국어 2~3문장으로 도출하라:\n{mem_text}",
            system="메모리를 분석하고 패턴을 발견하는 반성 에이전트이다.",
            temperature=0.3,
        )
        self.add(f"[반성] {insight}", importance=0.8, mem_type="reflection")
        return insight

    def __len__(self):
        return len(self.memories)


# ── 4. 보상 함수 ─────────────────────────────────────────
def llm_reward(text, criteria="정확성, 완전성, 유용성", max_score=10.0):
    """LLM을 심판(Judge)으로 사용하여 텍스트 품질 점수를 매긴다."""
    score_str = ask(
        f"평가 기준: {criteria}\n응답: {text}\n\n0~{max_score} 사이 숫자 하나만 반환하라.",
        temperature=0.0, max_tokens=10,
    )
    return min(max(float(score_str.strip()), 0.0), max_score)


# ── 5. 깔끔한 출력 헬퍼 ──────────────────────────────────
def heading(title):
    """섹션 제목을 깔끔하게 출력한다."""
    w = max(len(title) + 4, 40)
    print(f"\n{'─' * w}")
    print(f"  {title}")
    print(f"{'─' * w}")


def step_print(step_num, label, content, indent=2):
    """단계별 진행 상황을 출력한다."""
    prefix = " " * indent
    print(f"{prefix}[Step {step_num}] {label}")
    if isinstance(content, list):
        for item in content:
            print(f"{prefix}  • {item}")
    else:
        for line in str(content).split("\n"):
            print(f"{prefix}  {line}")


def kv_print(pairs, indent=2):
    """키-값 쌍을 정렬하여 출력한다."""
    prefix = " " * indent
    if isinstance(pairs, dict):
        pairs = pairs.items()
    max_k = max((len(str(k)) for k, _ in pairs), default=0)
    for k, v in pairs:
        print(f"{prefix}{str(k):<{max_k}}  {v}")
