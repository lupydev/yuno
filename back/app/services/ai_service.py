"""
AI Service - LangChain Integration

Handles all AI/LLM operations using LangChain and LangGraph.
Provides structured extraction, web scraping, and response formatting.
"""

import json
from typing import TypedDict

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from app.infraestructure.core.config import settings
from app.infraestructure.core.logging import logger


# Pydantic models for structured output
class LocationCategoryExtraction(BaseModel):
    """Schema for location and category extraction from tweet."""

    city: str | None = Field(None, description="City name or null")
    country: str | None = Field(None, description="Country name or null")
    state: str | None = Field(None, description="State/province or null")
    category: str | None = Field(
        None, description="Event category/type or null")


class EventScrapingState(TypedDict):
    """State for LangGraph web scraping workflow."""

    city: str | None
    country: str | None
    category: str | None
    limit: int
    search_query: str
    raw_events: list[dict]
    events: list[dict]
    error: str | None


class AIService:
    """Service for all AI/LLM operations using LangChain"""

    def __init__(self):
        # Initialize LLMs with different configurations
        self.extraction_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.1,  # Low temperature for deterministic extraction
            max_tokens=150,
            api_key=settings.openai_api_key,
        )

        self.scraping_llm = ChatOpenAI(
            model="gpt-4o", temperature=0.3, max_tokens=2000, api_key=settings.openai_api_key
        )

        self.formatting_llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,  # Higher temperature for creative formatting
            max_tokens=500,
            api_key=settings.openai_api_key,
        )

    async def extract_location_and_category_from_tweet(
        self, tweet_text: str
    ) -> dict[str, str | None] | None:
        """
        Extract city and event category from tweet using LangChain.

        Args:
            tweet_text: The text content of the tweet

        Returns:
            dict with 'city', 'country', 'state', 'category' or None if nothing found
        """
        parser = JsonOutputParser(pydantic_object=LocationCategoryExtraction)

        system_template = """You are a location and event category extraction assistant.
        Extract the city name and event category/type from the tweet.

        Event categories can be: tech, music, art, sports, food, conference,
        concert, theater, nightlife, festival, workshop, etc.

        Examples:
        - "What's happening in New York this weekend?"
          -> {{"city": "New York", "country": "USA", "state": "New York", "category": null}}
        - "tech events in San Francisco"
          -> {{"city": "San Francisco", "country": "USA", "state": "California", "category": "tech"}}
        - "best concerts in London"
          -> {{"city": "London", "country": "UK", "state": null, "category": "concert"}}
        - "art exhibitions in Paris"
          -> {{"city": "Paris", "country": "France", "state": null, "category": "art"}}
        - "music festivals"
          -> {{"city": null, "country": null, "state": null, "category": "music"}}

        {format_instructions}
        """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", "{tweet_text}")]
        ).partial(format_instructions=parser.get_format_instructions())

        # Create LangChain chain
        chain = prompt | self.extraction_llm | parser

        try:
            result = await chain.ainvoke({"tweet_text": tweet_text})
            # Return result if at least city or category is found
            if result.get("city") or result.get("category"):
                logger.info(
                    f"Extracted: city={result.get('city')}, category={result.get('category')}"
                )
                return result
            return None
        except Exception as e:
            logger.error(
                f"Failed to extract location/category with LangChain: {e}")
            return None

    async def scrape_events_with_langgraph(
        self, city: str | None, country: str | None, category: str | None, limit: int = 5
    ) -> list[dict]:
        """
        Use LangGraph to orchestrate web scraping for events when DB is empty.

        LangGraph manages a multi-step workflow:
        1. Build search query
        2. Search web for events using LLM
        3. Parse and validate event data

        Args:
            city: City name
            country: Country name
            category: Event category/type
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries
        """

        # Define graph nodes
        def build_query(state: EventScrapingState) -> EventScrapingState:
            """Build search query from parameters."""
            query_parts = []
            if state["category"]:
                query_parts.append(f"{state['category']} events")
            else:
                query_parts.append("events")

            if state["city"]:
                query_parts.append(f"in {state['city']}")
                if state["country"]:
                    query_parts.append(f", {state['country']}")

            state["search_query"] = " ".join(query_parts)
            logger.info(f"Built search query: {state['search_query']}")
            return state

        async def search_events(state: EventScrapingState) -> EventScrapingState:
            """Search web for events using LLM."""
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an event discovery assistant. Search the web for upcoming events
                based on the user's query and return structured event information.

                Return a JSON object with an 'events' array containing up to {limit} events.
                Each event should have: name, description, date (YYYY-MM-DD), time (HH:MM or null),
                venue, city, price, url, category.

                Focus on real, upcoming events happening in the next 30 days.
                Prioritize official event pages and reputable sources.
                """,
                    ),
                    ("user", "Find {search_query}"),
                ]
            )

            parser = JsonOutputParser()
            chain = prompt | self.scraping_llm | parser

            try:
                result = await chain.ainvoke(
                    {"search_query": state["search_query"],
                        "limit": state["limit"]}
                )
                state["raw_events"] = result.get("events", [])
                logger.info(
                    f"Found {len(state['raw_events'])} raw events from web")
            except Exception as e:
                logger.error(f"Error searching events: {e}")
                state["error"] = str(e)
                state["raw_events"] = []

            return state

        def parse_events(state: EventScrapingState) -> EventScrapingState:
            """Convert raw event data to structured dictionaries."""
            events = []
            for event_data in state["raw_events"][: state["limit"]]:
                try:
                    event = {
                        "name": event_data.get("name", "Unknown Event"),
                        "description": event_data.get("description", ""),
                        "date": event_data.get("date"),
                        "time": event_data.get("time"),
                        "venue": event_data.get("venue"),
                        "city": event_data.get("city", state["city"]),
                        "price": event_data.get("price"),
                        "url": event_data.get("url"),
                        "category": event_data.get("category", state["category"]),
                    }
                    events.append(event)
                except Exception as e:
                    logger.warning(f"Failed to parse event: {e}")
                    continue

            state["events"] = events
            logger.info(f"Parsed {len(events)} events successfully")
            return state

        # Build LangGraph workflow
        workflow = StateGraph(EventScrapingState)

        workflow.add_node("build_query", build_query)
        workflow.add_node("search_events", search_events)
        workflow.add_node("parse_events", parse_events)

        workflow.set_entry_point("build_query")
        workflow.add_edge("build_query", "search_events")
        workflow.add_edge("search_events", "parse_events")
        workflow.add_edge("parse_events", END)

        graph = workflow.compile()

        # Execute workflow
        initial_state: EventScrapingState = {
            "city": city,
            "country": country,
            "category": category,
            "limit": limit,
            "search_query": "",
            "raw_events": [],
            "events": [],
            "error": None,
        }

        try:
            final_state = await graph.ainvoke(initial_state)
            return final_state["events"]
        except Exception as e:
            logger.error(f"Error in LangGraph scraping workflow: {e}")
            return []

    async def format_event_response(
        self, events: list[dict], city: str | None, category: str | None, original_tweet: str
    ) -> str:
        """
        Format events into an engaging Twitter response using LangChain.

        Args:
            events: List of event dictionaries
            city: City name
            category: Event category
            original_tweet: Original tweet text

        Returns:
            Formatted tweet response (or first tweet if thread needed)
        """

        # Initialize LangChain components
        parser = StrOutputParser()

        system_template = """You are @invme_bot, a friendly event discovery assistant on Twitter/X.
        Format the following events into an engaging tweet response.

        Requirements:
        - Start with a friendly greeting mentioning the city and/or category
        - List up to 5 events in a clean, readable format
        - Use emojis appropriately (🎵 for concerts, 🎨 for art, 🎭 for theater, etc.)
        - Include: event name, date, and link
        - Keep each event to 1-2 lines maximum
        - End with a call to action
        - Total length must be under 280 characters per tweet
        - Use proper formatting with line breaks
        - Be enthusiastic but professional

        Format each event like this:
        [emoji] **Event Name** - Date
        [Venue] | [Price] | [Link]
        """

        user_template = """Original question: "{original_tweet}"
        {search_context}

        Events to include:
        {events_json}

        Create an engaging tweet response.
        """

        # Build search context
        search_parts = []
        if category:
            search_parts.append(f"Category: {category}")
        if city:
            search_parts.append(f"City: {city}")
        search_context = ", ".join(
            search_parts) if search_parts else "General search"

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_template), ("user", user_template)]
        )

        # Create LangChain chain
        chain = prompt | self.formatting_llm | parser

        try:
            formatted_response = await chain.ainvoke(
                {
                    "original_tweet": original_tweet,
                    "search_context": search_context,
                    "events_json": json.dumps(events, indent=2),
                }
            )

            logger.info("Successfully formatted event response")
            return formatted_response

        except Exception as e:
            logger.error(f"Error formatting response with LangChain: {e}")
            # Fallback to simple template
            return self._fallback_format(events, city, category)

    def _fallback_format(self, events: list[dict], city: str | None, category: str | None) -> str:
        """Simple template-based formatting as fallback."""
        location_text = city or "your area"
        category_text = category or "events"

        lines = [f"🎉 Top {category_text} in {location_text}!\n"]

        for i, event in enumerate(events[:5], 1):
            name = event.get("name", "Event")
            date = event.get("date", "TBA")
            lines.append(f"{i}. {name} - {date}")

        lines.append("\n💬 Reply for more recommendations!")
        return "\n".join(lines)
