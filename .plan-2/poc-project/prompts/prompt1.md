I've inspected the agent results, and it looks like we still didn't instruct the browser to use correctly to get results step-by-step, extracting truly valuable test
cases on each step. '/workspace/.plan-2/poc-project/outputs/basic_example_results.json'. Those test cases they don't look like a real test case in a real world, so it's lacking a lot of relevant
information. Actually, the whole test case is too basic. The agent is just navigating to the page basically. And we really need very, very useful test cases as a senior, a QA specialist should do.
Here is the prd to help you understand what are our goals with this code: '/workspace/.plan-2/poc-project/prd.md'.

The selectors don't look good for a Playwright perspective. I'm not sure about them.
But the real problem is that we are not structuring browser use very well to extract this information from the web pages to interact with the components as it should.
Here is the browser use original system prompt, revise it carefully, adjust your system prompts to make sure browser_use will act and work as we expect according to our goal. '/workspace/browser_use/agent/system_prompt.md'.

Important:

- Don't do unnecessary changes
- Be very careful on your changes and very focused on what we are looking for
- Don't create unnecessary files or code .
- Make sure to use ruv mcp tools and Swarm of claude code agents with 3 at maximum.


Here is the script to execute the application: `source .plan-2/poc-project/venv/bin/activate && python3 .plan-2/poc-project/examples/basic_usage.py`

CRITICAL: NEVER WRITE MORE THAN 30 LINES OF CODE PER AGENT. PASSTROUGHT THIS INSTRUCTION TO THE AGENT AND WHEN HE REACHS THIS LIMIT, HE MUST FINISH HIS WORK GIVING INSTRUCTIONS BACK TO THE ORCHESTRATOR, TO THEN SPAWN ANOTHER AGENT TO CONTINUE THE WORK