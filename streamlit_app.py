# streamlit_app.py

import os
import streamlit as st
from openai import OpenAI
import dotenv
# Optional: for better markdown rendering
# import markdown2

headers = {
    "authorization": st.secrets["OPENAI_API_KEY"]
}

# Create the OpenAI client
client = OpenAI(api_key=api_key)

# Paste the vector store ID
vector_store_id = "vs_686c824aa2c8819184dae0f92444d54d"

# And Storage ID's of the files looking at
plan_to_file_id = {
    "APWU CDHP": "file-KT4xRXKvzhQ2pMp6GzzLvZ",
    "APWU High": "file-1ppMvRTLnsRHD6cSKGx1yH",
    "BCBS FEP Blue Basic": "file-9xqhVbboesRzfNb8iXmjzX",
    "BCBS Focus": "file-Hjv7oSeWsFnUG7EJMBqbNd",
    "BCBS Standard": "file-RnZTLYqjRY98RyapZkDquq",
    "Compass Rose High": "file-VyHKX442xrdNjJpHDh9o5L",
    "Compass Rose Standard": "file-Lub9VPe5e5ETEzAJ3xR4mH",
    "GEHA High": "file-2yKwW8KjWGpp3VLivFtZ33",
    "GEHA Standard": "file-BeiAYGLKC4nywUZqfbCg5m",
    "GEHA HDHP": "file-DxcYeRchQXpoz27A67FKSG",
    "GEHA Indemnity Elevate Plus": "file-QuvX42N15J9eLLXZe8LTRT",
    "GEHA Indemnity Elevate": "file-CLYVQGMJSUphBmAMQwQf5q",
    "MHBP Consumer Option HDHP": "file-JiN51Gcn1JmhE1S5jV3g7d",
    "MHBP Standard Option": "file-8Dwe7RsXMAtkzXsPCT8SGu",
    "MHBP Value Plan": "file-SZGznWjKu3z8TCCiQhGzSy",
    "NALC Health Benefit Plan CDHP": "file-D4oZmdTDY78jakqBnvfuo9",
    "NALC Health Benefit Plan High": "file-EcEFVqsqhVD2xaXTN1nbgn",
    "SAMBA Health Benefit Plan High": "file-8D1AVeuVrARUw6HEtoJNdE",
    "SAMBA Health Benefit Plan Standard": "file-8A5KYTkKcVEPFniddbpT6g",

}

# Build the streamlit UI
st.markdown(
    "<h1 style='text-align: center;'>🩺 Federal Health Benefits Assistant</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "Ask a question and select which health plans to compare.  \n \n"
    "*This is only for demonstration purposes. For full decisions consult your plan's documentation.*"
)

query = st.text_input("📝 What would you like to know?")
selected_plans = st.multiselect("📂 Select health plans to search:", list(plan_to_file_id.keys()))

if st.button("🔍 Submit") and query and selected_plans:
    with st.spinner("Your question is being queried. Thank you for your patience."):

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        st.session_state.chat_history.append({"user": query})

        selected_file_ids = [
            plan_to_file_id[plan] for plan in selected_plans if plan in plan_to_file_id
        ]

        search_response = client.responses.create(
            model="gpt-4.1-mini",
            input=query,
            instructions="Use only the selected documents to find your answer, then summarize the outputs.",
            tools=[{
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
                "max_num_results": 25
            }],
            include=["file_search_call.results"]
        )

        retrieved_texts = [
            r for r in search_response.output[0].results
            if r.file_id in selected_file_ids
        ]

        combined_context = "\n\n".join(
            [f"[{r.file_id}] {r.text.strip()}" for r in retrieved_texts if r.text.strip()]
        )
        summary_prompt = f"""You are a federal health benefits assistant.

        Only use the context below to answer the user’s question. If a section comes from a plan not in this list, ignore it.

        Plans to compare: {', '.join(selected_plans)}

        User question: "{query}"

        Instructions:
        - Answer clearly in 2–4 sentences.
        - Compare plans using bullet points or a markdown table.
        - If nothing relevant is found for a plan, say "Not mentioned".
        - Use only document text. Do not guess or hallucinate.

        CONTEXT:
        {combined_context}
        """

        chat_response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are a clear, structured benefits analyst."},
                {"role": "user", "content": summary_prompt}
            ]
        )

        answer = chat_response.choices[0].message.content.strip()

        # Show Summary and Comparison
        st.subheader("Summary / Results")
        st.markdown(answer)

        with st.expander("🔎 Retrieved Document Snippets (Debug)"):
            for r in retrieved_texts:
                st.markdown(f"**File ID:** {r.file_id}\n\n```{r.text.strip()}```")


