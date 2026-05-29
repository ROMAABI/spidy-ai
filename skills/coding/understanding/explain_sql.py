import asyncio
import re
from skills.coding.base import SkillResult, BaseCodingSkill


class ExplainSqlSkill(BaseCodingSkill):
    name = "explain_sql"
    description = "Explain what a SQL query does, step by step"

    @classmethod
    def _tool_params(cls) -> dict:
        return {
            "query": {"type": "string", "description": "The SQL query to explain"},
        }

    @classmethod
    def _tool_required(cls) -> list[str]:
        return ["query"]

    async def execute(self, **kwargs) -> SkillResult:
        query = kwargs.get("query", "")
        if not query:
            return SkillResult(success=False, output="No query provided")

        parts = []
        parts.append(f"Query:")
        parts.append(f"```sql\n{query}\n```")
        parts.append("")

        # Basic structural breakdown
        query_upper = query.upper().strip()
        clauses = []
        for kw in ["SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN",
                     "INNER JOIN", "GROUP BY", "HAVING", "ORDER BY", "LIMIT",
                     "OFFSET", "UNION", "INSERT", "UPDATE", "DELETE", "SET",
                     "INTO", "VALUES", "CREATE", "ALTER", "DROP", "INDEX"]:
            idx = query_upper.find(kw)
            if idx >= 0:
                clauses.append((kw, idx))

        clauses.sort(key=lambda x: x[1])
        parts.append("Clauses detected (in order):")
        for kw, idx in clauses:
            parts.append(f"  • {kw}")

        parts.append("")

        try:
            import ollama
            resp = await asyncio.to_thread(
                ollama.chat,
                model="kimi-k2",
                messages=[{"role": "user", "content": f"Explain this SQL query step by step in plain English. Tell me what each part does and what the overall query returns.\n\n```sql\n{query}\n```"}],
                stream=False,
            )
            explanation = resp["message"]["content"]
        except Exception as e:
            explanation = f"(LLM explanation unavailable: {e})"

        parts.append(explanation)
        return SkillResult(success=True, output="\n".join(parts), data={"query": query})
