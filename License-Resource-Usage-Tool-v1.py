import streamlit as st
import pandas as pd
import io
import re

def parse_license_data(uploaded_file):
    """Parses the uploaded text file and extracts license resource usage data."""

    # Read and decode the file content
    full_content = uploaded_file.read().decode('utf-8')

    # Define a simplified pattern to directly capture the 3 lines of data
    pattern = r'<([^>]+)>\s*display license resource usage.*\|\s*inc\s+LCR9S9KNBSL0Q\|LCR9S9KNEVN0P\|LCR9S9KNL3V0P\s*(?:[\s\S]*?-{5,}\s*)FeatureName\s+ConfigureItemName\s+ResourceUsage\s*(?:-{5,}\s*)(\S+\s+\S+\s+\S+)\s*(\S+\s+\S+\s+\S+)\s*(\S+\s+\S+\s+\S+)' 

    # Find all matches of the pattern in the file content
    matches = re.findall(pattern, full_content, re.MULTILINE)

    # Initialize an empty list to store the extracted data
    data = []

    # Iterate through the matches and extract the required information
    for site, line1, line2, line3 in matches:
        for line in [line1, line2, line3]:
            parts = line.split()
            # Append the extracted information to the data list
            data.append({
                'Site': site,
                'FeatureName': parts[0],
                'ConfigureItemName': parts[1],
                'ResourceUsage': parts[2]
            })

    # Create a DataFrame from the extracted data
    df = pd.DataFrame(data)

    # Split the `ResourceUsage` column into `Used` and `Total`
    df[['Used', 'Total']] = df['ResourceUsage'].str.split('/', expand=True)

    # Convert `Used` and `Total` to numeric
    df['Used'] = pd.to_numeric(df['Used'], errors='coerce')
    df['Total'] = pd.to_numeric(df['Total'], errors='coerce')

    return df

def main():
    """Main function to create the Streamlit app."""

    st.title("License Resource Usage Extractor")

    uploaded_file = st.file_uploader("Choose a text file", type="txt")

    if uploaded_file is not None:
        df = parse_license_data(uploaded_file)

        # Display the DataFrame
        st.dataframe(df)

        # Download the DataFrame as an Excel file
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='License Resource Usage Data')
            return output.getvalue()

        st.download_button(
            label="Download Excel",
            data=to_excel(df),
            file_name="License Resource Usage.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Group the DataFrame by `Site` and count the number of unique values for `ConfigureItemName` and `ResourceUsage`
        counts_per_site = df.groupby('Site')[['ConfigureItemName', 'ResourceUsage']].nunique()

        # Check if all sites have 3 unique ConfigureItemNames and at least 1 unique ResourceUsage
        if (counts_per_site['ConfigureItemName'] == 3).all() and (counts_per_site['ResourceUsage'] >= 1).all():
            st.write("All sites have 3 unique ConfigureItemNames and varying ResourceUsages.")
        else:
            # Identify sites that don't have 3 unique ConfigureItemNames or at least 1 unique ResourceUsage
            sites_not_compliant = counts_per_site[
                (counts_per_site['ConfigureItemName'] != 3) | (counts_per_site['ResourceUsage'] < 1)
            ].index.tolist()
            st.write("Sites that do not meet the criteria:", sites_not_compliant)

if __name__ == "__main__":
    main()