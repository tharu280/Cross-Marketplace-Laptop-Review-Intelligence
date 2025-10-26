import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import plotly.express as px
import json
from urllib.parse import urlencode


API_BASE_URL = "http://localhost:8000/api/v1"


def fetch_api_data(endpoint):
    """Fetches data from a GET endpoint of the backend API."""
    url = f"{API_BASE_URL}/{endpoint}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"Error: Request timed out fetching data from {endpoint}.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"Error: Could not connect to the API backend at {API_BASE_URL}. Is it running?")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return None
    except json.JSONDecodeError:

        st.error(
            f"Error decoding JSON response from {endpoint}. Response text: {response.text[:200]}...")
        return None


def post_chat_query(query, history):
    """Sends a query and history to the chat endpoint."""
    url = f"{API_BASE_URL}/chat"
    payload = {"query": query, "history": history}

    try:

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error(f"Error: Chat request timed out.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(
            f"Error: Could not connect to the API backend at {API_BASE_URL}. Is it running?")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error sending chat message: {e}")

        try:
            error_detail = response.json().get('detail', str(e))
            st.error(f"API Error Detail: {error_detail}")
        except:
            pass
        return None
    except json.JSONDecodeError:
        st.error(
            f"Error decoding chat JSON response. Response text: {response.text[:200]}...")
        return None


st.set_page_config(page_title="Laptop Insights Engine", layout="wide")
st.title("💻 Cross-Marketplace Laptop & Review Intelligence")


tab_explore, tab_reviews, tab_chat = st.tabs(
    ["Explore & Compare", "Reviews Intelligence", "Chat & Recommend"])


with tab_explore:
    st.header("Explore & Compare Laptops")

    st.sidebar.subheader("Filters")

    @st.cache_data(ttl=300)
    def get_brands():
        laptop_list = fetch_api_data("laptops")
        if laptop_list:
            return sorted(list(set(laptop['brand'] for laptop in laptop_list)))
        return []

    available_brands = get_brands()

    selected_brand = st.sidebar.selectbox("Brand", ["All"] + available_brands)
    selected_min_rating = st.sidebar.slider(
        "Minimum Rating", 0.0, 5.0, 0.0, 0.5)

    selected_availability = st.sidebar.selectbox(
        "Availability", ["All", "In Stock", "Out of Stock", "Unknown", "Check Website"])

    filter_params = {}
    if selected_brand != "All":
        filter_params['brand'] = selected_brand
    if selected_min_rating > 0.0:
        filter_params['min_rating'] = selected_min_rating

    if selected_availability != "All":
        filter_params['availability'] = selected_availability

    filtered_laptops_endpoint = f"laptops?{urlencode(filter_params)}"
    filtered_laptops = fetch_api_data(filtered_laptops_endpoint)

    if filtered_laptops is None:
        st.error("Failed to fetch laptop data from the API.")
    elif not filtered_laptops:
        st.warning("No laptops match the selected filters.")
    else:
        st.write(f"Found {len(filtered_laptops)} laptops matching criteria:")

        cols = st.columns(st.sidebar.number_input(
            "Columns:", 1, 4, 2))
        col_index = 0
        for laptop in filtered_laptops:
            container = cols[col_index % len(cols)].container(
                border=True)
            container.subheader(
                f"{laptop.get('brand','N/A')} {laptop.get('model_name','N/A')}")
            container.caption(f"SKU: {laptop.get('sku','N/A')}")
            rating = laptop.get('average_rating')
            rating_str = f"{rating:.1f}/5.0" if rating is not None else "N/A"
            container.markdown(
                f"**Rating:** {rating_str} ({laptop.get('review_count', 0)} reviews)")
            container.markdown(
                f"**Availability:** {laptop.get('availability', 'N/A')}")

            if container.button("Show Details", key=f"details_{laptop['sku']}"):

                container.subheader("Price History")
                price_history = fetch_api_data(
                    f"laptops/{laptop['sku']}/price-history")
                if price_history:
                    try:
                        price_df = pd.DataFrame(price_history)
                        price_df['date'] = pd.to_datetime(price_df['date'])
                        price_df = price_df.sort_values('date')
                        fig_price = px.line(price_df, x='date', y='price', title="Price Trend", markers=True,
                                            hover_data=['vendor_name', 'promo_badges'])
                        fig_price.update_layout(
                            xaxis_title='Date', yaxis_title=f"Price ({laptop.get('currency', '')})")
                        container.plotly_chart(
                            fig_price, use_container_width=True)
                    except Exception as e:
                        container.error(f"Error processing price data: {e}")
                        container.json(price_history)  # Show raw data on error
                else:
                    container.write("No price history available or API error.")

                container.subheader("Recent Reviews")
                reviews = fetch_api_data(f"laptops/{laptop['sku']}/reviews")
                if reviews:
                    for review in reviews[:3]:
                        container.markdown(
                            f"**Rating: {review['rating']}/5** ({review['date']}) - _{review.get('source', 'N/A')}_")
                        container.write(
                            f"> {review.get('review_text', 'No text provided.')}")
                        container.divider()
                else:
                    container.write("No reviews available or API error.")

                pdf_map = {
                    "ThinkPad E14 Gen 5 (Intel)": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_E14_Gen_5_Intel/ThinkPad_E14_Gen_5_Intel_Spec.PDF",
                    "Lenovo ThinkPad E14 Gen 5 (AMD)": "https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_E14_Gen_5_AMD/ThinkPad_E14_Gen_5_AMD_Spec.pdf",
                    "HP ProBook 450 G10 — Datasheet": "https://h20195.www2.hp.com/v2/GetPDF.aspx/c08504822.pdf",
                    "HP ProBook 440 14 inch G11 Notebook PC": "https://h20195.www2.hp.com/v2/getpdf.aspx/c08947328.pdf"
                }
                pdf_url = pdf_map.get(laptop['sku'])
                if pdf_url:
                    container.markdown(
                        f"[View Full Spec Sheet (PDF)]({pdf_url})", unsafe_allow_html=True)

            col_index += 1


with tab_reviews:
    st.header("Reviews Intelligence")

    @st.cache_data(ttl=300)
    def get_sku_list():
        laptop_list = fetch_api_data("laptops")
        if laptop_list:
            return [laptop['sku'] for laptop in laptop_list]
        return []

    skus = get_sku_list()

    if not skus:
        st.warning("Laptop data not available to select SKU. Is the API running?")
    else:
        selected_sku_reviews = st.selectbox(
            "Select Laptop SKU for Review Analysis", skus, key="review_sku_select")

        if selected_sku_reviews:
            st.subheader(f"Analysis for: {selected_sku_reviews}")

            @st.cache_data(ttl=60)
            def get_reviews_for_analysis(sku):
                return fetch_api_data(f"laptops/{sku}/reviews")

            reviews_data = get_reviews_for_analysis(selected_sku_reviews)

            if reviews_data is None:
                st.error("Failed to fetch review data from the API.")
            elif not reviews_data:
                st.warning("No reviews found for this SKU in the database.")
            else:
                try:
                    reviews_df = pd.DataFrame(reviews_data)
                    # Convert types safely
                    reviews_df['date'] = pd.to_datetime(
                        reviews_df['date'], errors='coerce')
                    reviews_df['rating'] = pd.to_numeric(
                        reviews_df['rating'], errors='coerce')
                    # Drop rows where conversion failed
                    reviews_df = reviews_df.dropna(subset=['date', 'rating'])

                    if reviews_df.empty:
                        st.warning(
                            "No valid review data found after processing.")
                    else:
                        reviews_df['year_month'] = reviews_df['date'].dt.to_period(
                            'M').astype(str)

                        st.markdown("#### Review Volume Over Time")
                        volume_trend = reviews_df.groupby(
                            'year_month').size().reset_index(name='count')
                        volume_trend = volume_trend.sort_values('year_month')
                        if not volume_trend.empty:
                            fig_volume = px.bar(
                                volume_trend, x='year_month', y='count', title="Number of Reviews per Month")
                            fig_volume.update_layout(
                                xaxis_title='Month', yaxis_title='Number of Reviews')
                            st.plotly_chart(
                                fig_volume, use_container_width=True)
                        else:
                            st.write("Not enough data for volume trend.")

                        st.markdown("#### Rating Distribution")
                        rating_dist = reviews_df['rating'].value_counts(
                        ).reset_index(name='count')
                        rating_dist.columns = ['rating', 'count']
                        rating_dist = rating_dist.sort_values(
                            'rating')  # Sort by rating
                        if not rating_dist.empty:
                            fig_rating_dist = px.bar(
                                rating_dist, x='rating', y='count', title="Distribution of Ratings")
                            fig_rating_dist.update_layout(
                                xaxis_title='Rating (Stars)', yaxis_title='Number of Reviews')
                            st.plotly_chart(fig_rating_dist,
                                            use_container_width=True)
                        else:
                            st.write(
                                "Not enough data for rating distribution.")

                        st.markdown("#### Average Rating Over Time")
                        avg_rating_trend = reviews_df.groupby(
                            'year_month')['rating'].mean().reset_index(name='average_rating')
                        avg_rating_trend = avg_rating_trend.sort_values(
                            'year_month')
                        if len(avg_rating_trend) > 1:  # Need at least 2 points for a line chart
                            fig_avg_rating = px.line(
                                avg_rating_trend, x='year_month', y='average_rating', title="Average Rating per Month", markers=True)
                            fig_avg_rating.update_layout(
                                xaxis_title='Month', yaxis_title='Average Rating', yaxis=dict(range=[1, 5]))
                            st.plotly_chart(
                                fig_avg_rating, use_container_width=True)
                        else:
                            st.write(
                                "Not enough data points for average rating trend.")

                except Exception as e:
                    st.error(f"Error processing review data for plots: {e}")
                    st.write("Raw Review Data:")
                    st.json(reviews_data)  # Show raw data on error


with tab_chat:
    st.header("Chat & Recommend")

    if "messages" not in st.session_state:

        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about specs, prices, or request recommendations..."):

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        api_history = st.session_state.messages[:-1]
        api_history_formatted = [{"role": msg["role"], "content": msg["content"]}
                                 for msg in api_history[-5:]]  # Keep last 5

        with st.spinner("Thinking..."):
            response_data = post_chat_query(prompt, api_history_formatted)

        if response_data and "llm_answer" in response_data:
            model_response = response_data["llm_answer"]

            import re
            citations_found = re.findall(
                r'\[(\d+(?:,\s*\d+)*)\]', model_response)
            citations = set()
            for group in citations_found:
                nums = [int(n.strip()) for n in group.split(',')]
                citations.update(nums)
            citations_list = sorted(list(citations))

            response_message = {"role": "model", "content": model_response}
            st.session_state.messages.append(response_message)
            with st.chat_message("model"):
                st.markdown(model_response)

                if citations_list:
                    st.caption(
                        f"Cited Sources: {', '.join(map(str, citations_list))}")

        else:
            # Display error if API call failed
            st.error(
                "Failed to get response from the chatbot. Please check if the backend API is running and responding correctly.")
