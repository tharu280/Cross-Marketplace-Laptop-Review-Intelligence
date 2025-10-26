import time
import numpy as np
import google.generativeai as genai
from . import utils
from .models import RetrievedChunk, ChatMessage
from typing import List, Optional


def get_rag_response(query: str, history: Optional[List[ChatMessage]] = None, k: int = 10):
    """
    Performs the full RAG pipeline using pre-loaded artifacts.
    Returns a dictionary containing the LLM answer and retrieved context.
    """
    start_time = time.time()
    print(f"\nRAG Handler: Processing Query: '{query}' ")
    if history:
        print(f"  > Received {len(history)} messages in history.")

    if not utils.artifacts_loaded or not all([
        utils.embedding_model_instance,
        utils.faiss_index_instance,
        utils.metadata_store_instance,
        utils.llm_model_instance
    ]):
        print("Error: RAG components not loaded.")

        return {"llm_answer": "Error: System components not loaded.", "retrieved_context": []}

    print("Step 1: Retrieving static specs...")
    start_retrieve_static = time.time()
    try:

        query_vector = utils.embedding_model_instance.encode(
            [query]).astype('float32')
        distances, indices = utils.faiss_index_instance.search(query_vector, k)

        retrieved_chunks = [RetrievedChunk(
            **utils.metadata_store_instance[i]) for i in indices[0]]
    except Exception as e:
        print(f"  Error during FAISS search: {e}")
        return {"llm_answer": f"Error during search: {e}", "retrieved_context": []}
    end_retrieve_static = time.time()
    print(
        f"  > Done ({len(retrieved_chunks)} chunks) in {end_retrieve_static - start_retrieve_static:.3f} seconds.")

    print("Step 1b: Retrieving dynamic data...")
    start_retrieve_dynamic = time.time()

    mentioned_skus = sorted(
        list(set(chunk.sku for chunk in retrieved_chunks if chunk.sku)))
    print(f"  Identified SKUs: {mentioned_skus}")

    dynamic_context_dict = {}
    if mentioned_skus:
        for sku in mentioned_skus:

            dynamic_context_dict[sku] = utils.get_dynamic_data_for_sku(sku)
    else:
        print("  > No specific SKUs identified in static context.")
    end_retrieve_dynamic = time.time()
    print(
        f"  > Done in {end_retrieve_dynamic - start_retrieve_dynamic:.3f} seconds.")

    print("Step 2: Augmenting context...")

    static_context_string = "\n STATIC SPECIFICATIONS CONTEXT \n"
    if not retrieved_chunks:
        static_context_string += "No relevant specifications found.\n"
    else:
        for i, chunk in enumerate(retrieved_chunks):

            static_context_string += f"Context {i+1} (Source: {chunk.sku}, Section: {chunk.section_title}):\n"
            static_context_string += f"  Content: {chunk.text}\n"
            if chunk.citations:
                static_context_string += f"  Citations: {chunk.citations}\n\n"
            else:
                static_context_string += "\n"

    dynamic_context_string = "\n--- CURRENT DYNAMIC DATA ---\n"
    if not dynamic_context_dict:
        dynamic_context_string += "No dynamic data retrieved.\n"
    else:
        for sku, data in dynamic_context_dict.items():
            dynamic_context_string += f"For '{sku}':\n"
            dynamic_context_string += f"  - Latest Price: {data.get('latest_price', 'N/A')}\n"
            dynamic_context_string += f"  - Availability: {data.get('availability', 'N/A')}\n"
            dynamic_context_string += f"  - Average Rating: {data.get('avg_rating', 'N/A')}\n\n"

    combined_retrieved_context = static_context_string + dynamic_context_string

    formatted_history = []
    if history:

        for msg in history[-5:]:
            formatted_history.append(
                {"role": msg.role, "parts": [{"text": msg.content}]})

    system_instruction = (
        "You are an expert Q&A assistant and recommender for laptop specifications. "
        "Base your answers *only* on the provided context (static specs, dynamic data) and conversation history. "
        "Do not use outside knowledge. "
        "Prioritize dynamic data (price, availability, rating) if relevant to the query. "
        "When using static specs, cite the 'Citations' number (e.g., [cite: 123]). "
        "When using dynamic data, state it clearly (e.g., 'The current price is...')."
    )

    gemini_messages = []

    gemini_messages.extend(formatted_history)

    gemini_messages.append({
        "role": "user",
        "parts": [{
            "text": f"""SYSTEM INSTRUCTIONS: {system_instruction}

                CONTEXT FOR YOUR RESPONSE:
                {combined_retrieved_context}
                --- END CONTEXT ---

                Based *only* on the CONTEXT provided AND the conversation history (if any), answer this question: {query}"""
        }]
    })

    print("Step 3: Generating answer using Google Gemini...")
    llm_answer = "Error: LLM generation failed."
    start_generate = time.time()
    try:
        generation_config = genai.types.GenerationConfig(
            temperature=0.5,
            max_output_tokens=2048,
        )

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = utils.llm_model_instance.generate_content(
            gemini_messages,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        if not response.parts and hasattr(response, 'prompt_feedback') and response.prompt_feedback.block_reason:
            reason = response.prompt_feedback.block_reason
            llm_answer = f"Error: Content generation blocked by safety filters. Reason: {reason}"
            print(f"  > Generation Blocked: {reason}")
        elif not response.parts:
            llm_answer = "Error: LLM response was empty or blocked for an unknown reason."
            print("  > Generation Error: Empty or unknown block.")
        else:

            llm_answer = response.text.strip()
            end_generate = time.time()
            print(f"  > Done in {end_generate - start_generate:.3f} seconds.")

    except Exception as e:
        end_generate = time.time()
        print(
            f"  > Generation failed after {end_generate - start_generate:.3f} seconds.")
        print(f"  Error during Google Gemini API call: {e}")
        llm_answer = f"Error during LLM call: {e}"

    total_time = time.time() - start_time
    print(f"--- RAG Handler: Query processed in {total_time:.3f} seconds ---")

    return {"llm_answer": llm_answer, "retrieved_context": retrieved_chunks}
