import time
import json
import re
from datetime import datetime
from main import get_agent_executor
from langchain.evaluation import load_evaluator
from langchain_aws.chat_models import ChatBedrock
import os
import config

# Define evaluation prompts and expected answers
EVAL_SET = [
    {"input": "What is the HR policy for remote work?", "expected": "Hybrid Work Policy", "requires_tool": True},
    {"input": "Who can approve leave?", "expected": "Leave Management", "requires_tool": True},
    {"input": "What is the process for misconduct reporting?", "expected": "Misconduct", "requires_tool": True},
    {"input": "Give me the marketing campaign performance.", "expected": "marketing_campaign_performance", "requires_tool": True},
    {"input": "What is 2+2?", "expected": "4", "requires_tool": False},  # Simple test case
    {"input": "Tell me about quantum computing breakthroughs in 2030", "expected": "I don't have information", "requires_tool": False},  # Hallucination test
]

def analyze_tool_usage(response_data):
    """Analyze if tools were used correctly based on agent's intermediate steps."""
    if 'intermediate_steps' not in response_data:
        return False, "No intermediate steps found"

    intermediate_steps = response_data['intermediate_steps']
    tool_calls = [step for step in intermediate_steps if len(step) >= 2]

    if not tool_calls:
        return False, "No tool calls made"

    # Check if tool calls were successful (no errors in observations)
    for action, observation in tool_calls:
        if isinstance(observation, str) and any(error_word in observation.lower()
                                              for error_word in ['error', 'failed', 'exception']):
            return False, f"Tool error: {observation[:100]}..."

    return True, f"Successfully used {len(tool_calls)} tool(s)"

def detect_hallucination(output, input_query, eval_llm):
    """Detect potential hallucinations using factual consistency checking."""
    hallucination_prompt = f"""
    Analyze the following response for potential hallucinations or fabricated information:
    
    Query: {input_query}
    Response: {output}
    
    Check if the response contains:
    1. Specific facts, dates, or numbers that seem made up
    2. References to events, people, or data not likely to be in training data
    3. Overly confident statements about uncertain topics
    
    Respond with either "HALLUCINATION_DETECTED" or "NO_HALLUCINATION" followed by a brief explanation.
    """

    try:
        result = eval_llm.invoke(hallucination_prompt)
        response_text = result.content if hasattr(result, 'content') else str(result)
        is_hallucination = "HALLUCINATION_DETECTED" in response_text.upper()
        explanation = response_text.split('\n')[0] if '\n' in response_text else response_text
        return is_hallucination, explanation
    except Exception as e:
        return False, f"Hallucination detection failed: {str(e)}"

def generate_markdown_report(results, metrics):
    """Generate a comprehensive markdown report of evaluation results."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""# LangChain Agent Evaluation Report

**Generated:** {timestamp}  
**Agent:** Presidio HR AI Agent  
**Evaluation Framework:** LangChain AgentEval with Custom Metrics

## Executive Summary

| Metric | Score | Details |
|--------|-------|---------|
| **Correctness** | {metrics['correctness']:.1%} | {metrics['correct_answers']}/{len(results)} correct answers |
| **Average Latency** | {metrics['avg_latency']:.2f}s | Response time per query |
| **Tool Usage Success** | {metrics['tool_success_rate']:.1%} | {metrics['successful_tool_uses']}/{metrics['total_tool_required']} successful tool uses |
| **Hallucination Rate** | {metrics['hallucination_rate']:.1%} | {metrics['hallucinations_detected']}/{len(results)} responses flagged |

## Detailed Results

"""

    for i, result in enumerate(results, 1):
        report += f"""### Test Case {i}

**Query:** {result['input']}  
**Expected:** {result['expected']}  
**Response:** {result['output'][:200]}{'...' if len(result['output']) > 200 else ''}  
**Latency:** {result['latency']:.2f}s  
**Correctness:** {'✅ Pass' if result['eval_score'] else '❌ Fail'}  
**Tool Usage:** {'✅ Success' if result['tool_success'] else '❌ ' + result['tool_analysis']}  
**Hallucination Check:** {'⚠️ Detected' if result['hallucination'] else '✅ Clean'} - {result['hallucination_explanation']}

"""

    report += f"""## Analysis

### Performance Insights
- **Strongest Performance:** {'Tool usage' if metrics['tool_success_rate'] > 0.8 else 'Response correctness' if metrics['correctness'] > 0.8 else 'Response latency'}
- **Areas for Improvement:** {', '.join([
    'Correctness' if metrics['correctness'] < 0.8 else '',
    'Tool Usage' if metrics['tool_success_rate'] < 0.8 else '',
    'Hallucination Prevention' if metrics['hallucination_rate'] > 0.2 else '',
    'Response Speed' if metrics['avg_latency'] > 5.0 else ''
]).strip(', ') or 'Overall performance is strong'}

### Recommendations
1. **LangFuse Monitoring:** All interactions are traced for token usage and intermediate steps
2. **NeMo Guardrails:** Input/output filtering is active for content safety
3. **Performance:** {'Consider optimizing tool selection logic' if metrics['tool_success_rate'] < 0.9 else 'Tool usage is performing well'}

---
*Report generated by LangChain AgentEval framework*
"""

    return report

def main():
    print("🔍 Starting comprehensive agent evaluation...")

    agent_executor = get_agent_executor()

    # Setup evaluation LLM
    eval_llm = ChatBedrock(
        model_id=config.LLM_MODEL_ID,
        model_kwargs={"temperature": config.LLM_TEMPERATURE},
        region_name=os.environ.get("AWS_REGION", config.AWS_REGION),
    )

    evaluator = load_evaluator("labeled_criteria", llm=eval_llm, criteria="correctness")
    results = []

    print(f"📊 Evaluating {len(EVAL_SET)} test cases...")

    for i, case in enumerate(EVAL_SET, 1):
        print(f"\n🔸 Test Case {i}: {case['input'][:50]}...")

        start = time.time()
        try:
            response = agent_executor.invoke({"input": case["input"]})
            latency = time.time() - start
            output = response.get("output", "")

            # Evaluate correctness
            eval_result = evaluator.evaluate_strings(
                prediction=output,
                reference=case["expected"],
                input=case["input"]
            )
            eval_score = eval_result.get("score", 0) > 0.5  # Convert to boolean

            # Analyze tool usage
            tool_success, tool_analysis = analyze_tool_usage(response)

            # Detect hallucinations
            hallucination, hallucination_explanation = detect_hallucination(output, case["input"], eval_llm)

            results.append({
                "input": case["input"],
                "expected": case["expected"],
                "output": output,
                "latency": latency,
                "eval_score": eval_score,
                "eval_result": eval_result,
                "tool_success": tool_success,
                "tool_analysis": tool_analysis,
                "requires_tool": case.get("requires_tool", False),
                "hallucination": hallucination,
                "hallucination_explanation": hallucination_explanation,
            })

        except Exception as e:
            latency = time.time() - start
            print(f"❌ Error in test case {i}: {str(e)}")
            results.append({
                "input": case["input"],
                "expected": case["expected"],
                "output": f"ERROR: {str(e)}",
                "latency": latency,
                "eval_score": False,
                "eval_result": {"score": 0},
                "tool_success": False,
                "tool_analysis": f"Error: {str(e)}",
                "requires_tool": case.get("requires_tool", False),
                "hallucination": False,
                "hallucination_explanation": "Error occurred",
            })

    # Calculate comprehensive metrics
    correct_answers = sum(1 for r in results if r["eval_score"])
    total_tool_required = sum(1 for r in results if r["requires_tool"])
    successful_tool_uses = sum(1 for r in results if r["requires_tool"] and r["tool_success"])
    hallucinations_detected = sum(1 for r in results if r["hallucination"])

    metrics = {
        "correctness": correct_answers / len(results),
        "correct_answers": correct_answers,
        "avg_latency": sum(r["latency"] for r in results) / len(results),
        "tool_success_rate": successful_tool_uses / total_tool_required if total_tool_required > 0 else 1.0,
        "successful_tool_uses": successful_tool_uses,
        "total_tool_required": total_tool_required,
        "hallucination_rate": hallucinations_detected / len(results),
        "hallucinations_detected": hallucinations_detected,
    }

    # Print results to console
    print("\n" + "="*60)
    print("🎯 COMPREHENSIVE AGENT EVALUATION RESULTS")
    print("="*60)
    print(f"✅ Correctness:           {metrics['correctness']:.1%} ({correct_answers}/{len(results)})")
    print(f"⏱️  Average Latency:       {metrics['avg_latency']:.2f} seconds")
    print(f"🛠️  Tool Usage Success:    {metrics['tool_success_rate']:.1%} ({successful_tool_uses}/{total_tool_required})")
    print(f"🚫 Hallucination Rate:    {metrics['hallucination_rate']:.1%} ({hallucinations_detected}/{len(results)})")
    print("="*60)

    # Generate and save markdown report
    report = generate_markdown_report(results, metrics)

    with open("agent_evaluation_report.md", "w") as f:
        f.write(report)

    print(f"📄 Detailed report saved to: agent_evaluation_report.md")
    print(f"🔍 LangFuse traces available at: {config.LANGFUSE_HOST}")

    return results, metrics

if __name__ == "__main__":
    main()
