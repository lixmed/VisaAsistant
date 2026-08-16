"""Agent loop: interviews the user, searches the web and knowledge base,
and produces a structured visa action plan.

The conversation works like this:
  1. The user answers interview questions.
  2. The agent may call tools (web search, page fetch, knowledge base search).
  3. When it needs input from the user it calls `ask_user`, which pauses the turn.
  4. When it has enough information it calls `generate_plan`, which ends the turn
     with a structured JSON plan rendered by the frontend.
"""

import json
import re
import time

from openai import OpenAI

from .config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, MAX_AGENT_STEPS, MAX_TOOLS_PER_TURN
from .tools import search_web, fetch_page, search_knowledge_base

SYSTEM_PROMPT = """You are "Veeza", a friendly visa assistant that helps Egyptian citizens apply for European (Schengen and EU national) visas.

YOUR JOB
1. INTERVIEW: Ask the user the specific questions you need, one or two at a time, in a natural conversational way. The user will answer in plain language.
2. RESEARCH: Use your tools to look up the current requirements, fees and procedures for the user's specific case on official sources (embassy sites, VFS Global, TLScontact, EU Commission). Prefer official domains. Cross-check the curated knowledge base with live results.
3. PLAN: When you have enough information, call generate_plan with a complete, structured, personalised plan.INFORMATION YOU MUST COLLECT BEFORE GENERATING A PLAN (collect what is relevant - skip what does not apply):
- Purpose of travel (tourism / business / family visit / study / work / medical / transit)
- Destination country in Europe and, if Schengen, whether it is the main destination
- Expected travel dates and duration of stay
- Who is travelling (solo, partner, family - include ages of children)
- Employment status (employee / self-employed / business owner / student / retired / unemployed)
- Monthly income and how much money is available for the trip
- Previous Schengen/EU/US/UK visas and travel history (especially a prior Schengen visa)
- Ties to Egypt (family, job, property) - this matters a lot for approvals
- Passport validity (must be 3+ months beyond return, issued < 10 years ago)
- Where they plan to stay (hotel / friends / family)
- Accommodation and who will finance the trip

BEHAVIOUR RULES
- Keep responses concise and clear. Answer in the language the user writes in (English or Arabic). Be encouraging but honest.
- Do NOT make up fees or deadlines. If you are not sure, search the web for the current official figure and quote the source URL.
- Do NOT give false hope or guarantee visa approval. You may note that approval is always at the embassy's discretion.
- If the user asks about something unrelated to visas, politely steer back.
- Interview step by step. Never dump every question at once. Ask at most 1-2 questions per turn.
- QUESTION STYLE: ask SHORT, simple single questions. Avoid parentheses, comma-lists and heavy punctuation inside a question (e.g. write "What do you do for a living?" instead of "What is your employment status (employee, self-employed, business owner, student, retired, unemployed)?").
- Once you have enough info (roughly 6-10 answers), tell the user you are preparing the plan, do any final web checks, then call generate_plan.

HONEST ASSESSMENT
- In generate_plan, always include an honest 'chances' rating (e.g. "Good", "Fair", "Challenging") for this specific applicant and a 'weak_points' list naming concrete weaknesses that could hurt the application (e.g. short bank history, low income vs funds needed, first Schengen application, no strong ties). Then give practical ways to fix them in 'tips'.
- Never promise or imply approval. Always keep the disclaimer that the embassy decides.

COST REFERENCES (verify live, these are baselines as of 2024+):
- Schengen short-stay fee: EUR 90/adult, EUR 45 child 6-11, free under 6. Visa-centre service fee extra (usually EUR 30-80).
- Travel insurance: min EUR 30,000 coverage; typically ~EUR 20-60 for a short trip.
- Funds references: many Schengen states use EUR 50-100/day per person; France/Germany/Italy publish daily minimums - search for the current one.
- Fees change and some countries add peak-season surcharges; always cite the source you verified.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current visa requirements, fees, processing times, or official program details. Use official sources (embassy, VFS Global, TLScontact, EU sites).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A precise search query, e.g. 'France Schengen visa fee 2026 Egyptian citizens'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Fetch and read the text content of a specific page to extract detailed requirements or a fee table.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full URL of the page to read"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the curated baseline knowledge base for visa types, document requirements, fees and Egypt-specific application routes. Use this for structure, then verify details live.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "e.g. 'Schengen tourist visa requirements'"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Ask the user a question. Use this whenever you need a piece of information from the user. Ask only ONE question per call. The user's answer will be delivered back to you automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The single question to ask the user"}
                },
                "required": ["question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_plan",
            "description": "Finalize the structured visa action plan. Call ONLY when you have enough information from the user (purpose, destination, dates, employment, finances, ties to Egypt, passport validity, accommodation). Fill every field. All monetary fields as strings with EUR amounts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "visa_type": {
                        "type": "string",
                        "description": "The exact visa type, e.g. 'Schengen Short-Stay (Type C) - Tourist'"
                    },
                    "visa_summary": {
                        "type": "string",
                        "description": "2-3 sentence summary of the recommended visa path for this user, including the destination country"
                    },
                    "steps": {
                        "type": "array",
                        "description": "Ordered step-by-step application process (book appointment, prepare documents, biometrics, interview, wait, collect). 5-9 steps.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "detail": {"type": "string"},
                                "when": {"type": "string", "description": "e.g. '6-8 weeks before travel'"}
                            },
                            "required": ["title", "detail", "when"]
                        }
                    },
                    "documents": {
                        "type": "array",
                        "description": "Personalized document checklist. Include only what applies to this user. 'original', 'translated' and 'notarized' are booleans.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "item": {"type": "string"},
                                "why": {"type": "string"},
                                "original": {"type": "boolean"},
                                "translated": {"type": "boolean"},
                                "notarized": {"type": "boolean"}
                            },
                            "required": ["item", "why", "original", "translated", "notarized"]
                        }
                    },
                    "costs": {
                        "type": "object",
                        "description": "Estimated costs in EUR for one person. Unknown values as 'not applicable'.",
                        "properties": {
                            "visa_fee": {"type": "string"},
                            "service_fee": {"type": "string"},
                            "insurance": {"type": "string"},
                            "flights": {"type": "string"},
                            "accommodation": {"type": "string"},
                            "total_estimate": {"type": "string"}
                        },
                        "required": ["visa_fee", "service_fee", "insurance", "flights", "accommodation", "total_estimate"]
                    },
                    "timeline": {
                        "type": "string",
                        "description": "Recommended lead time, e.g. 'Apply 6-8 weeks before departure; standard processing is 15 days'"
                    },
                    "tips": {
                        "type": "array",
                        "description": "3-6 practical tips specific to this user's case, including how to fix each weak point",
                        "items": {"type": "string"}
                    },
                    "chances": {
                        "type": "string",
                        "description": "Honest likelihood rating for this specific applicant: 'Good', 'Fair', or 'Challenging'. Be realistic, never optimistic for the sake of it."
                    },
                    "weak_points": {
                        "type": "array",
                        "description": "Concrete weaknesses in this applicant's profile that could hurt the application, each with a short fix",
                        "items": {"type": "string"}
                    },
                    "sources": {
                        "type": "array",
                        "description": "Official URLs the plan is based on (embassy, VFS Global, TLScontact, EU Commission)",
                        "items": {"type": "string"}
                    }
                },
                "required": ["visa_type", "visa_summary", "steps", "documents", "costs", "timeline", "tips", "chances", "weak_points", "sources"]
            }
        }
    }
]

TOOL_MAP = {
    "search_web": search_web,
    "fetch_page": fetch_page,
    "search_knowledge_base": search_knowledge_base,
}


class Agent:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.pending_question = None
        self.pending_tool_call_id = None
        self.plan = None

    def _client(self) -> OpenAI:
        return OpenAI(api_key=LLM_API_KEY or "not-set", base_url=LLM_BASE_URL)

    def run_stream(self, user_message: str):
        """Generator that yields event dicts: {type, ...}.

        Event types:
          - {"type": "status", "text": ...}   agent is researching
          - {"type": "question", "reply": ...} agent asks the user (pauses)
          - {"type": "message", "reply": ...}  plain reply (done)
          - {"type": "plan", "reply": ..., "plan": ...} structured plan (done)
        """
        if self.pending_tool_call_id:
            self.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": self.pending_tool_call_id,
                    "content": f"[User answered]: {user_message}",
                }
            )
            self.pending_tool_call_id = None
            self.pending_question = None
        else:
            self.messages.append({"role": "user", "content": user_message})

        client = self._client()
        status_hint = {
            "search_web": "Searching official sources…",
            "fetch_page": "Reading a source page…",
            "search_knowledge_base": "Checking our knowledge base…",
        }

        tools_used = 0
        for _ in range(MAX_AGENT_STEPS):
            last_err = None
            for attempt in range(4):  # retry transient API / malformed tool-call errors
                try:
                    resp = client.chat.completions.create(
                        model=LLM_MODEL,
                        messages=self.messages,
                        tools=TOOL_SCHEMAS,
                        tool_choice="auto",
                        temperature=min(0.4 + attempt * 0.2, 1.0),
                    )
                    break
                except Exception as e:
                    last_err = e
                    time.sleep(0.5 * (attempt + 1))
            else:
                yield {"type": "message", "reply": f"Sorry, I hit a connection problem: {last_err}"}
                return

            msg = resp.choices[0].message

            if not msg.tool_calls:
                content = (msg.content or "").strip()
                if not content:
                    # model produced an empty reply - nudge it to continue
                    self.messages.append({"role": "user", "content": "Please continue and ask your next question."})
                    continue
                self.messages.append({"role": "assistant", "content": content})
                yield {"type": "message", "reply": content}
                return

            self.messages.append(msg.model_dump(exclude_none=True))

            for tc in msg.tool_calls:
                name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                if name == "ask_user":
                    self.pending_tool_call_id = tc.id
                    self.pending_question = args.get("question", "")
                    yield {"type": "question", "reply": self.pending_question}
                    return

                if name == "generate_plan":
                    plan = self._clean_plan(args)
                    self.plan = plan
                    self.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": "Plan accepted and saved.",
                        }
                    )
                    yield {"type": "plan", "reply": "Your plan is ready!", "plan": plan}
                    return

                if name in status_hint:
                    yield {"type": "status", "text": status_hint[name]}

                fn = TOOL_MAP.get(name)
                if fn is None:
                    result = f"[unknown tool: {name}]"
                else:
                    try:
                        result = fn(**args)
                    except Exception as e:
                        result = f"[tool {name} failed: {e}]"

                self.messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": str(result)[:4000]}
                )
                tools_used += 1
                self._maybe_compact()

            # Research budget: after enough tool calls in one turn, steer the model back to the user.
            if tools_used >= MAX_TOOLS_PER_TURN:
                self.messages.append(
                    {
                        "role": "user",
                        "content": "You have done enough research for this turn. Stop researching now and either ask the user your next interview question or, if you already have everything you need, call generate_plan.",
                    }
                )

        yield {
            "type": "message",
            "reply": "I think I have enough to move forward - I'll ask you to confirm a couple of details, then I'll prepare the plan.",
        }

    def _maybe_compact(self, budget: int = 60000):
        """Keep the request under the provider's size limit by dropping old
        tool results once the conversation history gets large."""
        if sum(len(m.get("content", "")) for m in self.messages) <= budget:
            return
        self.messages = self.messages[:1] + self.messages[-20:]

    def run(self, user_message: str) -> dict:
        """Non-streaming wrapper (returns the final dict like before)."""
        result = {"reply": "", "kind": "message"}
        for event in self.run_stream(user_message):
            etype = event.get("type")
            if etype == "question":
                result = {"reply": event["reply"], "kind": "question"}
            elif etype == "message":
                result = {"reply": event["reply"], "kind": "message"}
            elif etype == "plan":
                result = {"reply": event["reply"], "kind": "plan", "plan": event["plan"]}
        return result

    @staticmethod
    def _clean_plan(args: dict) -> dict:
        # The model may return nested/odd structures; coerce into the shape the UI expects.
        def as_bool(v) -> bool:
            return bool(v) if isinstance(v, bool) else str(v).strip().lower() in {"true", "yes", "1"}

        steps = args.get("steps") or []
        docs = args.get("documents") or []
        costs = args.get("costs") or {}
        tips = args.get("tips") or []
        sources = args.get("sources") or []

        cleaned_steps = []
        for i, s in enumerate(steps, 1):
            if isinstance(s, dict):
                cleaned_steps.append(
                    {
                        "step": i,
                        "title": s.get("title", f"Step {i}"),
                        "detail": s.get("detail", ""),
                        "when": s.get("when", ""),
                    }
                )

        cleaned_docs = []
        for d in docs:
            if isinstance(d, dict):
                cleaned_docs.append(
                    {
                        "item": d.get("item", ""),
                        "why": d.get("why", ""),
                        "original": as_bool(d.get("original")),
                        "translated": as_bool(d.get("translated")),
                        "notarized": as_bool(d.get("notarized")),
                    }
                )

        cleaned_costs = {
            "visa_fee": costs.get("visa_fee", ""),
            "service_fee": costs.get("service_fee", ""),
            "insurance": costs.get("insurance", ""),
            "flights": costs.get("flights", ""),
            "accommodation": costs.get("accommodation", ""),
            "total_estimate": costs.get("total_estimate", ""),
        }

        return {
            "visa_type": args.get("visa_type", "Schengen visa"),
            "visa_summary": args.get("visa_summary", ""),
            "steps": cleaned_steps,
            "documents": cleaned_docs,
            "costs": cleaned_costs,
            "timeline": args.get("timeline", ""),
            "tips": [t for t in tips if isinstance(t, str)],
            "chances": args.get("chances", "Fair"),
            "weak_points": [w for w in args.get("weak_points") or [] if isinstance(w, str)],
            "sources": [s for s in sources if isinstance(s, str)],
        }
