import streamlit as st

from graph import app as code_mind_graph


st.set_page_config(
    page_title="CodeMind AI",
    page_icon="🤖",
    layout="wide",
)


st.title("CodeMind AI")
st.write("Multi-Agent AI system for planning, coding, testing, and reviewing software.")


requirement = st.text_area(
    "Enter your software requirement",
    placeholder="Example: Create a Python calculator application.",
    height=150,
)


if st.button("Build Project", type="primary"):

    if not requirement.strip():
        st.warning("Please enter a requirement.")
        st.stop()

    with st.spinner("CodeMind AI is working..."):

        try:
            result = code_mind_graph.invoke(
                {
                    "requirement": requirement,
                    "manager_plan": "",
                    "research_plan": "",
                    "generated_code": "",
                    "test_result": "",
                    "review_result": "",
                    "retry_count": 0,
                }
            )

            st.success("Project workflow completed!")

            st.subheader("Manager Plan")
            st.write(result["manager_plan"])

            st.subheader("Research Plan")
            st.write(result["research_plan"])

            st.subheader("Generated Code")
            st.code(result["generated_code"], language="python")

            st.subheader("Test Result")
            st.text(result["test_result"])

            st.subheader("Retry Count")
            st.write(result["retry_count"])

            st.subheader("Review Result")
            st.text(result["review_result"])

        except Exception as e:
            st.error("CodeMind AI encountered an error.")
            st.exception(e)