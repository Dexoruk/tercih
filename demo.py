import requests
from bs4 import BeautifulSoup
import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Function to convert Turkish string to a URL-friendly format
def refactor_turkish_string(string):
    replacements = {
        'Ç': 'c', 'ç': 'c',
        'Ğ': 'g', 'ğ': 'g',
        'I': 'i', 'ı': 'i',
        'İ': 'i', 'i̇': 'i',
        'Ö': 'o', 'ö': 'o',
        'Ş': 's', 'ş': 's',
        'Ü': 'u', 'ü': 'u',
        ' ': '-',
        'é': 'e'
    }
    # Convert to lowercase and replace Turkish characters
    string = string.lower()
    for search, replace in replacements.items():
        string = string.replace(search, replace)
    return string

# Main Streamlit app
st.title("University Başarı Sırası")

# Input for department name
department_input = st.text_input("Bölüm Seçin", "Bilgisayar Mühendisliği")

# Convert the input to URL-friendly format
department_url_part = refactor_turkish_string(department_input)

# Generate the URL for the selected department
url = f"https://www.universitego.com/{department_url_part}-2024-taban-puanlari-ve-basari-siralamalari/"

# Step 1: Fetch the website content with the generated URL
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Step 2: Parse the data for the first 50 rows of the table
table = soup.find('table')
if table:
    rows = table.find_all('tr')

    data = []
    for row in rows[1:51]:  # Limiting to the first 50 rows, skipping the header row
        cols = row.find_all('td')
        university_name = cols[0].text.strip()
        basari_sirasi = cols[-1].text.strip()  # Assuming the last column contains the Başarı Sırası
        data.append([university_name, basari_sirasi])

    # Convert the data to a DataFrame
    df = pd.DataFrame(data, columns=['University', 'Başarı Sırası'])

    # Split the 'Başarı Sırası' column into separate columns for each year
    df[['2023', '2022', '2021', '2020']] = df['Başarı Sırası'].str.split('\n', expand=True)

    # Replace dots in numbers and convert to numeric values
    for year in ['2023', '2022', '2021', '2020']:
        df[year] = df[year].str.replace('.', '', regex=False)  # Remove thousand separator dots
        df[year] = pd.to_numeric(df[year], errors='coerce')  # Convert to numeric

    # Drop any rows where all values are NaN
    df.dropna(how='all', subset=['2023', '2022', '2021', '2020'], inplace=True)

    # Filter universities with "Devlet" in their names, regardless of format or case
    devlet_universities = df[df['University'].str.contains("Devlet", case=False, na=False)].head(10)

    # Calculate the average Başarı Sırası for the filtered Devlet universities
    average_sirasi = devlet_universities[['2023', '2022', '2021', '2020']].mean()

    # Reverse the order of years (since Year_1 is the newest)
    years = ['2020', '2021', '2022', '2023']

    # Dropdown for university selection
    university_choice = st.selectbox("Üniversite Seçin", df['University'])

    # Filter the selected university data
    selected_university = df[df['University'] == university_choice].iloc[0]

    # Filter out NaN values from the selected university's data
    selected_university_data = selected_university[years].dropna().values

    # Corresponding average data
    average_sirasi_data = average_sirasi[years].values

    # Plotting the data with Plotly
    fig = go.Figure()

    # Add the university's data line
    fig.add_trace(go.Scatter(
        x=years,
        y=selected_university_data,
        mode='lines+markers',
        name=selected_university['University'],
        text=[f"{year}: {val}" for year, val in zip(years, selected_university_data)],
        hoverinfo='text'
    ))

    # Add the Devlet average line
    fig.add_trace(go.Scatter(
        x=years,
        y=average_sirasi_data,
        mode='lines+markers',
        name='Top 10 Devlet Üniversiteleri Ortalama Sıralaması',
        line=dict(dash='dash', color='red'),
        text=[f"{year}: {val}" for year, val in zip(years, average_sirasi_data)],
        hoverinfo='text'
    ))

    # Update layout for larger and more readable graph
    fig.update_layout(
        title={
            'text': f"Başarı Sırası for {selected_university['University']} (Son 4 Yıl)",
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Yıl",
        yaxis_title="Başarı Sırası",
        hovermode="x unified",
        legend=dict(
            x=1,
            y=1,
            xanchor='right',
            yanchor='top',
            font=dict(size=12),  # Make legend font smaller
            bgcolor="rgba(255, 255, 255, 0.7)"  # Add slight background to make it stand out
        ),
        font=dict(size=18),  # Adjust overall font size
        width=1200,  # Increase figure width to take up more space on the page
        height=800   # Increase figure height to be larger on the page
    )

    # Show plot in Streamlit
    st.plotly_chart(fig)
else:
    st.error("The specified department could not be found. Please check the name and try again.")
