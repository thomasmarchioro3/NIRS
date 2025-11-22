import json

from langgraph.graph import StateGraph, END
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage, SystemMessage, AIMessage, HumanMessage
from langchain_core.messages import AIMessage, ToolCall
from langchain_core.messages import BaseMessage, SystemMessage

from .config import DEFAULT_TARGET_CBR, DEFAULT_TARGET_WBR
from .runtime import RunTimeState, ChatState, CURRENT_RUNTIME


"""
Example: 
User: Generate a rule
Assistant: <rule>...</rule>
Observation:  Wrong block rate too high
User: Try again, improve based on this feedback
"""


def extract_rule_from_llm_output(text: str) -> str:
    import re
    match = re.search(r"<rule>(.*?)</rule>", text, re.DOTALL)
    if match:
        rule = match.group(1).strip()
        print("Extracted rule:", repr(rule))
        return rule
    print("No rule found in LLM output:", text)
    return "none"

def build_graph(llm: Runnable, tools: list, target_cbr: float=DEFAULT_TARGET_CBR, target_wbr: float=DEFAULT_TARGET_WBR, max_attempts: int=5):

    evaluate_rule_tool = ToolNode(tools=[tool for tool in tools if tool.name == "evaluate_rule"])


    def llm_node(state: ChatState, config: RunnableConfig | None = None) -> ChatState:
        print("llm_node called")
        new_runtime = dict(state["runtime"])
        new_runtime["attempts"] += 1
        new_instruction = HumanMessage(
        content="Generate an iptables rule following the same instructions as before."
        )
        messages = state["messages"] + [new_instruction]
        response = llm.invoke(messages, config=config)

        return ChatState(
            messages=messages + [response],
            #runtime=state["runtime"],        
            runtime=new_runtime,  
        )



    def evaluate_rule_node(state: ChatState, config=None) -> ChatState:
        print("evaluate_rule_node called")

        # Find the latest AIMessage that has a tool call for evaluate_rule
        tool_call = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage):
                for tc in (msg.tool_calls or []):
                    if tc.get("name") == "evaluate_rule":
                        tool_call = tc
                        break
            if tool_call:
                break
        last_ai = next((m for m in reversed(state["messages"]) if isinstance(m, AIMessage)), None)
        if last_ai:
            print("AI message content:", last_ai.content)
            print("AI tool_calls:", last_ai.tool_calls)

        if not tool_call:
            print("no tool call")
            # No tool call found just return the state unchanged
            return state
        
        rule = tool_call["args"].get("rule", "none")
        print(rule)
        new_runtime = dict(state["runtime"])
        tool_call_id = tool_call["id"]

        CURRENT_RUNTIME.set(state["runtime"])
        # Execute the actual tool
        tool_result_state = evaluate_rule_tool.invoke(
            ChatState(messages=state["messages"], runtime=state["runtime"]),
            config=config
        )

        if not tool_result_state.get("messages"):
            print("ToolNode returned no messages, skipping evaluation")
            return state   

        result_str = tool_result_state["messages"][-1].content
        print("result_str",result_str)
        try:
            ev = json.loads(result_str)
        except json.JSONDecodeError:
            ev = {"status": "INVALID: JSON parse failed", "cbr": 0.0, "wbr": 1.0}

        status = ev.get("status", "")
        cbr = float(ev.get("cbr", 0.0))
     
        wbr = float(ev.get("wbr", 1.0))
  
        #print(type(cbr))
        #print(type(wbr))

        cbr_r = round(cbr, 3)
        wbr_r = round(wbr, 3)

        if "INVALID" in status:
            decision = "llm"
            reason = "Invalid rule, failed validation."

        elif "blocks a critical" in status:
            decision = "llm"
            reason = "Blocked a critical subnet, generate an other rule that doesnt block critical subnets 59.166.0.0/24 and 149.171.126.0/24"

        elif (cbr >= target_cbr) and (wbr <= target_wbr):
            decision = "end"
            reason = (
            f"Thresholds met: CBR={cbr_r} (≥ {target_cbr:.2f}) "
            f"and WBR={wbr_r} (≤ {target_wbr:.2f})."
            )
        elif cbr < target_cbr:
            decision = "llm"
            reason = (
            "Too low Correct Block Rate. "
            f"CBR={cbr_r} (target > {target_wbr:.2f}), "
            )
        elif wbr > target_wbr:
            decision = "llm"
            reason = (
            "Too high Wrong Block Rate. "
            f"WBR={wbr_r} (target ≤ {target_wbr:.2f})."
            )
        else:
            raise ValueError("This statement should never be reached")

        # Create ToolMessage with the same tool_call_id so the LLM can read the raw result
        tool_msg = ToolMessage(
        content=json.dumps({"status": status, "cbr": cbr, "wbr": wbr}),
        name="evaluate_rule",
        tool_call_id=tool_call_id
        )

        # System feedback message that includes thresholds and a clear reason
        eval_msg = SystemMessage(content=(
        "EVALUATION\n"
        f"- Status: {status}\n"
        # f"- CBR: {cbr_r}\n"
        # f"- WBR: {wbr_r}\n"
        f"- Decision: {reason}\n"
        f"Guidance: Generate a different valid rule that that does not block critical traffic"
        ))

        # Save evaluation + decision in runtime
        print(decision)
        print(reason)
        new_runtime = dict(state["runtime"])
        new_runtime["evaluation"] = {"status": status, "cbr": cbr, "wbr": wbr}
        new_runtime["decision"] = decision
        new_runtime["decision_reason"] = reason
        new_runtime["targets"] = {"cbr": DEFAULT_TARGET_CBR, "wbr": DEFAULT_TARGET_WBR}
        new_runtime["last_rule"] = rule

        return ChatState(
        messages=state["messages"] + [tool_msg, eval_msg],
        runtime=new_runtime
        )

    def router(state: ChatState) -> str:
        rt = state["runtime"]
        eval_data = rt.get("evaluation", {"status": "init", "cbr": 0.0, "wbr": 1.0})

        status = str(eval_data.get("status", ""))
        cbr = float(eval_data.get("cbr", 0.0))
        wbr = float(eval_data.get("wbr", 1.0))
        print("router")
        print(cbr)
        print(wbr)
        # thresholds
        print("Target CBR", target_cbr)

        print("Target WBR", target_wbr)
        attempts = rt.get("attempts", 0)
        print("attempts")
        print(attempts)
        # success → end
        if cbr >= target_cbr and wbr <= target_wbr:
            print("thresholds are met")
            return "end"

        elif attempts >= max_attempts:
            return "none"  

        return "llm"
    def none_node(state: ChatState) -> ChatState:
        new_runtime = dict(state["runtime"])

        #rt = state["runtime"]
        new_runtime["last_rule"] = "none"  

        
        return ChatState(messages=[], runtime=new_runtime)


    # Graph Structure
    builder = StateGraph(ChatState, RunnableConfig)
    builder.set_entry_point("llm")

    builder.add_node("llm", llm_node)
    builder.add_node("evaluate_rule", evaluate_rule_node)

    builder.add_node("none", none_node)

    builder.add_edge("llm", "evaluate_rule")

    builder.add_conditional_edges(
    "evaluate_rule",
    router,
    {
        "llm": "llm",
        "end": END,
        "none": "none",   # <-- this fixes KeyError: 'none'
    },
    )

    builder.add_edge("none", END)

    return builder.compile()
