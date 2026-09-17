- simple agent with llm agents
    - we can define an agent ( Agent / LLM agent) with name , descriptions , model , tools (optional ) tools gives external capabitility to an llm that an llm doesnt have.
    - we can guide the agent using instruction   ( they defines core task , when it can be used etx) , can also take variables as inputs
    - Tools parameter ( these are just pure python functions with specialized task ) and we provide a list of tools to the agent/ llm agent
    - we can also configure a default model across our agents
    - to get structured i/o data from agent ( use input / output schema )

- function tools
    - when a pre built framework don’t meet our req. we can make custom functions tools registering a function tool is simple jsut put the function name in tool list and the adk auto wraps ur function in the FunctioTools
    - while making a function tool we can define req. paramters , optional parameters also context injection can be done in a tool ( allows to access a agent envi.)
    - prefered return type is dict in py.
    - also to pass data bw multiple tools we use temp: so other agent can read the data.
    
- long running fucntion tools
    - this is basically used when we want to runa long runnugn operations and is outside the execution scope of an agent
    - when it is invoked it can init. return an init result. ( such as task_id)
    - so when a long_runnign_agent is invoked the agent has to decide whether to contunue the execution of agent or to wait for long_runnign_agent.
    
- agent as a tool - when agent A calls agent B as a tool and agent B’s answer si then passed back to agent A and agent A then summarizes the answer or uses the response in some way.
    - it is diff from subagent because subagent because subagent calls another agent as an agnt and here agent A is fully out of the loop the task’s responsibility is fully on agent B