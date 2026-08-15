
import streamlit as st
import pandas as pd
import requests

# Base URL of the Flask backend.
# 'backend' is the container name on the shared Docker network,
# so Docker's internal DNS resolves it - no hard-coded IP addresses.
BACKEND_URL = "http://backend:7860"

st.set_page_config(page_title="SuperKart Sales Prediction", layout="centered")

# Page title
st.title("SuperKart Sales Prediction System")
st.write(
    "Enter the product and store details below to predict the total sales revenue "
    "for that product at that store."
)

st.subheader("Product Details")

# Input fields for product data
Product_Weight = st.number_input("Product Weight", min_value=0.0, value=12.66)
Product_Sugar_Content = st.selectbox("Product Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
Product_Allocated_Area = st.number_input("Product Allocated Area (share of display area)",
                                         min_value=0.0, max_value=1.0, value=0.027, format="%.3f")
Product_MRP = st.number_input("Product MRP", min_value=0.0, value=117.08)
Product_Id_char = st.selectbox("Product ID Character (FD=Food, DR=Drinks, NC=Non-Consumable)",
                               ["FD", "DR", "NC"])
Product_Type_Category = st.selectbox("Product Type Category", ["Perishables", "Non Perishables"])

st.subheader("Store Details")

# Input fields for store data
Store_Size = st.selectbox("Store Size", ["Small", "Medium", "High"])
Store_Location_City_Type = st.selectbox("Store Location City Type", ["Tier 1", "Tier 2", "Tier 3"])
Store_Type = st.selectbox("Store Type", ["Supermarket Type1", "Supermarket Type2",
                                         "Departmental Store", "Food Mart"])
Store_Age_Years = st.number_input("Store Age (Years)", min_value=0, value=16)

# Create JSON payload matching the API contract
product_data = {
    "Product_Weight": Product_Weight,
    "Product_Sugar_Content": Product_Sugar_Content,
    "Product_Allocated_Area": Product_Allocated_Area,
    "Product_MRP": Product_MRP,
    "Store_Size": Store_Size,
    "Store_Location_City_Type": Store_Location_City_Type,
    "Store_Type": Store_Type,
    "Product_Id_char": Product_Id_char,
    "Store_Age_Years": Store_Age_Years,
    "Product_Type_Category": Product_Type_Category
}

# Single (online) prediction
if st.button("Predict Sales", type="primary"):

    try:
        response = requests.post(f"{BACKEND_URL}/v1/predict", json=product_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            predicted_sales = result["Sales"]
            st.success(f"Predicted Product Store Sales Total: Rs. {predicted_sales:,.2f}")
        else:
            st.error(f"Prediction failed. Status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"Unable to connect to the prediction API: {e}")

# Batch prediction
st.divider()
st.subheader("Batch Prediction")
st.write(
    "Upload a CSV containing the same 10 feature columns to score many "
    "product-store combinations at once."
)

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:

    # Showing a preview of what was uploaded
    preview = pd.read_csv(uploaded_file)
    st.write("Preview of uploaded data:")
    st.dataframe(preview.head(), use_container_width=True)
    uploaded_file.seek(0)  # rewind so the file can be re-read for the request

    if st.button("Predict for Batch", type="primary"):

        try:
            response = requests.post(
                f"{BACKEND_URL}/v1/predictbatch",
                files={"file": uploaded_file},
                timeout=120
            )

            if response.status_code == 200:
                results = response.json()
                st.success("Predictions completed successfully!")

                # Convert the {index: prediction} response into a readable table
                results_df = pd.DataFrame(
                    {"Predicted_Sales": pd.Series(results)}
                )
                results_df.index.name = "Row"

                # Join the predictions back onto the uploaded rows
                output = preview.reset_index(drop=True).copy()
                output["Predicted_Sales"] = [results[str(i)] for i in range(len(output))]

                st.dataframe(output, use_container_width=True)

                # Let the user download the scored file
                st.download_button(
                    "Download predictions as CSV",
                    data=output.to_csv(index=False).encode("utf-8"),
                    file_name="superkart_predictions.csv",
                    mime="text/csv",
                )
            else:
                st.error(f"Prediction failed. Status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            st.error(f"Unable to connect to the prediction API: {e}")
