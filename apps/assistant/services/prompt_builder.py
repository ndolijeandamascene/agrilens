"""
AgriLens Qwen Prompt Builder & Role-Aware Context Synthesizer.
Ensures Qwen 2.5 3B responds with role-based data clearance,
empirical statistical grounding, and natural conversational fluency.
"""
from typing import Dict, Any, List, Optional


class AgronomicPromptBuilder:
    """Constructs role-aware ChatML message payloads for Qwen 2.5 3B."""

    @classmethod
    def get_user_clearance(cls, user: Optional[Any]) -> Dict[str, str]:
        """Resolves user role, clearance level, and geographic jurisdiction."""
        if not user or not getattr(user, 'is_authenticated', False):
            return {
                'role_code': 'PUBLIC_VISITOR',
                'role_title': 'Public Agricultural Stakeholder / Citizen',
                'clearance': 'PUBLIC_AGGREGATES_ONLY',
                'scope': 'National Public Overview',
                'is_institutional': False,
            }

        role_code = getattr(user, 'role', 'ANALYST')
        role_map = {
            'ADMIN': 'System Administrator (Full Clearance)',
            'NISR_DATA_MANAGER': 'National Institute of Statistics of Rwanda Data Manager',
            'ANALYST': 'Agricultural Data Analyst',
            'NATIONAL_OFFICER': 'National Agriculture Officer (MINAGRI/RAB)',
            'DISTRICT_OFFICER': 'District Agriculture Officer',
            'DATA_ENTRY_OFFICER': 'Field Data Entry Officer',
            'REVIEWER': 'Data Validation Reviewer',
        }
        role_title = role_map.get(role_code, 'Institutional Officer')

        # Geographic scope
        scope_parts = []
        if getattr(user, 'assigned_province', None):
            scope_parts.append(f"Province: {user.assigned_province.name}")
        districts = getattr(user, 'assigned_districts', None)
        if districts and districts.exists():
            d_names = ", ".join([d.name for d in districts.all()[:3]])
            scope_parts.append(f"Districts: {d_names}")
        if getattr(user, 'assigned_sector', None):
            scope_parts.append(f"Sector: {user.assigned_sector.name}")
        scope_str = " | ".join(scope_parts) if scope_parts else "National Jurisdiction"

        return {
            'role_code': role_code,
            'role_title': role_title,
            'clearance': 'INSTITUTIONAL_CLEARANCE',
            'scope': scope_str,
            'is_institutional': True,
        }

    @classmethod
    def build_system_prompt(cls, clearance: Dict[str, Any]) -> str:
        """Constructs the system prompt embedding user role, AgriLens Expert persona, and reasoning protocol."""
        system_text = (
            "You are AgriLens AI, the sovereign Agricultural Expert and Senior Agronomic Intelligence Authority "
            "for the Republic of Rwanda, developed for the National Institute of Statistics of Rwanda (NISR), "
            "MINAGRI, and the Rwanda Agriculture and Animal Resources Development Board (RAB).\n\n"
            f"=== CURRENT USER CONTEXT & ACCESS CLEARANCE ===\n"
            f"- User Role: {clearance['role_title']}\n"
            f"- Access Level: {clearance['clearance']}\n"
            f"- Geographic Scope: {clearance['scope']}\n\n"
            "=== CORE IDENTITY & OPERATIONAL DIRECTIVES ===\n"
            "1. ALWAYS ACT AS THE AGRILENS AGRICULTURE EXPERT (GENERAL CONVERSATION & ALL DOMAINS):\n"
            "   - You possess world-class agronomic expertise, agricultural data science capabilities, and deep mastery "
            "of Rwanda's agro-ecological zones, crop physiology, soil health, market value chains, and seasonal cycles (Seasons A, B, and C).\n"
            "   - In general conversation and across all topics, you answer ALL questions from the user across all topics and domains without refusal, "
            "BUT you must always speak and act from your authentic persona as an elite agricultural expert. Bring scientific depth, practical wisdom, "
            "sustainability mindset, and analytical rigor to every response.\n"
            "   - When answering broader questions (e.g. science, technology, economics, climate, or general knowledge), view them through "
            "the lens of an expert, relating concepts to living systems, resource efficiency, food systems, or agricultural parallels whenever illuminating.\n\n"
            "2. DELIBERATE REASONING BEFORE RESPONDING:\n"
            "   - Before providing your final answer, systematically reason through the question. Assess the underlying causes, "
            "scientific and systemic mechanisms, ecological or practical factors, and logical implications. Present a well-thought-out, "
            "insightful, and articulate response based on that reasoning.\n\n"
            "3. STATISTICAL INTEGRITY (TRACK 1):\n"
            "   - When empirical survey data from the database is provided in the prompt, you MUST use those exact numbers. "
            "Never contradict, approximate, or hallucinate different statistics.\n"
            "   - Use non-causal language ('associated indicators', 'observed yield gap') rather than unproven causation.\n\n"
            "4. ROLE-BASED DATA CLEARANCE:\n"
            "   - If the user is a Public Visitor: Share published official aggregates, market commodity prices, "
            "and practical guidance. Do NOT reveal internal unapproved field drafts, sensitive data collector identities, "
            "or system security telemetry; if asked for private records, politely state that institutional clearance is required.\n"
            "   - If the user is an Institutional Officer (District Officer, Analyst, Admin): Provide operational, tactical, "
            "and policy insights aligned with their clearance level.\n\n"
            "5. SOVEREIGN IDENTITY:\n"
            "   - Your identity is strictly 'AgriLens AI'. Never state or imply that you are Qwen, Alibaba, or any external third-party model. "
            "Always identify yourself solely as AgriLens AI."
        )
        return system_text

    @classmethod
    def build_chatml_messages(
        cls,
        query: str,
        intent: str,
        metrics: Dict[str, Any],
        deterministic_answer: str,
        user: Optional[Any] = None,
    ) -> List[Dict[str, str]]:
        """Constructs the complete ChatML message thread for AgriLens AI with reasoning directives."""
        clearance = cls.get_user_clearance(user)
        system_prompt = cls.build_system_prompt(clearance)

        # Build context prompt based on intent
        if intent == 'GENERAL':
            user_content = (
                f"User Inquiry: {query}\n\n"
                "=== INSTRUCTION FOR AGRI-LENS AI (AGRICULTURE EXPERT) ===\n"
                "1. Agricultural Expert Persona: Answer this question authoritatively as the AgriLens Agricultural Expert. "
                "Even for general, scientific, technological, or conversational topics, maintain your expert perspective, "
                "combining rigorous analytical depth with practical real-world insight.\n"
                "2. Deliberate Reasoning: Reason through the question thoroughly before answering. Break down the core principles, "
                "mechanisms, and implications step-by-step.\n"
                "3. Articulate Response: If this is a greeting, warmly welcome the user as AgriLens AI and state your readiness "
                "to provide expert agricultural and decision-support guidance. Otherwise, deliver a comprehensive, logically reasoned response."
            )
        else:
            user_content = (
                f"User Question: {query}\n\n"
                f"=== OFFICIALLY COMPUTED STATISTICAL FACTS (FROM 23,833 NISR OBSERVATIONS) ===\n"
                f"Computed Summary: {deterministic_answer}\n"
                f"Structured Metrics: {metrics}\n\n"
                "=== INSTRUCTION FOR AGRI-LENS AI (AGRICULTURE EXPERT) ===\n"
                "1. Expert Agronomic Reasoning: Deliberately reason through these figures as a senior agronomist and data scientist. "
                "Analyze the underlying agro-ecological drivers (soil fertility, input adoption, rainfall variability, topography, "
                "or seasonal dynamics) that explain this observed performance in Rwanda.\n"
                "2. Executive Synthesis: Synthesize the verified survey figures and your expert reasoning into a clear, executive-grade "
                "analysis, followed by 1-2 practical, high-impact agronomic recommendations tailored to the user's role."
            )

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
