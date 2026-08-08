from datetime import date
import json

from django.conf import settings
from groq import Groq


client = Groq(api_key=settings.GROQ_API_KEY)


def generate_smart_goal_plan(prompt):

    today = date.today().isoformat()
    
    system_prompt = f"""
You are a Smart Goal Planner for a savings application.

Today's date is {today}.

Extract structured savings goal information from the user's message.

Return ONLY valid JSON with exactly these fields:

{{
    "name": string,
    "target_amount": number or null,
    "target_date": "YYYY-MM-DD" or null,
    "is_shared": boolean
}}

Rules:

1. Extract the goal name into the "name" field.

2. Extract target_amount ONLY if the user explicitly provides
   a target amount.

3. If the user does not provide a target amount, return null.
   NEVER invent or estimate a target amount.

4. Extract the requested goal date into the "target_date" field.

5. If the user does not provide a target date, return null.

6. Interpret relative dates using today's date.

7. For phrases such as:
   - "by September"
   - "end of September"
   - "next March"
   - "in 3 months"

   calculate the appropriate future date based on today's date.

8. NEVER return a target_date that is already in the past unless
   the user explicitly specifies a past date.

9. Set is_shared to true ONLY when the user explicitly says
   that the goal should be shared, collaborative, or that
   other people should contribute.

10. If the user does not mention sharing, return false.

11. If the user explicitly says they do NOT want the goal shared,
    return false.

12. Return JSON only.

13. Do not add any fields.

User message:
{prompt}
"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    return json.loads(content)