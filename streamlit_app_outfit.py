import streamlit as st
import pandas as pd

st.title("Pilih Outfitmu :shirt:")

cnx= st.connection("snowflake")
session = cnx.session()

# Get a list of colors for the dropdown selector
table_colors = session.sql("SELECT color_or_style FROM catalog_for_website")
pd_colors = table_colors.to_pandas()
color_options = pd_colors['COLOR_OR_STYLE'].tolist()  # Convert to list for selectbox

# Drop-down selector for color
option = st.selectbox('Pick a sweatsuit color or style:', color_options)

if option:
    # Get product data based on the selected color
    table_prod_data = session.sql("SELECT file_name, price, size_list, qty, upsell_product_desc, file_url FROM catalog_for_website WHERE color_or_style = ?", (option,))
    pd_prod_data = table_prod_data.to_pandas()

    # Extract product details
    price = '$' + str(pd_prod_data['PRICE'].iloc[0]) + '0'
    file_name = pd_prod_data['FILE_NAME'].iloc[0]
    size_list = pd_prod_data['SIZE_LIST'].iloc[0]
    upsell = pd_prod_data['UPSELL_PRODUCT_DESC'].iloc[0]
    url = pd_prod_data['FILE_URL'].iloc[0]

    # Display product image and price
    product_caption = 'Our warm, comfortable, ' + option + ' sweatsuit!'
    st.image(image=url, width=400, caption=product_caption)
    st.markdown('**Price:** ' + price)

    # Get available sizes
    size_list = session.sql("SELECT DISTINCT size FROM zenas_athleisure_db.products.quantity ORDER BY size ASC")
    pd_size = size_list.to_pandas()
    size_options = pd_size['SIZE'].tolist()  # Convert to list for selectbox

    size_option = st.selectbox('Pick a size:', size_options)

    if size_option:
        # Get quantity based on the selected color and size
        table_prod_data_qty = session.sql("SELECT qty FROM zenas_athleisure_db.products.quantity WHERE color = ? AND size = ?", (option, size_option))
        pd_prod_data_qty = table_prod_data_qty.to_pandas()

        if not pd_prod_data_qty.empty:
            qty = str(pd_prod_data_qty['QTY'].iloc[0])
            st.markdown('**Quantity left:** ' + qty)
            
            # Input quantity to buy
            user_qty = st.number_input("Enter quantity to buy:", min_value=1, value=1)
            user_name = st.text_input("Enter your name:")

            buy_button = st.button("Buy")
            if buy_button:
                if int(qty) >= user_qty:
                    try:
                        # Update stock
                        update_query = """
                        UPDATE zenas_athleisure_db.products.quantity 
                        SET qty = qty - ? 
                        WHERE color = ? AND size = ?;
                        """
                        session.sql(update_query, (user_qty, option, size_option)).collect()

                        # Query to get the updated quantity
                        qty_left_query = session.sql("SELECT qty FROM zenas_athleisure_db.products.quantity WHERE color = ? AND size = ?", (option, size_option))
                        qty_left_df = qty_left_query.to_pandas()
                        qty_left = str(qty_left_df['QTY'].iloc[0]) if not qty_left_df.empty else '0'

                        insert_query = """
                        insert into zenas_athleisure_db.products.orders 
                        (name, color, size, qty)
                        values (?,?,?,?);
                        """
                        session.sql(insert_query, (user_name, option, size_option, int(user_qty))).collect()
                        st.success(f'Purchase successful! Quantity left: {qty_left}', icon="✅")
                        

                    except Exception as e:
                        st.error(f"An error occurred while updating the stock: {e}")
                else:
                    st.error('Purchase unsuccessful! Quantity not enough.')
        else:
            st.error('No data available for the selected color and size.')
