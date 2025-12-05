import streamlit as st
import pandas as pd
import base64

# ---------------------------------------------------------
# CUSTOM HEADER WITH NAME
# ---------------------------------------------------------
st.markdown("""
    <div style="
        background-color:#1e3d59;
        padding:18px;
        border-radius:12px;
        text-align:center;
    ">
        <h1 style="color:white; font-family:Verdana; margin:0;">
            Sunil Kumar Talabhaktula
        </h1>
        <h3 style="color:#f5f0e1; margin-top:6px;">
            Intelligent CSV Processing Tool
        </h3>
    </div>
    <br>
""", unsafe_allow_html=True)



# ---------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------

st.title("")

uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

if uploaded_file:

    # Reset session state when a new file is uploaded
    if "last_filename" not in st.session_state or st.session_state.last_filename != uploaded_file.name:
        st.session_state.last_filename = uploaded_file.name
        st.session_state.working_df = pd.read_csv(uploaded_file)
        st.session_state.merge_active = True
        st.session_state.filter_active = True
    else:
        if "working_df" not in st.session_state:
            st.session_state.working_df = pd.read_csv(uploaded_file)

    df = st.session_state.working_df

    # Show row count at top
    st.write(f"### Total Rows in Uploaded File: **{len(df)}**")

    # Show preview
    st.write("### Preview of Uploaded File:")
    st.dataframe(df.head())

    # Sort columns
    sorted_columns = sorted(df.columns)
    st.write("### Current Columns (Sorted):")
    st.write(sorted_columns)

    # ---------------------------------------------------------
    # STEP 2: MERGING LOOP
    # ---------------------------------------------------------
    if st.session_state.merge_active:
        st.write("## 🔧 Column Merging")

        merge_cols = st.multiselect(
            "Select columns to merge into one (sorted):",
            sorted_columns,
            key="merge_cols"
        )

        new_col_name = st.text_input("Enter name for the merged column:", key="new_col_name")

        if st.button("Merge Columns"):
            if merge_cols and new_col_name.strip():
                df[new_col_name] = df[merge_cols].astype(str).agg(" ".join, axis=1)
                st.session_state.working_df = df
                st.success(f"Merged column '{new_col_name}' created!")

                # Clear the input field
                st.session_state.new_col_name = ""

                sorted_columns = sorted(df.columns)
            else:
                st.warning("Please select columns and enter a valid merged column name.")

        merge_continue = st.radio(
            "Do you want to merge more columns?",
            ("Yes", "No"),
            key="merge_continue"
        )

        if merge_continue == "No":
            st.session_state.merge_active = False

    # ---------------------------------------------------------
    # STEP 3: FILTERING LOOP
    # ---------------------------------------------------------
    if not st.session_state.merge_active and st.session_state.filter_active:
        st.write("## 🔍 Filtering Options")

        st.write("### Available Columns (Sorted):")
        st.write(sorted_columns)

        filter_col = st.selectbox(
            "Select a column to filter on:",
            sorted_columns,
            key="filter_col"
        )

        col_series = df[filter_col]

        # Build list including blanks/nulls/spaces
        unique_raw_vals = col_series.astype("object").unique().tolist()
        display_vals = []

        for v in unique_raw_vals:
            if pd.isna(v) or (isinstance(v, str) and v.strip() == ""):
                label = "(Blank / Empty)"
                if label not in display_vals:
                    display_vals.append(label)
            else:
                display_vals.append(v)

        display_vals = sorted(display_vals, key=lambda x: str(x))

        filter_vals = st.multiselect(
            f"Select values in '{filter_col}' to keep (sorted):",
            options=display_vals,
            key="filter_vals"
        )

        if st.button("Apply Filter", key="apply_filter"):
            if filter_vals:
                mask = pd.Series(False, index=df.index)

                # Blank/Empty filter
                if "(Blank / Empty)" in filter_vals:
                    mask |= col_series.isna() | col_series.astype(str).str.strip().eq("")

                non_blank_vals = [v for v in filter_vals if v != "(Blank / Empty)"]
                if non_blank_vals:
                    mask |= col_series.isin(non_blank_vals)

                df = df[mask]
                st.session_state.working_df = df

                st.success("Filter applied!")
                st.dataframe(df.head())
            else:
                st.warning("Please select at least one value to filter on.")

        filter_continue = st.radio(
            "Do you want to apply more filters?",
            ("Yes", "No"),
            key="filter_continue"
        )

        if filter_continue == "No":
            st.session_state.filter_active = False

    # ---------------------------------------------------------
    # STEP 4: SELECT COLUMNS + FINAL OUTPUT
    # ---------------------------------------------------------
    if not st.session_state.filter_active and not st.session_state.merge_active:
        st.write("## ✅ Final Output")

        df = st.session_state.working_df

        st.write("### Total Rows After Processing:")
        st.write(len(df))

        sorted_columns = sorted(df.columns)

        # Column selection UI
        st.write("### 📌 Select Columns for Final Output")

        column_choice = st.radio(
            "Choose columns for output:",
            ("All Columns", "Select Specific Columns"),
            key="column_choice"
        )

        if column_choice == "All Columns":
            final_df = df.copy()

        else:
            selected_columns = st.multiselect(
                "Select columns to include in the output (sorted):",
                options=sorted_columns,
                default=sorted_columns,
                key="selected_output_cols"
            )

            if not selected_columns:
                st.warning("Select at least one column for output.")
                final_df = df.copy()
            else:
                final_df = df[selected_columns].copy()

        # Convert to CSV
        csv_data = final_df.to_csv(index=False)

        # DOWNLOAD BUTTON
        st.download_button(
            label="⬇️ Download Output CSV",
            data=csv_data,
            file_name="processed_output.csv",
            mime="text/csv"
        )

        st.write("---")
        st.write("### Or enter a system path to save the file manually:")

        output_path = st.text_input("Enter output file path (including .csv filename):")

        if st.button("Save File to Path", key="save_to_path"):
            if output_path.strip():
                try:
                    final_df.to_csv(output_path, index=False)
                    st.success(f"CSV file successfully created at:\n**{output_path}**")
                except Exception as e:
                    st.error(f"Error saving file: {e}")
            else:
                st.warning("Please provide a valid file path.")
