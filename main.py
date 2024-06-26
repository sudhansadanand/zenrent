import streamlit as st
import folium
from streamlit_folium import st_folium, folium_static
import json
# import geocoder
# from openai import OpenAI
import pandas as pd
import os
import time
import sys
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO

# Load data from the JSON file

@st.cache_data
def load_json_data(file_path):
    with open(file_path, 'r') as json_file:
        json_data = json.load(json_file)
    return json_data


@st.cache_data
def get_localities(listings):
    localities = []

    for listing in listings:
        localities.append(listing["locality"])

    uniq_localities = list(set(localities))
    localities = sorted(uniq_localities)
    return localities


# Define a function to format a cell as a hyperlink
@st.cache_data
def make_hyperlink(url):
    return f'<a href="{url}" target="_blank">Link</a>'


# Main Streamlit app
def main():
    # Configure the page layout
    st.set_page_config(
        page_title="Chennai Rental Listings from Magic Bricks",
        page_icon=":rocket:",
        layout="wide",  # You can use "wide" or "centered" for the layout
        initial_sidebar_state="expanded",  # "auto" or "expanded" or "collapsed"
    )

    # st.title("Chennai Rental Listings from Magic Bricks")
    tab_search, tab_insights = st.tabs(['Search', 'Insights'])

    with tab_insights:
        json_data = load_json_data('mb_stats.json')
        df = pd.DataFrame(json_data["pincode_stats"])
        date = json_data["date"]
        date_obj = datetime.strptime(date, "%d-%m-%Y")
        formatted_date = date_obj.strftime("%B %d, %Y")
        summary = json_data["total_stats"]
        listings_count = summary["total_count"]
        st.text("Total Listings as of {} is: {}".format(formatted_date,listings_count))
        #plt.figure(figsize=(6, 6))

        #Show number of units available
        # Define the categories and their corresponding values
        categories = ['1 Bed', '2 Bed', '3 Bed', "4+ Bed"]
        values = [summary["1"]["count"],summary["2"]["count"],summary["3"]["count"],summary["4+"]["count"]]  # Sample values for each category

        #width = st.sidebar.slider("plot width", 0.1, 25., 3.)
        #height = st.sidebar.slider("plot height", 0.1, 25., 1.)

        # Create a pie chart using Matplotlib
        fig, ax = plt.subplots(figsize=(5.46, 5.46))
        wedges, texts, autotexts = ax.pie(values, labels=categories, autopct='%1.1f%%', startangle=90, textprops=dict(color="w"))

        # Add absolute values to the pie chart
        for i, (text, autotext) in enumerate(zip(texts, autotexts)):
            autotext.set_text(f"{categories[i]} \n {values[i]} \n ({autotext.get_text()})")


        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle

        #bar_data = pd.DataFrame([values], columns=categories)
        # Create a bar graph
        #st.pyplot(fig)
        buf = BytesIO()
        fig.savefig(buf, format="png")
        st.image(buf)

        nbed = st.slider("Bedrooms", 1, 4, 1)
        nbed_stats = {}
        for pc,values in json_data["pincode_stats"].items():
            for bedtype,stats in values.items():
                if bedtype == str(nbed):
                    nbed_stat = {}
                    nbed_stat.update(stats)
                    nbed_stats[pc] = nbed_stat
                else:
                    if bedtype == "4+" and str(nbed) == "4":
                        nbed_stat = {}
                        nbed_stat.update(stats)
                        nbed_stats[pc] = nbed_stat

        #st.text(json.dumps(nbed_stats,indent=4))
        # Add labels and title
        """st.xlabel('Bedrooms')
        st.ylabel('Number of Listings')
        st.title('Number of listings')"""

        # Show the plot
        #plt.show()
        df = pd.DataFrame(nbed_stats).T  # Transpose the DataFrame to have records as rows

        df_sorted = df.sort_values(by='avg', ascending=False)
        df_display = df_sorted.drop(columns=['count'])
        # Display the DataFrame
        #st.dataframe(df)
        st.bar_chart(df_display["avg"])

        #Histogram
        fig, ax = plt.subplots(figsize=(5.46,5.46))
        averages = df['avg']
        n, bins, patches = ax.hist(averages, bins=10, color='skyblue', edgecolor='black')
        ax.set_xlabel('Average')
        ax.set_ylabel('Frequency')
        ax.set_title('Histogram of Average Values')

        # Add count values on top of each bar
        for i, count in enumerate(n):
            ax.text(bins[i] + 0.5 * (bins[i + 1] - bins[i]), count, str(int(count)), ha='center', va='bottom')

        # Display the plot using Streamlit
        buf = BytesIO()
        fig.savefig(buf, format="png")
        st.image(buf)

        #st.pyplot(fig)

        st.dataframe(df_display)

        fig, ax = plt.subplots()
        ax.scatter(df['min'], df['max'], color='skyblue', edgecolor='black')
        ax.set_xlabel('Min')
        ax.set_ylabel('Max')
        ax.set_title('Scatter Plot of Min vs Max')

        # Display the plot using Streamlit
        st.pyplot(fig)

    with tab_search:
        with st.expander("Filter Listings", expanded=True):
            st.header("Search Listings")

            # Search contents

            # Load JSON data and extract coordinates
            json_data = load_json_data('final_mb_data.json')
            # st.write(str(len(json_data))+" total listings.")
            localities = ["All"]
            localities.extend(get_localities(json_data))
            # localities.append("All")
            default_option = "All"

            df = pd.DataFrame(json_data)
            df = df[df["listing_status"] == "valid"]
            df['id'] = df.reset_index().index + 1
            df['rent'] = df['rent'].astype(int)

            lowest_rent = df['rent'].min()
            highest_rent = df['rent'].max()

            col1, col2, col3 = st.columns(3)

            with col1:
                pass
            with col2:
                rent_options = ["Any", "Less than 20K", "20K - 40K", "40K - 60K", "Above 60K"]
                rent_option = st.selectbox("Rent Range", rent_options, rent_options.index("Any"))
                bed_options = ["Any", "1", "2", "3", "4", "5+"]
                num_beds = st.selectbox("Bedrooms", bed_options, bed_options.index("1"))
                locality = st.selectbox("Locality:", localities, localities.index(default_option))
                submit_button = st.button("Submit")
            with col3:
                pass
        if submit_button:
            # Filter the DataFrame based on the selected minimum value
            df['bedroom'].fillna(0, inplace=True)
            # df['address']['addressLocality'].fillna("na", inplace=True)
            try:
                df['bedroom'] = df['bedroom'].astype(int)
            except ValueError as error:
                print(error)
            # st.table(df)

            if num_beds != "Any":
                if num_beds != "5+":
                    bed_data = df[df["bedroom"] == int(num_beds)]
                else:
                    bed_data = df[df["bedroom"] > 4]
            else:
                bed_data = df
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

            # st.write(locality)
            if locality != "All":
                map_data = filtered_data[filtered_data["locality"] == locality]
            else:
                map_data = filtered_data
            # Filter data based on the query result
            # filtered_data = [entry for entry in json_data if query_result in entry['description']]

            # Display filtered data
            if locality != "All":
                cols_to_display = ['id','url','prop_type','society_name','summary_Availability','summary_Super_Area','summary_Furnishing','summary_Floor','summary_facing','bedroom','bathroom','balcony','rent','cost_monthly_maintenance','cost_security_deposit','cost_brokerage','summary_Tenant_Preferred','summary_Car_Parking']
            else:
                cols_to_display = ['id','url','locality','society_name', 'prop_type','summary_Availability','summary_Super_Area','summary_Furnishing','summary_Floor','summary_facing','bedroom','bathroom','balcony', 'rent','cost_monthly_maintenance','cost_security_deposit','cost_brokerage','summary_Tenant_Preferred','summary_Car_Parking']

            filtered_cols = map_data[cols_to_display]

            if not filtered_cols.empty:
                disp_data = pd.DataFrame(filtered_cols)
                st.write("Found " + str(len(filtered_cols)) + " Matching Listings")

                vis_data = json.loads(map_data.to_json(orient='records'))

                # Create a map centered at a specific location
                time.sleep(3)
                with st.container():
                    m = folium.Map(location=[vis_data[0]['geo_latitude'], vis_data[0]['geo_longitude']], zoom_start=12)

                    # Add markers for each coordinate
                    for entry in vis_data:
                        popup_str = "{" + str(entry['bedroom']) + " BHK, Rs " + str(entry['rent']) + "}"
                        # popup=f"({entry['geo']['latitude']}, {entry['geo']['longitude']})"

                        title = str(entry["title"])
                        url_link = str(entry['url'])
                        listing_id = str(entry['id'])
                        society_name = str(entry['society_name'])
                        if entry["summary_Super_Area"] == None:
                            bed_bath_sqft = "Bed/Bath: "+str(entry['bedroom'])+"/"+str(entry['bathroom'])
                        else:
                            bed_bath_sqft = "Bed/Bath/Sqft: "+str(entry['bedroom'])+"/"+str(entry['bathroom'])+"/"+str(entry["summary_Super_Area"])
                        rent = str(entry["rent"])
                        advance = str(entry["cost_security_deposit"])
                        availability = str(entry["summary_Availability"])
                        if "N/A" in society_name:
                            if entry["summary_Super_Area"] == None:
                                bed_bath = str(entry['bedroom']) + "/" + str(
                                    entry['bathroom'])
                                popup_content = f"""
                                                 <p><b>{title}</b></p><p><b>Bed/Bath: </b>{bed_bath}</p><p><b>Availability: </b>{availability} <b>Rent: </b>{rent}, <b>Advance: </b>{advance} </p><p><b>Id: </b>{listing_id}</p><a href={url_link} target="_blank"><b>Listing URL</b></a>
                                                 """
                            else:
                                bed_bath_sqft = str(entry['bedroom']) + "/" + str(
                                    entry['bathroom']) + "/" + str(entry["summary_Super_Area"])
                                popup_content = f"""
                                                 <p><b>{title}</b></p><p><b>Bed/Bath/Sqft: </b>{bed_bath_sqft}</p><p><b>Availability: </b>{availability} <b>Rent: </b>{rent}, <b>Advance: </b>{advance} </p><p><b>Id: </b>{listing_id}</p><a href={url_link} target="_blank"><b>Listing URL</b></a>
                                                 """

                        else:
                            if entry["summary_Super_Area"] == None:
                                bed_bath = str(entry['bedroom']) + "/" + str(
                                    entry['bathroom'])
                                popup_content = f"""
                                                 <p><b>{title}</b></p><p><b>Society Name: </b>{society_name} </p><p><b>Bed/Bath: </b>{bed_bath}</p><p><b>Availability: </b>{availability} <b>Rent: </b>{rent}, <b>Advance: </b>{advance} </p><p><b>id: </b>{listing_id}</p><a href={url_link} target="_blank"><b>Listing URL</b></a>
                                                 """
                            else:
                                bed_bath_sqft = str(entry['bedroom']) + "/" + str(
                                    entry['bathroom']) + "/" + str(entry["summary_Super_Area"])
                                popup_content = f"""
                                                 <p><b>{title}</b></p><p><b>Society Name: </b>{society_name} </p><p><b>Bed/Bath/Sqft: </b>{bed_bath_sqft}</p><p><b>Availability: </b>{availability} <b>Rent: </b>{rent}, <b>Advance: </b>{advance} </p><p><b>id: </b>{listing_id}</p><a href={url_link} target="_blank"><b>Listing URL</b></a>
                                                 """
                        folium.Marker(
                            location=[entry['geo_latitude'], entry['geo_longitude']],

                            popup=folium.Popup(popup_content, max_width=300)
                        ).add_to(m)

                    # Define CSS to set the map width to 100% of the viewport width
                    # Define a CSS class that captures the screen width using JavaScript
                    css = """
                    <style>
                    .screen-width {
                        display: none;
                    }
                    </style>
                    <script>
                    window.addEventListener('DOMContentLoaded', (event) => {
                        const screenWidth = window.innerWidth;
                        document.querySelector('.screen-width').innerText = screenWidth;
                    });
                    </script>
                    """

                    # Display the CSS
                    st.markdown(css, unsafe_allow_html=True)
                    # screen_width = st.markdown('<div class="screen-width"></div>', unsafe_allow_html=True)

                    # Print the screen width in Streamlit
                    # st.write(f"Screen Width: ", 0, key="screen-width")
                    folium_static(m, width=1600)
                    disp_data['url'] = disp_data['url'].apply(make_hyperlink)

                    disp_data = disp_data.fillna("N/A")
                    disp_data["balcony"] = disp_data['balcony'].replace('', 'N/A')

                    # commenting out this to experiment with sorting
                    html_table = disp_data.to_html(escape=False, index=False, render_links=True)
                    styled_html_table = html_table.replace('<th>', '<th style="font-weight: bold">')

                    # Display the HTML table in Streamlit with bold column names
                    with st.expander("Listings: ", expanded=False):
                        st.write(styled_html_table, unsafe_allow_html=True)


            else:
                st.write("No Matching Listings found")


if __name__ == "__main__":
    main()
