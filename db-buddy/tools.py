# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import os
from google.adk.tools import FunctionTool
from vertexai import rag

def _rag_response_func(query: str, db_technology: str) -> str:
    """Retrieves contextually relevant information from a RAG corpus for a specific database technology.

    Args:
        query (str): The query string to search within the corpus.
        db_technology (str): The database technology (e.g., 'postgres').

    Returns:
        str: The response containing retrieved information from the corpus, or an error message if the technology is not supported.
    """
    corpus_name = None
    if db_technology.lower() == 'postgres':
        corpus_name = os.getenv("GOOGLE_CLOUD_RAG_ENGINE_CORPUS_NAME")
    else:
        return f"No RAG corpus available for database technology: {db_technology}"

    if not corpus_name:
        return "RAG corpus name not configured for the specified database technology."

    rag_retrieval_config = rag.RagRetrievalConfig(
        top_k=3,  # Optional
        filter=rag.Filter(vector_distance_threshold=0.5),  # Optional
    )
    response = rag.retrieval_query(
        rag_resources=[
            rag.RagResource(
                rag_corpus=corpus_name,
            )
        ],
        text=query,
        rag_retrieval_config=rag_retrieval_config,
    )
    return str(response)

rag_response = FunctionTool(_rag_response_func)