import litellm
import json
import os

from langfuse import Langfuse

litellm.success_callback = ['langfuse']
litellm.failure_callback = ['langfuse']

langfuse = Langfuse()

# https://litellm.vercel.app/docs/completion/function_call => TODO: 做成Emacs的助理Assistant，function calling本地的函数完成编辑，比如语音说一句，然后function calling调用Emacs函数编辑本地代码

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
    elif "san francisco" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})


def test_parallel_function_call():
    try:
        # Step 1: send the conversation and available functions to the model
        messages = [{"role": "user", "content": "What's the weather like in San Francisco, Tokyo, and Paris?"}]
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                    },
                },
            }
        ]
        # ----- https://github.com/BerriAI/litellm/issues/1832 => Error occurred: module 'litellm' has no attribute 'generate'
        #trace = langfuse.trace(name="test-funcall")
        #span = trace.span(trace_id="test-funcall-tid")
        #litellm.generate(langfuseSpan= span) ## =>
        #litellm.generate(langfuseTrace= trace)
        # ------- https://langfuse.com/docs/sdk/python/low-level-sdk => 能创建一颗树，但是没有数据在上面。。。都是空的
        trace = langfuse.trace(name = "llm-feature")
        retrieval = trace.span(name = "retrieval")
        retrieval.generation(name = "query-creation")
        retrieval.span(name = "vector-db-search")
        retrieval.event(name = "db-summary")
        trace.generation(name = "user-output")
        # -----
        response = litellm.completion(
            model="gpt-3.5-turbo-1106",
            messages=messages,
            tools=tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
        )
        print("\nFirst LLM Response:\n", response)
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        print("\nLength of tool calls", len(tool_calls))

        # Step 2: check if the model wanted to call a function
        if tool_calls:
            # Step 3: call the function
            # Note: the JSON response may not always be valid; be sure to handle errors
            available_functions = {
                "get_current_weather": get_current_weather,
            }  # only one function in this example, but you can have multiple
            messages.append(response_message)  # extend conversation with assistant's reply

            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                function_response = function_to_call(
                    location=function_args.get("location"),
                    unit=function_args.get("unit"),
                )
                messages.append(
                    {
                        "tool_call_id": tool_call.id,
                        "role": "tool", ## Assistant API 支持三种 工具：代码解释器（Code Interpreter）、信息检索（Retrieval）和函数调用（Function calling） 。=> Function calling是tools属性。
                        "name": function_name,
                        "content": function_response,
                    }
                )  # extend conversation with function response
            second_response = litellm.completion(
                model="gpt-3.5-turbo-1106",
                messages=messages,
            )  # get a new response from the model where it can see the function response
            print("\nSecond LLM response:\n", second_response)
            return second_response
    except Exception as e:
      print(f"Error occurred: {e}")

test_parallel_function_call()