import numpy as np
import pandas as pd
import streamlit as st
from toolkit.queries import (
    query_flag_missing_institution,
    query_access_requirements,
)
from toolkit.utils import get_data_from_snowflake

# Configure the layout of the Streamlit app page
st.set_page_config(
    layout="wide",
    page_title="NF Internal Dashboard",
    page_icon="🔒",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def main():
    # SIDE BAR --------------------------------------------------------------------------------#
    st.sidebar.header("Internal Dashboard Controls")
    
    # Update Mode Selection
    st.sidebar.header("Update Mode")
    update_mode = st.sidebar.radio(
        "Select Update Mode",
        options=["Dynamic Updates", "Manual Updates (Press Go)"],
        key="update_mode"
    )

    # Show the "Go" button if the user selected Manual Updates
    if update_mode == "Manual Updates (Press Go)":
        filter_applied = st.sidebar.button("🚀**Go**!", key="apply_filters")
    else:
        filter_applied = True

    if filter_applied:
        # Plot Width Slider
        plot_width = st.sidebar.slider("Plot Width", min_value=800, max_value=1800, value=1400)

        # MAIN CONTENT ----------------------------------------------------------------------#
        st.title("NF Internal Dashboard")
        st.markdown("""
        This dashboard provides internal metrics and compliance information for the NF Data Coordinating Center team.
        """)

        # Missing Institution Information -------------------------------------------------#
        st.header("Missing Institution Information")
        st.subheader("Projects with Missing or Unclear PI Information")
        
        # Get data for missing institution information
        missing_institution_df = get_data_from_snowflake(query_flag_missing_institution())
        
        if missing_institution_df.empty:
            st.success("No projects with missing or unclear PI information found.")
        else:
            # Display metrics
            col1, col2, col3 = st.columns([1, 1, 1])
            col1.metric("Total Projects with Issues", len(missing_institution_df))
            col2.metric("Missing Email", len(missing_institution_df[missing_institution_df['ISSUE_TYPE'] == 'Missing Email']))
            col3.metric("Missing/Unclear Institution", len(missing_institution_df[missing_institution_df['ISSUE_TYPE'].isin(['Missing Institution', 'Unclear Institution'])]))
            
            # Format the DataFrame for display
            display_df = missing_institution_df[['PROJECT_NAME', 'PI_EMAIL', 'PI_INSTITUTION', 'ISSUE_TYPE']].copy()
            display_df.columns = ['Project Name', 'PI Email', 'Institution', 'Issue Type']
            
            # Add styling to highlight different issue types
            def highlight_issues(row):
                if row['Issue Type'] == 'Missing Email':
                    return ['background-color: #941E24'] * len(row)
                elif row['Issue Type'] == 'Missing Institution':
                    return ['background-color: #bc590b'] * len(row)
                elif row['Issue Type'] == 'Unclear Institution':
                    return ['background-color: #af316c'] * len(row)
                return [''] * len(row)
            
            # Display the styled table
            st.dataframe(
                display_df.style.apply(highlight_issues, axis=1),
                use_container_width=True,
                height=400
            )
            
            # Add download button for the data
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Missing Institution Data",
                csv,
                "missing_institution_data.csv",
                "text/csv",
                key='download-missing-institution'
            )

        # Access Requirements -----------------------------------------------------#
        st.header("Access Requirements")
        st.subheader("Project Access Requirements and Conditions")
        
        # Get access requirements data
        access_req_df = get_data_from_snowflake(query_access_requirements())
        
        if access_req_df.empty:
            st.warning("No access requirements data available.")
        else:
            # Format boolean columns to be more readable
            bool_columns = [
                'IS_DUC_REQUIRED', 'IS_IRB_APPROVAL_REQUIRED', 'IS_IDU_REQUIRED',
                'IS_CERTIFIED_USER_REQUIRED', 'IS_VALIDATED_PROFILE_REQUIRED', 'IS_TWO_FA_REQUIRED'
            ]
            
            # Replace nulls with "null" string and format booleans
            for col in bool_columns:
                access_req_df[col] = access_req_df[col].fillna("null")
                access_req_df[col] = access_req_df[col].apply(lambda x: str(x).upper())
            
            # Rename columns for display
            display_cols = {
                'ENTITY_ID': 'Project ID',
                'ENTITY_NAME': 'Project Name',
                'AR_ID': 'AR ID',
                'AR_NAME': 'AR Name',
                'IS_DUC_REQUIRED': 'DUC Required',
                'IS_IRB_APPROVAL_REQUIRED': 'IRB Required',
                'IS_IDU_REQUIRED': 'IDU Required',
                'IS_CERTIFIED_USER_REQUIRED': 'Certified User',
                'IS_VALIDATED_PROFILE_REQUIRED': 'Validated Profile',
                'IS_TWO_FA_REQUIRED': '2FA Required'
            }
            
            display_df = access_req_df.rename(columns=display_cols)
            
            # Style the dataframe
            def highlight_requirements(val):
                if val == 'TRUE':
                    return 'background-color: #59A159; color: white'
                elif val == 'FALSE':
                    return 'background-color: #941E24; color: white'
                else:
                    return 'background-color: #636E83; color: white'
            
            # Apply styling to boolean columns
            styled_df = display_df.style.applymap(
                highlight_requirements,
                subset=[display_cols[col] for col in bool_columns]
            )
            
            # Display summary metrics
            st.subheader("Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                duc_count = len(access_req_df[access_req_df['IS_DUC_REQUIRED'] == 'TRUE'])
                st.metric("Projects Requiring DUC", duc_count)
            
            with col2:
                irb_count = len(access_req_df[access_req_df['IS_IRB_APPROVAL_REQUIRED'] == 'TRUE'])
                st.metric("Projects Requiring IRB", irb_count)
            
            with col3:
                idu_count = len(access_req_df[access_req_df['IS_IDU_REQUIRED'] == 'TRUE'])
                st.metric("Projects Requiring IDU", idu_count)
            
            with col4:
                certified_count = len(access_req_df[access_req_df['IS_CERTIFIED_USER_REQUIRED'] == 'TRUE'])
                st.metric("Projects Requiring Certification", certified_count)
            
            # Display the table
            st.dataframe(
                styled_df,
                use_container_width=True,
                height=600
            )
            
            # Add download button
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Access Requirements Data",
                csv,
                "access_requirements.csv",
                "text/csv",
                key='download-access-requirements'
            )

if __name__ == "__main__":
    main() 