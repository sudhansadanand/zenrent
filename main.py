import streamlit as st
import folium
from streamlit_folium import st_folium, folium_static
import json
#import geocoder
#from openai import OpenAI
import pandas as pd
import os
import time
import sys

# Load data from the JSON file

@st.cache
def load_json_data(file_path):
    with open(file_path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data

@st.cache
def get_localities(listings):
    localities = []

    for listing in listings:
        localities.append(listing["locality"])

    uniq_localities = list(set(localities))
    localities = sorted(uniq_localities)
    return localities

# Define a function to format a cell as a hyperlink
@st.cache
def make_hyperlink(url):
    return f'<a href="{url}" target="_blank">Link</a>'

# Main Streamlit app
def main():
    st.title("Chennai Rental Listings from Magic Bricks")

    # Load JSON data and extract coordinates
    json_data = load_json_data('clean_data.json')
    st.write(str(len(json_data))+" total listings.")
    localities = ["All"]
    localities.extend(get_localities(json_data))
    #localities.append("All")
    default_option = "All"

    df = pd.DataFrame(json_data)

    df['rent'] = df['rent'].astype(int)

    lowest_rent = df['rent'].min()
    highest_rent = df['rent'].max()

    rent_options = ["Less than 20K", "20K - 40K", "40K - 60K", "Above 60K", "Any"]
    rent_option = st.radio("Select your Rent Range", rent_options)

    num_beds = st.slider("Bedrooms", min_value=1, max_value=5, step=1)
    locality = st.selectbox("Locality:", localities, localities.index(default_option))
    # Filter the DataFrame based on the selected minimum value
    df['bedroom'].fillna(0, inplace=True)
    #df['address']['addressLocality'].fillna("na", inplace=True)
    try:
        df['bedroom'] = df['bedroom'].astype(int)
    except ValueError as error:
        print(error)
    #st.table(df)

    bed_data = df[df["bedroom"] == num_beds]
    if rent_option == "Less than 20K":
        filtered_data = bed_data[bed_data["rent"] < 20000]
    elif rent_option == "20K - 40K":
        mask = (bed_data["rent"] >= 20000) & (df["rent"] <= 40000)
        filtered_data = bed_data[mask]
    elif rent_option == "40K - 60K":
        mask = (bed_data["rent"] >= 40000) & (df["rent"] <= 60000)
        filtered_data = bed_data[mask]
    elif rent_option == "Above 60K":
        filtered_data = bed_data[bed_data["rent"] > 60000]
    else:
        filtered_data = bed_data

    #st.write(locality)
    if locality != "All":
        map_data = filtered_data[filtered_data["locality"] == locality]
    else:
        map_data = filtered_data
    # Filter data based on the query result
    #filtered_data = [entry for entry in json_data if query_result in entry['description']]

    # Display filtered data
    if locality != "All":
        cols_to_display = ['Availability','Floor','bedroom','bathroom','rent','Tenant_Preference','Carpet_Area','Balcony','Car_Parking','url']
    else:
        cols_to_display = ['locality', 'Availability', 'Floor', 'bedroom', 'bathroom', 'rent', 'Tenant_Preference', 'Carpet_Area',
                           'Balcony', 'Car_Parking', 'url']

    filtered_cols = map_data[cols_to_display]


    if not filtered_cols.empty:
        disp_data = pd.DataFrame(filtered_cols)
        st.write("Found "+str(len(filtered_cols))+" Matching Listings")


        vis_data = json.loads(map_data.to_json(orient='records'))

        # Create a map centered at a specific location
        time.sleep(3)
        m = folium.Map(location=[vis_data[0]['latitude'], vis_data[0]['longitude']], zoom_start=12)

        # Add markers for each coordinate
        for entry in vis_data:
            popup_str = "{" + str(entry['bedroom']) + " BHK, Rs " + str(entry['rent']) + "}"
            # popup=f"({entry['geo']['latitude']}, {entry['geo']['longitude']})"
            folium.Marker(
                location=[entry['latitude'], entry['longitude']],

                popup='<a href="'+str(entry['url'])+'" target="_blank">Link</a>'
            ).add_to(m)

        # Display the map in the Streamlit app
        folium_static(m)
        disp_data['url'] = disp_data['url'].apply(make_hyperlink)

        disp_data = disp_data.fillna("N/A")
        st.markdown(disp_data.to_html(escape=False, index=False, render_links=True), unsafe_allow_html = True)
        #st.table(disp_data.to_html(escape=False, render_links=True), unsafe_allow_html = True)
    else:
        st.write("No Matching Listings found")

    """

    """
if __name__ == "__main__":
    main()
