import streamlit as st
import os

from agents.supervisor import run

st.set_page_config(
    page_title="SmartRMC-AI",
    layout="centered"
)

st.title("📄 SmartRMC-AI")

uploaded_files = st.file_uploader(
    "Upload PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if st.button("Generate Excel"):

    if not uploaded_files:

        st.warning(
            "Please upload at least one PDF."
        )

    else:

        os.makedirs(
            "uploads",
            exist_ok=True
        )

        file_paths = []

        for uploaded_file in uploaded_files:

            save_path = os.path.join(
                "uploads",
                uploaded_file.name
            )

            with open(
                save_path,
                "wb"
            ) as f:

                f.write(
                    uploaded_file.getbuffer()
                )

            file_paths.append(
                save_path
            )

        with st.spinner(
            "Running SmartRMC-AI..."
        ):

            try:

                excel_path = run(
                    file_paths
                )

                st.success(
                    "Excel Generated Successfully!"
                )

                with open(
                    excel_path,
                    "rb"
                ) as file:

                    st.download_button(
                        label="Download Excel",
                        data=file,
                        file_name="final_output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:

                st.error(
                    "Pipeline failed"
                )

                st.write(e)