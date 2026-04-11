1. detectmodel should output an annotated usermessage (lets call it modifiedmessage) to better identify PII in user prompts. This is more accurate than the current approach of replacing all matching terms in entire query, which can redact unintended text, a major concern for longer queries. 
Possible approaches:
- usermessage is annotated with special markers to signal PPI for quicker identification. (Markers replicated by user?)
- model returns indexes of PII in question (Prone to LLM errors?)

2. Action decider model: Weighs the importance of found PIIs in message context, uses this to decide the best course of action for them
- Includes message streaming

3. Scorer: Scores the outputs of the action decider model based on effectiveness
- Additional tools for logging prompts, outputs, scores into text files for further evaluation
- Optimized prompting model: Creates self-feedback loop with action decider and scorer to find most optimal prompts
    - Feedback loop uses aggregates to determine average scores for reliability